"""
Multi-provider LLM configuration, subject registry, and routing.
Supports CAIE A-Level, and designed to extend to IB, Edexcel, AQA, etc.
"""
import os
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# Load .env if exists
def _load_dotenv():
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    key, val = key.strip(), val.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = val
_load_dotenv()
CHROMA_DIR = DATA_DIR / "chroma_db"
TEXTBOOK_DIR = DATA_DIR / "textbooks"
PAPERS_DIR = DATA_DIR / "past_papers"
GUIDES_DIR = DATA_DIR / "study_guides"
PATTERNS_DIR = DATA_DIR / "patterns"

# ── API Keys (set via environment or .env) ──
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"

ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"

QWEN_API_KEY = os.getenv("DASHSCOPE_API_KEY", os.getenv("QWEN_API_KEY", ""))
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 4096


# Model Registry — latest model IDs as of 2026-05
MODELS = {
    "tutor": LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.7,
        max_tokens=4096,
    ),
    "reasoner": LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.3,
        max_tokens=8192,
    ),
    "fast": LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.1,
        max_tokens=1024,
    ),
    "vision": LLMConfig(
        provider="zhipu",
        model="glm-4v-plus",
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_BASE_URL,
        temperature=0.3,
        max_tokens=2048,
    ),
    "vision_qwen": LLMConfig(
        provider="qwen",
        model="qwen-vl-max",
        api_key=QWEN_API_KEY,
        base_url=QWEN_BASE_URL,
        temperature=0.3,
        max_tokens=2048,
    ),
}


def get_active_vision_model() -> LLMConfig:
    for key in ["vision", "vision_qwen"]:
        config = MODELS[key]
        if config.api_key:
            return config
    return MODELS["vision"]


def get_active_tutor() -> LLMConfig:
    cfg = MODELS["tutor"]
    if not cfg.api_key:
        raise ValueError(
            "No LLM API key configured. Set DEEPSEEK_API_KEY, ZHIPU_API_KEY, "
            "or DASHSCOPE_API_KEY environment variable."
        )
    return cfg


# ═══════════════════════════════════════════════════════════
# Subject Registry — parameterized for multiple exam boards
# ═══════════════════════════════════════════════════════════

@dataclass
class Subject:
    """A subject within an exam board. Future-proof: add IB, Edexcel, AQA, etc."""
    board: str           # "caie-alevel", "caie-igcse", "ib-dp", "edexcel-ial", "aqa-alevel"
    code: str            # "9701", "0620", "chem-hl", "WCH11"
    name: str            # "Chemistry", "Physics"
    level: str = "A-Level"  # "AS", "A-Level", "IGCSE", "HL", "SL"

    @property
    def display_name(self) -> str:
        labels = {
            "caie-alevel": "CAIE AS & A Level",
            "caie-igcse": "CAIE IGCSE",
            "ib-dp": "IB Diploma",
            "edexcel-ial": "Edexcel IAL",
            "aqa-alevel": "AQA A-Level",
        }
        board_label = labels.get(self.board, self.board)
        return f"{board_label} {self.name} ({self.code})"

    @property
    def pattern_file(self) -> Path:
        return PATTERNS_DIR / f"{self.board}_{self.code}.json"

    @property
    def prompt_context(self) -> dict:
        """Returns a dict for prompt template interpolation."""
        labels = {
            "caie-alevel": "Cambridge International AS & A Level",
            "caie-igcse": "Cambridge IGCSE",
            "ib-dp": "International Baccalaureate Diploma",
            "edexcel-ial": "Edexcel International A Level",
            "aqa-alevel": "AQA A Level",
        }
        return {
            "board_full": labels.get(self.board, self.board),
            "board_short": self.board,
            "code": self.code,
            "name": self.name,
            "level": self.level,
        }


# Current active subjects (the 4 we support in MVP)
SUBJECTS: List[Subject] = [
    Subject(board="caie-alevel", code="9701", name="Chemistry"),
    Subject(board="caie-alevel", code="9702", name="Physics"),
    Subject(board="caie-alevel", code="9708", name="Economics"),
    Subject(board="caie-alevel", code="9709", name="Mathematics"),
]

# Quick lookup
SUBJECT_BY_CODE: dict[str, Subject] = {s.code: s for s in SUBJECTS}


def register_subject(board: str, code: str, name: str, level: str = "A-Level") -> Subject:
    """Add a new subject at runtime (e.g. for future expansion)."""
    s = Subject(board=board, code=code, name=name, level=level)
    if code not in SUBJECT_BY_CODE:
        SUBJECTS.append(s)
        SUBJECT_BY_CODE[code] = s
    return s


def ensure_dirs():
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
