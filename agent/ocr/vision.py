"""
Vision module: homework grading and image analysis.
Supports: LM Studio local VLM, Zhipu GLM-4V, Qwen-VL.
"""
import base64
import io
from pathlib import Path
from typing import Optional

import requests
from rich.console import Console

from agent.config import MODELS, get_active_vision_model
from agent.tutoring.prompts import HOMEWORK_GRADING_PROMPT

console = Console()


def _call_vision_api(image_data: str, mime_type: str, prompt: str, config=None) -> str:
    """Generic OpenAI-compatible vision API call. Works with LM Studio, Zhipu, Qwen."""
    if config is None:
        config = get_active_vision_model()

    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": config.model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_data}",
                        },
                    },
                ],
            }
        ],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }

    console.print(f"[dim]Vision: {config.provider}/{config.model}...[/dim]")
    resp = requests.post(
        f"{config.base_url}/chat/completions",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def _encode_image(image_path: str) -> tuple:
    """Encode an image file to base64, return (mime_type, base64_string)."""
    path = Path(image_path)
    suffix = path.suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp", ".gif": "image/gif"}
    mime_type = mime_map.get(suffix, "image/jpeg")
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return mime_type, encoded


def grade_homework(image_path: str, subject_context: str = "", question_context: str = "") -> str:
    """Grade a student's homework from an image using available vision model."""
    with console.status("[cyan]正在识别和批改作业...[/cyan]"):
        mime_type, image_data = _encode_image(image_path)
        prompt = HOMEWORK_GRADING_PROMPT
        if subject_context:
            prompt += f"\n\n科目: {subject_context}"
        if question_context:
            prompt += f"\n题目信息: {question_context}"
        return _call_vision_api(image_data, mime_type, prompt)


def analyze_diagram(image_path: str, subject_context: str = "") -> str:
    """Analyze a diagram/graph in an exam question."""
    with console.status("[cyan]正在分析图像...[/cyan]"):
        mime_type, image_data = _encode_image(image_path)
        prompt = f"""请分析这张 A-Level {subject_context} 相关的图片/图表。
1. 用中文描述图中内容
2. 解释这张图/图表说明了什么概念
3. 用一个巧妙的比喻帮助理解
4. 给出相关的考试注意事项
"""
        return _call_vision_api(image_data, mime_type, prompt)
