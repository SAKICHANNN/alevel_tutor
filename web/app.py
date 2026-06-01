"""
Gradio Web App — A-Level Tutor Agent
Blocks-based interface with chat, image grading, subject switcher, and cost panel.
W5: Real-time LLM processing status with animated display.
"""
import os
import sys
import json
import queue
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

# Workaround: Gradio 4.44.1 schema bug on Python 3.9
import gradio_client.utils as _gcu
_orig_get_type = _gcu.get_type
def _patched_get_type(schema):
    if isinstance(schema, bool):
        return "boolean"
    return _orig_get_type(schema)
_gcu.get_type = _patched_get_type

import gradio as gr

from agent.tutoring.core import Agent
from agent.tutoring.core import (
    _last_katex_fixes as _read_katex_fixes,
    _last_raw_output,
    _last_tool_calls,
    _last_response_time,
    _last_model,
    _last_svg_count,
    _last_conv_len,
    _token_limit_enabled,
    _budget_enabled,
)
from agent.tutoring.prompts import welcome_message
from agent.config import SUBJECTS, SUBJECT_BY_CODE, PROJECT_ROOT
from agent.database import (
    create_conversation, get_total_cost, get_daily_costs, check_budget,
    get_messages,
)
from agent.ocr.vision import grade_homework
from agent.security import validate_file, strip_exif, detect_injection

# ── Debug log ──
DEBUG_LOG = PROJECT_ROOT / "data" / "gui_debug.log"
_MAX_LOG_ENTRIES = 500  # keep last 500 entries


def _log_debug(entry: dict):
    """Append a JSON line to the debug log. Auto-rotates to keep size bounded."""
    entry["ts"] = datetime.now().isoformat()
    try:
        DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        if DEBUG_LOG.exists():
            lines = DEBUG_LOG.read_text().strip().split("\n")
        lines.append(json.dumps(entry, ensure_ascii=False, default=str))
        if len(lines) > _MAX_LOG_ENTRIES:
            lines = lines[-_MAX_LOG_ENTRIES:]
        DEBUG_LOG.write_text("\n".join(lines) + "\n")
    except Exception:
        pass  # never crash the app because of logging

# ── State ──
AGENT_INSTANCES: dict = {}  # session_id → Agent


def _get_agent(session_id: str, status_cb=None) -> Agent:
    if session_id not in AGENT_INSTANCES:
        conv_id = create_conversation(title=f"Web Session {session_id[:8]}")
        AGENT_INSTANCES[session_id] = Agent(conv_id=conv_id, status_callback=status_cb)
    elif status_cb:
        AGENT_INSTANCES[session_id].status_callback = status_cb
    return AGENT_INSTANCES[session_id]


def _get_welcome():
    subs = SUBJECTS
    return f"""## 🎓 A-Level AI Tutor

目前支持: {', '.join(f'{s.code} {s.name}' for s in subs)}

**直接提问** — 教材问答、真题讲解、考试套路、作业批改

📸 上传作业图片 → 自动批改（需 LM Studio 运行中）
"""


# ── Animated Status Display ──

STATUS_STYLE = """
<style>
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.status-grid {
  display: flex;
  gap: 6px;
  justify-content: center;
  padding: 6px 0;
}
.status-cell {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  text-align: center;
  white-space: nowrap;
  transition: all 0.3s ease;
  opacity: 0.35;
  filter: grayscale(0.6);
  transform: scale(0.95);
}
.status-cell.active {
  opacity: 1;
  filter: grayscale(0);
  transform: scale(1);
  box-shadow: 0 2px 8px rgba(0,0,0,0.15);
}
.c-think { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: #fff; }
.c-textbook { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: #fff; }
.c-paper { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: #1a1a2e; }
.c-pattern { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); color: #1a1a2e; }
.c-technique { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: #1a1a2e; }
</style>
"""

STATUS_MATRIX = [
    ("thinking", "c-think", "🧠 思考"),
    ("search_textbook", "c-textbook", "📚 教材"),
    ("search_past_paper", "c-paper", "📝 真题"),
    ("get_exam_pattern", "c-pattern", "🎯 套路"),
    ("search_exam_techniques", "c-technique", "💡 技巧"),
]

