from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tools.crawler.config import SUBJECTS
from tools.crawler.downloader import clone_repo_sparse, verify_subjects
from tools.crawler.organizer import organize_papers

console = Console()


def run_full_pipeline(subjects=None):
    if subjects is None:
        subjects = SUBJECTS

    console.print(Panel.fit(
        "[bold cyan]A-Level Past Papers Crawler[/bold cyan]\n"
        f"Target subjects: {', '.join(f'{s.code} ({s.name})' for s in subjects)}",
        border_style="cyan"
    ))

    console.print("\n[bold]Step 1/3: Downloading from GitHub mirror...[/bold]")
    success = clone_repo_sparse(subjects)
    if not success:
        console.print("[red]Download failed. Aborting.[/red]")
        return

    console.print("\n[bold]Step 2/3: Verifying downloaded files...[/bold]")
    results = verify_subjects(subjects)

    all_ok = all(r["exists"] for r in results.values())
    if not all_ok:
        console.print("[red]Some subjects missing. Check the repo structure.[/red]")

    console.print("\n[bold]Step 3/3: Organizing papers into structured directories...[/bold]")
    manifest = organize_papers(subjects)

    summary_table = Table(title="Download Summary")
    summary_table.add_column("Subject", style="cyan")
    summary_table.add_column("Code", style="yellow")
    summary_table.add_column("Files", style="green")
    summary_table.add_column("Years", style="blue")

    for s in subjects:
        info = manifest.get(s.code, {})
        summary_table.add_row(
            s.name,
            s.code,
            str(info.get("total_files", "N/A")),
            str(info.get("year_count", "N/A")),
        )

    console.print(summary_table)
    console.print("\n[bold green]Pipeline complete![/bold green]")


def run_download_only(subjects=None):
    if subjects is None:
        subjects = SUBJECTS

    console.print("[bold]Downloading resources...[/bold]")
    clone_repo_sparse(subjects)
    verify_subjects(subjects)
    console.print("[green]Download complete.[/green]")


def run_organize_only(subjects=None):
    if subjects is None:
        subjects = SUBJECTS

    console.print("[bold]Organizing files...[/bold]")
    organize_papers(subjects)
    console.print("[green]Organization complete.[/green]")
