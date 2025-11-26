from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, TypedDict

from langgraph.graph import START, END, StateGraph
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import House, Question, SessionModel
from app.services.embeddings import SimpleEmbeddingGenerator
from app.services.lmstudio import LMStudioClient
from app.services.vector_store import VectorStoreService


class RAGGraphState(TypedDict, total=False):
    question: str
    context: Dict
    session: Session
    session_id: Optional[str]
    query_vector: List[float]
    matches: List[tuple[int, float]]
    house_ids: List[int]
    houses: List[House]
    sources: List[str]
    prompt: str
    answer: str
    confidence: float
    response: Dict[str, Any]


class RAGService:
    def __init__(
        self,
        settings: Settings | None = None,
        embedding_generator: SimpleEmbeddingGenerator | None = None,
        vector_service: VectorStoreService | None = None,
        lm_client: LMStudioClient | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.embedding_generator = embedding_generator or SimpleEmbeddingGenerator(self.settings)
        self.vector_service = vector_service or VectorStoreService(self.settings)
        self.lm_client = lm_client or LMStudioClient(self.settings)
        self._graph = self._build_graph()

    def answer_question(
        self,
        session: Session,
        question_text: str,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None,
    ) -> Dict:
        state = self._graph.invoke(
            {
                "question": question_text,
                "context": context or {},
                "session": session,
                "session_id": session_id,
            }
        )
        return state["response"]

    def _build_graph(self):
        graph = StateGraph(RAGGraphState)
        graph.add_node("embed", self._embed_node)
        graph.add_node("retrieve", self._retrieve_node)
        graph.add_node("hydrate", self._hydrate_node)
        graph.add_node("prompt", self._prompt_node)
        graph.add_node("generate", self._generate_node)
        graph.add_node("finalize", self._finalize_node)

        graph.add_edge(START, "embed")
        graph.add_edge("embed", "retrieve")
        graph.add_edge("retrieve", "hydrate")
        graph.add_edge("hydrate", "prompt")
        graph.add_edge("prompt", "generate")
        graph.add_edge("generate", "finalize")
        graph.add_edge("finalize", END)
        return graph.compile()

    def _embed_node(self, state: RAGGraphState) -> RAGGraphState:
        question = state["question"]
        query_vector = self.embedding_generator.embed(question)
        return {"query_vector": query_vector}

    def _retrieve_node(self, state: RAGGraphState) -> RAGGraphState:
        matches = self.vector_service.query(state["query_vector"], self.settings.max_results)
        house_ids = [match[0] for match in matches]
        return {"matches": matches, "house_ids": house_ids}

    def _hydrate_node(self, state: RAGGraphState) -> RAGGraphState:
        house_ids = state.get("house_ids", [])
        houses = self._fetch_houses(state["session"], house_ids)
        sources = [str(h.external_id) for h in houses]
        return {"houses": houses, "sources": sources}

    def _prompt_node(self, state: RAGGraphState) -> RAGGraphState:
        prompt = self._build_prompt(state["question"], state.get("houses", []), state.get("context", {}))
        return {"prompt": prompt}

    def _generate_node(self, state: RAGGraphState) -> RAGGraphState:
        answer_text = self.lm_client.generate(state["prompt"])
        return {"answer": answer_text}

    def _finalize_node(self, state: RAGGraphState) -> RAGGraphState:
        confidence = self._calculate_confidence(state.get("matches", []))
        question_record = self._persist_question(
            session=state["session"],
            session_id=state.get("session_id"),
            question_text=state["question"],
            answer_text=state.get("answer", ""),
            confidence=confidence,
            sources=state.get("sources", []),
        )
        response = {
            "answer": state.get("answer", ""),
            "sources": state.get("sources", []),
            "confidence": confidence,
            "question_id": question_record.id,
        }
        return {"confidence": confidence, "response": response}

    def _fetch_houses(self, session: Session, ids: Sequence[int]) -> List[House]:
        if not ids:
            return []
        rows = session.scalars(select(House).where(House.id.in_(ids))).all()
        rows.sort(key=lambda house: ids.index(house.id))
        return rows

    def _build_prompt(self, question_text: str, houses: Sequence[House], context: Dict) -> str:
        context_lines = ["Context:"]
        for house in houses:
            context_lines.append(
                f"- #{house.external_id} in {house.location}: {house.title} priced at {house.price_rupees or house.amount_rupees}"
            )
        if not houses:
            context_lines.append("- No similar houses found; provide general guidance based on available data.")
        context_lines.append("User question: " + question_text)
        if context:
            context_lines.append("Extra context: " + str(context))
        return "\n".join(context_lines)

    def _calculate_confidence(self, matches: Sequence[tuple[int, float]]) -> float:
        if not matches:
            return 0.2
        avg = sum(score for _, score in matches) / len(matches)
        return round(max(0.1, min(0.99, avg)), 3)

    def _persist_question(
        self,
        session: Session,
        question_text: str,
        answer_text: str,
        confidence: float,
        sources: List[str],
        session_id: Optional[str] = None,
    ) -> Question:
        session_model = None
        if session_id:
            session_model = session.get(SessionModel, session_id)
        if not session_model:
            session_model = SessionModel(id=session_id) if session_id else SessionModel()
            session.add(session_model)

        record = Question(
            session=session_model,
            question_text=question_text,
            answer_text=answer_text,
            confidence=confidence,
            sources=sources,
            created_at=datetime.utcnow(),
        )
        session.add(record)
        session.flush()
        return record
