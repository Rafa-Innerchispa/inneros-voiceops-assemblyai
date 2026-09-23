from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules"}
MAX_BYTES = 2_000_000

PATTERNS = [
    ("private_key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("github_classic_token", re.compile(r"ghp_[A-Za-z0-9]{30,}")),
    ("github_pat", re.compile(r"github_pat_[A-Za-z0-9_]{40,}")),
    ("openai_like_key", re.compile(r"\\bsk-[A-Za-z0-9_-]{20,}\\b")),
    ("aws_access_key", re.compile(r"\\bAKIA[0-9A-Z]{16}\\b")),
    ("assemblyai_literal", re.compile(r"ASSEMBLYAI_API_KEY\\s*=\\s*['\\\"]?([^\\s'\\\"]+)")),
]

PLACEHOLDERS = {
    "", "<server-side secret>", "<secret>", "<redacted>", "changeme", "example",
    "your-key", "your_key", "placeholder"
}


def test_release_tree_contains_no_obvious_committed_secrets() -> None:
    findings: list[tuple[str, str]] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size > MAX_BYTES:
                continue
            raw = path.read_bytes()
            if b"\\x00" in raw[:4096]:
                continue
            text = raw.decode("utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(path.relative_to(ROOT))
        for label, pattern in PATTERNS:
            for match in pattern.finditer(text):
                if label == "assemblyai_literal":
                    value = match.group(1).strip().lower()
                    if value in PLACEHOLDERS or value.startswith("$") or value.startswith("{"):
                        continue
                findings.append((rel, label))
    assert not sorted(set(findings)), f"Potential secret patterns found: {sorted(set(findings))}"
