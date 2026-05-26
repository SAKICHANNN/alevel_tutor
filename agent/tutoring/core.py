"""
Core agent: multi-provider LLM routing, tool calling, conversation management.
Uses parameterized subject system — add new boards/subjects via JSON config.
"""
import json
import re
from datetime import datetime
from typing import Optional

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from agent.config import get_active_tutor, get_active_vision_model, MODELS, SUBJECTS, SUBJECT_BY_CODE
from agent.tutoring.prompts import system_prompt, welcome_message
from agent.retrieval.search import search_textbooks, search_past_papers, get_collection_stats
from agent.tutoring.patterns import get_pattern, format_pattern_for_prompt, PATTERNS
from agent.ocr.vision import grade_homework, analyze_diagram
from agent.retrieval.search import search_techniques as _search_techniques

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
            "name": "search_exam_techniques",
            "description": "搜索考试技巧和备考指南。包含 command words、常见错误、答题模板等结构化技巧。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "subject_code": {"type": "string", "description": "科目代码: 9701/9702/9708/9709"},
                },
                "required": ["query"],
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
    def __init__(self, subjects: list = None):
        self.subjects = subjects or SUBJECTS
        self._subjects_summary = " · ".join(
            f"{s.code} {s.name}" for s in self.subjects
        )
        self.conversation = [
            {"role": "system", "content": system_prompt(self._subjects_summary)},
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
            return "图片批改功能需要学生直接上传图片。请提示学生使用 `/grade <图片路径>` 命令。也可直接在聊天中附上图片。"

        elif tool_name == "search_exam_techniques":
            results = _search_techniques(
                arguments.get("query", ""),
                arguments.get("subject_code"),
            )
            if not results:
                return "未找到匹配的考试技巧。请尝试更具体的问题。"
            return "\n\n".join(
                f"[考试技巧 {r['metadata'].get('filename','')}]\n{r['content'][:1200]}"
                for r in results[:3]
            )

        elif tool_name == "get_subject_info":
            subject_code = arguments.get("subject_code", "")
            s = SUBJECT_BY_CODE.get(subject_code)
            if s:
                return f"{s.display_name} — 考试局: {s.board}, 级别: {s.level}"
            return f"科目代码 {subject_code} 不在当前支持列表中。"

        else:
            return f"Unknown tool: {tool_name}"

    def _detect_subject(self, text: str) -> Optional[str]:
        """Detect subject from text keywords — uses current subject registry."""
        text_lower = text.lower()
        scores = {}
        for s in self.subjects:
            score = 0
            # code match
            if s.code in text:
                score += 5
            # name match (English + Chinese)
            name_map = {
                "9701": ["chemistry", "chem", "化学", "mole", "equilibrium", "organic", "enthalpy", "titration", "periodic", "bond"],
                "9702": ["physics", "phys", "物理", "velocity", "force", "circuit", "wave", "momentum"],
                "9708": ["economics", "econ", "经济", "demand", "supply", "inflation", "market", "elasticity"],
                "9709": ["mathematics", "math", "maths", "数学", "integr", "differenti", "calculus", "algebra", "trig", "vector"],
            }
            keywords = name_map.get(s.code, [s.name.lower()])
            score += sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                scores[s.code] = score
        return max(scores, key=scores.get) if scores else None

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
            {"role": "system", "content": system_prompt(self._subjects_summary)},
        ]
        self.current_subject = None

    def grade(self, question: str, mark_scheme: str, student_answer: str) -> dict:
        """Grade a student answer against a mark scheme. Returns structured JSON."""
        from agent.tutoring.prompts import grading_prompt

        prompt = grading_prompt(question, mark_scheme, student_answer)
        messages = [
            {"role": "system", "content": "You are an A-Level examiner. Output valid JSON only. No markdown, no explanation."},
            {"role": "user", "content": prompt},
        ]

        try:
            resp = self._call_llm(messages, model_key="fast")
            content = resp["choices"][0]["message"]["content"]
            content = content.strip().removeprefix("```json").removesuffix("```").strip()
            return json.loads(content)
        except (json.JSONDecodeError, KeyError) as e:
            console.print(f"[yellow]Grading JSON parse failed: {e}[/yellow]")
            return {
                "score_awarded": 0, "score_max": 0, "confidence": 0.0,
                "verdict": "评分系统出错，请重试",
                "rubric": {}, "strengths": [], "mistakes": [],
                "misconception_tags": ["system_error"],
                "next_step": "请重新提交批改", "citations": [],
            }

    def set_subject(self, subject_code: str):
        s = SUBJECT_BY_CODE.get(subject_code)
        if s:
            self.current_subject = subject_code
            self.conversation.append({
                "role": "system",
                "content": f"当前科目已切换到: {s.display_name}",
            })
            return f"已切换到 {s.display_name}"
        return f"未找到科目: {subject_code}"
