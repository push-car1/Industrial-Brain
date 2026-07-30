from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.knowledge_graph.graph_queries import GraphQueries


class LessonsLearnedAgent:
    def __init__(self, graph_queries: GraphQueries):
        self.graph_queries = graph_queries
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            temperature=0.1,
            num_predict=512,
            num_ctx=2048,
            timeout=120,
        )

    def run(self, query: str) -> dict:
        query_lower = query.lower()

        context_parts = []
        sources = []

        if "near" in query_lower or "miss" in query_lower or "incident" in query_lower or "pattern" in query_lower:
            results = self.graph_queries.search("incident", limit=10)
            for r in results:
                name = r.get("name", "")
                if name:
                    context_parts.append(f"- {name}")
                    sources.append(r.get("id", ""))

            results = self.graph_queries.search("near miss", limit=5)
            for r in results:
                name = r.get("name", "")
                if name and name not in context_parts:
                    context_parts.append(f"- {name}")
                    sources.append(r.get("id", ""))

        from app.utils.helpers import EQUIPMENT_TYPE_KEYWORDS
        for kw in EQUIPMENT_TYPE_KEYWORDS:
            if kw in query_lower:
                results = self.graph_queries.search(kw, limit=3)
                for r in results:
                    equip_id = r.get("id", "")
                    incidents = self.graph_queries.get_incidents_for_equipment(equip_id)
                    for inc in incidents[:3]:
                        context_parts.append(f"- [{inc.get('date', '')}] {inc.get('description', '')} ({inc.get('severity', '')})")
                        sources.append(inc.get("incident_id", ""))
                break

        if not context_parts:
            context_parts.append("No incident patterns found in the knowledge graph database. Ingest incident reports to enable pattern analysis.")

        context = "\n".join(context_parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a lessons-learned and failure pattern intelligence agent.
Analyze incident data, near-miss reports, and failure records to:

1. Identify recurring patterns across different incidents
2. Highlight common root causes
3. Suggest preventive measures
4. Prioritize risks based on frequency and severity

Look for patterns even across different equipment types. Focus on actionable insights."""),
            ("human", "Query: {query}\n\nIncident Data:\n{context}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"query": query, "context": context})

        return {
            "answer": response.content if hasattr(response, "content") else str(response),
            "sources": sources,
        }
