"""REQ-031 §3.1 / NFR-007 — unit tests for ``AiAuditLogger``.

The audit trail must never store question/answer plaintext, only a sha256 hash
and the answer length.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.domain.services.ai_audit_logger import AiAuditLogger, hash_question


def test_record_stores_only_hash_and_length() -> None:
    repo = MagicMock()
    repo.create.side_effect = lambda entry: entry
    logger = AiAuditLogger(repo)

    question = "Soll ich in Woche 4 der Bluete den PK-Boost starten?"
    entry = logger.record(
        tenant_key="home",
        user_key="anna",
        endpoint="tips",
        question=question,
        answer_length=142,
        model_name="gemma3:12b",
        status="ok",
    )

    assert entry.question_hash == hash_question(question)
    assert entry.answer_length == 142
    # The plaintext question never appears anywhere on the entry.
    dumped = entry.model_dump_json()
    assert question not in dumped
    assert "PK-Boost" not in dumped
    assert entry.created_at is not None


def test_record_swallows_repo_failure() -> None:
    repo = MagicMock()
    repo.create.side_effect = RuntimeError("db down")
    logger = AiAuditLogger(repo)

    # A failed audit write must not raise into the user-facing KI call.
    entry = logger.record(
        tenant_key="home",
        endpoint="public.ask",
        question="Was ist VPD?",
        answer_length=10,
        status="ok",
    )
    assert entry.question_hash == hash_question("Was ist VPD?")


def test_hash_question_is_stable_and_non_reversible() -> None:
    assert hash_question("abc") == hash_question("abc")
    assert hash_question("abc") != hash_question("abcd")
    assert len(hash_question("abc")) == 64  # sha256 hex digest
