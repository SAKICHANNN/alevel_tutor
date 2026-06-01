"""
Core agent: multi-provider LLM routing, tool calling, conversation management.
Uses parameterized subject system — add new boards/subjects via JSON config.

W4 updates: cost logging, error logging, conversation persistence, BudgetGuard.
"""
import json
import re
import time
import traceback
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
from agent.database import (
    save_message, save_grading_result, log_cost, log_error, check_budget,
    create_conversation, update_conversation,
)
from agent.security import detect_injection, validate_tool_call, sanitize_retrieved_content

console = Console()

# ── W5: Output sanitizer — detect self-correction artifacts ──

_SELF_CORRECTION_PATTERNS = [
    r'(?:❌|不对|等等|重新算|实际上|查到了).*?(?:不对|重新|纠正)',
    r'等等.*?重新.*?算',
]

_ASCII_ART_PATTERN = re.compile(r'[┌┐└┘├┤│─┬┴┼╭╮╰╯→←↑↓●○]')

# ── W6: KaTeX compatibility fixer ──
# Gradio renders $...$ and $$...$$ as KaTeX. LLMs often use $ for currency,
# which creates unpaired $ delimiters and causes KaTeX parse errors.

_CURRENCY_DOLLAR_RE = re.compile(r'\$(\d[\d,.]*)(?![\d$])')
_AMPERSAND_IN_MATH_RE = re.compile(r'(?<!\\)&(?!\s*amp;)')
_last_katex_fixes: dict = {"currency": 0, "stray_dollar": 0, "ampersand": 0, "ce_command": 0}
_last_raw_output: str = ""
_last_tool_calls: list = []
_last_response_time: float = 0.0
_last_model: str = ""
_last_svg_count: int = 0
_last_conv_len: int = 0
_token_limit_enabled: bool = True
_budget_enabled: bool = True


def _fix_katex(content: str) -> str:
    """Fix common patterns that cause KaTeX parse errors in Gradio Chatbot.
    
    Returns only the fixed content. Use _fix_katex_with_report() to get details."""
    return _fix_katex_with_report(content)[0]


def _fix_katex_with_report(content: str) -> tuple:
    """Fix KaTeX patterns and return (fixed_content, fix_report dict)."""
    fixes = {"currency": 0, "stray_dollar": 0, "ampersand": 0, "ce_command": 0}

    # Pre-pass: fix currency $ before scanning LaTeX blocks
    currency_matches = _CURRENCY_DOLLAR_RE.findall(content)
    fixes["currency"] = len(currency_matches)
    content = _CURRENCY_DOLLAR_RE.sub(r'\1元', content)

    # Scan LaTeX blocks with proper nesting ($$ takes priority over $)
    latex_blocks = []  # list of (start, end, is_display)
    i = 0
    while i < len(content):
        if content.startswith('$$', i):
            j = content.find('$$', i + 2)
            if j != -1:
                latex_blocks.append((i, j + 2, True))
                i = j + 2
            else:
                i += 2
        elif content[i] == '$':
            j = content.find('$', i + 1)
            if j != -1 and not content.startswith('$$', j):
                latex_blocks.append((i, j + 1, False))
                i = j + 1
            else:
                i += 1
        else:
            i += 1

    if not latex_blocks:
        before = content
        content = content.replace('$', '＄')
        fixes["stray_dollar"] = before.count('$')
        return content, fixes

    # Build result piece by piece, protecting LaTeX blocks
    result = []
    last_end = 0
    for start, end, is_display in latex_blocks:
        non_latex = content[last_end:start]
        stray_count = non_latex.count('$')
        fixes["stray_dollar"] += stray_count
        non_latex = non_latex.replace('$', '＄')
        result.append(non_latex)

        block = content[start:end]
        before_block = block
        block = _AMPERSAND_IN_MATH_RE.sub(r'\\text{ and }', block)
        if block != before_block:
            fixes["ampersand"] += before_block.count('&')
        before_block = block
        block = re.sub(r'\\ce\{([^}]+)\}', r'\\text{\1}', block)
        if block != before_block:
            fixes["ce_command"] += 1
        result.append(block)

        last_end = end

    non_latex = content[last_end:]
    fixes["stray_dollar"] += non_latex.count('$')
    non_latex = non_latex.replace('$', '＄')
    result.append(non_latex)

    return ''.join(result), fixes


