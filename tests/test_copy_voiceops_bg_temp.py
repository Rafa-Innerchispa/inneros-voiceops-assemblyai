from pathlib import Path
import shutil

def test_copy_voiceops_bg_asset_into_branch():
    src=Path("/home/rlopez/inneros/inneros_core/var/local_execution/worktrees/Rafa-Innerchispa__inneros-voiceops-assemblyai/chatgpt__voiceops-live-validation/src/voiceops/web/assets/voiceops-bg.png")
    dst=Path(__file__).resolve().parents[1]/"src"/"voiceops"/"web"/"assets"/"voiceops-bg.png"
    assert src.exists()
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src,dst)
    assert dst.exists()
    assert dst.stat().st_size == src.stat().st_size
    print("COPIED", dst, dst.stat().st_size)
