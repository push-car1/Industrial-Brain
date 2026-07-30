import os
import uuid
import shutil
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.config import settings
from app.core.document_processor import DocumentProcessor
from app.core.entity_extractor import EntityExtractor
from app.knowledge_graph.graph_builder import GraphBuilder
from app.knowledge_graph.models import ExtractedEntities
from app.rag.vector_store import VectorStore
from app.utils.helpers import generate_id

router = APIRouter(prefix="/api/documents", tags=["documents"])

doc_processor = DocumentProcessor(
    chunk_size=settings.max_chunk_size,
    chunk_overlap=settings.chunk_overlap,
)


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(400, f"File type {ext} not allowed. Supported: {settings.allowed_extensions}")

    doc_id = generate_id("doc")
    upload_dir = os.path.join("data", "processed")
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, f"{doc_id}{ext}")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        processed = doc_processor.process(file_path, doc_id)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(500, f"Document processing failed: {str(e)}")

    try:
        extractor = EntityExtractor()
        entities = extractor.extract_all(
            processed["text"], doc_id, file.filename, processed["file_type"]
        )
    except Exception as e:
        entities = ExtractedEntities(doc_id=doc_id)
        print(f"Entity extraction failed: {e}")

    try:
        builder = GraphBuilder()
        builder.insert_entities(entities)
        builder.close()
    except Exception as e:
        print(f"Graph insertion failed: {e}")

    try:
        vector_store = VectorStore()
        vector_store.add_document(
            doc_id,
            processed["chunks"],
            {"filename": file.filename, "doc_type": "GENERAL"},
        )
    except Exception as e:
        print(f"Vector store insertion failed: {e}")

    entity_count = (
        len(entities.equipment) + len(entities.regulations) +
        len(entities.personnel) + len(entities.incidents)
    )

    return {
        "id": doc_id,
        "filename": file.filename,
        "file_type": processed["file_type"],
        "page_count": processed["page_count"],
        "chunk_count": len(processed["chunks"]),
        "entity_count": entity_count,
        "status": "success",
        "message": f"Processed {processed['page_count']} pages, extracted {entity_count} entities",
    }


@router.get("/")
async def list_documents():
    vector_store = VectorStore()
    builder = GraphBuilder()
    summary = builder.get_graph_summary()
    builder.close()

    docs = summary.get("recent_documents", [])
    return {
        "documents": [
            {
                "id": f"doc_{i}",
                "filename": d.get("name", ""),
                "file_type": d.get("type", ""),
                "upload_date": "",
                "status": "processed",
                "entity_count": 0,
            }
            for i, d in enumerate(docs)
        ],
        "total_chunks": vector_store.get_chunk_count(),
    }


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    vector_store = VectorStore()
    vector_store.delete_document(doc_id)
    return {"status": "deleted", "id": doc_id}
