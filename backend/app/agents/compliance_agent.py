from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.knowledge_graph.graph_queries import GraphQueries


REGULATORY_FRAMEWORKS = {
    "OISD": {
        "name": "Oil Industry Safety Directorate",
        "standards": ["OISD-116", "OISD-118", "OISD-129", "OISD-140", "OISD-150"],
    },
    "FACTORY_ACT": {
        "name": "Factories Act, 1948",
        "standards": ["Section 21", "Section 22", "Section 23", "Section 28", "Section 36", "Section 37", "Section 38"],
    },
    "DGMS": {
        "name": "Directorate General of Mines Safety",
        "standards": ["DGMS Circular 1", "DGMS Technical Instruction"],
    },
    "PESO": {
        "name": "Petroleum and Explosives Safety Organization",
        "standards": ["SMPV Rules", "Gas Cylinder Rules", "Petroleum Rules"],
    },
}


class ComplianceAgent:
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

        framework = None
        for key in REGULATORY_FRAMEWORKS:
            if key.lower() in query_lower or REGULATORY_FRAMEWORKS[key]["name"].lower() in query_lower:
                framework = key
                break

        context_parts = []
        sources = []

        if framework:
            regs = self.graph_queries.search(framework, limit=5)
            if regs:
                context_parts.append(f"Regulations found for {REGULATORY_FRAMEWORKS[framework]['name']}:")
                for r in regs:
                    context_parts.append(f"- {r.get('name', '')}")
                    sources.append(r.get("id", ""))

        results = self.graph_queries.search("regulation", limit=5)
        for r in results:
            name = r.get("name", "")
            if name not in context_parts:
                context_parts.append(f"Related: {name}")
                sources.append(r.get("id", ""))

        context = "\n".join(context_parts) if context_parts else "No specific regulatory data found in the knowledge graph."

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a regulatory compliance intelligence agent for industrial operations.
Analyze the query against available regulatory frameworks and provide:

1. Which regulations are relevant to this query
2. Key compliance requirements that must be met
3. Potential gaps or risks
4. Recommended actions to ensure compliance

Be specific about regulation names and section numbers. If you don't have specific data, provide general guidance based on known regulatory requirements for industrial safety."""),
            ("human", "Query: {query}\n\nRegulatory Context:\n{context}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"query": query, "context": context})

        return {
            "answer": response.content if hasattr(response, "content") else str(response),
            "sources": sources,
        }
