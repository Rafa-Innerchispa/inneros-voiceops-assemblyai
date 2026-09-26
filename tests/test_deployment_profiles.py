from __future__ import annotations

from pathlib import Path

from voiceops.webapp import _deployment_profile


def test_cloud_run_deployment_profile(monkeypatch) -> None:
    monkeypatch.setenv("VOICEOPS_DEPLOYMENT_MODE", "cloud_run")
    profile = _deployment_profile("synthetic")
    assert profile["mode"] == "cloud_run"
    assert profile["label"] == "GOOGLE CLOUD RUN"
    assert profile["compute"] == "Google Cloud Run"
    assert profile["local_inference"] is False


def test_sovereign_local_deployment_profile(monkeypatch) -> None:
    monkeypatch.setenv("VOICEOPS_DEPLOYMENT_MODE", "sovereign_local")
    profile = _deployment_profile("amd5")
    assert profile["mode"] == "sovereign_local"
    assert profile["label"] == "SOVEREIGN LOCAL"
    assert profile["inference"] == "AMD / Qwen local"
    assert profile["local_inference"] is True


def test_judge_ui_exposes_both_deployment_planes() -> None:
    html = Path("src/voiceops/web/index.html").read_text(encoding="utf-8")
    js = Path("src/voiceops/web/app.js").read_text(encoding="utf-8")
    for token in (
        "cloudPlaneCard",
        "localPlaneCard",
        "deploymentBadge",
        "runtimeModeLabel",
        "runtimeInference",
    ):
        assert token in html
        assert token in js
    assert "Google Cloud Run" in html
    assert "AMD / Qwen local" in html
    assert "ONE PRODUCT · TWO DEPLOYMENT PLANES" in html
