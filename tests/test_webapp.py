from voiceops.webapp import DemoSessionStore, MAX_TRANSCRIPT_CHARS


def test_web_demo_starts_safe_and_empty() -> None:
    store = DemoSessionStore()
    state = store.snapshot()
    assert state["mode"] == "synthetic_demo"
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