def _render_matrix(active_keys: set) -> str:
    cells = []
    for key, cls, label in STATUS_MATRIX:
        active = "active" if key in active_keys else ""
        cells.append(f'<div class="status-cell {cls} {active}">{label}</div>')
    return STATUS_STYLE + '<div class="status-grid">' + "".join(cells) + '</div>'


def _render_status(status_key: str) -> str:
    return _render_matrix({status_key})


# ── Callbacks ──

def chat_fn(message: str, history: list, session_id: str, subject_code: str):
    """Handle text chat message — generator for real-time status updates."""
    if not message.strip():
        yield "", history, ""
        return

    history = history or []
    history.append({"role": "user", "content": message})

    status_queue = queue.Queue()
    result_container = {"response": None, "error": None}

    def status_cb(msg):
        status_queue.put(msg)

    agent = _get_agent(session_id, status_cb=status_cb)
    if subject_code and subject_code != agent.current_subject:
        agent.set_subject(subject_code)

    def run_agent():
        try:
            result_container["response"] = agent.chat(message)
        except Exception as e:
            result_container["error"] = str(e)
        finally:
            status_queue.put("__DONE__")

    thread = threading.Thread(target=run_agent, daemon=True)
    thread.start()

    # Multi-status display
    active_keys = set()
    while True:
        try:
            status = status_queue.get(timeout=0.15)
        except queue.Empty:
            if not thread.is_alive():
                break
            if active_keys:
                yield "", history, _render_matrix(active_keys)
            continue

        if status == "__DONE__":
            yield "", history, ""
            break

        key = STATUS_KEY_MAP.get(status, "thinking")
        if key == "thinking":
            active_keys = {"thinking"}
        else:
            active_keys.discard("thinking")
            active_keys.add(key)
        yield "", history, _render_matrix(active_keys)

    thread.join(timeout=5)

    # Final result
    if result_container["error"]:
        response = f"❌ 错误: {result_container['error']}"
    else:
        response = result_container["response"] or "（无响应）"

    history.append({"role": "assistant", "content": response})

    # Save to DB
    if agent.conv_id:
        from agent.database import save_message
        save_message(agent.conv_id, "user", message)
        save_message(agent.conv_id, "assistant", response)

    # Debug log
    _log_debug({
        "session": session_id[:8],
        "subject": subject_code or agent.current_subject,
        "model": _last_model,
        "conv_len": _last_conv_len,
        "token_limit": _token_limit_enabled,
        "budget": _budget_enabled,
        "user_msg": message[:300],
        "response_len": len(response),
        "svg_count": _last_svg_count,
        "raw_len": len(_last_raw_output),
        "katex_fixes": dict(_read_katex_fixes),
        "tool_calls": list(_last_tool_calls),
        "elapsed_s": round(_last_response_time, 2),
        "error": result_container["error"],
        "response": response[:5000],
    })

    yield "", history, ""


def grade_image_fn(image, session_id: str, subject_code: str):
    """Handle image upload for grading."""
    if image is None:
        return "", None

    # W5: File validation + EXIF stripping
    ok, reason = validate_file(image)
    if not ok:
        return f"❌ {reason}", None
    clean_path = strip_exif(image)

    agent = _get_agent(session_id)
    subject = subject_code or agent.current_subject or "9709"

    try:
        result = grade_homework(clean_path, subject)
    except Exception as e:
        result = f"❌ 批改失败: {str(e)}\n请确保 LM Studio 正在运行。"

    history = [{"role": "assistant", "content": f"📸 **作业批改** ({subject})\n\n{result}"}]
    return result, history


def get_cost_html():
    """Render cost panel as HTML."""
    total = get_total_cost(days=30)
    daily = get_daily_costs(days=7)
    ok, msg = check_budget()

    calls = total.get("calls", 0) or 0
    tokens = total.get("total_tokens", 0) or 0
    cost_cny = total.get("cost_cny", 0) or 0
    cost_usd = total.get("cost_usd", 0) or 0

    status_color = "#2e7d32" if ok else "#c62828"
    status_icon = "✅" if ok else "🚫"

    html = f"""
    <div style="font-size:13px;line-height:1.6">
    <b>本月成本</b><br>
    API 调用: {calls} 次<br>
    Tokens: {tokens:,}<br>
    费用: ¥{cost_cny:.4f} (${cost_usd:.4f})<br>
    <span style="color:{status_color}">{status_icon} {msg}</span>
    <hr style="margin:4px 0">
    <b>最近 7 天</b><br>
    """
    for d in daily[:7]:
        html += f"{d['day'][-5:]}: ¥{d['cost_cny']:.4f} | {d['calls']} calls<br>"
    html += "</div>"
    return html


