"""Knowledge service — orchestrates embedding, vector search, and LLM generation for RAG."""

import structlog

from app.data_access.vectordb.vector_chunk_repository import VectorChunk, VectorChunkRepository
from app.domain.engines.embedding_engine import EmbeddingEngine
from app.domain.interfaces.llm_adapter import ILlmAdapter, LlmResponse

logger = structlog.get_logger(__name__)

_SYSTEM_PROMPTS: dict[str, str] = {
    "en": (
        "You are a knowledgeable plant care assistant for Kamerplanter, "
        "an agricultural technology system.\n\n"
        "Rules:\n"
        "1. Answer in the SAME LANGUAGE as the user's question (German or English).\n"
        "2. Use ONLY the provided context to answer. Do not use outside knowledge.\n"
        "3. When citing information, mention the source title in parentheses.\n"
        "4. If the context does not contain enough information to answer the question, "
        "say so clearly — do not make up facts.\n"
        "5. Be concise but thorough. Use bullet points for lists.\n"
        "6. For technical values (EC, pH, VPD, PPFD, GDD), include units and "
        "typical ranges when available."
    ),
    "de": (
        "Du bist ein fachkundiger Pflanzenberater fuer Kamerplanter, "
        "ein Agrar-Technologie-System.\n\n"
        "Regeln:\n"
        "1. Antworte auf Deutsch.\n"
        "2. Nutze NUR den bereitgestellten Kontext. Verwende kein externes Wissen.\n"
        "3. Nenne beim Zitieren den Quellentitel in Klammern.\n"
        "4. Wenn der Kontext nicht ausreicht, sage das klar — erfinde keine Fakten.\n"
        "5. Sei praezise aber gruendlich. Verwende Aufzaehlungszeichen fuer Listen.\n"
        "6. Bei technischen Werten (EC, pH, VPD, PPFD, GDD) Einheiten und "
        "typische Bereiche angeben."
    ),
}


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
        default_doc_language: str = "de",
        default_prompt_language: str = "de",
    ) -> None:
        self._embedding = embedding_engine
        self._repo = chunk_repo
        self._llm = llm_adapter
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._default_doc_language = default_doc_language
        self._default_prompt_language = default_prompt_language

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
    ) -> list[VectorChunk]:
        """Semantic search — embed query and find similar chunks.

        Args:
            query: Natural-language search query.
            top_k: Number of results to return.
            doc_language: Filter by document language ("de", "en", "all").
                          None uses the configured default.

        Returns:
            List of VectorChunk ordered by similarity score (descending).
        """
        effective_lang = doc_language or self._default_doc_language
        logger.debug("knowledge_search", query=query, top_k=top_k, doc_language=effective_lang)
        embedding = self._embedding.embed(query, prefix="query: ")
        chunks = self._repo.hybrid_search(embedding, query, top_k=top_k, language=effective_lang)
        logger.info("knowledge_search_complete", query=query, results=len(chunks))
        return chunks

    def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
        prompt_language: str | None = None,
    ) -> KnowledgeAnswer:
        """Full RAG pipeline: search context chunks, then generate an LLM answer.

        Args:
            question: The user's question.
            top_k: Number of context chunks to retrieve.
            doc_language: Filter by document language ("de", "en", "all").
                          None uses the configured default.
            prompt_language: System prompt language ("de", "en").
                             None uses the configured default.

        Returns:
            KnowledgeAnswer with generated text, source chunks, model info, and usage.
        """
        effective_doc_lang = doc_language or self._default_doc_language
        effective_prompt_lang = prompt_language or self._default_prompt_language

        logger.info(
            "knowledge_ask",
            question=question,
            top_k=top_k,
            doc_language=effective_doc_lang,
            prompt_language=effective_prompt_lang,
        )

        chunks = self.search(question, top_k=top_k, doc_language=effective_doc_lang)

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
        system_prompt = _SYSTEM_PROMPTS.get(effective_prompt_lang, _SYSTEM_PROMPTS["en"])

        response: LlmResponse = self._llm.generate(
            system_prompt,
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
