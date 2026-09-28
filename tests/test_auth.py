from __future__ import annotations

import json
import threading
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from voiceops.auth import AuthPrincipal, VoiceOpsAuth, hash_password, verify_password
from voiceops.inneros_system_bridge import _restart_proposal
from voiceops.webapp import VoiceOpsDemoServer


def test_password_hash_and_session_tamper_fail_closed() -> None:
    encoded = hash_password("Judge-VoiceOps-Strong-2026!")
    assert verify_password("Judge-VoiceOps-Strong-2026!", encoded) is True
    assert verify_password("wrong-password", encoded) is False

    auth = VoiceOpsAuth(session_secret="session-secret-for-tests")
    token = auth.issue_session(
        AuthPrincipal(
            subject="judge:demo",
            role="judge",
            display_name="VoiceOps Judge",
            auth_source="judge_credentials",
        )
    )
    assert auth.parse_session(token).role == "judge"
    assert auth.parse_session(token + "tampered") is None


def test_judge_credentials_create_restricted_principal() -> None:
    encoded = hash_password("Judge-VoiceOps-Strong-2026!")
    auth = VoiceOpsAuth(
        session_secret="session-secret-for-tests",
        judge_user="judge",
        judge_password_hash=encoded,
    )
    principal = auth.authenticate_judge("judge", "Judge-VoiceOps-Strong-2026!")
    assert principal is not None
    assert principal.role == "judge"
    assert principal.auth_source == "judge_credentials"
    assert auth.authenticate_judge("judge", "not-the-password") is None


def test_oauth_begin_uses_inneros_issuer_and_pkce() -> None:
    auth = VoiceOpsAuth(
        issuer="https://auth.pcdoctor.ai",
        client_id="voiceops",
        redirect_uri="https://voiceops.creatorcore.ai/auth/callback",
        session_secret="session-secret-for-tests",
    )
    url, flow = auth.begin_oauth()
    assert url.startswith("https://auth.pcdoctor.ai/authorize?")
    assert "code_challenge_method=S256" in url
    assert "client_id=voiceops" in url
    assert flow.count(".") == 1


def test_network_restart_requires_exact_allowlisted_target() -> None:
    proposal = _restart_proposal("Restart U7")
    assert proposal is not None
    assert proposal["tool"] == "voiceops_restart_network_device"
    assert proposal["args"]["entity_id"] == "button.u7_lite_restart"

    assert _restart_proposal("Restart the network") is None
    assert _restart_proposal("Restart camera estudio") is None


def test_http_auth_gate_blocks_anonymous_and_allows_judge_session() -> None:
    encoded = hash_password("Judge-VoiceOps-Strong-2026!")
    auth = VoiceOpsAuth(
        session_secret="session-secret-for-tests",
        judge_user="judge",
        judge_password_hash=encoded,
    )
    server = VoiceOpsDemoServer(
        ("127.0.0.1", 0),
        auth_required=True,
        auth=auth,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        try:
            urlopen(base + "/api/state", timeout=3)  # noqa: S310
        except HTTPError as exc:
            assert exc.code == 401
        else:
            raise AssertionError("anonymous access must be blocked")

        login = Request(
            base + "/api/auth/judge-login",
            data=json.dumps(
                {"username": "judge", "password": "Judge-VoiceOps-Strong-2026!"}
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(login, timeout=3) as response:  # noqa: S310
            cookie = response.headers.get("Set-Cookie", "").split(";", 1)[0]
            payload = json.loads(response.read().decode("utf-8"))
        assert payload["principal"]["role"] == "judge"
        assert cookie.startswith("voiceops_session=")

        request = Request(base + "/api/state", headers={"Cookie": cookie})
        with urlopen(request, timeout=3) as response:  # noqa: S310
            state = json.loads(response.read().decode("utf-8"))
        assert state["auth"]["authenticated"] is True
        assert state["auth"]["principal"]["role"] == "judge"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
