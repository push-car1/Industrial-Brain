import uuid
import hashlib
import os
from typing import Optional


def generate_id(prefix: str = "") -> str:
    uid = str(uuid.uuid4())[:8]
    return f"{prefix}_{uid}" if prefix else uid


def generate_file_hash(file_path: str) -> str:
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()[:16]


def ensure_dir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower()


def is_image_file(filename: str) -> bool:
    ext = get_file_extension(filename)
    return ext in [".png", ".jpg", ".jpeg", ".tiff", ".bmp"]


def is_pdf_file(filename: str) -> bool:
    return get_file_extension(filename) == ".pdf"


def is_csv_file(filename: str) -> bool:
    return get_file_extension(filename) == ".csv"


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[str]:
    if not text:
        return []
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


EQUIPMENT_TYPE_KEYWORDS = {
    "pump", "compressor", "turbine", "heat exchanger", "heater", "boiler",
    "tank", "vessel", "reactor", "column", "valve", "pipe", "piping",
    "motor", "generator", "conveyor", "crusher", "mill", "grinder",
    "cooling tower", "chiller", "fan", "blower", "filter", "separator",
    "transformer", "switchgear", "breaker", "panel", "controller",
    "sensor", "transmitter", "gauge", "meter", "analyzer",
    "dryer", "kiln", "furnace", "oven", "condenser", "evaporator",
}

DOCUMENT_TYPE_KEYWORDS = {
    "standard operating procedure": "SOP",
    "sop": "SOP",
    "maintenance manual": "MAINTENANCE_MANUAL",
    "safety procedure": "SAFETY_PROCEDURE",
    "incident report": "INCIDENT_REPORT",
    "inspection record": "INSPECTION_RECORD",
    "permit": "PERMIT",
    "work order": "WORK_ORDER",
    "regulatory": "REGULATORY_DOCUMENT",
    "compliance": "REGULATORY_DOCUMENT",
    "training": "TRAINING_MATERIAL",
    "engineering drawing": "ENGINEERING_DRAWING",
    "p&id": "ENGINEERING_DRAWING",
    "technical specification": "TECHNICAL_SPEC",
    "datasheet": "TECHNICAL_SPEC",
}

REGULATORY_KEYWORDS = {
    "oisd": "OISD",
    "factory act": "FACTORY_ACT",
    "dgms": "DGMS",
    "peso": "PESO",
    "cpcb": "CPCB",
    "bis": "BIS",
    "iso ": "ISO",
    "bureau of indian standards": "BIS",
    "central pollution control board": "CPCB",
    "director general of mines safety": "DGMS",
    "petroleum and explosives safety organization": "PESO",
}
