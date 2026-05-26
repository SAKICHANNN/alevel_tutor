"""
Multi-provider LLM configuration and routing.
Supports: DeepSeek, ZhipuAI (GLM), Qwen (Alibaba)
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
TEXTBOOK_DIR = DATA_DIR / "textbooks"
PAPERS_DIR = DATA_DIR / "past_papers"
GUIDES_DIR = DATA_DIR / "study_guides"

# ── API Keys (set via environment) ──
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


# ── Model Registry ──
MODELS = {
    # Text reasoning (primary tutor)
    "tutor": LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.7,
        max_tokens=4096,
    ),
    # Deep thinking for complex problems
    "reasoner": LLMConfig(
        provider="deepseek",
        model="deepseek-reasoner",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.3,
        max_tokens=8192,
    ),
    # Fast/cheap for simple tasks
    "fast": LLMConfig(
        provider="deepseek",
        model="deepseek-chat",
        api_key=DEEPSEEK_API_KEY,
        base_url=DEEPSEEK_BASE_URL,
        temperature=0.1,
        max_tokens=1024,
    ),
    # Vision (homework grading, diagram analysis)
    "vision": LLMConfig(
        provider="zhipu",
        model="glm-4v-plus",
        api_key=ZHIPU_API_KEY,
        base_url=ZHIPU_BASE_URL,
        temperature=0.3,
        max_tokens=2048,
    ),
    # Alternative vision provider
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
    """Return the first available vision model."""
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
