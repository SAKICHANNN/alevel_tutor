"""
Textbook downloader module for Cambridge A-Level textbooks.
Sources indexed:
  - pdfdrive.to (multiple subjects, direct PDF access)
  - papacambridge.com/ebooks (direct file hosting)
  - chemistry.com.pk (Chemistry specific)
  - cienotes.com (Physics specific)
"""
import hashlib
import json
import re
import time
from pathlib import Path

import requests
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn
from rich.table import Table

from tools.crawler.config import SUBJECTS, DATA_DIR

console = Console()

TEXTBOOKS_DIR = DATA_DIR / "textbooks"

TEXTBOOK_URLS = {
    "9701_chemistry": [
        {
            "title": "Cambridge AS & A Level Chemistry Coursebook (CUP - Ryan & Norris)",
            "url": "https://www.exampaperspractice.co.uk/wp-content/uploads/CambridgeInternationalASALevelChemistryCoursebook.pdf",
            "source": "exampaperspractice.co.uk",
            "direct_pdf": True,
        },
        {
            "title": "Cambridge AS & A Level Chemistry 2nd Ed (Hodder - Cann & Hughes)",
            "url": "https://chemistry.com.pk/books/cambridge-international-as-a-level-chemistry-2e-peter-cann/",
            "source": "chemistry.com.pk",
            "direct_pdf": True,
        },
        {
            "title": "Chemistry in Context for Cambridge AS & A Level (7th Ed)",
            "url": "https://chemistry.com.pk/books/chemistry-in-context-for-a-level-7e/",
            "source": "chemistry.com.pk",
            "direct_pdf": True,
        },
        {
            "title": "Cambridge AS & A Level Chemistry Coursebook 3rd Ed (CUP)",
            "url": "https://chemistry.com.pk/books/cambridge-international-as-and-a-level-chemistry-coursebook-3e/",
            "source": "chemistry.com.pk",
            "direct_pdf": True,
        },
    ],
    "9702_physics": [
        {
            "title": "Cambridge AS & A Level Physics Coursebook 2nd Ed (David Sang)",
            "url": "https://www.cienotes.com/wp-content/uploads/2018/07/Cambridge-International-AS-and-A-Level-Physics-Coursebook-by-David-Sang-Graham-Jones-Gurinder-Chadha-and-Richard-Woodside.pdf",
            "source": "cienotes.com",
            "direct_pdf": True,
        },
    ],
    "9708_economics": [
        {
            "title": "Cambridge AS & A Level Economics 2nd Ed (Hodder - Peter Smith)",
            "url": "https://pdfcoffee.com/hodder-education-cambridge-international-as-and-a-level-economics-pdf-free.html",
            "source": "pdfcoffee.com",
            "direct_pdf": True,
        },
    ],
    "9709_mathematics": [
        {
            "title": "Pure Mathematics 1 Coursebook (CUP - Sue Pemberton)",
            "url": "https://www.learnedguys.com/uploads/files/335/Cambridge%20International%20AS%20A%20Level%20Mathematics%20Pure%20Mathematics%201.pdf",
            "source": "learnedguys.com",
            "direct_pdf": True,
        },
        {
            "title": "Pure Mathematics 1 (CUP) - from PapaCambridge",
            "url": "https://ebooks.papacambridge.com/directories/CAIE/CAIE-ebooks/upload/cambridge-international-as-and-a-level-mathematics-pure-mathematics-1.pdf",
            "source": "papacambridge.com",
            "direct_pdf": True,
        },
        {
            "title": "Pure Mathematics 2 & 3 (CUP) - from PapaCambridge",
            "url": "https://ebooks.papacambridge.com/directories/CAIE/CAIE-ebooks/upload/cambridge-international-as-and-a-level-mathematics-pure-mathematics-2-and-3.pdf",
            "source": "papacambridge.com",
            "direct_pdf": True,
        },
        {
            "title": "Pure Mathematics 1 Coursebook (Hodder - Sophie Goldie)",
            "url": "https://ebooks.papacambridge.com/directories/CAIE/CAIE-ebooks/upload/cambridge-international-as-and-a-level-pure-mathematics-1-coursebook.pdf",
            "source": "papacambridge.com",
            "direct_pdf": True,
        },
        {
            "title": "Mechanics (CUP) - from PapaCambridge",
            "url": "https://ebooks.papacambridge.com/directories/CAIE/CAIE-ebooks/upload/cambridge-international-as-a-level-mathematics-mechanics-practice-book.pdf",
            "source": "papacambridge.com",
            "direct_pdf": True,
        },
        {
            "title": "Probability & Statistics 1 (CUP) - from PapaCambridge",
            "url": "https://ebooks.papacambridge.com/directories/CAIE/CAIE-ebooks/upload/cambridge-international-as-a-level-mathematics-probability-statistics-1-coursebook.pdf",
            "source": "papacambridge.com",
            "direct_pdf": True,
        },
        {
            "title": "Probability & Statistics (CUP) - from PapaCambridge",
            "url": "https://ebooks.papacambridge.com/directories/CAIE/CAIE-ebooks/upload/cambridge-international-as-and-a-level-mathematics-statistics.pdf",
            "source": "papacambridge.com",
            "direct_pdf": True,
        },
    ],
}


