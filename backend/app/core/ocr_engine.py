import os
from typing import Optional
from PIL import Image


class OCRProcessor:
    def __init__(self):
        self._reader = None

    def _get_reader(self):
        if self._reader is None:
            try:
                import easyocr
                self._reader = easyocr.Reader(["en"], gpu=False)
            except Exception as e:
                print(f"EasyOCR init failed: {e}")
                self._reader = None
        return self._reader

    def process_image(self, image_path: str) -> str:
        reader = self._get_reader()
        if reader:
            try:
                results = reader.readtext(image_path)
                return "\n".join([r[1] for r in results])
            except Exception as e:
                print(f"OCR error: {e}")

        try:
            from PIL import Image
            import pytesseract
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text.strip()
        except Exception as e:
            print(f"Tesseract fallback error: {e}")

        return ""

    def process_pdf_images(self, pdf_path: str) -> str:
        try:
            import fitz
            doc = fitz.open(pdf_path)
            all_text = []
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=300)
                img_path = f"/tmp/pdf_page_{page_num}.png"
                pix.save(img_path)
                text = self.process_image(img_path)
                all_text.append(text)
                if os.path.exists(img_path):
                    os.remove(img_path)
            doc.close()
            return "\n\n".join(all_text)
        except Exception as e:
            print(f"PDF OCR error: {e}")
            return ""
