import json
from types import SimpleNamespace

from voiceops.webapp import (
    DemoSessionStore,
    MAX_TRANSCRIPT_CHARS,
    mint_voice_agent_token_from_inneros_provider,
)


def test_web_demo_starts_safe_and_empty() -> None:
    store = DemoSessionStore()
    state = store.snapshot()
    assert state["mode"] == "hybrid_live"
    assert state["production_writes"] is False
    assert state["proposal"] is None
    assert state["action"] is None


def test_web_demo_intent_reaches_guardian_and_approval_gate() -> None:
    store = DemoSessionStore()
    state = store.submit_transcript("Revisa la incidencia del acceso norte")
    assert state["pending_approval"] is True
    assert state["guardian"]["contract_projection"] == "NormalizedEvent"
    assert state["guardian"]["contract_owner"] == "Rafa-Innerchispa/inneros-physical-guardian"
    assert state["route"]["policy"] == "local_first"
    assert state["route"]["truth"] == "SYNTHETIC"
    assert state["proposal"]["action_type"] == "create_work_order"


def test_web_demo_ambiguous_approval_fails_closed() -> None:
    store = DemoSessionStore()
    store.submit_transcript("Revisa la incidencia")
    state = store.submit_transcript("Si crees que hace falta")
    assert state["pending_approval"] is True
    assert state["approval"]["approved"] is False
    assert state["action"] is None
    assert state["last_result"]["status"] == "blocked"


def test_web_demo_explicit_approval_executes_synthetic_action_and_htr() -> None:
    store = DemoSessionStore()
    store.submit_transcript("Revisa la incidencia")
    state = store.submit_transcript("Si, autorizo")
    assert state["pending_approval"] is False
    assert state["approval"]["approved"] is True
    assert state["action"]["status"] == "created"
    assert state["htr"]["classification"] == "ESTIMATED"
    assert state["production_writes"] is False


def test_web_demo_replay_uses_captured_evidence_only() -> None:
    store = DemoSessionStore()
    store.submit_transcript("Revisa la incidencia")
    store.submit_transcript("Si, autorizo")
    replay = store.replay()
    assert replay["replay_source"] == "captured_evidence_only"
    assert replay["action_id"] is not None


def test_web_demo_rejects_unbounded_transcript() -> None:
    store = DemoSessionStore()
    try:
        store.submit_transcript("x" * (MAX_TRANSCRIPT_CHARS + 1))
    except ValueError as exc:
        assert "exceeds" in str(exc)
    else:
        raise AssertionError("oversized transcript must be rejected")


def test_tool_inspect_duplicate_same_intent_is_idempotent_while_pending() -> None:
    store = DemoSessionStore()
    intent = "Revisa la incidencia del acceso norte"
    first = store.tool_inspect(intent)
    second = store.tool_inspect(intent)
    evidence = store.evidence()
    proposals = [event for event in evidence["events"] if event["kind"] == "action_proposed"]
    assert first["requires_approval"] is True
    assert second["status"] == "already_pending"
    assert second["requires_approval"] is True
    assert len(proposals) == 1


def test_tool_recall_and_inspect_return_memory_to_voice_agent() -> None:
    store = DemoSessionStore()
    recalled = store.tool_recall("qué recuerda VoiceOps del acceso norte")
    assert recalled["count"] >= 1
    assert recalled["truth"] == "SYNTHETIC"
    inspected = store.tool_inspect("Revisa la incidencia del acceso norte")
    assert inspected["memory"]["count"] >= 1
    assert inspected["memory_bridge"]["provider"] == "judge-safe-memory"


def test_tool_approve_duplicate_is_idempotent_and_does_not_reexecute() -> None:
    store = DemoSessionStore()
    store.tool_inspect("Revisa la incidencia del acceso norte")
    first = store.tool_approve("Si, autorizo")
    second = store.tool_approve("Si, autorizo")
    evidence = store.evidence()
    executions = [event for event in evidence["events"] if event["kind"] == "action_executed"]
    assert first["action"]["status"] == "created"
    assert second["status"] == "already_completed"
    assert second["action"]["action_id"] == first["action"]["action_id"]
    assert len(executions) == 1


