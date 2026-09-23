from __future__ import annotations

from pathlib import Path


DOC = Path("docs/SUBMISSION_PACKAGE.md")


def _section(text: str, heading: str, next_heading: str) -> str:
    start_marker = f"## {heading}"
    end_marker = f"## {next_heading}"
    assert start_marker in text, f"missing section: {heading}"
    assert end_marker in text, f"missing section: {next_heading}"
    return text.split(start_marker, 1)[1].split(end_marker, 1)[0].strip()


def _plain(value: str) -> str:
    return value.replace("**", "").replace(chr(96), "").strip()


def test_lablab_submission_copy_respects_field_limits() -> None:
    text = DOC.read_text(encoding="utf-8")
    title = _plain(_section(text, "Final title", "Short description"))
    short = _plain(_section(text, "Short description", "Long description"))
    long_description = _plain(_section(text, "Long description", "What is novel"))

    assert len(title) <= 50, f"title is {len(title)} chars"
    assert len(short) <= 255, f"short description is {len(short)} chars"
    assert len(long_description.split()) >= 100, "long description must be at least 100 words"
