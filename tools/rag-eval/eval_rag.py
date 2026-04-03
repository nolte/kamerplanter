#!/usr/bin/env python3
"""Standalone RAG quality benchmark runner.

Calls the Knowledge Service microservice via HTTP — no direct DB or LLM access.

Usage:
  python eval_rag.py                                     # Full benchmark (100 questions)
  python eval_rag.py --smoke                             # Quick smoke test (abort on first failure)
  python eval_rag.py --resume                            # Resume interrupted run from partial results
  python eval_rag.py --categories diagnostik duengung    # Only specific categories
  python eval_rag.py --retrieval-only                    # Debug retrieval without LLM generation
  python eval_rag.py --top-k 10                          # Retrieve more chunks (default: 5)
  python eval_rag.py --doc-language de                   # Filter chunks by language (de/en/all)
  python eval_rag.py --output results.json               # Custom output path
  python eval_rag.py --service-url http://host:8000      # Custom Knowledge Service URL

Environment variables (used as defaults when CLI args are not provided):
  KNOWLEDGE_SERVICE_URL   Knowledge Service URL           (default: http://localhost:8090)
  EVAL_DATA_DIR           Directory with benchmark YAML   (default: spec/rag-eval/)
  EVAL_OUTPUT_DIR         Directory for result files      (default: test-reports/rag-eval/)
"""

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

import httpx
import yaml

# ── Defaults (overridable via CLI args or env vars) ─────────────────

KNOWLEDGE_SERVICE_URL = os.environ.get("KNOWLEDGE_SERVICE_URL", "http://localhost:8090")
EVAL_DATA_DIR = os.environ.get("EVAL_DATA_DIR", str(Path(__file__).parent / "../../spec/rag-eval"))
EVAL_OUTPUT_DIR = os.environ.get("EVAL_OUTPUT_DIR", str(Path(__file__).parent / "../../test-reports/rag-eval"))


# ── Data classes ────────────────────────────────────────────────────


@dataclass
class QuestionResult:
    id: str
    category: str
    score: float
    topic_hits: list[str]
    topic_misses: list[str]
    false_positives: list[str]
    answer: str = ""
    question_type: str = "factual"
    chunks_used: int = 0
    chunk_sources: list[str] = field(default_factory=list)


@dataclass
class EvalResult:
    method: str
    total_score: float
    passed: bool
    min_pass_score: float
    category_scores: dict[str, float]
    questions_evaluated: int
    failures: list[dict] = field(default_factory=list)


# ── Knowledge Service client ──────────────────────────────────────


def ks_search(
    service_url: str,
    query: str,
    top_k: int = 5,
    doc_language: str | None = None,
) -> list[dict]:
    """Call Knowledge Service /search endpoint."""
    params: dict = {"q": query, "top_k": top_k}
    if doc_language:
        params["doc_language"] = doc_language

    resp = httpx.get(f"{service_url}/search", params=params, timeout=120.0)
    resp.raise_for_status()
    return resp.json().get("results", [])


def ks_ask(
    service_url: str,
    question: str,
    top_k: int = 5,
    doc_language: str | None = None,
    context: dict | None = None,
) -> dict:
    """Call Knowledge Service /ask endpoint."""
    payload: dict = {"question": question, "top_k": top_k}
    if doc_language:
        payload["doc_language"] = doc_language
    if context:
        payload["context"] = context

    resp = httpx.post(f"{service_url}/ask", json=payload, timeout=600.0)
    resp.raise_for_status()
    return resp.json()


# ── Evaluation logic (scoring — eval-specific, stays here) ────────

_UMLAUT_MAP = str.maketrans({
    "ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss",
    "Ä": "Ae", "Ö": "Oe", "Ü": "Ue",
})


def _normalize(text: str) -> str:
    """Normalize Unicode umlauts to ASCII digraphs so patterns match both forms."""
    return text.translate(_UMLAUT_MAP)


_NEGATION_RE = re.compile(
    r"(?i)\b(kein|keine|keinen|keinem|nicht|ohne|ausschlie.en|unwahrscheinlich)\b.{0,30}",
)


