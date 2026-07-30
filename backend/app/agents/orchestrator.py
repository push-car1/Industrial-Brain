import json
import operator
from typing import Annotated, Sequence, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from app.config import settings


class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    query: str
    classification: str
    sub_questions: dict
    agent_results: dict
    final_answer: str
    sources: list
    next_agents: list


class AgentOrchestrator:
    def __init__(self, rag_agent=None, maintenance_agent=None,
                 compliance_agent=None, lessons_agent=None):
        self.rag_agent = rag_agent
        self.maintenance_agent = maintenance_agent
        self.compliance_agent = compliance_agent
        self.lessons_agent = lessons_agent

        self.llm = ChatOllama(
            base_url=settings.ollama_base_url,
            model=settings.llm_model,
            temperature=0.1,
            num_predict=256,
            num_ctx=2048,
            timeout=600,
        )

        self.graph = self._build_graph()

    def _classify_query(self, state: AgentState) -> dict:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a query classifier for an industrial knowledge system.
Classify the user's query into ONE or MORE of these categories:

- "rag": Operational queries about documents, procedures, equipment specs, general information
- "maintenance": Queries about failures, work orders, predictive maintenance, root cause analysis
- "compliance": Queries about regulations, standards, compliance gaps, audits
- "lessons": Queries about incident patterns, near-misses, recurring issues, lessons learned

Return a JSON object:
{{
  "primary": "rag|maintenance|compliance|lessons",
  "all": ["rag", ...],
  "sub_questions": {{
    "rag": "specific sub-question for the RAG agent",
    "maintenance": "specific sub-question for the maintenance agent"
  }}
}}

Respond ONLY with valid JSON, no markdown formatting."""),
            ("human", "{query}")
        ])
        chain = prompt | self.llm
        try:
            response = chain.invoke({"query": state["query"]})
            content = response.content if hasattr(response, 'content') else str(response)
            content = content.replace("```json", "").replace("```", "").strip()
            classification = json.loads(content)
        except Exception as e:
            print(f"Classification error: {e}")
            classification = {
                "primary": "rag",
                "all": ["rag"],
                "sub_questions": {"rag": state["query"]}
            }

        return {
            "classification": classification["primary"],
            "next_agents": classification.get("all", ["rag"]),
            "sub_questions": classification.get("sub_questions", {"rag": state["query"]}),
        }

    def _route_to_agents(self, state: AgentState) -> Literal["agents", "synthesize"]:
        return "agents" if state["next_agents"] else "synthesize"

    def _run_agents(self, state: AgentState) -> dict:
        results = {}
        for agent_name in state["next_agents"]:
            sub_query = state["sub_questions"].get(agent_name, state["query"])
            try:
                if agent_name == "rag" and self.rag_agent:
                    results[agent_name] = self.rag_agent.run(sub_query)
                elif agent_name == "maintenance" and self.maintenance_agent:
                    results[agent_name] = self.maintenance_agent.run(sub_query)
                elif agent_name == "compliance" and self.compliance_agent:
                    results[agent_name] = self.compliance_agent.run(sub_query)
                elif agent_name == "lessons" and self.lessons_agent:
                    results[agent_name] = self.lessons_agent.run(sub_query)
                else:
                    results[agent_name] = {"answer": f"No agent available for {agent_name}", "sources": []}
            except Exception as e:
                results[agent_name] = {"answer": f"Agent error: {str(e)}", "sources": []}

        all_sources = []
        for r in results.values():
            all_sources.extend(r.get("sources", []))

        return {
            "agent_results": results,
            "sources": list(set(all_sources)),
        }

    def _synthesize(self, state: AgentState) -> dict:
        parts = []
        for agent_name, result in state["agent_results"].items():
            parts.append(f"### {agent_name.upper()} ANALYSIS ###\n{result.get('answer', 'No answer')}\n")

        combined = "\n".join(parts)

        prompt = ChatPromptTemplate.from_messages([
            ("system", """Synthesize the following multi-agent analysis results into a single coherent answer.
Combine insights from different agents, resolve any contradictions, and present a unified response.
The user should not see individual agent labels - just a seamless answer.

If sources are available, cite them naturally in the response."""),
            ("human", "Original query: {query}\n\nAnalysis results:\n{results}")
        ])
        chain = prompt | self.llm
        response = chain.invoke({"query": state["query"], "results": combined})
        final = response.content if hasattr(response, 'content') else str(response)

        return {"final_answer": final}

    def _build_graph(self):
        workflow = StateGraph(AgentState)

        workflow.add_node("classify", self._classify_query)
        workflow.add_node("agents", self._run_agents)
        workflow.add_node("synthesize", self._synthesize)

        workflow.set_entry_point("classify")

        workflow.add_conditional_edges(
            "classify",
            self._route_to_agents,
            {"agents": "agents", "synthesize": "synthesize"},
        )
        workflow.add_edge("agents", "synthesize")
        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def run(self, query: str) -> dict:
        initial_state = {
            "messages": [HumanMessage(content=query)],
            "query": query,
            "classification": "",
            "sub_questions": {},
            "agent_results": {},
            "final_answer": "",
            "sources": [],
            "next_agents": [],
        }

        result = self.graph.invoke(initial_state)

        return {
            "answer": result.get("final_answer", ""),
            "sources": result.get("sources", []),
            "agent_trace": [
                {"agent": k, "summary": v.get("answer", "")[:100]}
                for k, v in result.get("agent_results", {}).items()
            ],
        }
