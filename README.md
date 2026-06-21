# ComfyUI Gonza Translate Lite

Custom node บาง ๆ สำหรับแปล prompt ไทยเป็นอังกฤษใน ComfyUI โดยไม่ต้องพึ่ง `ComfyUI_NYJY` หรือ Google Translate

## จุดเด่น

- ใช้ local model ล้วน
- default เป็น `OPUS-MT / CPU` เพื่อไม่กิน VRAM ของ Flux
- แปลเฉพาะ chunk ที่มีอักษรไทย ทำให้ tag อังกฤษเช่น `rating_explicit` หรือ `source_pony` ผ่านตรง
- ใช้ node type เป็น `Translate` เพื่อแทน workflow เดิมได้ง่าย

## ทำไมไม่ใช้ Gemma

Gemma ตัวเล็กใช้ได้ถ้าจะเอา general-purpose LLM แต่สำหรับงานนี้มันไม่คุ้ม:

- model ใหญ่กว่า translator เฉพาะทาง
- เดา/แต่งคำเพิ่มได้ง่ายกว่า
- prompt tag style แบบ ComfyUI มักแปลเพี้ยนกว่าพวก MarianMT / NLLB

ถ้าจะเอาบางและนิ่ง ให้เริ่มที่ `Helsinki-NLP/opus-mt-th-en` ก่อน แล้วค่อยขยับไป `NLLB-600M` ถ้าอยากลองคุณภาพอีกแบบ

## ติดตั้ง

คัดลอกโฟลเดอร์นี้ไปไว้ใน `ComfyUI/custom_nodes/` แล้วติดตั้ง requirements:

```bash
cd /path/to/ComfyUI
pip install -r custom_nodes/ComfyUI_Gonza_Translate_Lite/requirements.txt
```

รีสตาร์ต ComfyUI จากนั้น node `Translate` เดิมใน workflow จะใช้ local translator ตัวนี้แทนได้

## การใช้งาน

- `OPUS-MT / CPU`: เบาสุด เหมาะเป็นค่าเริ่มต้น
- `OPUS-MT / CUDA`: เร็วขึ้น แต่จะกิน VRAM เพิ่ม
- `NLLB-600M / CPU`: อาจแปลบางวลีดีขึ้น แต่หนักกว่า
- `NLLB-600M / CUDA`: เร็วและหนักสุดในตัวเลือกนี้

รันครั้งแรกจะดาวน์โหลด model จาก Hugging Face เข้ามาใน cache ของเครื่องก่อน

## Compatibility

- รองรับ workflow เก่าที่เคยใช้ค่า `泰语`, `英语`, และ `Google`
- ถ้า prompt เป็นอังกฤษล้วน node จะส่งผ่านข้อความเดิมโดยไม่แปล