def _is_negated(keyword: str, text: str) -> bool:
    """Return True if *keyword* only appears in a negated context in *text*."""
    kw_lower = keyword.lower()
    text_lower = text.lower()
    if kw_lower not in text_lower:
        return False
    for m in re.finditer(re.escape(kw_lower), text_lower):
        start = max(0, m.start() - 40)
        prefix = text_lower[start:m.start()]
        if not _NEGATION_RE.search(prefix):
            return False
    return True


def topic_matches(topic_key: str, answer: str, synonyms: dict, check_negation: bool = False) -> bool:
    """Check if a topic is mentioned in the answer."""
    topic_def = synonyms.get(topic_key, {})
    answer_normalized = _normalize(answer)

    pattern = topic_def.get("pattern")
    if pattern:
        match_orig = re.search(pattern, answer)
        match_norm = re.search(pattern, answer_normalized)
        if match_orig or match_norm:
            if check_negation:
                matched_text = (match_orig or match_norm).group(0)
                if _is_negated(matched_text, answer) or _is_negated(matched_text, answer_normalized):
                    return False
            return True

    keywords = topic_def.get("de", [])
    answer_lower = answer.lower()
    answer_norm_lower = answer_normalized.lower()
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in answer_lower or kw_lower in answer_norm_lower:
            if check_negation and (_is_negated(kw, answer) or _is_negated(kw, answer_normalized)):
                continue
            return True
    return False


def evaluate_question(
    question: dict,
    synonyms: dict,
    service_url: str,
    top_k: int = 10,
    retrieval_only: bool = False,
    doc_language: str | None = None,
) -> QuestionResult:
    """Evaluate a single benchmark question through the Knowledge Service."""
    q_id = question.get("id", "unknown")
    category = question.get("category", "unknown")
    q_text = question.get("question", "")
    expected_topics = question.get("expected_topics", [])
    expected_not = question.get("expected_NOT", [])

    # Build context dict for the Knowledge Service
    ctx = question.get("context", {}) or {}
    context_dict = {k: v for k, v in ctx.items() if v is not None} or None

    if retrieval_only:
        # Use /search for retrieval-only mode
        chunks = ks_search(service_url, q_text, top_k=top_k, doc_language=doc_language)
        print(f"\n  {'─' * 60}")
        print(f"  {q_id}: {q_text}")
        print(f"  Expected topics: {', '.join(expected_topics)}")
        print(f"  Retrieved {len(chunks)} chunks:")
        for i, c in enumerate(chunks, 1):
            print(f"    [{i}] {c['source_key']:<40s} score={c['score']:.4f}")
            print(f"        {c['title']}")
            preview = c["content"].replace("\n", " ")[:120]
            print(f"        {preview}...")
        return QuestionResult(
            id=q_id, category=category, score=0.0,
            topic_hits=[], topic_misses=expected_topics,
            false_positives=[], answer="[retrieval-only]",
            chunks_used=len(chunks),
            chunk_sources=[c["source_key"] for c in chunks],
        )

    # Use /ask for full RAG pipeline
    try:
        data = ks_ask(
            service_url, q_text,
            top_k=top_k,
            doc_language=doc_language,
            context=context_dict,
        )
        answer = data.get("answer", "")
        question_type = data.get("question_type", "factual")
        sources = data.get("sources", [])
    except Exception as exc:
        print(f"  Knowledge Service error for {q_id}: {exc}", file=sys.stderr)
        answer = ""
        question_type = "factual"
        sources = []

    # Score
    hits = [t for t in expected_topics if topic_matches(t, answer, synonyms)]
    misses = [t for t in expected_topics if not topic_matches(t, answer, synonyms)]
    fps = [t for t in expected_not if topic_matches(t, answer, synonyms, check_negation=True)]

    total = len(expected_topics) if expected_topics else 1
    score = max(0.0, min(1.0, (len(hits) / total) - (len(fps) * 0.5)))

    return QuestionResult(
        id=q_id,
        category=category,
        score=score,
        topic_hits=hits,
        topic_misses=misses,
        false_positives=fps,
        answer=answer[:2000],
        question_type=question_type,
        chunks_used=len(sources),
        chunk_sources=[s["source_key"] for s in sources],
    )


