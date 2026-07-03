"""Unit tests for MFA claim evaluation and the progressive rate limiter."""

from legacy_api.auth import FailureRateLimiter
from legacy_api.verifier import VerifiedToken


def token_with(claims: dict) -> VerifiedToken:
    return VerifiedToken(subject="s", claims=claims)


class TestMfaClaims:
    def test_supabase_aal2_satisfies(self) -> None:
        assert token_with({"aal": "aal2"}).mfa_satisfied

    def test_amr_totp_satisfies(self) -> None:
        assert token_with({"amr": ["totp"]}).mfa_satisfied

    def test_amr_webauthn_object_form_satisfies(self) -> None:
        assert token_with({"amr": [{"method": "webauthn"}]}).mfa_satisfied

    def test_password_only_is_not_mfa(self) -> None:
        assert not token_with({"amr": ["pwd"]}).mfa_satisfied

    def test_absent_claims_are_not_mfa(self) -> None:
        assert not token_with({}).mfa_satisfied

    def test_aal1_is_not_mfa(self) -> None:
        assert not token_with({"aal": "aal1"}).mfa_satisfied


class TestFailureRateLimiter:
    def test_no_delay_below_threshold(self) -> None:
        limiter = FailureRateLimiter(threshold=3)
        for _ in range(2):
            limiter.record_failure("k")
        assert limiter.retry_after("k") == 0

    def test_cooldown_at_threshold_and_progressive_growth(self) -> None:
        limiter = FailureRateLimiter(threshold=2, base_cooldown_s=30, max_cooldown_s=3600)
        limiter.record_failure("k")
        limiter.record_failure("k")
        first = limiter.retry_after("k")
        assert 0 < first <= 30
        limiter.record_failure("k")
        assert limiter.retry_after("k") > first

    def test_cap_applies(self) -> None:
        limiter = FailureRateLimiter(threshold=1, base_cooldown_s=30, max_cooldown_s=60)
        for _ in range(10):
            limiter.record_failure("k")
        assert limiter.retry_after("k") <= 60

    def test_reset_clears_key(self) -> None:
        limiter = FailureRateLimiter(threshold=1)
        limiter.record_failure("k")
        limiter.reset("k")
        assert limiter.retry_after("k") == 0

    def test_keys_are_independent(self) -> None:
        limiter = FailureRateLimiter(threshold=1)
        limiter.record_failure("a")
        assert limiter.retry_after("b") == 0
