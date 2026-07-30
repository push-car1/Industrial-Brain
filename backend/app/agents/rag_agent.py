from app.rag.copilot import RAGCopilot


class RAGAgent:
    def __init__(self, copilot: RAGCopilot):
        self.copilot = copilot

    def run(self, query: str) -> dict:
        result = self.copilot.answer(query)
        return result
