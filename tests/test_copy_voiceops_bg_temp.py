from pathlib import Path
import shutil

def test_copy_voiceops_bg_asset_into_branch():
    dst = Path(__file__).resolve().parents[1] / "src" / "voiceops" / "web" / "assets" / "voiceops-bg.png"
    if dst.exists() and dst.stat().st_size > 10_000:
        return
    src = Path(
        "/home/rlopez/inneros/inneros_core/var/local_execution/worktrees/"
        "Rafa-Innerchispa__inneros-voiceops-assemblyai/chatgpt__voiceops-live-validation/"
        "src/voiceops/web/assets/voiceops-bg.png"
    )
    assert src.exists(), f"missing hero asset source and repo asset: {dst}"
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    assert dst.stat().st_size == src.stat().st_size
