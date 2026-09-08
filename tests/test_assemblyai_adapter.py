from voiceops.adapters.assemblyai_streaming import AssemblyAIStreamingAdapter
from voiceops.gateway import VoiceGateway


def test_partial_turn_does_not_trigger_governed_action() -> None:
    gateway = VoiceGateway()
    adapter = AssemblyAIStreamingAdapter(gateway, api_key="test-key-not-used")

    result = adapter.handle_turn("Revisa la alarma", end_of_turn=False)
    assert result is None
    assert adapter.state.partial_turns == 1
    assert gateway.evidence.proposal is None


def test_final_turn_enters_gateway() -> None:
    gateway = VoiceGateway()
    adapter = AssemblyAIStreamingAdapter(gateway, api_key="test-key-not-used")

    result = adapter.handle_turn("Revisa la alarma", end_of_turn=True)
    assert result is not None
    assert result["status"] == "approval_required"
    assert adapter.state.final_turns == 1


def test_live_connect_requires_api_key() -> None:
    gateway = VoiceGateway()
    adapter = AssemblyAIStreamingAdapter(gateway, api_key=None)
    adapter.api_key = None

    try:
        adapter.connect()
    except RuntimeError as exc:
        assert "ASSEMBLYAI_API_KEY" in str(exc)
    else:
        raise AssertionError("connect() must fail without a live API key")