def _write_partial(results: list[QuestionResult], min_pass: float, path: str, errors: int = 0) -> None:
    """Write intermediate results after each question so progress survives crashes."""
    cat_scores: dict[str, list[float]] = {}
    for r in results:
        cat_scores.setdefault(r.category, []).append(r.score)
    category_avgs = {cat: sum(s) / len(s) for cat, s in cat_scores.items()}
    total_score = sum(r.score for r in results) / len(results) if results else 0.0

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "partial": True,
        "method": "topic_match",
        "total_score": round(total_score, 4),
        "passed": total_score >= min_pass,
        "min_pass_score": min_pass,
        "category_scores": {k: round(v, 4) for k, v in category_avgs.items()},
        "questions_evaluated": len(results),
        "errors": errors,
        "results": [
            {
                "id": r.id,
                "category": r.category,
                "score": round(r.score, 2),
                "question_type": r.question_type,
                "topic_hits": r.topic_hits,
                "topic_misses": r.topic_misses,
                "false_positives": r.false_positives,
                "answer": r.answer,
                "chunk_sources": r.chunk_sources,
            }
            for r in results
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)


def _load_partial_results(partial_path: str) -> list[QuestionResult]:
    """Load previously saved partial results for resume support."""
    path = Path(partial_path)
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    results = []
    for r in data.get("results", []):
        results.append(QuestionResult(
            id=r["id"],
            category=r["category"],
            score=r["score"],
            topic_hits=r.get("topic_hits", []),
            topic_misses=r.get("topic_misses", []),
            false_positives=r.get("false_positives", []),
            answer=r.get("answer", ""),
            question_type=r.get("question_type", "factual"),
            chunks_used=0,
            chunk_sources=r.get("chunk_sources", []),
        ))
    return results


