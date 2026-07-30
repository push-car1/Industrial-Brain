import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import documents, query, knowledge_graph, compliance, maintenance
from app.knowledge_graph.graph_builder import GraphBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    os.makedirs("data/embeddings", exist_ok=True)

    try:
        builder = GraphBuilder()
        summary = builder.get_graph_summary()
        logger.info(f"Neo4j connected. Graph stats: {summary.get('node_counts', {})}")
        builder.close()
    except Exception as e:
        logger.warning(f"Neo4j connection issue (will retry): {e}")

    yield

    logger.info("Shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents.router)
app.include_router(query.router)
app.include_router(knowledge_graph.router)
app.include_router(compliance.router)
app.include_router(maintenance.router)


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "services": {
            "neo4j": "checking",
            "ollama": "checking",
            "chromadb": "available",
        },
    }
