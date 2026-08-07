"""REQ-033 §2.1 — the RAG bridge to REQ-031 (``search_plant_knowledge``).

Both external analysis processes must justify every finding with a rationale.
Before this tool that rationale could cite the photo, the species master data and
the phase definition — but not the knowledge base, which is where the reasoning
behind a symptom-to-cause link actually lives. ``search_glossary`` covers
terminology, not substance. An agent was therefore left with two bad options:
state a causal claim unsourced, or omit it. The consuming specs require naming
the evidence, which pushed towards omission.

**Citable references, not prose.** Every hit carries ``source_key``,
``source_type``, ``title``, ``score`` and ``language`` alongside its text, so a
rationale can name where it came from and a reader can go back to it. That is the
whole point of the tool (AC-4): a summarised answer with no handle back to its
source is exactly what it must not return, which is also why it delegates to
``search`` and not to ``ask`` — ``ask`` puts a language model between the caller
and the corpus, and REQ-050 §7 keeps Kamerplanter itself out of the business of
calling one.

**Tenant-independent and PII-free.** The knowledge base is global corpus data —
``spec/knowledge/rag/`` — so the ``Input`` derives from :class:`ToolInput` and
carries no ``tenant``. Nothing tenant-derived is attached to the outbound call:
no ``QuestionContext``, no plant, no species resolved from the caller's records.
The query is the agent's own free text and is the only thing that leaves
(REQ-033 §AC, NFR-007 §LLM-Sicherheit). Because the tool is tenant-agnostic it
must reach for :meth:`ToolContext.global_link` — ``api_link``/``ui_link`` resolve
through a membership the dispatcher never binds here and would raise on the real
dispatch path.

**Degradation is reported, never faked.** The Knowledge Service is optional
(REQ-033 §Abhaengigkeiten: "ohne RAG nutzbar (Tool faellt weg)"). When it is down
or its circuit breaker is open, this tool fails with ``service.unavailable`` and
HTTP 503. Answering ``results: []`` instead would be indistinguishable from "the
corpus knows nothing about this", and an agent would record an unsourced claim as
a searched-and-found-nothing one.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.common.enums import McpPermission
from app.domain.models.mcp import McpToolResponse
from app.mcp_server.base import McpToolError, ToolBase, ToolInput, mcp_tool
from app.mcp_server.context import ToolContext

#: Upper bound on hits per call. The REST proxy allows 50; the palette caps
#: lower because these chunks are read into a model's context window, and a
#: 50-chunk answer costs more than it informs.
MAX_TOP_K = 20

#: Default number of hits. AC-4 requires at least three usable ones for a
#: well-covered topic, so the default leaves headroom above that.
DEFAULT_TOP_K = 5

#: How much of a chunk's text travels by default. Full chunks are available on
#: request; the excerpt exists so a broad search stays affordable and the caller
#: can re-ask for the one chunk it wants in full.
DEFAULT_EXCERPT_CHARS = 1200


def _chunk_payload(chunk: Any, *, excerpt_chars: int | None) -> dict[str, Any]:
    """One hit in citable form.

    ``source_key`` and ``source_type`` are the citation handle and are always
    present, even when the text is truncated — a shortened excerpt that could no
    longer be traced back would defeat the tool's purpose.
    """

    content = chunk.content or ""
    truncated = excerpt_chars is not None and len(content) > excerpt_chars
    return {
        "source_key": chunk.source_key,
        "source_type": chunk.source_type,
        "title": chunk.title,
        "score": chunk.score,
        "language": chunk.language,
        "content": content[:excerpt_chars] if truncated else content,
        "content_truncated": truncated,
        "metadata": dict(chunk.metadata or {}),
    }


@mcp_tool(name="search_plant_knowledge", permission=McpPermission.READ)
class SearchPlantKnowledge(ToolBase):
    """Search the plant knowledge base (RAG) and return citable source chunks."""

    class Input(ToolInput):
        query: str = Field(
            min_length=1,
            max_length=500,
            description="What to look up, e.g. 'Spinnmilben Bekaempfung biologisch'. The corpus is German-first.",
        )
        top_k: int = Field(
            default=DEFAULT_TOP_K,
            ge=1,
            le=MAX_TOP_K,
            description="How many chunks to retrieve, 1-20.",
        )
        min_score: float = Field(
            default=0.0,
            ge=0.0,
            le=1.0,
            description=(
                "Drop hits below this similarity score. Use 0.6 to keep only hits solid enough "
                "to cite; the default keeps everything and reports each score."
            ),
        )
        doc_language: Literal["de", "en", "all"] | None = Field(
            default=None,
            description="Restrict to chunks in one language. Omit for the server default.",
        )
        full_content: bool = Field(
            default=False,
            description=(f"Return each chunk's whole text instead of the first {DEFAULT_EXCERPT_CHARS} characters."),
        )

    async def run(self, ctx: ToolContext, args: Input) -> McpToolResponse:
        chunks = await self._search(ctx, args)
        excerpt_chars = None if args.full_content else DEFAULT_EXCERPT_CHARS

        # Filtering after retrieval rather than asking the service for it: the
        # score is the service's own and it exposes no threshold parameter, so
        # doing it here keeps one definition of the cut instead of two.
        kept = [chunk for chunk in chunks if chunk.score >= args.min_score]
        items = [_chunk_payload(chunk, excerpt_chars=excerpt_chars) for chunk in kept]

        dropped = len(chunks) - len(kept)
        summary = f"{len(items)} knowledge chunks match '{args.query}'"
        if items:
            summary += f" (best score {max(chunk.score for chunk in kept):.2f})."
        else:
            summary += "."
        if dropped:
            summary += f" {dropped} further hits were below min_score={args.min_score}."
        if not items:
            summary += " Nothing in the knowledge base clears the threshold — do not state a sourced claim."

        return self._response(
            summary=summary,
            data={
                "query": args.query,
                "count": len(items),
                "retrieved": len(chunks),
                "min_score": args.min_score,
                "doc_language": args.doc_language,
                "results": items,
            },
            # Tenant-agnostic tool: no membership is bound, so api_link/ui_link
            # would raise on the real dispatch path.
            links=[ctx.global_link("/knowledge/search")],
        )

    @staticmethod
    async def _search(ctx: ToolContext, args: Input) -> list[Any]:
        """Call the async RAG port, turning an outage into an explicit failure.

        The adapter already carries the per-call timeout, the retries and the
        circuit breaker (NFR-007), so nothing is re-implemented here — only the
        translation into the MCP error contract.
        """

        from app.data_access.external.knowledge_service_adapter import KnowledgeServiceUnavailableError

        try:
            return list(
                await ctx.knowledge_service.search(
                    args.query,
                    top_k=args.top_k,
                    doc_language=args.doc_language,
                )
            )
        except KnowledgeServiceUnavailableError as exc:
            raise McpToolError(
                "service.unavailable",
                "The knowledge base is not reachable right now; retry later. "
                "It is an optional component and may not be deployed on this instance.",
                details={"service": "knowledge-service"},
                # 503 is set explicitly: the contract-code prefix table has no
                # entry for this class and would otherwise answer 422, which
                # says "your request was wrong" for an outage that was not.
                status_code=503,
            ) from exc


__all__ = ["DEFAULT_EXCERPT_CHARS", "DEFAULT_TOP_K", "MAX_TOP_K", "SearchPlantKnowledge"]
