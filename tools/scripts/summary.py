#!/usr/bin/env python3
"""Print a summary of all downloaded resources."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

DATA = Path(__file__).parent.parent / "data"
PAPERS = DATA / "past_papers"
TEXTBOOKS = DATA / "textbooks"

MANUAL_SOURCES = [
    {
        "subject": "9701 Chemistry",
        "title": "Chemistry 2nd Ed (Hodder - Cann & Hughes) - 634 pages",
        "url": "https://chemistry.com.pk/books/cambridge-international-as-a-level-chemistry-2e-peter-cann/",
        "note": "Password: chemistry.com.pk, then click Download Link",
    },
    {
        "subject": "9701 Chemistry",
        "title": "Chemistry in Context 7th Ed (Hill & Holman) - 578 pages",
        "url": "https://chemistry.com.pk/books/chemistry-in-context-for-a-level-7e/",
        "note": "Password: chemistry.com.pk",
    },
    {
        "subject": "9708 Economics",
        "title": "Economics Coursebook 3rd Ed (Bamford & Grant)",
        "url": "https://gamatrain.com/paper/109/Cambridge-International-AS-and-A-level-Economics-Coursebook",
        "note": "Free PDF download",
    },
    {
        "subject": "9708 Economics",
        "title": "Economics 2nd Ed (Hodder - Peter Smith)",
        "url": "https://pdfcoffee.com/hodder-education-cambridge-international-as-and-a-level-economics-pdf-free.html",
        "note": "Requires clicking Download button on page",
    },
    {
        "subject": "9708 Economics",
        "title": "Economics Coursebook (PapaCambridge)",
        "url": "https://ebooks.papacambridge.com/directories/OCR/OCR-ebooks/upload/as%20and%20a%20level%20economics.pdf",
        "note": "Open in browser first, then right-click Save As",
    },
    {
        "subject": "9709 Mathematics",
        "title": "Pure Mathematics 2 & 3 Coursebook (CUP) - 348 pages",
        "url": "https://dokumen.pub/cambridge-international-as-and-a-level-mathematics-pure-mathematics-2-amp-3-coursebook-9781108407199-1108407196.html",
        "note": "Free download on dokumen.pub",
    },
    {
        "subject": "9709 Mathematics",
        "title": "Pure Mathematics 1 (Hodder - Sophie Goldie) - 320 pages",
        "url": "https://ebooks.papacambridge.com/ebooks/caie/cambridge-advancedcambridge-asa-level-mathematics-9709",
        "note": "Browse the page, find the PDF, open then Save As",
    },
    {
        "subject": "9709 Mathematics",
        "title": "All Math books (mechanics, stats, pure) - PapaCambridge",
        "url": "https://ebooks.papacambridge.com/ebooks/caie/cambridge-advancedcambridge-asa-level-mathematics-9709",
        "note": "Multiple PDFs available. Open in browser first.",
    },
    {
        "subject": "All subjects",
        "title": "Search on Anna's Archive",
        "url": "https://annas-archive.org/search?q=Cambridge+International+AS+A+Level+970",
        "note": "Comprehensive search engine for free ebooks",
    },
]


def main():
    console.print(Panel.fit(
        "[bold cyan]A-Level Resource Collection Summary[/bold cyan]",
        border_style="cyan"
    ))

    # Past papers
    if PAPERS.exists():
        manifest_path = PAPERS / "manifest.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                manifest = json.load(f)

            table = Table(title="Past Papers (Questions + Mark Schemes + Reports)")
            table.add_column("Subject", style="cyan")
            table.add_column("Code", style="yellow")
            table.add_column("Files", style="green")
            table.add_column("Years", style="blue")
            table.add_column("Size", style="magenta")

            sizes = {
                "9701": "708M",
                "9702": "792M",
                "9708": "372M",
                "9709": "554M",
            }
            for code, info in manifest.items():
                table.add_row(
                    info["name"], code,
                    str(info.get("total_files", "?")),
                    str(info.get("year_count", "?")),
                    sizes.get(code, "?"),
                )
            console.print(table)

    # Textbooks
    console.print()
    real_pdfs = list(TEXTBOOKS.rglob("*.pdf")) if TEXTBOOKS.exists() else []
    real_pdfs = [p for p in real_pdfs if p.stat().st_size > 100000]

    if real_pdfs:
        table = Table(title="Downloaded Textbooks (Auto-downloaded)")
        table.add_column("Subject", style="cyan")
        table.add_column("Title", style="white")
        table.add_column("Size", style="green")

        for p in real_pdfs:
            size = p.stat().st_size / 1024 / 1024
            subject = p.parent.name.replace("_", " ").title()
            table.add_row(subject, p.name, f"{size:.1f}MB")
        console.print(table)

    console.print()
    table = Table(title="Textbooks - Manual Download (open in browser)")
    table.add_column("Subject", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("How to get", style="yellow")

    for s in MANUAL_SOURCES:
        table.add_row(s["subject"], s["title"], s["note"])

    console.print(table)

    console.print("\n[bold]URLs to open in browser:[/bold]")
    seen_urls = set()
    for s in MANUAL_SOURCES:
        if s["url"] not in seen_urls:
            console.print(f"  {s['url']}")
            seen_urls.add(s["url"])


if __name__ == "__main__":
    main()
