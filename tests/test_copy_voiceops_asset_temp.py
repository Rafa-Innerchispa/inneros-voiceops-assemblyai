from pathlib import Path

def test_voiceops_hero_asset_is_packaged():
    asset=Path(__file__).resolve().parents[1]/"src"/"voiceops"/"web"/"assets"/"voiceops.png"
    assert asset.exists()
    assert asset.stat().st_size > 100_000
