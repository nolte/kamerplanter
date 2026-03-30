"""Knowledge service — orchestrates embedding, vector search, and LLM generation for RAG."""

import structlog

from app.data_access.vectordb.vector_chunk_repository import VectorChunk, VectorChunkRepository
from app.domain.engines.embedding_engine import EmbeddingEngine
from app.domain.interfaces.llm_adapter import ILlmAdapter, LlmResponse

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPT = """You are a knowledgeable plant care assistant for Kamerplanter, an agricultural technology system.

Rules:
1. Answer in the SAME LANGUAGE as the user's question (German or English).
2. Use ONLY the provided context to answer. Do not use outside knowledge.
3. When citing information, mention the source title in parentheses.
4. If the context does not contain enough information to answer the question, say so clearly — do not make up facts.
5. Be concise but thorough. Use bullet points for lists.
6. For technical values (EC, pH, VPD, PPFD, GDD), include units and typical ranges when available."""


class KnowledgeAnswer:
    """Result of a RAG ask() call."""

    __slots__ = ("answer", "sources", "model", "usage")

    def __init__(
        self,
        answer: str,
        sources: list[VectorChunk],
        model: str,
        usage: dict[str, int],
    ) -> None:
        self.answer = answer
        self.sources = sources
        self.model = model
        self.usage = usage


class KnowledgeService:
    """Orchestrates semantic search and RAG-based question answering."""

    def __init__(
        self,
        embedding_engine: EmbeddingEngine,
        chunk_repo: VectorChunkRepository,
        llm_adapter: ILlmAdapter,
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
    ) -> None:
        self._embedding = embedding_engine
        self._repo = chunk_repo
        self._llm = llm_adapter
        self._max_tokens = max_tokens
        self._temperature = temperature

    def search(self, query: str, *, top_k: int = 5) -> list[VectorChunk]:
        """Semantic search — embed query and find similar chunks.

        Args:
            query: Natural-language search query.
            top_k: Number of results to return.

        Returns:
            List of VectorChunk ordered by similarity score (descending).
        """
        logger.debug("knowledge_search", query=query, top_k=top_k)
        embedding = self._embedding.embed(query)
        chunks = self._repo.search(embedding, top_k=top_k)
        logger.info("knowledge_search_complete", query=query, results=len(chunks))
        return chunks

    def ask(self, question: str, *, top_k: int = 5) -> KnowledgeAnswer:
        """Full RAG pipeline: search context chunks, then generate an LLM answer.

        Args:
            question: The user's question.
            top_k: Number of context chunks to retrieve.

        Returns:
            KnowledgeAnswer with generated text, source chunks, model info, and usage.
        """
        logger.info("knowledge_ask", question=question, top_k=top_k)

        chunks = self.search(question, top_k=top_k)

        if not chunks:
            logger.info("knowledge_ask_no_context", question=question)
            return KnowledgeAnswer(
                answer="No relevant knowledge found for this question.",
                sources=[],
                model="none",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )

        context = self._build_context(chunks)
        user_message = f"Context:\n{context}\n\nQuestion: {question}"

        response: LlmResponse = self._llm.generate(
            _SYSTEM_PROMPT,
            user_message,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        logger.info(
            "knowledge_ask_complete",
            question=question,
            model=response.model,
            sources=len(chunks),
            prompt_tokens=response.usage.get("prompt_tokens", 0),
            completion_tokens=response.usage.get("completion_tokens", 0),
        )

        return KnowledgeAnswer(
            answer=response.content,
            sources=chunks,
            model=response.model,
            usage=response.usage,
        )

    @staticmethod
    def _build_context(chunks: list[VectorChunk]) -> str:
        """Build a numbered context string from retrieved chunks."""
        sections: list[str] = []
        for i, chunk in enumerate(chunks, start=1):
            sections.append(f"[{i}] {chunk.title}\n{chunk.content}")
        return "\n\n---\n\n".join(sections)