def _sanitize_output(content: str) -> str:
    """Post-process LLM output: render diagrams, flag self-correction and ASCII art."""
    from agent.diagrams.renderer import render_all_diagrams
    content = render_all_diagrams(content)

    # W6: Fix KaTeX-breaking patterns — currency $ and & in math mode
    content, katex_fixes = _fix_katex_with_report(content)
    _last_katex_fixes.clear()
    _last_katex_fixes.update(katex_fixes)

    for pattern in _SELF_CORRECTION_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            if "⚠️" not in content[:200]:
                content = (
                    "⚠️ 此回答可能包含自我修正过程，部分信息请以教材为准。\n"
                    "如有疑问，请追问确认。\n\n" + content
                )
            break

    # Detect ASCII art diagrams (only if no rendered diagrams present)
    if "data:image/" not in content:
        ascii_matches = _ASCII_ART_PATTERN.findall(content)
        if len(ascii_matches) >= 3:
            content += (
                "\n\n---\n"
                "⚠️ **图表提示**：以上包含 ASCII 字符拼图，可能排版错乱。"
                "请重新提问，我会用正确的图表格式回答。"
            )

    return content

# ── Tool Definitions for function calling ──

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_textbook",
            "description": "搜索教材/课本内容。任何问题必须首先调用此工具。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "subject_code": {"type": "string", "description": "科目代码: 9701/9702/9708/9709"},
                    "n_results": {"type": "integer", "description": "需要检索多少条结果（1-50）。少则1-3条确认概念，多则30-50条系统性梳理。按信息需求判断", "default": 3},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_past_paper",
            "description": "搜索历年真题。当学生问解题方法、类似题型时触发。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索关键词"},
                    "subject_code": {"type": "string", "description": "科目代码: 9701/9702/9708/9709"},
                    "paper_type": {"type": "string", "description": "试卷类型: qp(题目)/ms(答案)/er(考官报告)"},
                    "n_results": {"type": "integer", "description": "需要检索多少条结果（1-50）。按信息需求判断", "default": 5},
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
    def __init__(self, subjects: list = None, conv_id: int = None, status_callback=None):
        self.subjects = subjects or SUBJECTS
        self._subjects_summary = " · ".join(
            f"{s.code} {s.name}" for s in self.subjects
        )
        self.conversation = [
            {"role": "system", "content": system_prompt(self._subjects_summary)},
        ]
        self.current_subject = None
        self._pending_image = None
        self.conv_id = conv_id
        self.status_callback = status_callback  # fn(str) called on tool/thinking events

    def _call_llm(self, messages: list, model_key: str = "tutor", max_retries: int = 2,
                   tools_list: list = TOOLS) -> dict:
        config = MODELS[model_key]
        if not config.api_key:
            raise ValueError(f"No API key configured for {model_key}. Set environment variables.")

        # BudgetGuard check (skippable via toggle)
        global _budget_enabled
        if _budget_enabled:
            ok, budget_msg = check_budget()
            if not ok:
                raise RuntimeError(f"预算限制: {budget_msg}")

        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": config.model,
            "messages": messages,
            "temperature": config.temperature,
        }
        global _token_limit_enabled
        if _token_limit_enabled and config.max_tokens:
            payload["max_tokens"] = config.max_tokens
        if tools_list:
            payload["tools"] = tools_list
            payload["tool_choice"] = "auto"
        if config.thinking:
            payload["thinking"] = {"type": "enabled"}

        last_error = None
        t0 = time.time()
        for attempt in range(max_retries + 1):
            try:
                resp = requests.post(
                    f"{config.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=120,
                )
                resp.raise_for_status()
                result = resp.json()
                latency_ms = int((time.time() - t0) * 1000)

                # Log cost from usage info
                usage = result.get("usage", {})
                if usage:
                    log_cost(
                        model_key=model_key,
                        model_name=config.model,
                        prompt_tokens=usage.get("prompt_tokens", 0),
                        completion_tokens=usage.get("completion_tokens", 0),
                        reasoning_tokens=usage.get("completion_tokens_details", {}).get("reasoning_tokens", 0),
                        latency_ms=latency_ms,
                        conversation_id=self.conv_id,
                    )
                return result
            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else 0
                if status == 429 and attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                if status >= 500 and attempt < max_retries:
                    time.sleep(1)
                    continue
                last_error = e
                log_error(
                    error_type="api_call",
                    error_source=f"core.py:_call_llm({model_key})",
                    error_message=f"HTTP {status}: {str(e)[:200]}",
                    conversation_id=self.conv_id,
                    subject_code=self.current_subject,
                    stack_trace=traceback.format_exc()[-500:],
                )
            except requests.exceptions.RequestException as e:
                if attempt < max_retries:
                    time.sleep(1)
                    continue
                last_error = e
                log_error(
                    error_type="api_call",
                    error_source=f"core.py:_call_llm({model_key})",
                    error_message=str(e)[:200],
                    conversation_id=self.conv_id,
                    subject_code=self.current_subject,
                    stack_trace=traceback.format_exc()[-500:],
                )

        raise last_error or RuntimeError(f"LLM call failed after {max_retries+1} attempts")

    def _execute_tool(self, tool_name: str, arguments: dict) -> str:
        """Execute a tool call and return the result as a string."""
        valid, reason = validate_tool_call(tool_name, arguments)
        if not valid:
            log_error("tool_fail", f"core.py:_execute_tool({tool_name})",
                      f"Blocked: {reason}", self.conv_id, self.current_subject)
            return f"工具调用被安全策略拦截: {reason}"

        # W5: Status callback for Web UI animations
        TOOL_STATUS = {
            "search_textbook": "📚 正在检索教材...",
            "search_past_paper": "📝 正在检索真题...",
            "get_exam_pattern": "🎯 正在分析解题套路...",
            "search_exam_techniques": "💡 正在查找答题技巧...",
            "grade_homework_image": "📸 正在 AI 批改...",
            "get_subject_info": "📋 正在查询科目信息...",
        }
        if self.status_callback:
            self.status_callback(TOOL_STATUS.get(tool_name, f"🔧 正在调用 {tool_name}..."))

        console.print(f"[dim]🔧 调用工具: {tool_name}...[/dim]")

        if tool_name == "search_textbook":
            n = max(1, min(50, int(arguments.get("n_results", 3))))
            results = search_textbooks(
                arguments.get("query", ""),
                arguments.get("subject_code"),
                n_results=n,
                use_rerank=True,
            )
            if not results:
                return "教材中未找到相关内容。改为用通用知识回答。"
            return sanitize_retrieved_content("\n\n".join(
                f"[来源: 教材 {r['metadata'].get('filename','')} | 引用时请写 📎 {arguments.get('subject_code','')} §{r['metadata'].get('filename','')[:20]} (textbook)]\n{r['content'][:1500]}"
                for r in results[:n]
            ))

        elif tool_name == "search_past_paper":
            n = max(1, min(50, int(arguments.get("n_results", 5))))
            results = search_past_papers(
                arguments.get("query", ""),
                arguments.get("subject_code"),
                arguments.get("paper_type"),
                n_results=n,
                use_rerank=True,
            )
            if not results:
                return "未找到匹配的真题。改为用通用知识回答。"
            return "\n\n".join(
                f"[真题 {r['metadata'].get('year','')} {r['metadata'].get('type','')}]\n{r['content'][:1500]}"
                for r in results[:n]
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
            image_desc = arguments.get("image_description", "")
            subject_code = arguments.get("subject_context", self.current_subject or "")
            # If we have vision access, try real grading
            try:
                img_path = self._pending_image
                if img_path:
                    result = grade_homework(img_path, subject_code)
                    return result
            except Exception:
                pass
            # Text-only fallback: grade based on the description the LLM provides
            if image_desc:
                return f"基于图片描述 ({subject_code})，请用 grading 功能评分。\n描述: {image_desc}"
            return "请上传图片。在 CLI 中使用 `/grade <路径>`，或直接在聊天中附上图片。"

        elif tool_name == "search_exam_techniques":
            n = max(1, min(20, int(arguments.get("n_results", 3))))
            results = _search_techniques(
                arguments.get("query", ""),
                arguments.get("subject_code"),
                n_results=n,
            )
            if not results:
                return "未找到匹配的考试技巧。请尝试更具体的问题。"
            return "\n\n".join(
                f"[考试技巧 {r['metadata'].get('filename','')}]\n{r['content'][:1200]}"
                for r in results[:n]
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
        """Detect subject from text using subject registry + keyword overlap."""
        text_lower = text.lower()
        scores = {}
        # Known aliases for our 4 subjects — optimization, not requirement
        _aliases = {
            "9701": ["chemistry", "chem", "化学", "equilibrium", "enthalpy", "organic", "mole", "bond", "periodic",
                     "le chatelier", "titration", "redox", "electrolysis", "polymer", "catalyst"],
            "9702": ["physics", "phys", "物理", "velocity", "circuit", "wave", "momentum", "kinetic", "magnetic",
                     "ohm", "resistance", "acceleration", "force", "newton", "energy"],
            "9708": ["economics", "econ", "经济", "demand", "supply", "inflation", "market", "elasticity", "gdp",
                     "interest rate", "aggregate demand", "monetary", "fiscal", "subsidy", "tax"],
            "9709": ["math", "maths", "mathematics", "数学", "integrat", "differenti", "calculus", "algebra", "trig", "vector",
                     "logarithm", "binomial", "coordinate", "sequence", "series"],
        }
        for s in self.subjects:
            score = 0
            if s.code in text:
                score += 5
            # Always check subject name (works for any future board/subject)
            if s.name.lower() in text_lower:
                score += 3
            # Add known aliases if available
            for kw in _aliases.get(s.code, []):
                if kw in text_lower:
                    score += 1
            if score > 0:
                scores[s.code] = score
        return max(scores, key=scores.get) if scores else None

    def chat(self, user_input: str, image_path: Optional[str] = None) -> str:
        """Process a chat message with optional image."""
        global _last_raw_output, _last_tool_calls, _last_response_time, _last_model, _last_svg_count, _last_conv_len
        _last_raw_output = ""
        _last_tool_calls = []
        _last_tc_key = None
        _last_response_time = 0.0
        _last_model = MODELS["tutor"].model if "tutor" in MODELS else "unknown"
        _last_svg_count = 0

        t_start = time.time()

        # Append user message first, then record conv length
        user_msg = {"role": "user", "content": user_input}
        self.conversation.append(user_msg)
        _last_conv_len = len(self.conversation)
        # W5: Prompt injection guard — check before processing
        is_injection, reason = detect_injection(user_input)
        if is_injection:
            log_error("api_call", "core.py:chat(injection_blocked)",
                      f"Injection blocked: {reason}", self.conv_id, self.current_subject)
            blocked_msg = f"⚠️ 安全拦截：检测到不当指令。请重新提问。"
            self.conversation.append({"role": "assistant", "content": blocked_msg})
            if self.conv_id:
                save_message(self.conv_id, "user", user_input[:100] + "...")
                save_message(self.conv_id, "assistant", blocked_msg)
            return blocked_msg

        # Detect subject
        detected = self._detect_subject(user_input)
        if detected and detected != self.current_subject:
            self.current_subject = detected
        if self.conv_id:
            update_conversation(self.conv_id, subject_code=detected)

        if self.conv_id:
            save_message(self.conv_id, "user", user_input)

        if image_path:
            try:
                subject = self.current_subject or "未知科目"
                grading_result = grade_homework(image_path, subject)
                self.conversation.append({
                    "role": "assistant",
                    "content": f"📸 **作业批改结果**\n\n{grading_result}",
                })
                if self.conv_id:
                    save_message(self.conv_id, "assistant",
                                 f"📸 **作业批改结果**\n\n{grading_result}",
                                 citation_chips=[f"{subject}§grading"])
                return grading_result
            except Exception as e:
                error_msg = f"批改失败: {str(e)}。请确保设置了 ZHIPU_API_KEY 或 DASHSCOPE_API_KEY。"
                self.conversation.append({"role": "assistant", "content": error_msg})
                if self.conv_id:
                    save_message(self.conv_id, "assistant", error_msg)
                log_error("vision_fail", "core.py:chat(image)", str(e),
                          self.conv_id, self.current_subject)
                return error_msg

        api_messages = [self.conversation[0]]
        api_messages.extend(self.conversation[-19:])

        if self.status_callback:
            self.status_callback("🎯 正在深度思考...")

        _last_model = MODELS["tutor"].model if "tutor" in MODELS else "unknown"

        with console.status("[cyan]思考中...[/cyan]"):
            try:
                response = self._call_llm(api_messages)
            except Exception as e:
                error_msg = f"❌ 调用 LLM 失败: {str(e)}\n请检查 API key 是否设置正确。"
                self.conversation.append({"role": "assistant", "content": error_msg})
                if self.conv_id:
                    save_message(self.conv_id, "assistant", error_msg)
                _last_response_time = time.time() - t_start
                return error_msg

        msg = response["choices"][0]["message"]

        # Preserve reasoning_content for API continuity
        reasoning_content = msg.get("reasoning_content", "")

        for _ in range(20):
            if msg.get("tool_calls"):
                # Detect consecutive duplicate — filter out repeated tool calls
                filtered = []
                for tc in msg["tool_calls"]:
                    tc_key = (tc["function"]["name"], tc["function"]["arguments"])
                    if tc_key == _last_tc_key:
                        continue  # skip duplicate, but keep other valid calls
                    _last_tc_key = tc_key
                    filtered.append(tc)
                if not filtered:
                    final_content = "⚠️ 检测到全部重复检索，已停止。请细化你的问题后重新提问。"
                    assistant_msg = {"role": "assistant", "content": final_content}
                    self.conversation.append(assistant_msg)
                    if self.conv_id:
                        save_message(self.conv_id, "assistant", final_content)
                    return final_content
                msg["tool_calls"] = filtered
                api_messages.append(msg)
                if self.conv_id:
                    save_message(self.conv_id, "assistant", msg.get("content", ""),
                                 tool_calls=msg["tool_calls"])

                for tool_call in msg["tool_calls"]:
                    tool_name = tool_call["function"]["name"]
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError:
                        arguments = {}
                    try:
                        tool_result = self._execute_tool(tool_name, arguments)
                    except Exception as e:
                        tool_result = f"Tool error: {e}"
                        log_error("tool_fail", f"core.py:_execute_tool({tool_name})",
                                  str(e), self.conv_id, self.current_subject)

                    _last_tool_calls.append({
                        "tool": tool_name,
                        "args": arguments,
                        "key": (tool_name, tool_call["function"]["arguments"]),
                        "result_len": len(tool_result) if isinstance(tool_result, str) else 0,
                    })

                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    })
                    if self.conv_id:
                        save_message(self.conv_id, "tool", tool_result,
                                     tool_call_id=tool_call["id"])

                try:
                    if self.status_callback:
                        self.status_callback("🎯 正在深度思考...")
                    response = self._call_llm(api_messages)
                except Exception as e:
                    error_msg = f"❌ 工具调用后 LLM 失败: {str(e)}"
                    self.conversation.append({"role": "assistant", "content": error_msg})
                    if self.conv_id:
                        save_message(self.conv_id, "assistant", error_msg)
                    return error_msg
                msg = response["choices"][0]["message"]
            else:
                break

        final_content = msg.get("content", "")
        reasoning = msg.get("reasoning_content", "")
        _last_raw_output = final_content
        _last_response_time = time.time() - t_start
        # Sanitize — this renders ```plot → SVG
        final_content = _sanitize_output(final_content)
        # Count SVGs AFTER rendering
        _last_svg_count = final_content.count("data:image/svg+xml;base64,") if final_content else 0
        assistant_msg = {"role": "assistant", "content": final_content}
        if reasoning:
            assistant_msg["reasoning_content"] = reasoning
        self.conversation.append(assistant_msg)
        if self.conv_id:
            save_message(self.conv_id, "assistant", final_content)

        return final_content

    def reset(self):
        self.conversation = [
            {"role": "system", "content": system_prompt(self._subjects_summary)},
        ]
        self.current_subject = None
        if self.conv_id:
            self.conv_id = create_conversation()

    def grade(self, question: str, mark_scheme: str, student_answer: str) -> dict:
        """Grade a student answer. Uses PedCoT two-stage grading with real MS matching."""
        from agent.grading.grader import grade as pedcot_grade

        result = pedcot_grade(
            question=question,
            student_answer=student_answer,
            mark_scheme=mark_scheme if mark_scheme != "auto" else None,
            conv_id=self.conv_id,
            subject_code=self.current_subject,
        )
        return result

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

    @staticmethod
    def set_token_limit(enabled: bool):
        global _token_limit_enabled
        _token_limit_enabled = enabled
        return f"Token limit {'enabled' if enabled else 'disabled'}"

    @staticmethod
    def get_token_limit() -> bool:
        return _token_limit_enabled

    @staticmethod
    def set_budget(enabled: bool):
        global _budget_enabled
        _budget_enabled = enabled
        return f"Budget {'enabled' if enabled else 'disabled'}"

    @staticmethod
    def get_budget() -> bool:
        return _budget_enabled

    @staticmethod
    def set_retrieval_limit(n: int):
        pass  # removed — n_results now controlled by LLM per call

    @staticmethod
    def get_retrieval_limit() -> int:
        return 3  # stub — n_results now controlled by LLM per call