def _sanitize_filename(title: str):
    name = re.sub(r'[<>:"/\\|?*]', '-', title)
    return name.strip()


def _download_file(url, dest_path: Path, timeout=120):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True)
    resp.raise_for_status()

    total_size = int(resp.headers.get("content-length", 0))
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)
    return dest_path.stat().st_size


def list_available():
    table = Table(title="Available Textbook PDFs")
    table.add_column("Subject", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Source", style="green")
    table.add_column("Direct PDF", style="yellow")

    for key, books in TEXTBOOK_URLS.items():
        subject_name = key.replace("_", " ").title()
        for b in books:
            table.add_row(
                subject_name,
                b["title"],
                b["source"],
                "Yes" if b.get("direct_pdf") else "No",
            )

    console.print(table)
    return TEXTBOOK_URLS


def download_all():
    TEXTBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    results = {}

    for key, books in TEXTBOOK_URLS.items():
        subject_dir = TEXTBOOKS_DIR / key
        subject_dir.mkdir(parents=True, exist_ok=True)
        results[key] = {"downloaded": [], "failed": []}

        for book in books:
            filename = _sanitize_filename(book["title"]) + ".pdf"
            dest = subject_dir / filename

            if dest.exists() and dest.stat().st_size > 10000:
                console.print(f"  [green]Already exists:[/green] {filename} ({dest.stat().st_size / 1024 / 1024:.1f}MB)")
                results[key]["downloaded"].append({"title": book["title"], "path": str(dest), "size": dest.stat().st_size})
                continue

            console.print(f"  [cyan]Downloading:[/cyan] {book['title']} from {book['source']}...")
            try:
                size = _download_file(book["url"], dest)
                console.print(f"    [green]Success:[/green] {size / 1024 / 1024:.1f}MB")
                results[key]["downloaded"].append({"title": book["title"], "path": str(dest), "size": size})
            except Exception as e:
                console.print(f"    [red]Failed:[/red] {str(e)[:120]}")
                results[key]["failed"].append({"title": book["title"], "error": str(e)[:120]})

            time.sleep(1)

    results_path = TEXTBOOKS_DIR / "download_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    console.print(f"\n[bold green]Results saved to {results_path}[/bold green]")
    return results


def download_direct_pdfs():
    TEXTBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    for key, books in TEXTBOOK_URLS.items():
        direct_books = [b for b in books if b.get("direct_pdf")]
        for book in direct_books:
            subject_dir = TEXTBOOKS_DIR / key
            subject_dir.mkdir(parents=True, exist_ok=True)
            filename = _sanitize_filename(book["title"]) + ".pdf"
            dest = subject_dir / filename

            if dest.exists() and dest.stat().st_size > 10000:
                console.print(f"  [green]Already exists:[/green] {filename}")
                continue

            console.print(f"  [cyan]Downloading:[/cyan] {book['title']}...")
            try:
                size = _download_file(book["url"], dest)
                console.print(f"    [green]Done:[/green] {size / 1024 / 1024:.1f}MB")
            except Exception as e:
                console.print(f"    [red]Failed:[/red] {str(e)[:100]}")
            time.sleep(0.5)
