import os
import pandas as pd
from typing import Optional
from app.utils.helpers import (
    is_pdf_file, is_image_file, is_csv_file,
    chunk_text, generate_id
)
from app.core.ocr_engine import OCRProcessor


class DocumentProcessor:
    def __init__(self, chunk_size: int = 512, chunk_overlap: int = 64):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.ocr = OCRProcessor()

    def process(self, file_path: str, doc_id: str) -> dict:
        ext = os.path.splitext(file_path)[1].lower()
        if is_pdf_file(file_path):
            return self._process_pdf(file_path, doc_id)
        elif is_image_file(file_path):
            return self._process_image(file_path, doc_id)
        elif is_csv_file(file_path):
            return self._process_csv(file_path, doc_id)
        elif ext in [".txt", ".md"]:
            return self._process_text(file_path, doc_id)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def _process_pdf(self, file_path: str, doc_id: str) -> dict:
        import fitz
        doc = fitz.open(file_path)
        pages_text = []
        page_count = doc.page_count
        for page_num in range(page_count):
            page = doc.load_page(page_num)
            text = page.get_text()
            if text.strip():
                pages_text.append(text)
        doc.close()

        full_text = "\n\n".join(pages_text)
        if not full_text.strip():
            full_text = self.ocr.process_pdf_images(file_path)

        chunks = chunk_text(full_text, self.chunk_size, self.chunk_overlap)
        return {
            "doc_id": doc_id,
            "text": full_text,
            "chunks": chunks,
            "page_count": page_count,
            "file_type": "pdf",
        }

    def _process_image(self, file_path: str, doc_id: str) -> dict:
        text = self.ocr.process_image(file_path)
        chunks = chunk_text(text, self.chunk_size, self.chunk_overlap)
        return {
            "doc_id": doc_id,
            "text": text,
            "chunks": chunks,
            "page_count": 1,
            "file_type": "image",
        }

    def _process_csv(self, file_path: str, doc_id: str) -> dict:
        df = pd.read_csv(file_path)
        text_lines = []
        for _, row in df.iterrows():
            row_text = " | ".join(
                f"{col}: {val}" for col, val in row.items() if pd.notna(val)
            )
            text_lines.append(row_text)
        full_text = "\n".join(text_lines)
        chunks = chunk_text(full_text, self.chunk_size, self.chunk_overlap)
        return {
            "doc_id": doc_id,
            "text": full_text,
            "chunks": chunks,
            "page_count": len(df),
            "file_type": "csv",
        }

    def _process_text(self, file_path: str, doc_id: str) -> dict:
        with open(file_path, "r", encoding="utf-8") as f:
            full_text = f.read()
        chunks = chunk_text(full_text, self.chunk_size, self.chunk_overlap)
        return {
            "doc_id": doc_id,
            "text": full_text,
            "chunks": chunks,
            "page_count": 1,
            "file_type": "text",
        }
