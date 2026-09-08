from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from voiceops.gateway import VoiceGateway


@dataclass(slots=True)
class StreamingState:
    connected: bool = False
    provider_session_id: str | None = None
    final_turns: int = 0
    partial_turns: int = 0
    context_updates: int = 0
    errors: list[str] = field(default_factory=list)
    last_gateway_result: dict[str, object] | None = None


class AssemblyAIStreamingAdapter:
    """Thin AssemblyAI v3 streaming adapter around the governed VoiceGateway.

    The AssemblyAI SDK is imported lazily so the core demo and tests remain
    runnable without cloud credentials or optional audio dependencies.

    Live audio contract for Universal-3.5 Pro Realtime:
    - PCM16
    - mono
    - 16 kHz by default
    - explicit session termination

    VoiceOps owns governance/orchestration. AssemblyAI owns speech recognition.
    """

    AUDIO_ENCODING = "pcm_s16le"
    AUDIO_CHANNELS = 1

    def __init__(
        self,
        gateway: VoiceGateway,
        *,
        api_key: str | None = None,
        speech_model: str = "universal-3-5-pro",
        sample_rate: int = 16000,
    ) -> None:
        if sample_rate <= 0:
            raise ValueError("sample_rate must be positive")
        self.gateway = gateway
        self.api_key = api_key or os.getenv("ASSEMBLYAI_API_KEY")
        self.speech_model = speech_model
        self.sample_rate = sample_rate
        self.state = StreamingState()
        self._client: Any = None

    @property
    def audio_contract(self) -> dict[str, object]:
        return {
            "encoding": self.AUDIO_ENCODING,
            "channels": self.AUDIO_CHANNELS,
            "sample_rate": self.sample_rate,
        }

    def handle_turn(self, transcript: str, *, end_of_turn: bool) -> dict[str, object] | None:
        if not transcript.strip():
            return None
        if not end_of_turn:
            self.state.partial_turns += 1
            return None
        self.state.final_turns += 1
        result = self.gateway.process_final_transcript(transcript)
        self.state.last_gateway_result = result
        return result

    def connect(self, *, agent_context: str | None = None) -> None:
        if not self.api_key:
            raise RuntimeError("ASSEMBLYAI_API_KEY is required for live streaming")

        try:
            from assemblyai.streaming.v3 import (
                StreamingClient,
                StreamingClientOptions,
                StreamingEvents,
                StreamingParameters,
            )
        except ImportError as exc:  # pragma: no cover - optional live dependency
            raise RuntimeError(
                "Install the optional dependency with: pip install -e '.[assemblyai]'"
            ) from exc

        self._client = StreamingClient(StreamingClientOptions(api_key=self.api_key))

        def on_begin(_client: Any, event: Any) -> None:
            self.state.connected = True
            self.state.provider_session_id = getattr(event, "id", None)
            self.gateway.evidence.add_event(
                "assemblyai_session_started",
                provider_session_id=self.state.provider_session_id,
                speech_model=self.speech_model,
                audio_contract=self.audio_contract,
            )

        def on_turn(_client: Any, event: Any) -> None:
            self.handle_turn(
                getattr(event, "transcript", ""),
                end_of_turn=bool(getattr(event, "end_of_turn", False)),
            )

        def on_termination(_client: Any, event: Any) -> None:
            self.state.connected = False
            self.gateway.evidence.add_event(
                "assemblyai_session_terminated",
                audio_duration_seconds=getattr(event, "audio_duration_seconds", None),
            )

        def on_error(_client: Any, error: Any) -> None:
            message = str(error)
            self.state.errors.append(message)
            self.gateway.evidence.add_event("assemblyai_error", message=message)

        self._client.on(StreamingEvents.Begin, on_begin)
        self._client.on(StreamingEvents.Turn, on_turn)
        self._client.on(StreamingEvents.Termination, on_termination)
        self._client.on(StreamingEvents.Error, on_error)

        params: dict[str, Any] = {
            "speech_model": self.speech_model,
            "sample_rate": self.sample_rate,
        }
        if agent_context:
            params["agent_context"] = agent_context
        self._client.connect(StreamingParameters(**params))

    def update_agent_context(self, text: str) -> None:
        """Refresh STT context after an agent reply without storing reply content.

        AssemblyAI recommends updating agent_context during a live conversation.
        Evidence intentionally records only metadata, not the potentially sensitive
        spoken/agent text itself.
        """
        normalized = text.strip()
        if not normalized:
            raise ValueError("agent_context must not be empty")
        if self._client is None:
            raise RuntimeError("connect() must be called before update_agent_context()")
        updater = getattr(self._client, "update_configuration", None)
        if not callable(updater):
            raise RuntimeError("AssemblyAI client does not support update_configuration()")
        updater(agent_context=normalized)
        self.state.context_updates += 1
        self.gateway.evidence.add_event(
            "assemblyai_agent_context_updated",
            character_count=len(normalized),
            content_recorded=False,
        )

    def stream(self, audio_source: Any) -> None:
        if self._client is None:
            raise RuntimeError("connect() must be called before stream()")
        self._client.stream(audio_source)

    def close(self) -> None:
        if self._client is not None:
            try:
                self._client.disconnect(terminate=True)
            finally:
                self.state.connected = False
                self._client = None
