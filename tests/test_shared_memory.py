from __future__ import annotations

from pathlib import Path

from voiceops.shared_memory import SharedMemoryBridge
from voiceops.webapp import DemoSessionStore


def test_synthetic_shared_memory_is_truth_labeled_and_network_free() -> None:
    bridge = SharedMemoryBridge(mode="synthetic")
    recalled = bridge.recall("north access incident")
    assert recalled["status"] == "synthetic"
    assert recalled["truth"] == "SYNTHETIC"
    assert recalled["count"] >= 1
    assert recalled["provider"] == "judge-safe-memory"


def test_voiceops_shared_memory_defaults_to_voiceops_receiver_port(monkeypatch) -> None:
    monkeypatch.delenv("PERSONAL_BRAIN_URL", raising=False)
    bridge = SharedMemoryBridge(mode="synthetic")
    assert bridge.base_url == "http://127.0.0.1:8231"


def test_shared_memory_refuses_unverified_write() -> None:
    bridge = SharedMemoryBridge(mode="synthetic")
    receipt = bridge.remember_verified(
        correlation_id="corr_test",
        summary="action happened",
        evidence_ref="evidence://voiceops/test",
        source_truth="SYNTHETIC",
        verification_passed=False,
    )
    assert receipt["stored"] is False
    assert receipt["status"] == "blocked"


def test_synthetic_writeback_can_be_recalled_by_correlation_id() -> None:
    bridge = SharedMemoryBridge(mode="synthetic")
    receipt = bridge.remember_verified(
        correlation_id="corr_memory_001",
        summary="Governed work order created after explicit approval.",
        evidence_ref="evidence://voiceops/corr_memory_001/WO-DEMO",
        source_truth="SYNTHETIC",
        verification_passed=True,
    )
    recalled = bridge.recall("corr_memory_001")
    assert receipt["stored"] is True
    assert recalled["truth"] == "SYNTHETIC"
    assert recalled["count"] >= 1
    assert any(
        hit.get("metadata", {}).get("correlation_id") == "corr_memory_001"
        for hit in recalled["hits"]
    )


def test_web_demo_recall_reason_writeback_and_cross_agent_cycle() -> None:
    store = DemoSessionStore(memory_bridge=SharedMemoryBridge(mode="synthetic"))
    proposed = store.submit_intent("Review the north access incident and create a work order if appropriate.")
    assert proposed["shared_memory"]["before_action"]["count"] >= 1
    assert proposed["shared_memory"]["before_action"]["truth"] == "SYNTHETIC"
    evidence = store.evidence()
    assert any(event["kind"] == "shared_memory_recalled" for event in evidence["events"])

    completed = store.approve_pending("Yes, I authorize it.")
    shared = completed["shared_memory"]
    assert shared["writeback"]["stored"] is True
    assert shared["writeback"]["verification_passed"] is True
    assert shared["cross_agent_recall"]["count"] >= 1
    final_evidence = store.evidence()
    kinds = [event["kind"] for event in final_evidence["events"]]
    assert "shared_memory_writeback" in kinds
    assert "cross_agent_memory_recall" in kinds


def test_live_memory_failure_never_blocks_governed_demo() -> None:
    bridge = SharedMemoryBridge(
        mode="live",
        base_url="http://127.0.0.1:1",
        timeout_seconds=0.01,
    )
    store = DemoSessionStore(memory_bridge=bridge)
    state = store.submit_intent("Review the incident.")
    assert state["pending_approval"] is True
    assert state["shared_memory"]["before_action"]["status"] == "unavailable"
    assert state["shared_memory"]["before_action"]["truth"] == "UNVERIFIED"


def test_judge_ui_exposes_truth_labeled_shared_memory_loop() -> None:
    html = Path("src/voiceops/web/index.html").read_text(encoding="utf-8")
    js = Path("src/voiceops/web/app.js").read_text(encoding="utf-8")
    css = Path("src/voiceops/web/styles.css").read_text(encoding="utf-8")
    for token in ("flowVoice", "flowMemory", "flowReason", "flowApprove", "flowAct", "flowVerify", "flowShare"):
        assert token in html
        assert token in js
    assert "Personal Brain / Cognee" in html
    assert "memoryBeforeTruth" in html
    assert "memoryAfterTruth" in html
    assert "renderMemory" in js
    assert ".memory-proof-grid" in css
    assert '<button id="orbitAssembly"' in html
    assert '<button id="orbitRecall"' in html
    assert '<button id="orbitReason"' in html
    assert '<button id="orbitPermit"' in html
    assert '<button id="orbitProof"' in html
    assert 'output: {voice: "diego"' in js
    assert 'recall_verified_context' in js
    assert '/api/tool/recall' in js
    assert 'button:not(.signal-core):not(.orbit-node):hover:not(:disabled)' in css
    assert ".voice-stage:hover .orbit-node" in css
    assert "@keyframes orbitNodeSpin" in css
