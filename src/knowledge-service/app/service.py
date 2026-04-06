"""Knowledge service -- orchestrates embedding, vector search, and LLM generation."""

import structlog

from app.embedding import EmbeddingEngine
from app.llm.interface import ILlmAdapter, LlmResponse
from app.prompt_engine import PromptEngine, QuestionType
from app.reranker import RerankerEngine
from app.vectordb.repository import VectorChunk, VectorChunkRepository

logger = structlog.get_logger(__name__)


class KnowledgeAnswer:
    """Result of a RAG ask() call."""

    __slots__ = ("answer", "model", "question_type", "sources", "usage")

    def __init__(
        self,
        answer: str,
        question_type: QuestionType,
        sources: list[VectorChunk],
        model: str,
        usage: dict[str, int],
    ) -> None:
        self.answer = answer
        self.question_type = question_type
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
        prompt_engine: PromptEngine,
        *,
        reranker: RerankerEngine | None = None,
        reranker_initial_k: int = 20,
        reranker_top_k: int = 5,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        default_doc_language: str = "de",
        default_prompt_language: str = "de",
        answer_verification: bool = False,
    ) -> None:
        self._embedding = embedding_engine
        self._repo = chunk_repo
        self._llm = llm_adapter
        self._prompt_engine = prompt_engine
        self._reranker = reranker
        self._reranker_initial_k = reranker_initial_k
        self._reranker_top_k = reranker_top_k
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._default_doc_language = default_doc_language
        self._default_prompt_language = default_prompt_language
        self._answer_verification = answer_verification

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
    ) -> list[VectorChunk]:
        """Perform hybrid semantic + full-text search over the knowledge base."""
        effective_lang = doc_language or self._default_doc_language

        # Over-retrieve when reranker is available so it has more candidates
        retrieve_k = self._reranker_initial_k if self._reranker and self._reranker.available else top_k

        logger.debug("knowledge_search", query=query, top_k=top_k, retrieve_k=retrieve_k, doc_language=effective_lang)
        embedding = self._embedding.embed(query, prefix="query: ")
        chunks = self._repo.hybrid_search(embedding, query, top_k=retrieve_k, language=effective_lang, vector_weight=0.4)

        # Re-rank if available
        if self._reranker and self._reranker.available:
            chunks = self._reranker.rerank(query, chunks, top_k=top_k)
        else:
            chunks = chunks[:top_k]

        logger.info("knowledge_search_complete", query=query, results=len(chunks))
        return chunks

    def ask(
        self,
        question: str,
        *,
        top_k: int = 5,
        doc_language: str | None = None,
        prompt_language: str | None = None,
        context: dict | None = None,
    ) -> KnowledgeAnswer:
        """Retrieve context chunks and generate an LLM answer."""
        effective_doc_lang = doc_language or self._default_doc_language
        effective_prompt_lang = prompt_language or self._default_prompt_language

        logger.info(
            "knowledge_ask",
            question=question,
            top_k=top_k,
            doc_language=effective_doc_lang,
            prompt_language=effective_prompt_lang,
        )

        question_type = self._prompt_engine.classify(question)
        chunks = self.search(question, top_k=top_k, doc_language=effective_doc_lang)

        if not chunks:
            logger.info("knowledge_ask_no_context", question=question)
            return KnowledgeAnswer(
                answer="No relevant knowledge found for this question.",
                question_type=question_type,
                sources=[],
                model="none",
                usage={"prompt_tokens": 0, "completion_tokens": 0},
            )

        system_prompt = self._prompt_engine.build_system_prompt(question_type, effective_prompt_lang)
        user_message = self._prompt_engine.build_user_message(question, chunks, context)

        response: LlmResponse = self._llm.generate(
            system_prompt,
            user_message,
            max_tokens=self._max_tokens,
            temperature=self._temperature,
        )

        final_answer = response.content
        total_usage = dict(response.usage)

        # Optional verification pass — check completeness and fill gaps
        if self._answer_verification and response.content:
            logger.info("knowledge_verification_start", question=question)
            verification_system = self._prompt_engine.build_verification_prompt(effective_prompt_lang)
            verification_message = self._prompt_engine.build_verification_message(
                question, chunks, response.content,
            )
            verification_response: LlmResponse = self._llm.generate(
                verification_system,
                verification_message,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )
            final_answer = verification_response.content
            total_usage["prompt_tokens"] = (
                total_usage.get("prompt_tokens", 0) + verification_response.usage.get("prompt_tokens", 0)
            )
            total_usage["completion_tokens"] = (
                total_usage.get("completion_tokens", 0) + verification_response.usage.get("completion_tokens", 0)
            )
            logger.info(
                "knowledge_verification_complete",
                question=question,
                verification_prompt_tokens=verification_response.usage.get("prompt_tokens", 0),
                verification_completion_tokens=verification_response.usage.get("completion_tokens", 0),
            )

        logger.info(
            "knowledge_ask_complete",
            question=question,
            question_type=question_type,
            model=response.model,
            sources=len(chunks),
            prompt_tokens=total_usage.get("prompt_tokens", 0),
            completion_tokens=total_usage.get("completion_tokens", 0),
            verification=self._answer_verification,
        )

        return KnowledgeAnswer(
            answer=final_answer,
            question_type=question_type,
            sources=chunks,
            model=response.model,
            usage=total_usage,
        )