def switch_subject(code: str, session_id: str):
    """Switch current subject."""
    if not code:
        return f"当前: 未选择"
    agent = _get_agent(session_id)
    result = agent.set_subject(code)
    return f"当前: {code} {SUBJECT_BY_CODE[code].name}"


def build_ui():
    theme = gr.themes.Soft(primary_hue="blue", secondary_hue="indigo")

    with gr.Blocks(theme=theme, title="A-Level Tutor", css="""
        .cost-panel { font-size: 12px; }
        footer { display: none !important; }
    """) as demo:
        session_id = gr.State(value=lambda: os.urandom(8).hex())

        # ── Header ──
        gr.Markdown(_get_welcome())

        with gr.Row():
            # ── Left Sidebar ──
            with gr.Column(scale=1, min_width=220):
                subject_dd = gr.Dropdown(
                    choices=[(f"{s.code} {s.name}", s.code) for s in SUBJECTS],
                    value="9709",
                    label="📚 科目",
                    interactive=True,
                )
                subject_status = gr.Markdown("当前: 9709 Mathematics")

                token_limit_toggle = gr.Checkbox(
                    value=True,
                    label="🔒 Token 限制 (8192)",
                    info="关闭后模型无回复长度上限",
                    interactive=True,
                )

                budget_toggle = gr.Checkbox(
                    value=True,
                    label="💰 预算控制 (¥50/月)",
                    info="关闭后跳过 API 费用限制",
                    interactive=True,
                )

                gr.Markdown("---")
                cost_html = gr.HTML(value=get_cost_html, every=30)

                gr.Markdown("---")
                gr.Markdown("""
                **提示**
                - 上传作业图片 → 批改
                - 直接输入问题 → 辅导
                - 切换科目 → 左上角
                """)

            # ── Main Area ──
            with gr.Column(scale=3):
                status_display = gr.HTML(label="", value="", elem_classes=["status-display"])
                chatbot = gr.Chatbot(
                    label="对话",
                    type="messages",
                    height=500,
                    show_copy_button=True,
                    sanitize_html=False,
                    latex_delimiters=[
                        {"left": "$$", "right": "$$", "display": True},
                        {"left": "$", "right": "$", "display": False},
                    ],
                )

                with gr.Row():
                    msg_input = gr.Textbox(
                        placeholder="输入你的问题...",
                        label="",
                        scale=9,
                        container=False,
                    )
                    send_btn = gr.Button("发送", variant="primary", scale=1)

                # ── Image Upload ──
                with gr.Accordion("📸 上传作业批改", open=False):
                    with gr.Row():
                        image_input = gr.Image(
                            label="上传作业图片",
                            type="filepath",
                            height=200,
                        )
                        grade_output = gr.Markdown(
                            label="批改结果",
                            value="等待上传...",
                        )

                # ── Event Bindings ──
                msg_input.submit(
                    chat_fn,
                    [msg_input, chatbot, session_id, subject_dd],
                    [msg_input, chatbot, status_display],
                )
                send_btn.click(
                    chat_fn,
                    [msg_input, chatbot, session_id, subject_dd],
                    [msg_input, chatbot, status_display],
                )

                image_input.change(
                    grade_image_fn,
                    [image_input, session_id, subject_dd],
                    [grade_output, chatbot],
                )

                subject_dd.change(
                    switch_subject,
                    [subject_dd, session_id],
                    [subject_status],
                )

                token_limit_toggle.change(
                    lambda enabled: Agent.set_token_limit(enabled),
                    [token_limit_toggle],
                    None,
                )

                budget_toggle.change(
                    lambda enabled: Agent.set_budget(enabled),
                    [budget_toggle],
                    None,
                )

    return demo


def main():
    demo = build_ui()
    demo.queue(default_concurrency_limit=1, max_size=10)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )


if __name__ == "__main__":
    main()
