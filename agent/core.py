"""
Core agent: multi-provider LLM routing, tool calling, conversation management.
"""
import json
import re
from datetime import datetime
from typing import Optional

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .config import get_active_tutor, get_active_vision_model, MODELS
from .prompts import SYSTEM_PROMPT, WELCOME_MESSAGE
from .retriever import search_textbooks, search_past_papers, get_collection_stats
from .patterns import get_pattern, format_pattern_for_prompt, PATTERNS
from .vision import grade_homework, analyze_diagram

console = Console()

# ── Tool Definitions for function calling ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_textbook",
            "description": "搜索教材/课本内容。当学生问概念性问题、需要知识解释时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词，如 'Le Chatelier principle' 或 'integration by parts'"},
                    "subject_code": {"type": "string", "description": "科目代码: 9701/9702/9708/9709"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_past_paper",
            "description": "搜索历年真题。当学生问做题、考试题怎么解时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "subject_code": {"type": "string", "description": "科目代码: 9701/9702/9708/9709"},
                    "paper_type": {"type": "string", "description": "试卷类型: qp(题目)/ms(答案)/er(考官报告)"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_exam_pattern",
            "description": "获取某题型的考试套路模板。包含：题型识别方法、标准答题步骤、常见扣分点、关键词。",
            "parameters": {
                "type": "object",
                "properties": {
                    "subject_code": {"type": "string", "description": "科目代码: 9701/9702/9708/9709"},
                    "topic_keywords": {"type": "string", "description": "题目关键词，如 'equilibrium' / 'integration' / 'essay'"},
                },
                "required": ["subject_code", "topic_keywords"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grade_homework_image",
            "description": "批改学生上传的作业图片。只在学生明确上传了图片且需要批改时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "image_description": {"type": "string", "description": "图片内容的描述"},
                    "subject_context": {"type": "string", "description": "科目代码"},
                },
                "required": ["image_description"],
            },
        },
    },
]


class Agent:
    def __init__(self):
        self.conversation = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.current_subject = None

    def _call_llm(self, messages: list, model_key: str = "tutor") -> str:
        config = MODELS[model_key]
        if not config.api_key:
            raise ValueError(f"No API key configured for {model_key}. Set environment variables.")

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "tools": TOOLS,
            "tool_choice": "auto",
        }

        resp = requests.post(
            f"{config.base_url}/chat/completions",
            headers=headers,
            json=payload,
            timeout=120,
        )
        resp.raise_for_status()
        return resp.json()

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool call and return the result as a string."""
        console.print(f"[dim]🔧 调用工具: {tool_name}...[/dim]")

        if tool_name == "search_textbook":
            results = search_textbooks(
                arguments.get("query", ""),
                arguments.get("subject_code"),
            )
            if not results:
                return "教材中未找到相关内容。改为用通用知识回答。"
            return "\n\n".join(
                f"[教材]{r['metadata'].get('filename', '')}\n{r['content'][:1500]}"
                for r in results[:3]
            )

        elif tool_name == "search_past_paper":
            results = search_past_papers(
                arguments.get("query", ""),
                arguments.get("subject_code"),
                arguments.get("paper_type"),
            )
            if not results:
                return "未找到匹配的真题。改为用通用知识回答。"
            return "\n\n".join(
                f"[真题 {r['metadata'].get('year','')} {r['metadata'].get('type','')}]\n{r['content'][:1500]}"
                for r in results[:3]
            )

        elif tool_name == "get_exam_pattern":
            pattern = get_pattern(
                arguments.get("subject_code", ""),
                arguments.get("topic_keywords", ""),
            )
            if pattern:
                return format_pattern_for_prompt(pattern)
            else:
                return f"该科目暂无此 topic 的套路模板。可用通用考试技巧：先识别题型→回忆相关公式/概念→分步骤解答→检查单位和有效数字。"

        elif tool_name == "grade_homework_image":
            return "图片批改功能需要学生直接上传图片。请提示学生使用 `/grade <图片路径>` 命令。"

        else:
            return f"Unknown tool: {tool_name}"

    def _detect_subject(self, text: str) -> Optional[str]:
        """Detect subject from text keywords."""
        text_lower = text.lower()
        subject_keywords = {
            "9701": ["化学", "chemistry", "chem", "mole", "equilibrium", "organic", "enthalpy", "titration", "periodic table", "bond", "electro", "9701"],
            "9702": ["物理", "physics", "phys", "velocity", "force", "energy", "circuit", "wave", "magnetic", "kinetic", "momentum", "9702"],
            "9708": ["经济", "economics", "econ", "demand", "supply", "inflation", "gdp", "market", "fiscal", "monetary", "elasticity", "9708"],
            "9709": ["数学", "math", "maths", "integr", "differenti", "calculus", "algebra", "trig", "vector", "matrix", "9709", "equation", "function"],
        }
        scores = {}
        for code, keywords in subject_keywords.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[code] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    def chat(self, user_input: str, image_path: Optional[str] = None) -> str:
        """Process a chat message with optional image."""
        # Detect subject
        detected = self._detect_subject(user_input)
        if detected and detected != self.current_subject:
            self.current_subject = detected

        # Build user message
        user_msg = {"role": "user", "content": user_input}
        self.conversation.append(user_msg)

        # If image provided, handle it here (vision model handles separately for now)
        if image_path:
            try:
                subject = self.current_subject or "未知科目"
                grading_result = grade_homework(image_path, subject)
                self.conversation.append({
                    "role": "assistant",
                    "content": f"📸 **作业批改结果**\n\n{grading_result}",
                })
                return grading_result
            except Exception as e:
                error_msg = f"批改失败: {str(e)}。请确保设置了 ZHIPU_API_KEY 或 DASHSCOPE_API_KEY。"
                self.conversation.append({"role": "assistant", "content": error_msg})
                return error_msg

        # Prepare messages for API (keep last 20 to manage context)
        api_messages = [self.conversation[0]]  # system prompt
        api_messages.extend(self.conversation[-19:])  # last 19 messages

        # Call LLM
        with console.status("[cyan]思考中...[/cyan]"):
            try:
                response = self._call_llm(api_messages)
            except Exception as e:
                error_msg = f"❌ 调用 LLM 失败: {str(e)}\n请检查 API key 是否设置正确。"
                self.conversation.append({"role": "assistant", "content": error_msg})
                return error_msg

        msg = response["choices"][0]["message"]

        # Handle tool calls recursively
        max_tool_rounds = 3
        for _ in range(max_tool_rounds):
            if msg.get("tool_calls"):
                # Add assistant message with tool calls
                api_messages.append(msg)

                for tool_call in msg["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}
                    tool_result = self._execute_tool(tool_name, arguments)

                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    })

                # Get next response
                response = self._call_llm(api_messages)
                msg = response["choices"][0]["message"]
            else:
                break

        # Extract final response
        final_content = msg.get("content", "")
        self.conversation.append({"role": "assistant", "content": final_content})

        return final_content

    def reset(self):
        self.conversation = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.current_subject = None

    def set_subject(self, subject_code: str):
        subject_names = {
            "9701": "Chemistry",
            "9702": "Physics",
            "9708": "Economics",
            "9709": "Mathematics",
        }
        self.current_subject = subject_code
        name = subject_names.get(subject_code, subject_code)
        self.conversation.append({
            "role": "system",
            "content": f"当前科目已切换到: {name} ({subject_code})",
        })
        return f"已切换到 {name} ({subject_code})"
