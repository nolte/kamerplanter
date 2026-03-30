#!/usr/bin/env python3
"""Standalone RAG quality benchmark runner.

No dependency on the Kamerplanter backend — connects directly to:
  - Embedding Service (HTTP)
  - VectorDB / pgvector (PostgreSQL)
  - LLM / Ollama (HTTP)

Usage:
  python eval_rag.py
  python eval_rag.py --categories diagnostik duengung
  python eval_rag.py --ollama-url http://localhost:11434 --model gemma3:4b
  python eval_rag.py --output results.json
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
import psycopg
import yaml

# ── Defaults (overridable via CLI args or env vars) ─────────────────

EMBEDDING_URL = os.environ.get("EMBEDDING_SERVICE_URL", "http://localhost:8080")
VECTORDB_DSN = os.environ.get(
    "VECTORDB_DSN",
    "host=localhost port=5433 dbname=kamerplanter_vectors user=postgres password=devpassword",
)
OLLAMA_URL = os.environ.get("LLM_API_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("LLM_MODEL", "gemma3:4b")
EVAL_DATA_DIR = os.environ.get("EVAL_DATA_DIR", str(Path(__file__).parent / "../../tests/rag-eval"))

RAG_SYSTEM_PROMPT = (
    "Du bist ein Pflanzenberater. Antworte auf Deutsch, kurz und fachlich korrekt. "
    "Nenne: 1) Diagnose (Naehrstoff/Schaedling), 2) ob mobil/immobil und welche Blaetter betroffen, "
    "3) Ursachen (pH, EC pruefen), 4) Massnahmen. "
    "Nenne NUR die wahrscheinlichste Diagnose, nicht was es NICHT ist. "
    "Nutze NUR den Kontext. Erfinde nichts."
)


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
    chunks_used: int = 0


@dataclass
class EvalResult:
    method: str
    total_score: float
    passed: bool
    min_pass_score: float
    category_scores: dict[str, float]
    questions_evaluated: int
    failures: list[dict] = field(default_factory=list)


# ── Service clients (no backend imports) ────────────────────────────


def embed_text(text: str, service_url: str, model: str = "paraphrase-multilingual-MiniLM-L12-v2") -> list[float]:
    """Call the embedding service to get a vector."""
    resp = httpx.post(
        f"{service_url}/embed",
        json={"texts": [text], "model": model},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def search_chunks(
    embedding: list[float],
    dsn: str,
    top_k: int = 10,
) -> list[dict]:
    """Query pgvector for similar chunks."""
    embedding_str = f"[{','.join(str(v) for v in embedding)}]"
    sql = """
        SELECT source_key, source_type, title, content, metadata,
               1 - (embedding <=> %s::vector) AS score
        FROM ai_vector_chunks
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    with psycopg.connect(dsn) as conn:
        rows = conn.execute(sql, (embedding_str, embedding_str, top_k)).fetchall()
    return [
        {
            "source_key": r[0],
            "title": r[2],
            "content": r[3],
            "score": float(r[5]),
        }
        for r in rows
    ]


def llm_generate(
    system_prompt: str,
    user_message: str,
    ollama_url: str,
    model: str,
) -> str:
    """Call Ollama /api/chat and return the response text."""
    resp = httpx.post(
        f"{ollama_url}/api/chat",
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "stream": False,
            "options": {"num_predict": 512, "temperature": 0.1},
        },
        timeout=300.0,
    )
    resp.raise_for_status()
    return resp.json().get("message", {}).get("content", "")


# ── Evaluation logic ────────────────────────────────────────────────

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
    # Check all occurrences — if ANY occurrence is NOT negated, return False
    for m in re.finditer(re.escape(kw_lower), text_lower):
        start = max(0, m.start() - 40)
        prefix = text_lower[start:m.start()]
        if not _NEGATION_RE.search(prefix):
            return False  # at least one non-negated mention
    return True  # all mentions were negated


