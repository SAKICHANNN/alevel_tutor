#!/usr/bin/env python3
"""Master summary script showing all collected resources."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from tools.crawler.resource_index import ALL_RESOURCES, get_essential_resources, count_by_type

console = Console()
DATA = Path(__file__).parent.parent / "data"

def main():
    console.print(Panel.fit(
        "[bold cyan]🎓 A-Level Learning Resources — Complete Collection[/bold cyan]\n"
        "[dim]All free resources for 9701 Chemistry, 9702 Physics, 9708 Economics, 9709 Mathematics[/dim]",
        border_style="cyan"
    ))

    # ===== DOWNLOADED PDFs =====
    pdf_dir = DATA / "study_guides" / "pdf"
    pdfs = sorted(pdf_dir.glob("*.pdf")) if pdf_dir.exists() else []
    if pdfs:
        table = Table(title="Downloaded PDF Guides")
        table.add_column("File", style="cyan")
        table.add_column("Size", style="green")
        table.add_column("Content", style="white")
        descriptions = {
            "chemistry_examiner_tips.pdf": "Chemistry: Official Cambridge examiner tips for AS & A Level",
            "chemistry_example_responses.pdf": "Chemistry: Graded candidate answers (A/C/E) with examiner commentary",
            "chemistry_learner_guide.pdf": "Chemistry: Official Cambridge learner guide (paper structure, revision checklist)",
            "economics_specimen_answers_p4.pdf": "Economics: Specimen Paper 4 20-mark essay answers with examiner feedback",
            "physics_example_responses_p3.pdf": "Physics: Paper 3 practical skills example responses with feedback",
            "physics_example_responses_p5.pdf": "Physics: Paper 5 planning/analysis/evaluation example responses",
        }
        for p in pdfs:
            size = p.stat().st_size / 1024 / 1024
            table.add_row(p.name, f"{size:.1f}MB", descriptions.get(p.name, ""))
        console.print(table)

    # ===== EXAM TECHNIQUE GUIDES =====
    md_dir = DATA / "study_guides"
    mds = sorted(md_dir.glob("*.md")) if md_dir.exists() else []
    if mds:
        table = Table(title="Exam Technique Markdown Guides")
        table.add_column("File", style="cyan")
        table.add_column("Content Summary", style="white")
        content = {
            "9701_chemistry.md": "Command words, 10 keywords, 10 common mistakes, calculation rules, 5 paper tips, organic mechanisms",
            "9702_physics.md": "Command words, 11 keywords, 10 mistakes, calculation patterns, Paper 5 complete template",
            "9708_economics.md": "Command words, 10 keywords, AO breakdown (33/37/30%), 8/12/20-mark essay frameworks, 8 evaluation dimensions",
            "9709_mathematics.md": "Command words, 6 golden rules, topic techniques (quadratics, calculus, trig, vectors, mechanics, stats), 9 common mistakes",
        }
        for p in mds:
            if p.name != "index.md":
                table.add_row(p.name, content.get(p.name, ""))
        console.print(table)

    # ===== PAST PAPERS SUMMARY =====
    manifest_path = DATA / "past_papers" / "manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            papers = json.load(f)
        table = Table(title="Past Papers (Questions + Mark Schemes + Examiner Reports)")
        table.add_column("Subject", style="cyan")
        table.add_column("Code", style="yellow")
        table.add_column("Total Files", style="green")
        table.add_column("Year Range", style="blue")
        table.add_column("Size", style="magenta")
        sizes = {"9701": "708M", "9702": "792M", "9708": "372M", "9709": "554M"}
        for code, info in papers.items():
            years = info.get("years", [])
            yr_range = f"{years[0]}-{years[-1]}" if years else "?"
            table.add_row(info["name"], code, str(info.get("total_files", "?")), yr_range, sizes.get(code, "?"))
        console.print(table)

    # ===== TEXTBOOKS =====
    textbook_dir = DATA / "textbooks"
    real_pdfs = []
    for p in textbook_dir.rglob("*.pdf"):
        if p.stat().st_size > 100000:
            real_pdfs.append(p)
    if real_pdfs:
        table = Table(title="Downloaded Textbooks")
        table.add_column("Subject", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Size", style="green")
        for p in real_pdfs:
            size = p.stat().st_size / 1024 / 1024
            subject = p.parent.name.replace("_", " ").title()
            table.add_row(subject, p.name, f"{size:.1f}MB")
        console.print(table)

    # ===== RESOURCE INDEX SUMMARY =====
    table = Table(title="Web Resources Index (Free)")
    table.add_column("Subject", style="cyan")
    table.add_column("Total Indexed", style="green")
    table.add_column("Essential", style="yellow")
    table.add_column("Resource Types", style="white")

    for code, resources in ALL_RESOURCES.items():
        if code == "general":
            continue
        essential = get_essential_resources(code)
        counts = count_by_type(code)
        types = ", ".join(sorted(counts.keys()))
        subject_name = code.replace("_", " ").title().replace("Chemistry", "9701 Chemistry").replace("Physics", "9702 Physics").replace("Economics", "9708 Economics").replace("Mathematics", "9709 Mathematics")
        table.add_row(subject_name, str(len(resources)), str(len(essential)), types)

    console.print(table)

    # ===== TOOLS SUMMARY =====
    console.print(Panel.fit("""
[bold]Run these scripts to use the collection:[/bold]
  [cyan]python3 scripts/run_crawler.py[/cyan]         — Update past papers from GitHub mirror
  [cyan]python3 scripts/download_textbooks.py[/cyan]   — Download textbooks from indexed sources  
  [cyan]python3 scripts/summary.py[/cyan]             — Show complete resource summary
  [cyan]python3 -m crawler.techniques[/cyan]          — Regenerate exam technique guides

[bold]Key files:[/bold]
  [green]data/study_guides/9701_chemistry.md[/green]   — Chemistry exam techniques
  [green]data/study_guides/9702_physics.md[/green]     — Physics exam techniques  
  [green]data/study_guides/9708_economics.md[/green]   — Economics essay frameworks
  [green]data/study_guides/9709_mathematics.md[/green] — Math problem-solving techniques
  [green]data/study_guides/pdf/[/green]                — PDF guides (6 files, 41MB)

[bold]Quick access to all indexed web resources:[/bold]
  [cyan]python3 -c "from tools.crawler.resource_index import ALL_RESOURCES; ...[/cyan]
    """, border_style="green"))

    # Print essential resources per subject
    for code in ["9701_chemistry", "9702_physics", "9708_economics", "9709_mathematics"]:
        name = code.replace("_", " ").title()
        console.print(f"\n[bold cyan]⭐ {name} — Essential Resources:[/bold cyan]")
        for r in get_essential_resources(code):
            console.print(f"  [green][{r.res_type}][/green] {r.title}")
            console.print(f"  [dim]{r.url}[/dim]")


if __name__ == "__main__":
    main()