def _real_guardian_event(event_id: str = "evt_real_001") -> dict[str, object]:
    return {
        "event_id": event_id,
        "source_id": "camera-2",
        "event_type": "zone.person.prolonged",
        "severity": "high",
        "occurred_at": "2026-09-11T12:00:00+00:00",
        "tenant_id": "tenant-demo",
        "site_id": "site-demo",
        "zone_id": "Puerta",
        "confidence": 0.93,
        "evidence_refs": [f"evidence://guardian/{event_id}"],
    }


def test_guardian_whatsapp_voice_bridge_binds_exact_event_and_requires_two_step_approval() -> None:
    store = DemoSessionStore()
    event = _real_guardian_event()
    proposed = store.submit_guardian_voice_command(event, "Revisa y abre una orden si corresponde")
    assert proposed["bridge_surface"] == "whatsapp_voice"
    assert proposed["bridge_event_id"] == "evt_real_001"
    assert proposed["pending_approval"] is True
    assert proposed["guardian"]["source"] == "physical_guardian_normalized_event"
    blocked = store.submit_guardian_voice_command(event, "Si crees que hace falta")
    assert blocked["last_result"]["status"] == "blocked"
    approved = store.submit_guardian_voice_command(event, "Sí, autorizo")
    assert approved["last_result"]["status"] == "completed"
    assert approved["action"]["details"]["source_event_id"] == "evt_real_001"
    assert approved["last_result"]["permit_single_use"] is True


def test_guardian_whatsapp_voice_bridge_rejects_event_switch_while_approval_pending() -> None:
    store = DemoSessionStore()
    store.submit_guardian_voice_command(_real_guardian_event("evt_a"), "Revisa esta incidencia")
    try:
        store.submit_guardian_voice_command(_real_guardian_event("evt_b"), "Sí, autorizo")
    except ValueError as exc:
        assert "another Guardian event" in str(exc)
    else:
        raise AssertionError("approval must stay bound to the original Guardian event")


def test_guardian_whatsapp_voice_bridge_duplicate_after_completion_is_idempotent() -> None:
    store = DemoSessionStore()
    event = _real_guardian_event()
    store.submit_guardian_voice_command(event, "Revisa esta incidencia")
    completed = store.submit_guardian_voice_command(event, "Sí, autorizo")
    duplicate = store.submit_guardian_voice_command(event, "Sí, autorizo")
    executions = [e for e in store.evidence()["events"] if e["kind"] == "action_executed"]
    assert duplicate["bridge_status"] == "already_completed"
    assert duplicate["action"]["action_id"] == completed["action"]["action_id"]
    assert len(executions) == 1


def test_inneros_provider_token_bridge_returns_only_ephemeral_token(monkeypatch, tmp_path) -> None:
    python_path = tmp_path / "python3"
    python_path.write_text("", encoding="utf-8")
    platform_path = tmp_path / "platform"
    platform_path.mkdir()
    monkeypatch.setenv("VOICEOPS_INNEROS_PROVIDER_PYTHON", str(python_path))
    monkeypatch.setenv("VOICEOPS_INNEROS_PLATFORM_PATH", str(platform_path))
    captured = {}

    def fake_runner(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"ok": True, "token": "temporary-browser-token", "expires_in_seconds": 120}) + "\n",
            stderr="",
        )

    result = mint_voice_agent_token_from_inneros_provider(runner=fake_runner)
    assert result == {
        "token": "temporary-browser-token",
        "expires_in_seconds": 120,
        "auth_source": "inneros_owner_vault",
    }
    assert captured["argv"][0] == str(python_path)
    assert captured["argv"][-2:] == [str(platform_path), "120"]
    assert "assemblyai_api_key" not in " ".join(captured["argv"]).lower()


