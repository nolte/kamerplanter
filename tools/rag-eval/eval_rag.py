#!/usr/bin/env python3
"""Standalone RAG quality benchmark runner.

No dependency on the Kamerplanter backend — connects directly to:
  - Embedding Service (HTTP)
  - VectorDB / pgvector (PostgreSQL)
  - LLM / Ollama (HTTP)

Usage:
  python eval_rag.py                                     # Full benchmark (100 questions)
  python eval_rag.py --smoke                             # Quick smoke test (abort on first failure)
  python eval_rag.py --resume                            # Resume interrupted run from partial results
  python eval_rag.py --categories diagnostik duengung    # Only specific categories
  python eval_rag.py --retrieval-only                    # Debug retrieval without LLM generation
  python eval_rag.py --top-k 10                          # Retrieve more chunks (default: 5)
  python eval_rag.py --doc-language de                   # Filter chunks by language (de/en/all)
  python eval_rag.py --prompt-language en                # System prompt language (default: de)
  python eval_rag.py --model gemma3:4b                   # Use specific Ollama model
  python eval_rag.py --output results.json               # Custom output path
  python eval_rag.py --embedding-url http://host:8080    # Custom embedding service URL
  python eval_rag.py --ollama-url http://host:11434      # Custom Ollama URL
  python eval_rag.py --vectordb-dsn "host=... dbname=..."  # Custom PostgreSQL DSN

Environment variables (used as defaults when CLI args are not provided):
  EMBEDDING_SERVICE_URL   Embedding service URL        (default: http://localhost:8080)
  VECTORDB_DSN            PostgreSQL connection string  (default: localhost:5433/kamerplanter_vectors)
  LLM_API_URL             Ollama API URL               (default: http://localhost:11434)
  LLM_MODEL               Ollama model name            (default: gemma3:4b)
  EVAL_DATA_DIR           Directory with benchmark YAML (default: tests/rag-eval/)
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

_EXTRACTION_SUFFIX = {
    "de": "Zitiere konkrete Schritte, Werte und Reihenfolgen aus dem Kontext. Nutze NUR den Kontext. Erfinde nichts.",
    "en": "Quote specific steps, values, and sequences from the context. Use ONLY the provided context. Do not make up facts.",
}

_TYPED_PROMPTS: dict[str, dict[str, str]] = {
    "diagnosis": {
        "de": (
            "Du bist ein Pflanzenberater. Antworte auf Deutsch, kurz und fachlich korrekt. "
            "Nenne: 1) Diagnose (Naehrstoff/Schaedling), 2) ob mobil/immobil und welche Blaetter betroffen, "
            "3) Ursachen (pH, EC pruefen), 4) Massnahmen. "
            "Nenne NUR die wahrscheinlichste Diagnose, nicht was es NICHT ist. "
        ),
        "en": (
            "You are a plant care advisor. Answer concisely and technically correct. "
            "State: 1) Diagnosis (nutrient/pest), 2) whether mobile/immobile and which leaves affected, "
            "3) Causes (check pH, EC), 4) Remedies. "
            "State ONLY the most likely diagnosis, not what it is NOT. "
            "Answer in the SAME LANGUAGE as the user's question. "
        ),
    },
    "howto": {
        "de": (
            "Du bist ein Pflanzenberater. Antworte auf Deutsch, kurz und praktisch. "
            "Gib eine konkrete Schritt-fuer-Schritt-Anleitung. "
            "Nenne exakte Werte (Mengen, Temperaturen, Zeiten, Reihenfolgen) aus dem Kontext. "
            "Nummeriere die Schritte. "
            "WICHTIG: Verwende KEINE Diagnose-Struktur. Antworte NICHT mit '1) Diagnose', "
            "'2) Mobil/Immobil'. Gib stattdessen eine praktische Anleitung. "
        ),
        "en": (
            "You are a plant care advisor. Answer concisely and practically. "
            "Provide a concrete step-by-step guide. "
            "State exact values (amounts, temperatures, times, sequences) from the context. "
            "Number the steps. "
            "IMPORTANT: Do NOT use a diagnosis structure. Do NOT answer with '1) Diagnosis', "
            "'2) Mobile/Immobile'. Instead, provide a practical guide. "
            "Answer in the SAME LANGUAGE as the user's question. "
        ),
    },
    "factual": {
        "de": (
            "Du bist ein Pflanzenberater. Antworte auf Deutsch, kurz und fachlich korrekt. "
            "Beantworte die Frage direkt mit konkreten Fakten, Werten und Empfehlungen aus dem Kontext. "
            "Erklaere kurz warum. "
            "WICHTIG: Verwende KEINE Diagnose-Struktur. Antworte NICHT mit '1) Diagnose', "
            "'2) Mobil/Immobil', '3) Ursachen', '4) Massnahmen'. "
            "Beantworte die Frage stattdessen direkt und erklaerend. "
        ),
        "en": (
            "You are a plant care advisor. Answer concisely and technically correct. "
            "Answer the question directly with concrete facts, values, and recommendations from the context. "
            "Briefly explain why. "
            "IMPORTANT: Do NOT use a diagnosis structure. Do NOT answer with '1) Diagnosis', "
            "'2) Mobile/Immobile', '3) Causes', '4) Remedies'. "
            "Instead, answer the question directly and explanatorily. "
            "Answer in the SAME LANGUAGE as the user's question. "
        ),
    },
}

# Question type auto-detection keywords
_HOWTO_PATTERNS = re.compile(
    r"(?i)(reihenfolge|wie\s+(mische|mach|starte|bereite|soll\s+ich|trockne|keime|berechne|stelle|ueberw[ei]nter|pflege)|"
    r"schritt|anleitung|wann\s+(starte|beginne|soll|kann\s+ich|ernte|pflanze)|"
    r"how\s+(do|should|to)|step|procedure|order|"
    r"welche.*reihenfolge|in\s+welcher|wie\s+oft|wie\s+viel|wie\s+lange|"
    r"muss\s+ich|brauche\s+ich|kann\s+ich.*verwenden|soll\s+ich.*duengen|"
    r"soll\s+ich.*giessen|wie\s+funktioniert|"
    r"wie\s+stelle\s+ich|wie\s+beuge|tipps)",
)
_DIAGNOSIS_PATTERNS = re.compile(
    r"(?i)(gelb|braun|welk|fleck|symptom|mangel|schae?dling|krank|"
    r"trueb|runoff|drift|fliegen|streifen|krusten|klebrig|"
    r"yellow|brown|wilt|spot|deficien|pest|disease|"
    r"haengt.*schlaff|kuemmer|Gespinst|Schimmel|faul|"
    r"stirbt|verfaerb|vergilb|was.*fehlt|was.*stimmt.*nicht|was.*ist.*das)",
)


def _classify_question(question: dict) -> str:
    """Determine question type: 'diagnosis', 'howto', or 'factual'.

    Uses explicit question_type field if set, otherwise auto-detects from
    question text with keyword heuristics.
    """
    explicit = question.get("question_type")
    if explicit in ("diagnosis", "howto", "factual"):
        return explicit

    q_text = question.get("question", "")

    if _HOWTO_PATTERNS.search(q_text):
        return "howto"
    if _DIAGNOSIS_PATTERNS.search(q_text):
        return "diagnosis"
    return "factual"


def _get_system_prompt(question_type: str, lang: str) -> str:
    """Build system prompt from question type + extraction suffix."""
    base = _TYPED_PROMPTS.get(question_type, _TYPED_PROMPTS["factual"])
    prompt = base.get(lang, base["de"])
    suffix = _EXTRACTION_SUFFIX.get(lang, _EXTRACTION_SUFFIX["de"])
    return prompt + suffix


# Backward compatibility
_SYSTEM_PROMPTS: dict[str, str] = {
    "de": _get_system_prompt("diagnosis", "de"),
    "en": _get_system_prompt("diagnosis", "en"),
}
RAG_SYSTEM_PROMPT = _SYSTEM_PROMPTS["de"]

_LANG_TO_TSCONFIG: dict[str, str] = {"de": "german", "en": "english"}


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


# ── Service clients (no backend imports) ────────────────────────────


def embed_text(
    text: str,
    service_url: str,
    model: str = "multilingual-e5-base",
    prefix: str = "",
) -> list[float]:
    """Call the embedding service to get a vector."""
    resp = httpx.post(
        f"{service_url}/embed",
        json={"texts": [text], "model": model, "prefix": prefix},
        timeout=60.0,
    )
    resp.raise_for_status()
    return resp.json()["embeddings"][0]


def search_chunks(
    embedding: list[float],
    dsn: str,
    top_k: int = 10,
    query_text: str = "",
    doc_language: str | None = None,
) -> list[dict]:
    """Hybrid search combining vector cosine similarity and BM25 full-text search.

    Uses Reciprocal Rank Fusion (RRF) to merge rankings from both methods.
    Falls back to pure vector search if query_text is empty.
    """
    embedding_str = f"[{','.join(str(v) for v in embedding)}]"

    # Build language filter clause
    lang_filter = ""
    lang_params: list = []
    if doc_language and doc_language != "all":
        lang_filter = "AND language = %s"
        lang_params = [doc_language]

    if not query_text:
        # Pure vector search fallback
        sql = f"""
            SELECT source_key, source_type, title, content, metadata,
                   1 - (embedding <=> %s::vector) AS score
            FROM ai_vector_chunks
            WHERE TRUE {lang_filter}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
        """
        with psycopg.connect(dsn) as conn:
            rows = conn.execute(
                sql, (embedding_str, *lang_params, embedding_str, top_k),
            ).fetchall()
        return [
            {"source_key": r[0], "title": r[2], "content": r[3], "score": float(r[5])}
            for r in rows
        ]

    # Select tsquery regconfig based on doc language
    query_regconfig = _LANG_TO_TSCONFIG.get(doc_language, "german") if doc_language and doc_language != "all" else "german"

    # Hybrid search with RRF
    sql = f"""
        WITH vector_results AS (
            SELECT source_key, source_type, title, content, metadata,
                   1 - (embedding <=> %s::vector) AS cosine_score,
                   ROW_NUMBER() OVER (ORDER BY embedding <=> %s::vector) AS vector_rank
            FROM ai_vector_chunks
            WHERE TRUE {lang_filter}
            ORDER BY embedding <=> %s::vector
            LIMIT 50
        ),
        text_results AS (
            SELECT source_key, source_type, title, content, metadata,
                   ts_rank_cd(search_text, to_tsquery(%s::regconfig, %s)) AS text_score,
                   ROW_NUMBER() OVER (
                       ORDER BY ts_rank_cd(search_text, to_tsquery(%s::regconfig, %s)) DESC
                   ) AS text_rank
            FROM ai_vector_chunks
            WHERE search_text @@ to_tsquery(%s::regconfig, %s)
            {lang_filter}
            ORDER BY text_score DESC
            LIMIT 50
        )
        SELECT
            COALESCE(v.source_key, t.source_key) AS source_key,
            COALESCE(v.source_type, t.source_type) AS source_type,
            COALESCE(v.title, t.title) AS title,
            COALESCE(v.content, t.content) AS content,
            COALESCE(v.metadata, t.metadata) AS metadata,
            COALESCE(v.cosine_score, 0) AS cosine_score,
            (
                0.3 / (60.0 + COALESCE(v.vector_rank, 51))
                + 0.7 / (60.0 + COALESCE(t.text_rank, 51))
            ) AS rrf_score
        FROM vector_results v
        FULL OUTER JOIN text_results t ON v.source_key = t.source_key
        ORDER BY rrf_score DESC
        LIMIT %s
    """
    # Build OR-based tsquery with both umlaut variants for German stemmer compatibility
    # Filter common German stop words that add noise to OR queries
    _stop = {"meine", "mein", "eine", "sind", "noch", "nicht", "wird", "werden",
             "kann", "wie", "was", "die", "der", "das", "den", "dem", "des",
             "ein", "und", "oder", "aber", "auch", "nach", "bei", "mit",
             "von", "aus", "hat", "haben", "ist", "war", "sehr", "schon"}
    words = [w for w in re.findall(r"[a-zA-ZäöüÄÖÜßa-z]{3,}", query_text)
             if w.lower() not in _stop]
    terms = set()
    for w in words:
        terms.add(w)
        # digraph→umlaut (Blaetter→Blätter)
        w_umlaut = w
        for digraph, umlaut in [("ae", "ä"), ("oe", "ö"), ("ue", "ü"),
                                 ("Ae", "Ä"), ("Oe", "Ö"), ("Ue", "Ü")]:
            w_umlaut = w_umlaut.replace(digraph, umlaut)
        if w_umlaut != w:
            terms.add(w_umlaut)
    or_query = " | ".join(sorted(terms)) if terms else query_text
    with psycopg.connect(dsn) as conn:
        rows = conn.execute(
            sql,
            (embedding_str, embedding_str, *lang_params, embedding_str,
             query_regconfig, or_query, query_regconfig, or_query,
             query_regconfig, or_query, *lang_params, top_k),
        ).fetchall()

    return [
        {"source_key": r[0], "title": r[2], "content": r[3],
         "score": float(r[6]),  # rrf_score (column 7), not cosine_score (column 6)
         "cosine_score": float(r[5])}
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
            "options": {"num_predict": 768, "temperature": 0.1},
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
    retrieval_only: bool = False,
    doc_language: str | None = None,
    prompt_language: str = "de",
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
    embedding = embed_text(query, embedding_url, prefix="query: ")
    chunks = search_chunks(embedding, vectordb_dsn, top_k, query_text=query, doc_language=doc_language)

    if retrieval_only:
        print(f"\n  {'─' * 60}")
        print(f"  {q_id}: {q_text}")
        print(f"  Expected topics: {', '.join(expected_topics)}")
        print(f"  Retrieved {len(chunks)} chunks:")
        for i, c in enumerate(chunks, 1):
            print(f"    [{i}] {c['source_key']:<40s} score={c['score']:.4f}")
            print(f"        {c['title']}")
            # Show first 120 chars of content for quick inspection
            preview = c["content"].replace("\n", " ")[:120]
            print(f"        {preview}...")
        return QuestionResult(
            id=q_id, category=category, score=0.0,
            topic_hits=[], topic_misses=expected_topics,
            false_positives=[], answer="[retrieval-only]", chunks_used=len(chunks),
            chunk_sources=[c["source_key"] for c in chunks],
        )

    # 2. Generate
    chunk_texts = "\n\n---\n\n".join(
        f"[{c['source_key']}] {c['title']}\n{c['content']}" for c in chunks
    )
    user_message = f"Kontext aus Wissensdatenbank:\n{chunk_texts}\n\n"
    if context_str:
        user_message += f"Situation: {context_str}\n\n"
    user_message += f"Frage: {q_text}"

    try:
        q_type = _classify_question(question)
        system_prompt = _get_system_prompt(q_type, prompt_language)
        answer = llm_generate(system_prompt, user_message, ollama_url, ollama_model)
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
        answer=answer[:2000],
        chunks_used=len(chunks),
        chunk_sources=[c["source_key"] for c in chunks],
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
            chunks_used=0,
            chunk_sources=r.get("chunk_sources", []),
        ))
    return results


def run_eval(
    eval_dir: str,
    embedding_url: str,
    vectordb_dsn: str,
    ollama_url: str,
    ollama_model: str,
    categories: list[str] | None = None,
    top_k: int = 10,
    smoke: bool = False,
    retrieval_only: bool = False,
    doc_language: str | None = None,
    prompt_language: str = "de",
    resume: bool = False,
) -> EvalResult:
    """Run the full topic-match benchmark.

    If *smoke* is True, load smoke_questions.yaml instead and abort on the
    first failing question (fast gate before a full benchmark run).
    If *retrieval_only* is True, skip LLM generation and only show retrieved chunks.
    If *resume* is True, load eval_results_partial.json and skip already-evaluated questions.
    """
    eval_path = Path(eval_dir)

    questions_file = "smoke_questions.yaml" if smoke else "benchmark_questions.yaml"
    with open(eval_path / questions_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    with open(eval_path / "topic_synonyms.yaml", encoding="utf-8") as f:
        synonyms = yaml.safe_load(f).get("topics", {})

    min_pass = data.get("min_pass_score", 0.70)
    questions = data.get("questions", [])
    if categories:
        questions = [q for q in questions if q.get("category") in categories]

    # Partial results file — written after every question so progress survives crashes
    partial_path = str(Path(eval_dir) / "eval_results_partial.json")

    # Resume: load previous results and skip already-evaluated questions
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
    print(f"[{label}] Running {len(remaining)}/{len(questions)} questions against {ollama_model} ...\n")

    for i, question in enumerate(remaining, 1):
        try:
            result = evaluate_question(
                question, synonyms, embedding_url, vectordb_dsn, ollama_url, ollama_model, top_k,
                retrieval_only=retrieval_only,
                doc_language=doc_language,
                prompt_language=prompt_language,
            )
        except Exception as exc:
            q_id = question.get("id", "unknown")
            print(f"  [{len(results) + 1:3d}/{len(questions)}] {q_id:<20s} ERROR  {type(exc).__name__}: {exc!s:.80s}")
            errors += 1
            continue
        if not retrieval_only:
            q_type = _classify_question(question)
            status = "PASS" if result.score >= min_pass else "FAIL"
            print(f"  [{len(results) + 1:3d}/{len(questions)}] {result.id:<20s} {result.score:.2f}  {status}  ({q_type})")
            if result.topic_misses:
                print(f"           misses: {', '.join(result.topic_misses)}")
            if result.false_positives:
                print(f"           FPs:    {', '.join(result.false_positives)}")
        results.append(result)

        # Write partial results after every question
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
    parser.add_argument("--embedding-url", default=EMBEDDING_URL, help="Embedding service URL")
    parser.add_argument("--vectordb-dsn", default=VECTORDB_DSN, help="PostgreSQL DSN for VectorDB")
    parser.add_argument("--ollama-url", default=OLLAMA_URL, help="Ollama API URL")
    parser.add_argument("--model", default=OLLAMA_MODEL, help="LLM model name")
    parser.add_argument("--eval-dir", default=EVAL_DATA_DIR, help="Directory with benchmark YAML files")
    parser.add_argument("--categories", nargs="*", help="Only evaluate these categories")
    parser.add_argument("--smoke", action="store_true", help="Run only smoke-test golden-file questions (fast sanity check)")
    parser.add_argument("--retrieval-only", action="store_true", help="Show retrieved chunks per question without LLM generation (debug retrieval)")
    parser.add_argument("--top-k", type=int, default=5, help="Number of RAG chunks to retrieve")
    parser.add_argument("--doc-language", default=None, choices=["de", "en", "all"],
                        help="Filter knowledge chunks by language (default: no filter)")
    parser.add_argument("--prompt-language", default="de", choices=["de", "en"],
                        help="System prompt language for LLM (default: de)")
    parser.add_argument("--resume", action="store_true",
                        help="Resume from eval_results_partial.json, skipping already-evaluated questions")
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
        smoke=args.smoke,
        retrieval_only=args.retrieval_only,
        doc_language=args.doc_language,
        prompt_language=args.prompt_language,
        resume=args.resume,
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
