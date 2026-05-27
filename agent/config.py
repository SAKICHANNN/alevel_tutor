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

# HuggingFace mirror for China access (set before any HF imports)
if not os.environ.get("HF_ENDPOINT"):
    os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")
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

LMSTUDIO_BASE_URL = os.getenv("LMSTUDIO_BASE_URL", "http://127.0.0.1:1234/v1")
LMSTUDIO_VLM_MODEL = os.getenv("LMSTUDIO_VLM_MODEL", "qwen/qwen3-vl-8b")


@dataclass
class LLMConfig:
    provider: str
    model: str
    api_key: str
    base_url: str
    temperature: float = 0.7
    max_tokens: int = 4096
    thinking: bool = False  # Enable DeepSeek thinking/reasoning mode


# Model Registry — latest model IDs as of 2026-05
MODELS = {
    "tutor": LLMConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.7,
        max_tokens=4096,
    ),
    "reasoner": LLMConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.3,
        max_tokens=8192,
        thinking=True,  # Enables step-by-step reasoning chain
    ),
    "fast": LLMConfig(
        provider="deepseek",
        model="deepseek-v4-flash",
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
    "vision_local": LLMConfig(
        provider="lmstudio",
        model=LMSTUDIO_VLM_MODEL,
        api_key="lm-studio",
        base_url=LMSTUDIO_BASE_URL,
        temperature=0.2,
        max_tokens=2048,
    ),
}


def get_active_vision_model() -> LLMConfig:
    """Return the first available vision model. Prefers local LM Studio."""
    for key in ["vision_local", "vision", "vision_qwen"]:
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
    """A subject within an exam board. Fields marked Optional are for future boards."""
    board: str           # "caie-alevel", "caie-igcse", "ib-dp", "edexcel-ial", "aqa-alevel"
    code: str            # "9701", "0620", "chem-hl", "WCH11"
    name: str            # "Chemistry", "Physics"
    level: str = "A-Level"
    
    # ── Exam-board adapter metadata ──
    syllabus_years: str = ""           # "2025-2027"
    components: dict = None            # {"P1": "Multiple Choice", "P2": "Structured", ...}
    assessment_objectives: dict = None # {"AO1": "Knowledge", "AO2": "Application", ...}
    command_words: list = None         # ["Define", "Describe", "Explain", ...]
    calculator_policy: str = ""        # "Scientific calculator allowed, no CAS"
    notation_rules: str = ""           # "3 s.f. unless exact requested"

    def __post_init__(self):
        if self.components is None: self.components = {}
        if self.assessment_objectives is None: self.assessment_objectives = {}
        if self.command_words is None: self.command_words = []

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
            "syllabus_years": self.syllabus_years,
            "components": ", ".join(f"{k}: {v}" for k, v in self.components.items()) if self.components else "",
            "assessment_objectives": ", ".join(f"{k}: {v}" for k, v in self.assessment_objectives.items()) if self.assessment_objectives else "",
            "command_words": ", ".join(self.command_words) if self.command_words else "",
            "calculator_policy": self.calculator_policy,
            "notation_rules": self.notation_rules,
        }


