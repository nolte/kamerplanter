import hashlib
from datetime import UTC, datetime, timedelta

from app.domain.engines.invitation_engine import InvitationEngine


class TestCreateInvitationToken:
    def test_returns_raw_and_hash(self):
        raw, hashed = InvitationEngine.create_invitation_token()
        assert len(raw) > 20
        assert len(hashed) == 64  # SHA-256 hex digest

    def test_hash_matches_raw(self):
        raw, hashed = InvitationEngine.create_invitation_token()
        expected = hashlib.sha256(raw.encode()).hexdigest()
        assert hashed == expected

    def test_tokens_are_unique(self):
        tokens = {InvitationEngine.create_invitation_token()[0] for _ in range(10)}
        assert len(tokens) == 10


class TestHashToken:
    def test_deterministic(self):
        h1 = InvitationEngine.hash_token("test-token")
        h2 = InvitationEngine.hash_token("test-token")
        assert h1 == h2

    def test_different_inputs_different_hashes(self):
        h1 = InvitationEngine.hash_token("token-a")
        h2 = InvitationEngine.hash_token("token-b")
        assert h1 != h2


class TestCalculateExpiry:
    def test_default_7_days(self):
        before = datetime.now(UTC)
        expiry = InvitationEngine.calculate_expiry()
        after = datetime.now(UTC)
        assert expiry >= before + timedelta(days=6, hours=23)
        assert expiry <= after + timedelta(days=7, minutes=1)

    def test_custom_days(self):
        before = datetime.now(UTC)
        expiry = InvitationEngine.calculate_expiry(days=14)
        assert expiry >= before + timedelta(days=13, hours=23)


class TestIsExpired:
    def test_future_not_expired(self):
        future = datetime.now(UTC) + timedelta(days=1)
        assert InvitationEngine.is_expired(future) is False

    def test_past_is_expired(self):
        past = datetime.now(UTC) - timedelta(days=1)
        assert InvitationEngine.is_expired(past) is True

    def test_naive_datetime_past(self):
        past = datetime.now() - timedelta(days=1)
        assert InvitationEngine.is_expired(past) is True


class TestCanAccept:
    def test_valid_acceptance(self):
        ok, reason = InvitationEngine.can_accept(
            is_expired=False, is_pending=True, is_already_member=False
        )
        assert ok is True
        assert reason == ""

    def test_expired(self):
        ok, reason = InvitationEngine.can_accept(
            is_expired=True, is_pending=True, is_already_member=False
        )
        assert ok is False
        assert "expired" in reason.lower()

    def test_not_pending(self):
        ok, reason = InvitationEngine.can_accept(
            is_expired=False, is_pending=False, is_already_member=False
        )
        assert ok is False
        assert "pending" in reason.lower()

    def test_already_member(self):
        ok, reason = InvitationEngine.can_accept(
            is_expired=False, is_pending=True, is_already_member=True
        )
        assert ok is False
        assert "member" in reason.lower()
