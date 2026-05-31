"""
Gradio Web App — A-Level Tutor Agent
Blocks-based interface with chat, image grading, subject switcher, and cost panel.
"""
import os
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import gradio as gr

from agent.tutoring.core import Agent
from agent.tutoring.prompts import welcome_message
from agent.config import SUBJECTS, SUBJECT_BY_CODE
from agent.database import (
    create_conversation, get_total_cost, get_daily_costs, check_budget,
    get_messages,
)
from agent.ocr.vision import grade_homework
from agent.security import validate_file, strip_exif, detect_injection

# ── State ──
AGENT_INSTANCES: dict = {}  # session_id → Agent


def _get_agent(session_id: str) -> Agent:
    if session_id not in AGENT_INSTANCES:
        conv_id = create_conversation(title=f"Web Session {session_id[:8]}")
        AGENT_INSTANCES[session_id] = Agent(conv_id=conv_id)
    return AGENT_INSTANCES[session_id]


def _get_welcome():
    subs = SUBJECTS
    return f"""## 🎓 A-Level AI Tutor

目前支持: {', '.join(f'{s.code} {s.name}' for s in subs)}

**直接提问** — 教材问答、真题讲解、考试套路、作业批改

📸 上传作业图片 → 自动批改（需 LM Studio 运行中）
"""


# ── Callbacks ──

def chat_fn(message: str, history: list, session_id: str, subject_code: str):
    """Handle text chat message."""
    if not message.strip():
        return "", history

    agent = _get_agent(session_id)
    if subject_code and subject_code != agent.current_subject:
        agent.set_subject(subject_code)

    try:
        response = agent.chat(message)
    except Exception as e:
        response = f"❌ 错误: {str(e)}"

    history = history or []
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": response})
    return "", history


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
                chatbot = gr.Chatbot(
                    label="对话",
                    type="messages",
                    height=500,
                    show_copy_button=True,
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
            [msg_input, chatbot],
        )
        send_btn.click(
            chat_fn,
            [msg_input, chatbot, session_id, subject_dd],
            [msg_input, chatbot],
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

    return demo


def main():
    demo = build_ui()
    demo.queue(default_concurrency_limit=1, max_size=10)
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
    )


if __name__ == "__main__":
    main()
