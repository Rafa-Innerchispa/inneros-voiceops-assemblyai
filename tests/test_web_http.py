from __future__ import annotations

import json
import threading
from urllib.request import Request, urlopen

from voiceops.webapp import VoiceOpsDemoServer


def _get_json(url: str) -> dict[str, object]:
    with urlopen(url, timeout=3) as response:  # noqa: S310 - local ephemeral test server
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, object]) -> dict[str, object]:
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlopen(request, timeout=3) as response:  # noqa: S310 - local ephemeral test server
        return json.loads(response.read().decode("utf-8"))


def test_http_server_serves_ui_and_governed_api_flow() -> None:
    server = VoiceOpsDemoServer(("127.0.0.1", 0))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        with urlopen(base + "/", timeout=3) as response:  # noqa: S310 - local ephemeral test server
            page = response.read().decode("utf-8")
        assert "InnerOS VoiceOps" in page
        assert "NO PROD WRITES" in page

        health = _get_json(base + "/healthz")
        assert health["ok"] is True
        assert health["service"] == "inneros-voiceops"
        assert health["production_writes"] is False

        initial = _get_json(base + "/api/state")
        assert initial["production_writes"] is False

        proposed = _post_json(base + "/api/intent", {"transcript": "Revisa la incidencia"})
        assert proposed["pending_approval"] is True
        assert proposed["proposal"]["action_type"] == "create_work_order"  # type: ignore[index]

        blocked = _post_json(base + "/api/approve", {"transcript": "Si crees que hace falta"})
        assert blocked["pending_approval"] is True
        assert blocked["action"] is None

        completed = _post_json(base + "/api/approve", {"transcript": "Si, autorizo"})
        assert completed["pending_approval"] is False
        assert completed["action"]["status"] == "created"  # type: ignore[index]

        replay = _get_json(base + "/api/replay")
        assert replay["replay_source"] == "captured_evidence_only"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)


def test_browser_voice_agent_uses_progressive_tools_and_spanish_stt_context() -> None:
    server = VoiceOpsDemoServer(("127.0.0.1", 0), live_voice_enabled=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base = f"http://{host}:{port}"
    try:
        with urlopen(base + "/app.js", timeout=3) as response:  # noqa: S310 - local ephemeral test server
            script = response.read().decode("utf-8")
        assert 'tools: [inspectTool]' in script
        assert 'tools: [approveTool]' in script
        assert 'tools: []' in script
        assert 'language_codes: ["es"]' in script
        assert '"sí autorizo"' in script
        assert '"acceso norte"' in script
        assert 'execution_mode: "interactive"' in script
        assert 'handledToolCallIds: new Set()' in script
        assert 'pendingToolCalls.some((call) => call.call_id === msg.call_id)' in script
        assert 'handledToolCallIds.add(call.call_id)' in script
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
