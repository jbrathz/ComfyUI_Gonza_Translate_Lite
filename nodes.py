import re
import threading
from typing import Dict, List, Tuple


_MODEL_CACHE: Dict[Tuple[str, str], Tuple[object, object, str]] = {}
_MODEL_LOCK = threading.Lock()
_THAI_RE = re.compile(r"[\u0E00-\u0E7F]")
_WHITESPACE_RE = re.compile(r"\s+")


def _contains_thai(text: str) -> bool:
    return bool(_THAI_RE.search(text or ""))


def _normalize_prompt(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", (text or "")).strip(" ,\n\t")


def _split_prompt(text: str) -> List[str]:
    normalized = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    parts = re.split(r"[\n,]+", normalized)
    return [part.strip() for part in parts if part and part.strip()]


def _parse_engine(engine: str) -> Tuple[str, str]:
    mapping = {
        "OPUS-MT / CPU": ("Helsinki-NLP/opus-mt-th-en", "cpu"),
        "OPUS-MT / CUDA": ("Helsinki-NLP/opus-mt-th-en", "cuda"),
        "NLLB-600M / CPU": ("facebook/nllb-200-distilled-600M", "cpu"),
        "NLLB-600M / CUDA": ("facebook/nllb-200-distilled-600M", "cuda"),
        "Google": ("Helsinki-NLP/opus-mt-th-en", "cpu"),
    }
    return mapping.get(engine, mapping["OPUS-MT / CPU"])


def _get_model(model_name: str, device_name: str):
    with _MODEL_LOCK:
        cached = _MODEL_CACHE.get((model_name, device_name))
        if cached is not None:
            return cached

        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        resolved_device = device_name
        if device_name == "cuda" and not torch.cuda.is_available():
            resolved_device = "cpu"

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        if resolved_device == "cuda":
            model = model.to("cuda")
        model.eval()

        cached = (tokenizer, model, resolved_device)
        _MODEL_CACHE[(model_name, device_name)] = cached
        return cached


def _translate_chunks_opus(chunks: List[str], model_name: str, device_name: str) -> List[str]:
    if not chunks:
        return []

    import torch

    tokenizer, model, resolved_device = _get_model(model_name, device_name)
    inputs = tokenizer(chunks, return_tensors="pt", padding=True, truncation=True)
    if resolved_device == "cuda":
        inputs = {key: value.to("cuda") for key, value in inputs.items()}

    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            max_new_tokens=96,
            num_beams=4,
        )

    outputs = tokenizer.batch_decode(generated, skip_special_tokens=True)
    return [_normalize_prompt(output) for output in outputs]


def _translate_chunks_nllb(chunks: List[str], model_name: str, device_name: str) -> List[str]:
    if not chunks:
        return []

    import torch

    tokenizer, model, resolved_device = _get_model(model_name, device_name)
    tokenizer.src_lang = "tha_Thai"
    inputs = tokenizer(chunks, return_tensors="pt", padding=True, truncation=True)
    if resolved_device == "cuda":
        inputs = {key: value.to("cuda") for key, value in inputs.items()}

    forced_bos_token_id = tokenizer.convert_tokens_to_ids("eng_Latn")

    with torch.inference_mode():
        generated = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos_token_id,
            max_new_tokens=96,
            num_beams=4,
        )

    outputs = tokenizer.batch_decode(generated, skip_special_tokens=True)
    return [_normalize_prompt(output) for output in outputs]


def _translate_text(text: str, engine: str) -> str:
    prompt = _normalize_prompt(text)
    if not prompt:
        return ""

    chunks = _split_prompt(prompt)
    if not chunks:
        return prompt

    to_translate = []
    thai_indexes = []
    result = chunks[:]

    for index, chunk in enumerate(chunks):
        if _contains_thai(chunk):
            thai_indexes.append(index)
            to_translate.append(chunk)

    if not to_translate:
        return ", ".join(chunks)

    model_name, device_name = _parse_engine(engine)
    if model_name.startswith("facebook/"):
        translated = _translate_chunks_nllb(to_translate, model_name, device_name)
    else:
        translated = _translate_chunks_opus(to_translate, model_name, device_name)

    for index, translated_chunk in zip(thai_indexes, translated):
        result[index] = translated_chunk or chunks[index]

    return ", ".join(_normalize_prompt(chunk) for chunk in result if _normalize_prompt(chunk))


class TranslateLiteNode:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "from_lang": (["Thai", "泰语"], {"default": "Thai"}),
                "to_lang": (["English", "英语"], {"default": "English"}),
                "text": ("STRING", {"multiline": True, "default": ""}),
                "engine": (
                    [
                        "OPUS-MT / CPU",
                        "OPUS-MT / CUDA",
                        "NLLB-600M / CPU",
                        "NLLB-600M / CUDA",
                        "Google",
                    ],
                    {"default": "OPUS-MT / CPU"},
                ),
            }
        }

    RETURN_TYPES = ("STRING", "CONDITIONING")
    RETURN_NAMES = ("STRING", "CONDITIONING")
    FUNCTION = "translate"
    CATEGORY = "ThaiFlux Flow/Prompt"

    def translate(self, from_lang: str, to_lang: str, text: str, engine: str):
        translated = _translate_text(text, engine)
        return (translated, [])


NODE_CLASS_MAPPINGS = {
    "Translate": TranslateLiteNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Translate": "Translate TH→EN (Local Lite)",
}