def test_inneros_provider_token_bridge_fails_closed_without_paths(monkeypatch) -> None:
    monkeypatch.delenv("VOICEOPS_INNEROS_PROVIDER_PYTHON", raising=False)
    monkeypatch.delenv("VOICEOPS_INNEROS_PLATFORM_PATH", raising=False)
    try:
        mint_voice_agent_token_from_inneros_provider()
    except ValueError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("provider bridge must fail closed without explicit runtime paths")


class _FakeSystemBridge:
    def __init__(self):
        self.executed = []

    def status(self):
        return {"ok": True, "configured": True, "provider": "inneros-voice-mcp", "home_assistant_live": True}

    def query(self, text):
        if "sirena" in text.lower():
            return {
                "ok": True,
                "source_truth": "LIVE",
                "results": [{"tool": "alarm_intelbras_status", "result": {"ok": True}}],
                "write_proposals": [],
                "protected_proposals": [{"tool": "ha_call_service", "args": {}, "reason": "dedicated_approval_adapter_required"}],
                "detected": [{"tool": "alarm_intelbras_status", "args": {}}],
                "formatted": "Alarm status live.",
                "original_query": text,
            }
        if any(token in text.lower() for token in ("apaga", "turn off")):
            return {
                "ok": True,
                "source_truth": "LIVE",
                "results": [],
                "write_proposals": [{"tool": "ha_turn_off_light", "args": {"name_or_entity": "estudio"}}],
                "protected_proposals": [],
                "detected": [{"tool": "ha_turn_off_light", "args": {"name_or_entity": "estudio"}}],
                "formatted": "",
                "original_query": text,
            }
        return {
            "ok": True,
            "source_truth": "LIVE",
            "results": [{"tool": "ha_home_status", "result": {"ok": True, "summary": "2 cameras, lights available"}}],
            "write_proposals": [],
            "protected_proposals": [],
            "detected": [{"tool": "ha_home_status", "args": {}}],
            "formatted": "Home Assistant live: 2 cameras, lights available.",
            "original_query": text,
        }

    def execute(self, proposal):
        self.executed.append(proposal)
        return {"ok": True, "source_truth": "LIVE", "result": {"ok": True, "service": "turn_off"}}


def test_live_system_query_is_real_time_read_only_and_does_not_require_approval() -> None:
    store = DemoSessionStore(system_bridge=_FakeSystemBridge())
    result = store.tool_system_query("¿Cómo está Home Assistant?")
    assert result["ok"] is True
    assert result["source_truth"] == "LIVE"
    assert result["requires_approval"] is False
    assert "Home Assistant live" in result["formatted"]


def test_live_system_action_requires_explicit_voice_or_button_approval() -> None:
    bridge = _FakeSystemBridge()
    store = DemoSessionStore(system_bridge=bridge)
    proposed = store.tool_propose_system_action("Apaga la luz del estudio")
    assert proposed["requires_approval"] is True
    assert bridge.executed == []

    blocked = store.tool_approve("si crees que hace falta")
    assert blocked["status"] == "blocked"
    assert blocked["requires_approval"] is True
    assert bridge.executed == []

    completed = store.tool_approve("autorizar")
    assert completed["status"] == "completed"
    assert completed["requires_approval"] is False
    assert completed["action"]["status"] == "completed"
    assert bridge.executed[0]["tool"] == "ha_turn_off_light"

    duplicate = store.tool_approve("Yes, authorize")
    assert duplicate["status"] == "already_completed"
    assert len(bridge.executed) == 1


def test_protected_live_action_does_not_fall_through_generic_permit() -> None:
    store = DemoSessionStore(system_bridge=_FakeSystemBridge())
    proposed = store.tool_propose_system_action("Activa la sirena")
    assert proposed["status"] == "protected"
    assert proposed["requires_approval"] is False
    assert proposed["reason"] == "dedicated_approval_adapter_required"