def run_eval(
    eval_dir: str,
    service_url: str,
    categories: list[str] | None = None,
    top_k: int = 10,
    smoke: bool = False,
    retrieval_only: bool = False,
    doc_language: str | None = None,
    resume: bool = False,
    output_dir: str | None = None,
) -> EvalResult:
    """Run the full topic-match benchmark via the Knowledge Service.

    If *smoke* is True, load smoke_questions.yaml instead and abort on the
    first failing question (fast gate before a full benchmark run).
    If *retrieval_only* is True, skip LLM generation and only show retrieved chunks.
    If *resume* is True, load eval_results_partial.json and skip already-evaluated questions.
    """
    eval_path = Path(eval_dir)
    out_path = Path(output_dir) if output_dir else Path(EVAL_OUTPUT_DIR)
    out_path.mkdir(parents=True, exist_ok=True)

    questions_file = "smoke_questions.yaml" if smoke else "benchmark_questions.yaml"
    with open(eval_path / questions_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with open(eval_path / "topic_synonyms.yaml", encoding="utf-8") as f:
        synonyms = yaml.safe_load(f).get("topics", {})

    min_pass = data.get("min_pass_score", 0.70)
    questions = data.get("questions", [])
    if categories:
        questions = [q for q in questions if q.get("category") in categories]

    partial_path = str(out_path / "eval_results_partial.json")

    results: list[QuestionResult] = []
    completed_ids: set[str] = set()
    errors = 0
    if resume and not smoke:
        previous = _load_partial_results(partial_path)
        if previous:
            results.extend(previous)
            completed_ids = {r.id for r in previous}
            print(f"[RESUME] Loaded {len(previous)} previous results, skipping completed questions.\n")

    remaining = [q for q in questions if q.get("id", "unknown") not in completed_ids]

    label = "SMOKE" if smoke else ("RESUME" if completed_ids else "FULL")
    print(f"[{label}] Running {len(remaining)}/{len(questions)} questions via {service_url} ...\n")

    for _i, question in enumerate(remaining, 1):
        try:
            result = evaluate_question(
                question, synonyms, service_url, top_k,
                retrieval_only=retrieval_only,
                doc_language=doc_language,
            )
        except Exception as exc:
            q_id = question.get("id", "unknown")
            print(f"  [{len(results) + 1:3d}/{len(questions)}] {q_id:<20s} ERROR  {type(exc).__name__}: {exc!s:.80s}")
            errors += 1
            continue
        if not retrieval_only:
            status = "PASS" if result.score >= min_pass else "FAIL"
            print(
                f"  [{len(results) + 1:3d}/{len(questions)}] {result.id:<20s} "
                f"{result.score:.2f}  {status}  ({result.question_type})"
            )
            if result.topic_misses:
                print(f"           misses: {', '.join(result.topic_misses)}")
            if result.false_positives:
                print(f"           FPs:    {', '.join(result.false_positives)}")
        results.append(result)

        if not smoke:
            _write_partial(results, min_pass, partial_path, errors)

        if smoke and result.score < min_pass:
            print(f"\n  SMOKE FAILED on {result.id} — aborting (full benchmark not worthwhile)")
            break

    # Aggregate
    cat_scores: dict[str, list[float]] = {}
    for r in results:
        cat_scores.setdefault(r.category, []).append(r.score)
    category_avgs = {cat: sum(s) / len(s) for cat, s in cat_scores.items()}

    total_score = sum(r.score for r in results) / len(results) if results else 0.0
    failures = [
        {
            "id": r.id,
            "score": round(r.score, 2),
            "question_type": r.question_type,
            "misses": r.topic_misses,
            "fps": r.false_positives,
            "answer": r.answer,
            "chunk_sources": r.chunk_sources,
        }
        for r in results
        if r.score < min_pass
    ]

    return EvalResult(
        method="topic_match",
        total_score=round(total_score, 4),
        passed=total_score >= min_pass,
        min_pass_score=min_pass,
        category_scores={k: round(v, 4) for k, v in category_avgs.items()},
        questions_evaluated=len(results),
        failures=failures,
    )


# ── CLI ─────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(description="Kamerplanter RAG Quality Benchmark")
    parser.add_argument("--service-url", default=KNOWLEDGE_SERVICE_URL, help="Knowledge Service URL")
    parser.add_argument("--eval-dir", default=EVAL_DATA_DIR, help="Directory with benchmark YAML files")
    parser.add_argument("--categories", nargs="*", help="Only evaluate these categories")
    parser.add_argument("--smoke", action="store_true",
                        help="Run only smoke-test golden-file questions (fast sanity check)")
    parser.add_argument("--retrieval-only", action="store_true",
                        help="Show retrieved chunks per question without LLM generation (debug retrieval)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of RAG chunks to retrieve")
    parser.add_argument("--doc-language", default=None, choices=["de", "en", "all"],
                        help="Filter knowledge chunks by language (default: no filter)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from eval_results_partial.json, skipping already-evaluated questions")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for results (default: test-reports/rag-eval/)")
    parser.add_argument("--output", "-o", default=None,
                        help="Output JSON path (default: eval_results.json in output dir)")
    args = parser.parse_args()

    eval_dir = str(Path(args.eval_dir).resolve())
    if not Path(eval_dir).exists():
        print(f"Error: eval directory not found: {eval_dir}", file=sys.stderr)
        sys.exit(1)

    result = run_eval(
        eval_dir=eval_dir,
        service_url=args.service_url,
        categories=args.categories,
        top_k=args.top_k,
        smoke=args.smoke,
        retrieval_only=args.retrieval_only,
        doc_language=args.doc_language,
        resume=args.resume,
        output_dir=args.output_dir,
    )

    # Print summary
    print(f"\n{'=' * 60}")
    print(f"  Total Score:  {result.total_score:.2%}  {'PASS' if result.passed else 'FAIL'}")
    print(f"  Threshold:    {result.min_pass_score:.0%}")
    print(f"  Questions:    {result.questions_evaluated}")
    print(f"  Failures:     {len(result.failures)}")
    print(f"\n  Category Scores:")
    for cat, score in sorted(result.category_scores.items()):
        status = "PASS" if score >= result.min_pass_score else "FAIL"
        print(f"    {cat:<25s} {score:.2%}  {status}")
    print(f"{'=' * 60}")

    # Write JSON
    out_dir = Path(args.output_dir) if args.output_dir else Path(EVAL_OUTPUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output or str(out_dir / "eval_results.json")
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **asdict(result),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"\nResults written to {output_path}")

    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
