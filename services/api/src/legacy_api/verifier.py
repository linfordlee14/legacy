"""OIDC token verification (AUTHENTICATION 4.1 to 4.2).

The API is a resource server: the managed OIDC provider (Supabase Auth as the
default decision) performs primary authentication and MFA ceremonies and signs
tokens; this module verifies signature, issuer, audience, and expiry, and
exposes the claims the authentication layer needs (subject, MFA evidence,
auth_time, session id).
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient

# amr values accepted as proof of a second factor (AUTHENTICATION 4.2:
# passkeys preferred, TOTP fallback, SMS is not an accepted factor).
MFA_AMR_VALUES = {"webauthn", "hwk", "swk", "totp", "otp", "mfa"}

KeyProvider = Callable[[str], Any]


class TokenError(Exception):
    """Verification failed; the reason is safe to log but not to echo."""


@dataclass(frozen=True)
class VerifiedToken:
    subject: str
    claims: dict[str, Any]

    @property
    def mfa_satisfied(self) -> bool:
        """True when the token attests a second factor.

        Supabase expresses this as aal == 'aal2'; generic OIDC providers use
        amr entries. Either satisfies the check; absence of both fails it.
        """
        if self.claims.get("aal") == "aal2":
            return True
        amr = self.claims.get("amr") or []
        values = {
            entry.get("method") if isinstance(entry, dict) else entry for entry in amr
        }
        return bool(values & MFA_AMR_VALUES)

    @property
    def auth_time(self) -> int | None:
        value = self.claims.get("auth_time")
        return int(value) if value is not None else None

    @property
    def session_ref(self) -> str:
        """A stable per-session identifier for audit correlation."""
        return str(
            self.claims.get("session_id")
            or self.claims.get("sid")
            or self.claims.get("jti")
            or ""
        )


class TokenVerifier:
    def __init__(self, issuer: str, audience: str, key_provider: KeyProvider) -> None:
        self._issuer = issuer
        self._audience = audience
        self._key_provider = key_provider

    def verify(self, token: str) -> VerifiedToken:
        try:
            key = self._key_provider(token)
            claims = jwt.decode(
                token,
                key=key,
                algorithms=["RS256", "ES256"],
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "sub", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise TokenError(str(exc)) from exc
        return VerifiedToken(subject=str(claims["sub"]), claims=claims)


def jwks_key_provider(jwks_url: str) -> KeyProvider:
    """Production key provider: JWKS with caching via PyJWKClient."""
    client = PyJWKClient(jwks_url, cache_keys=True)

    def provide(token: str) -> Any:
        return client.get_signing_key_from_jwt(token).key

    return provide
