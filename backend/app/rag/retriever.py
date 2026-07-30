from typing import Optional
from app.rag.vector_store import VectorStore
from app.knowledge_graph.graph_queries import GraphQueries
from app.config import settings


class HybridRetriever:
    def __init__(self, vector_store: VectorStore, graph_queries: GraphQueries):
        self.vector_store = vector_store
        self.graph_queries = graph_queries
        self.top_k = settings.retriever_top_k

    def retrieve(self, query: str, top_k: Optional[int] = None) -> dict:
        k = top_k or self.top_k
        vector_results = self.vector_store.similarity_search(query, k=k)
        graph_results = self.graph_queries.search(query, limit=k)

        equipment_mentions = []
        query_lower = query.lower()
        for item in graph_results:
            name = (item.get("name") or "").lower()
            if any(word in query_lower for word in name.split()):
                equipment_mentions.append(item)
            elif any(word in name for word in query_lower.split()):
                equipment_mentions.append(item)

        return {
            "vector_results": vector_results,
            "graph_results": graph_results,
            "equipment_mentions": equipment_mentions[:5],
        }

    def _include_all_data(self, query: str) -> bool:
        q = query.lower()
        keywords = ["list all", "list every", "all equipment", "all the equipment",
                     "show all", "every equipment", "what equipment", "equipment list",
                     "all assets", "complete list", "full list",
                     "compliance", "regulation", "regulatory", "oisd", "standard",
                     "maintenance", "work order", "incident"]
        return any(k in q for k in keywords)

    def retrieve_with_context(self, query: str, top_k: Optional[int] = None) -> str:
        results = self.retrieve(query, top_k)
        context_parts = []

        if results["vector_results"]:
            context_parts.append("=== DOCUMENT EXCERPTS ===")
            for i, r in enumerate(results["vector_results"], 1):
                source = r["metadata"].get("source", "Unknown")
                text = r["text"][:400]
                context_parts.append(f"[{i}] (Source: {source})\n{text}\n")

        if results["equipment_mentions"]:
            context_parts.append("\n=== RELATED EQUIPMENT ===")
            for eq in results["equipment_mentions"]:
                context_parts.append(f"- {eq.get('name', '')} ({eq.get('label', '')})")

        if results["graph_results"]:
            context_parts.append("\n=== KNOWLEDGE GRAPH RESULTS ===")
            for r in results["graph_results"][:8]:
                context_parts.append(f"- {r.get('label', '')}: {r.get('name', '')}")

        if self._include_all_data(query):
            all_eq = self.graph_queries.get_all_equipment()
            if all_eq:
                context_parts.append(f"\n=== EQUIPMENT ({len(all_eq)} total) ===")
                for eq in all_eq[:15]:
                    loc = f" at {eq['location']}" if eq.get("location") else ""
                    crit = f" [{eq['criticality']}]" if eq.get("criticality") else ""
                    context_parts.append(f"- {eq['name']} ({eq['id']}){loc}{crit}")
                if len(all_eq) > 15:
                    context_parts.append(f"... and {len(all_eq) - 15} more")
            all_reg = self.graph_queries.get_all_regulations()
            if all_reg:
                context_parts.append(f"\n=== REGULATIONS ({len(all_reg)} total) ===")
                for reg in all_reg[:10]:
                    context_parts.append(f"- {reg['title']} ({reg.get('authority', '')})")

        if not context_parts:
            context_parts.append("No data found in the knowledge base.")

        return "\n".join(context_parts)