from pathlib import Path

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.md").read_text(encoding="utf-8")