def topic_matches(topic_key: str, answer: str, synonyms: dict, check_negation: bool = False) -> bool:
    """Check if a topic is mentioned in the answer.

    Matches against both the original answer and an umlaut-normalized version
    so that patterns written with 'ae/oe/ue' match LLM output with 'ä/ö/ü'.

    If check_negation is True (used for false-positive detection), a match is
    suppressed when the keyword only appears in negated context ("kein", "nicht").
    """
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
    embedding_url: str,
    vectordb_dsn: str,
    ollama_url: str,
    ollama_model: str,
    top_k: int = 10,
) -> QuestionResult:
    """Evaluate a single benchmark question through the full RAG pipeline."""
    q_id = question.get("id", "unknown")
    category = question.get("category", "unknown")
    q_text = question.get("question", "")
    expected_topics = question.get("expected_topics", [])
    expected_not = question.get("expected_NOT", [])

    # Build context string
    ctx = question.get("context", {}) or {}
    context_parts = []
    for key in ("species", "phase", "substrate", "ec", "ph"):
        if ctx.get(key):
            context_parts.append(f"{key}: {ctx[key]}")
    context_str = ", ".join(context_parts)

    # 1. Retrieve
    query = f"{q_text} {context_str}".strip()
    embedding = embed_text(query, embedding_url)
    chunks = search_chunks(embedding, vectordb_dsn, top_k)

    # 2. Generate
    chunk_texts = "\n\n---\n\n".join(
        f"[{c['source_key']}] {c['title']}\n{c['content']}" for c in chunks
    )
    user_message = f"Kontext aus Wissensdatenbank:\n{chunk_texts}\n\n"
    if context_str:
        user_message += f"Situation: {context_str}\n\n"
    user_message += f"Frage: {q_text}"

    try:
        answer = llm_generate(RAG_SYSTEM_PROMPT, user_message, ollama_url, ollama_model)
    except Exception as exc:
        print(f"  LLM error for {q_id}: {exc}", file=sys.stderr)
        answer = ""

    # 3. Score
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
        answer=answer[:500],
        chunks_used=len(chunks),
    )


def run_eval(
    eval_dir: str,
    embedding_url: str,
    vectordb_dsn: str,
    ollama_url: str,
    ollama_model: str,
    categories: list[str] | None = None,
    top_k: int = 10,
) -> EvalResult:
    """Run the full topic-match benchmark."""
    eval_path = Path(eval_dir)

    with open(eval_path / "benchmark_questions.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with open(eval_path / "topic_synonyms.yaml", encoding="utf-8") as f:
        synonyms = yaml.safe_load(f).get("topics", {})

    min_pass = data.get("min_pass_score", 0.70)
    questions = data.get("questions", [])
    if categories:
        questions = [q for q in questions if q.get("category") in categories]

    print(f"Running {len(questions)} questions against {ollama_model} ...\n")

    results: list[QuestionResult] = []
    for i, question in enumerate(questions, 1):
        result = evaluate_question(
            question, synonyms, embedding_url, vectordb_dsn, ollama_url, ollama_model, top_k
        )
        status = "PASS" if result.score >= min_pass else "FAIL"
        print(f"  [{i:3d}/{len(questions)}] {result.id:<20s} {result.score:.2f}  {status}")
        if result.topic_misses:
            print(f"           misses: {', '.join(result.topic_misses)}")
        if result.false_positives:
            print(f"           FPs:    {', '.join(result.false_positives)}")
        results.append(result)

    # Aggregate
    cat_scores: dict[str, list[float]] = {}
    for r in results:
        cat_scores.setdefault(r.category, []).append(r.score)
    category_avgs = {cat: sum(s) / len(s) for cat, s in cat_scores.items()}

    total_score = sum(r.score for r in results) / len(results) if results else 0.0
    failures = [
        {"id": r.id, "score": round(r.score, 2), "misses": r.topic_misses, "fps": r.false_positives, "answer": r.answer}
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
    parser.add_argument("--embedding-url", default=EMBEDDING_URL, help="Embedding service URL")
    parser.add_argument("--vectordb-dsn", default=VECTORDB_DSN, help="PostgreSQL DSN for VectorDB")
    parser.add_argument("--ollama-url", default=OLLAMA_URL, help="Ollama API URL")
    parser.add_argument("--model", default=OLLAMA_MODEL, help="LLM model name")
    parser.add_argument("--eval-dir", default=EVAL_DATA_DIR, help="Directory with benchmark YAML files")
    parser.add_argument("--categories", nargs="*", help="Only evaluate these categories")
    parser.add_argument("--top-k", type=int, default=5, help="Number of RAG chunks to retrieve")
    parser.add_argument("--output", "-o", default=None, help="Output JSON path (default: eval_results.json in eval dir)")
    args = parser.parse_args()

    eval_dir = str(Path(args.eval_dir).resolve())
    if not Path(eval_dir).exists():
        print(f"Error: eval directory not found: {eval_dir}", file=sys.stderr)
        sys.exit(1)

    result = run_eval(
        eval_dir=eval_dir,
        embedding_url=args.embedding_url,
        vectordb_dsn=args.vectordb_dsn,
        ollama_url=args.ollama_url,
        ollama_model=args.model,
        categories=args.categories,
        top_k=args.top_k,
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
    output_path = args.output or str(Path(eval_dir) / "eval_results.json")
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
