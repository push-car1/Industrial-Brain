import os
import json
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings
from app.rag.embeddings import get_embeddings


class VectorStore:
    def __init__(self):
        persist_dir = settings.chroma_persist_dir
        os.makedirs(persist_dir, exist_ok=True)

        self.client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = settings.chroma_collection_name
        self._collection = None
        self.embeddings = get_embeddings()

    @property
    def collection(self):
        if self._collection is None:
            try:
                self._collection = self.client.get_collection(self.collection_name)
            except Exception:
                self._collection = self.client.create_collection(
                    self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    def add_document(self, doc_id: str, chunks: list[str], metadata: Optional[dict] = None):
        if not chunks:
            return

        embeddings = self.embeddings.embed_documents(chunks)
        ids = [f"{doc_id}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "doc_id": doc_id,
                "chunk_index": i,
                "source": (metadata or {}).get("filename", ""),
                "doc_type": (metadata or {}).get("doc_type", ""),
            }
            for i in range(len(chunks))
        ]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

    def similarity_search(self, query: str, k: int = 5) -> list[dict]:
        query_embedding = self.embeddings.embed_query(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": 1.0 - (results["distances"][0][i] if results["distances"] else 0),
                })
        return formatted

    def delete_document(self, doc_id: str):
        existing = self.collection.get(
            where={"doc_id": doc_id}
        )
        if existing and existing["ids"]:
            self.collection.delete(ids=existing["ids"])

    def get_document_count(self) -> int:
        existing = self.collection.get()
        if existing and existing["metadatas"]:
            doc_ids = set(m["doc_id"] for m in existing["metadatas"])
            return len(doc_ids)
        return 0

    def get_chunk_count(self) -> int:
        existing = self.collection.get()
        return len(existing["ids"]) if existing and existing["ids"] else 0