# Current active subjects (the 4 we support in MVP)
SUBJECTS: List[Subject] = [
    Subject(
        board="caie-alevel", code="9701", name="Chemistry",
        syllabus_years="2025-2027",
        components={
            "P1": "Multiple Choice (40q, 60min)",
            "P2": "AS Structured Questions (60 marks)",
            "P3": "Advanced Practical Skills (40 marks, 2h)",
            "P4": "A Level Structured Questions (100 marks)",
            "P5": "Planning, Analysis and Evaluation (30 marks)",
        },
        assessment_objectives={
            "AO1": "Knowledge and understanding",
            "AO2": "Handling, applying and evaluating information",
            "AO3": "Experimental skills and investigations",
        },
        command_words=["State", "Define", "Describe", "Explain", "Suggest", "Calculate", "Predict", "Compare", "Evaluate", "Deduce", "Draw"],
        calculator_policy="Scientific calculator allowed. No programmable/graphical calculators.",
        notation_rules="3 s.f. unless specified otherwise. Keep intermediate values in calculator.",
    ),
    Subject(
        board="caie-alevel", code="9702", name="Physics",
        syllabus_years="2025-2027",
        components={
            "P1": "Multiple Choice (40q, 75min)",
            "P2": "AS Structured Questions (60 marks)",
            "P3": "Advanced Practical Skills (40 marks, 2h)",
            "P4": "A Level Structured Questions (100 marks)",
            "P5": "Planning, Analysis and Evaluation (30 marks)",
        },
        assessment_objectives={
            "AO1": "Knowledge and understanding",
            "AO2": "Handling, applying and evaluating information",
            "AO3": "Experimental skills and investigations",
        },
        command_words=["State", "Define", "Describe", "Explain", "Calculate", "Show that", "Determine", "Sketch", "Plot", "Compare", "Evaluate", "Deduce"],
        calculator_policy="Scientific calculator allowed. No programmable/graphical calculators.",
        notation_rules="Show formula → substitution → answer with unit. Vector direction must be indicated.",
    ),
    Subject(
        board="caie-alevel", code="9708", name="Economics",
        syllabus_years="2026-2028",
        components={
            "P1": "Multiple Choice (30q, 60min)",
            "P2": "Data Response and Essay (40 marks, 2h)",
            "P3": "Case Study and Essay (40 marks, 2h)",
            "P4": "Data Response and Essays (60 marks, 2h)",
        },
        assessment_objectives={
            "AO1": "Knowledge and understanding (33%)",
            "AO2": "Analysis (37%)",
            "AO3": "Evaluation (30%)",
        },
        command_words=["State", "Identify", "Define", "Describe", "Explain", "Analyse", "Assess", "Evaluate", "Discuss", "Compare", "Calculate"],
        calculator_policy="Scientific calculator allowed.",
        notation_rules="Diagrams must be labelled. Quotes from extract required in data response.",
    ),
    Subject(
        board="caie-alevel", code="9709", name="Mathematics",
        syllabus_years="2026-2027",
        components={
            "P1": "Pure Mathematics 1 (75 marks, 1h50m)",
            "P2": "Pure Mathematics 2 (50 marks, 1h15m)",
            "P3": "Pure Mathematics 3 (75 marks, 1h50m)",
            "P4": "Mechanics (50 marks, 1h15m)",
            "P5": "Probability & Statistics 1 (50 marks, 1h15m)",
            "P6": "Probability & Statistics 2 (50 marks, 1h15m)",
        },
        assessment_objectives={
            "AO1": "Knowledge and understanding",
            "AO2": "Application and communication",
        },
        command_words=["Calculate", "Show that", "Find", "Solve", "Simplify", "Prove", "Sketch", "Draw", "Determine", "Verify"],
        calculator_policy="Scientific calculator allowed. NO equation solvers, NO programmable, NO graphical calculators.",
        notation_rules="Show ALL working. No marks for unsupported calculator answers. Exact values unless decimal requested. 3 s.f. standard.",
    ),
]

# Quick lookup
SUBJECT_BY_CODE: dict[str, Subject] = {s.code: s for s in SUBJECTS}


def register_subject(board: str, code: str, name: str, level: str = "A-Level", **kwargs) -> Subject:
    """Add a new subject at runtime. Extra kwargs passed to Subject constructor."""
    s = Subject(board=board, code=code, name=name, level=level, **kwargs)
    if code not in SUBJECT_BY_CODE:
        SUBJECTS.append(s)
        SUBJECT_BY_CODE[code] = s
    return s


def ensure_dirs():
    PATTERNS_DIR.mkdir(parents=True, exist_ok=True)
