"""
Pattern system: loads exam technique patterns from JSON files under data/patterns/.
Each file follows the naming convention: {board}_{subject_code}.json

Adding a new exam board or subject = adding a new JSON file. No code change needed.
"""
import json
from pathlib import Path
from typing import Optional

from .config import PATTERNS_DIR, SUBJECT_BY_CODE

PATTERNS: dict = {}


def _load_all_patterns():
    """Load all pattern JSON files from data/patterns/ into memory."""
    global PATTERNS
    PATTERNS.clear()
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
    for f in sorted(PATTERNS_DIR.glob("*.json")):
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
            code = data.get("subject_code", "")
            for key, pattern in data.get("patterns", {}).items():
                pattern.setdefault("subject", code)
                PATTERNS[key] = pattern
        except (json.JSONDecodeError, KeyError) as e:
            print(f"[patterns] Skipping {f.name}: {e}")


def reload():
    """Force reload all patterns from disk."""
    _load_all_patterns()


def get_pattern(subject_code: str, topic_keywords: str) -> Optional[dict]:
    """Find matching exam pattern by subject code + topic keywords."""
    if not PATTERNS:
        _load_all_patterns()

    topic_lower = topic_keywords.lower()
    best_match = None
    best_score = 0

    for key, pattern in PATTERNS.items():
        if pattern.get("subject") != subject_code:
            continue
        topic = pattern.get("topic", "").lower()
        score = sum(1 for word in topic_lower.split() if word in topic)
        if score > best_score:
            best_score = score
            best_match = pattern

    return best_match


def list_patterns_by_subject(subject_code: str) -> list:
    if not PATTERNS:
        _load_all_patterns()
    return [
        {"key": key, "topic": p.get("topic", "")}
        for key, p in PATTERNS.items()
        if p.get("subject") == subject_code
    ]


def format_pattern_for_prompt(pattern: dict) -> str:
    if not pattern:
        return ""

    lines = [f"## {pattern.get('topic', '')}"]
    lines.append("\n### 题型识别")
    for item in pattern.get("question_recognition", []):
        lines.append(f"- {item}")

    lines.append("\n### 标准答题步骤")
    for item in pattern.get("answer_template", []):
        lines.append(f"- {item}")

    lines.append("\n### 常见扣分点")
    for item in pattern.get("common_mistakes", []):
        lines.append(f"- {item}")

    lines.append("\n### 关键词/公式")
    for item in pattern.get("keywords", []):
        lines.append(f"- {item}")

    if pattern.get("analogy"):
        lines.append(f"\n### 推荐比喻\n{pattern['analogy']}")

    return "\n".join(lines)


def add_pattern(subject_code: str, key: str, pattern: dict):
    """Programmatically add a pattern and persist to the correct JSON file."""
    subject = SUBJECT_BY_CODE.get(subject_code)
    if not subject:
        raise ValueError(f"Unknown subject: {subject_code}")
    fpath = subject.pattern_file
    if fpath.exists():
        with open(fpath, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"board": subject.board, "subject_code": subject_code, "patterns": {}}
    pattern["subject"] = subject_code
    data["patterns"][key] = pattern
    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    PATTERNS[key] = pattern


# Load on first import
_load_all_patterns()
