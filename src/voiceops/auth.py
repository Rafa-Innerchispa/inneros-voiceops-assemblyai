from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


SESSION_COOKIE = "voiceops_session"
OAUTH_FLOW_COOKIE = "voiceops_oauth_flow"
DEFAULT_ISSUER = "https://auth.pcdoctor.ai"
DEFAULT_SESSION_TTL = 8 * 60 * 60
PBKDF2_ITERATIONS = 260_000


def _b64e(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64d(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = PBKDF2_ITERATIONS) -> str:
    if len(password) < 12:
        raise ValueError("password must be at least 12 characters")
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"pbkdf2_sha256${iterations}${_b64e(salt)}${_b64e(digest)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations_raw, salt_raw, digest_raw = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_raw)
        salt = _b64d(salt_raw)
        expected = _b64d(digest_raw)
    except (TypeError, ValueError):
        return False
    actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return hmac.compare_digest(actual, expected)


@dataclass(frozen=True)
class AuthPrincipal:
    subject: str
    role: str
    display_name: str
    auth_source: str

    def to_dict(self) -> dict[str, str]:
        return {
            "subject": self.subject,
            "role": self.role,
            "display_name": self.display_name,
            "auth_source": self.auth_source,
        }


class VoiceOpsAuth:
    def __init__(
        self,
        *,
        issuer: str | None = None,
        client_id: str | None = None,
        redirect_uri: str | None = None,
        session_secret: str | None = None,
        judge_user: str | None = None,
        judge_password_hash: str | None = None,
        session_ttl_seconds: int = DEFAULT_SESSION_TTL,
    ) -> None:
        self.issuer = (issuer or os.getenv("VOICEOPS_OAUTH_ISSUER") or DEFAULT_ISSUER).rstrip("/")
        self.client_id = (client_id or os.getenv("VOICEOPS_OAUTH_CLIENT_ID") or "").strip()
        self.redirect_uri = (redirect_uri or os.getenv("VOICEOPS_OAUTH_REDIRECT_URI") or "").strip()
        self.session_secret = (session_secret or os.getenv("VOICEOPS_SESSION_SECRET") or "").encode("utf-8")
        self.judge_user = (judge_user or os.getenv("VOICEOPS_JUDGE_USER") or "").strip()
        self.judge_password_hash = (
            judge_password_hash or os.getenv("VOICEOPS_JUDGE_PASSWORD_HASH") or ""
        ).strip()
        self.session_ttl_seconds = max(300, int(session_ttl_seconds))

    def configured(self) -> bool:
        return bool(self.session_secret)

    def oauth_configured(self) -> bool:
        return bool(self.configured() and self.client_id and self.redirect_uri)

    def judge_configured(self) -> bool:
        return bool(self.configured() and self.judge_user and self.judge_password_hash)

    def _sign(self, payload: dict[str, Any]) -> str:
        if not self.session_secret:
            raise ValueError("VoiceOps session secret is not configured")
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        body = _b64e(raw)
        sig = _b64e(hmac.new(self.session_secret, body.encode("ascii"), hashlib.sha256).digest())
        return f"{body}.{sig}"

    def _verify(self, token: str) -> dict[str, Any] | None:
        if not self.session_secret or "." not in token:
            return None
        body, sig = token.rsplit(".", 1)
        expected = _b64e(hmac.new(self.session_secret, body.encode("ascii"), hashlib.sha256).digest())
        if not hmac.compare_digest(sig, expected):
            return None
        try:
            payload = json.loads(_b64d(body).decode("utf-8"))
        except (ValueError, json.JSONDecodeError):
            return None
        if not isinstance(payload, dict):
            return None
        if int(payload.get("exp") or 0) <= int(time.time()):
            return None
        return payload

    def issue_session(self, principal: AuthPrincipal) -> str:
        now = int(time.time())
        return self._sign({
            "kind": "session",
            "sub": principal.subject,
            "role": principal.role,
            "name": principal.display_name,
            "src": principal.auth_source,
            "iat": now,
            "exp": now + self.session_ttl_seconds,
            "nonce": secrets.token_urlsafe(10),
        })

    def parse_session(self, token: str) -> AuthPrincipal | None:
        payload = self._verify(token)
        if not payload or payload.get("kind") != "session":
            return None
        role = str(payload.get("role") or "")
        if role not in {"owner", "admin", "judge"}:
            return None
        return AuthPrincipal(
            subject=str(payload.get("sub") or ""),
            role=role,
            display_name=str(payload.get("name") or "VoiceOps User"),
            auth_source=str(payload.get("src") or "unknown"),
        )

    def authenticate_judge(self, username: str, password: str) -> AuthPrincipal | None:
        if not self.judge_configured():
            return None
        if not hmac.compare_digest(username.strip(), self.judge_user):
            return None
        if not verify_password(password, self.judge_password_hash):
            return None
        return AuthPrincipal(
            subject=f"judge:{self.judge_user}",
            role="judge",
            display_name="VoiceOps Judge",
            auth_source="judge_credentials",
        )

    def begin_oauth(self) -> tuple[str, str]:
        if not self.oauth_configured():
            raise ValueError("central OAuth is not configured for VoiceOps")
        state = secrets.token_urlsafe(24)
        verifier = secrets.token_urlsafe(48)
        challenge = _b64e(hashlib.sha256(verifier.encode("ascii")).digest())
        now = int(time.time())
        flow_cookie = self._sign({
            "kind": "oauth_flow",
            "state": state,
            "verifier": verifier,
            "iat": now,
            "exp": now + 600,
        })
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "openid profile email",
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
        return f"{self.issuer}/authorize?{urlencode(params)}", flow_cookie

    def complete_oauth(self, *, code: str, state: str, flow_token: str) -> AuthPrincipal:
        flow = self._verify(flow_token)
        if not flow or flow.get("kind") != "oauth_flow":
            raise ValueError("OAuth flow is missing or expired")
        if not hmac.compare_digest(str(flow.get("state") or ""), state):
            raise ValueError("OAuth state mismatch")
        verifier = str(flow.get("verifier") or "")
        token_data = urlencode({
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "code_verifier": verifier,
        }).encode("utf-8")
        token_request = Request(
            f"{self.issuer}/token",
            data=token_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        with urlopen(token_request, timeout=10) as response:
            token_payload = json.loads(response.read().decode("utf-8"))
        access_token = str(token_payload.get("access_token") or "")
        if not access_token:
            raise ValueError("OAuth token endpoint did not return an access token")
        user_request = Request(
            f"{self.issuer}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            method="GET",
        )
        with urlopen(user_request, timeout=10) as response:
            profile = json.loads(response.read().decode("utf-8"))
        subject = str(profile.get("sub") or profile.get("email") or "")
        if not subject:
            raise ValueError("OAuth userinfo did not return a subject")
        raw_role = str(profile.get("role") or profile.get("voiceops_role") or "admin").lower()
        role = raw_role if raw_role in {"owner", "admin", "judge"} else "admin"
        return AuthPrincipal(
            subject=subject,
            role=role,
            display_name=str(profile.get("name") or profile.get("email") or "InnerOS User"),
            auth_source="inneros_oauth",
        )

    def public_status(self) -> dict[str, Any]:
        return {
            "required": True,
            "issuer": self.issuer,
            "oauth_configured": self.oauth_configured(),
            "judge_configured": self.judge_configured(),
            "roles": ["owner", "admin", "judge"],
        }
