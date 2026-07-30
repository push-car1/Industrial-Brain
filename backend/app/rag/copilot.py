from typing import Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from app.config import settings
from app.rag.retriever import HybridRetriever


class RAGCopilot:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            num_predict=128,
            num_ctx=2048,
            timeout=600,
        )

    def answer(self, query: str, context: Optional[str] = None) -> dict:
        if not context:
            context = self.retriever.retrieve_with_context(query)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an industrial knowledge assistant for a process plant. You MUST follow these rules strictly:

1. ONLY answer using the actual data provided in the context below.
2. If the context lists specific equipment, regulations, incidents, or procedures, use those exact names and details.
3. NEVER make up or guess equipment names, regulations, or data that is not in the context.
4. If the question asks for a list, provide the complete list from the context.
5. If no relevant data exists in the context, say "I cannot find this information in the knowledge base."
6. Cite specific source documents when available.

Example good answer: "Based on the equipment list, the plant has Pump-001, Compressor-003, and Boiler-002."
Example bad answer: "In a general industrial setting, equipment might include robots, PLCs, and sensors."""),
            ("human", "Context:\n{context}\n\nQuestion: {question}")
        ])

        chain = prompt | self.llm
        response = chain.invoke({"context": context, "question": query})

        sources = []
        if context:
            for line in context.split("\n"):
                if line.startswith("[") and "(Source:" in line:
                    src_start = line.find("(Source: ") + len("(Source: ")
                    src_end = line.find(")", src_start)
                    if src_start > 0 and src_end > src_start:
                        sources.append(line[src_start:src_end])

        return {
            "answer": response.content if hasattr(response, "content") else str(response),
            "sources": list(set(sources)),
        }

    def generate_chat_title(self, message: str) -> str:
        prompt = ChatPromptTemplate.from_messages([
            ("system", "Generate a short title (max 6 words) for this chat about industrial knowledge: {message}\nTitle:"),
        ])
        chain = prompt | self.llm
        response = chain.invoke({"message": message[:100]})
        title = response.content if hasattr(response, "content") else str(response)
        return title.strip()[:50]
