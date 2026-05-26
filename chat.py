#!/usr/bin/env python3
"""
A-Level Tutor Agent CLI
Interactive chat interface with homework grading and subject switching.
"""
import os
import sys
import cmd
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from agent.tutoring.core import Agent
from agent.tutoring.prompts import welcome_message
from agent.config import MODELS, SUBJECTS, SUBJECT_BY_CODE

console = Console()


class TutorCLI(cmd.Cmd):
    intro = welcome_message(SUBJECTS)
    prompt = "\n[bold cyan]你 > [/bold cyan]"

    def __init__(self):
        super().__init__()
        self.agent = Agent()
        self._check_api_keys()

    def _check_api_keys(self):
        warnings = []
        if not MODELS["tutor"].api_key:
            warnings.append("DEEPSEEK_API_KEY 未设置 → 文字问答不可用")
        if not MODELS["vision"].api_key and not MODELS["vision_qwen"].api_key:
            warnings.append("ZHIPU_API_KEY / DASHSCOPE_API_KEY 未设置 → 图片批改不可用")

        if warnings:
            console.print("\n[bold yellow]⚠️  配置提醒:[/bold yellow]")
            for w in warnings:
                console.print(f"  [yellow]• {w}[/yellow]")
            console.print("\n[dim]通过环境变量设置 API key:[/dim]")
            console.print("  [dim]export DEEPSEEK_API_KEY=sk-...[/dim]")
            console.print("  [dim]export ZHIPU_API_KEY=...    (用于图片批改，GLM-4V)[/dim]")
            console.print("  [dim]export DASHSCOPE_API_KEY=... (用于图片批改，Qwen-VL)[/dim]")
            console.print("")

    def default(self, line: str):
        """Process a chat message."""
        line = line.strip()
        if not line:
            return

        response = self.agent.chat(line)
        if response:
            console.print()
            console.print(Markdown(response))

    def do_subject(self, arg: str):
        """切换科目: subject 9701 / subject 9702 / subject 9708 / subject 9709"""
        arg = arg.strip()
        valid = SUBJECT_BY_CODE
        if arg in valid:
            result = self.agent.set_subject(arg)
            console.print(f"[green]{result}[/green]")
        else:
            codes = ", ".join(f"{c}({s.name})" for c, s in valid.items())
            console.print(f"[yellow]用法: subject <code>  可选: {codes}[/yellow]")

    def do_grade(self, arg: str):
        """批改作业图片: grade <图片路径>"""
        arg = arg.strip()
        if not arg:
            console.print("[yellow]用法: grade <图片路径>  例如: grade /path/to/homework.jpg[/yellow]")
            return
        path = os.path.expanduser(arg)
        if not os.path.exists(path):
            console.print(f"[red]文件不存在: {path}[/red]")
            return

        try:
            subject = self.agent.current_subject or "未知科目"
            from agent.vision import grade_homework
            result = grade_homework(path, subject)
            console.print()
            console.print(Markdown(f"## 📸 作业批改\n\n{result}"))
            self.agent.conversation.append({"role": "assistant", "content": f"📸 作业批改结果:\n{result}"})
        except Exception as e:
            console.print(f"[red]批改失败: {e}[/red]")

    def do_analyze(self, arg: str):
        """分析图片/图表: analyze <图片路径>"""
        arg = arg.strip()
        if not arg:
            console.print("[yellow]用法: analyze <图片路径>[/yellow]")
            return
        path = os.path.expanduser(arg)
        if not os.path.exists(path):
            console.print(f"[red]文件不存在: {path}[/red]")
            return
        try:
            subject = self.agent.current_subject or ""
            from agent.vision import analyze_diagram
            result = analyze_diagram(path, subject)
            console.print()
            console.print(Markdown(result))
        except Exception as e:
            console.print(f"[red]分析失败: {e}[/red]")

    def do_reset(self, arg: str):
        """重置对话"""
        self.agent.reset()
        console.print("[green]对话已重置。[/green]")

    def do_stats(self, arg: str):
        """显示知识库统计"""
        from agent.retriever import get_collection_stats
        stats = get_collection_stats()
        for name, info in stats.items():
            console.print(f"  [cyan]{name}[/cyan]: {info['count']} chunks")
        if stats.get("textbooks", {}).get("count", 0) == 0:
            console.print("\n[yellow]知识库为空。运行 python3 build_kb.py 构建索引。[/yellow]")

    def do_model(self, arg: str):
        """显示当前使用的模型"""
        from agent.config import get_active_tutor, get_active_vision_model
        tutor = get_active_tutor()
        vision = get_active_vision_model()
        console.print(f"  对话模型: [green]{tutor.provider}/{tutor.model}[/green]")
        if vision.api_key:
            console.print(f"  视觉模型: [green]{vision.provider}/{vision.model}[/green]")
        else:
            console.print(f"  视觉模型: [red]未配置[/red]")

    def do_exit(self, arg: str):
        """退出"""
        console.print("[dim]再见！加油备考！🎓[/dim]")
        return True

    def do_quit(self, arg: str):
        return self.do_exit(arg)

    do_EOF = do_exit


def main():
    import argparse
    parser = argparse.ArgumentParser(description="A-Level Tutor Agent")
    parser.add_argument("--build-kb", action="store_true", help="Build knowledge base before starting")
    parser.add_argument("--subject", type=str, choices=["9701", "9702", "9708", "9709"], help="Set initial subject")
    args = parser.parse_args()

    if args.build_kb:
        from agent.kb_builder import build_all
        build_all()

    cli = TutorCLI()
    if args.subject:
        cli.agent.set_subject(args.subject)
        console.print(f"[green]初始科目: {args.subject}[/green]\n")

    try:
        cli.cmdloop()
    except KeyboardInterrupt:
        console.print("\n[dim]再见！[/dim]")


if __name__ == "__main__":
    main()
