from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / "src" / "voiceops" / "web"


def test_live_provenance_is_visible_and_real_provider_specific():
    html = (WEB / "index.html").read_text(encoding="utf-8")
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert "LIVE PROVENANCE" in html
    assert "provVoiceProvider" in html
    assert "provFallbackBadge" in html
    assert "wss://agents.assemblyai.com/v1/ws" in js
    assert "audioFramesSent" in js
    assert "eventCount" in js
    assert "FALLBACK · ACTIVE" in js
    assert "FALLBACK · NONE" in js


def test_button_approval_updates_voice_session_context():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert 'notifyVoiceAgentOfExternalAction(result, "button")' in js
    assert 'notifyVoiceAgentOfExternalAction(result, "permit_button")' in js
    assert "A governed action was just executed outside the voice tool-call path" in js
    assert '"session.update"' in js


def test_bilingual_turn_lock_and_premium_landing_are_present():
    js = (WEB / "app.js").read_text(encoding="utf-8")
    welcome = (WEB / "welcome.html").read_text(encoding="utf-8")
    css = (WEB / "welcome.css").read_text(encoding="utf-8")
    assert "detectTurnLanguage" in js
    assert "reply only in natural english" in js.lower()
    assert "reply only in natural latin american spanish" in js.lower()
    assert "Governed Voice" in welcome
    assert "GLOBAL OPERATIONS" in welcome
    assert "Camera Restart" in welcome
    assert ".assistant-slot" in css
