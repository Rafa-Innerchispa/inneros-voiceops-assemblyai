from voiceops.adapters.local_qwen import LocalQwenReasoner
from voiceops.webapp import _deployment_profile, _reasoning_mode, build_gateway_factory


def _facts():
    return {
        "event_id": "evt-1",
        "event_type": "camera_offline",
        "severity": "medium",
        "source_id": "cam-1",
        "zone_id": "north",
        "action_candidate": {
            "action_type": "create_work_order",
            "summary": "Create a bounded demo work order.",
            "requires_approval": True,
            "payload": {"priority": "high", "source_event_id": "evt-1"},
        },
    }


def test_local_qwen_preserves_governed_action_boundary():
    def fake_post(_endpoint, payload, _timeout):
        assert payload["model"] == "qwen2.5-coder:7b"
        return {"message": {"content": '{"summary":"Local Qwen confirms the bounded action."}'}}

    reasoner = LocalQwenReasoner(post_json=fake_post)
    result = reasoner.propose(_facts())

    assert result.proposal.action_type == "create_work_order"
    assert result.proposal.requires_approval is True
    assert result.proposal.payload == {"priority": "high", "source_event_id": "evt-1"}
    assert result.proposal.summary == "Local Qwen confirms the bounded action."
    assert result.route["provider"] == "local-intel-4"
    assert result.route["truth"] == "LIVE_MODEL_RESPONSE"
    assert result.route["external_fallback"] is False


def test_local_qwen_deployment_truth_label():
    profile = _deployment_profile("localqwen")
    assert profile["mode"] == "sovereign_local"
    assert profile["inference"] == "Intel / Qwen local"
    assert profile["local_inference"] is True
    assert _reasoning_mode({"provider": "local-intel-4", "truth": "LIVE_MODEL_RESPONSE"}) == "local_qwen_live"


def test_gateway_factory_accepts_localqwen():
    gateway = build_gateway_factory("localqwen")()
    assert isinstance(gateway.reasoner, LocalQwenReasoner)
