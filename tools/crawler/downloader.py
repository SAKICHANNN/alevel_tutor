import os
import subprocess
from pathlib import Path
from typing import List

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn

from tools.crawler.config import (
    SUBJECTS,
    GITHUB_REPO_URL,
    GITHUB_BRANCH,
    REPO_DIR,
)

console = Console()


def clone_repo_sparse(subjects: List = None):
    if subjects is None:
        subjects = SUBJECTS

    sparse_paths = [f"A-Levels/{s.directory_name}" for s in subjects]

    if REPO_DIR.exists():
        console.print("[yellow]Repo directory already exists. Pulling latest...[/yellow]")
        result = subprocess.run(
            ["git", "-C", str(REPO_DIR), "pull", "--ff-only"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            console.print("[yellow]Pull failed, re-cloning...[/yellow]")
            import shutil
            shutil.rmtree(REPO_DIR)
        else:
            console.print("[green]Repo updated successfully.[/green]")
            return True

    REPO_DIR.parent.mkdir(parents=True, exist_ok=True)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Cloning repository...", total=None)

        clone_cmd = [
            "git", "clone",
            "--branch", GITHUB_BRANCH,
            "--single-branch",
            "--depth", "1",
            "--filter=blob:none",
            "--sparse",
            GITHUB_REPO_URL,
            str(REPO_DIR),
        ]

        result = subprocess.run(clone_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[red]Clone failed: {result.stderr}[/red]")
            return False

        progress.update(task, description="[cyan]Setting up sparse checkout...")
        sparse_cmd = ["git", "-C", str(REPO_DIR), "sparse-checkout", "set"] + sparse_paths
        result = subprocess.run(sparse_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[red]Sparse checkout failed: {result.stderr}[/red]")
            return False

        progress.update(task, description="[cyan]Checking out files...")
        checkout_cmd = ["git", "-C", str(REPO_DIR), "checkout"]
        result = subprocess.run(checkout_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            console.print(f"[red]Checkout failed: {result.stderr}[/red]")
            return False

    console.print("[green]Repository cloned successfully![/green]")
    return True


def count_files(subject_dir: Path):
    total = 0
    for root, dirs, files in os.walk(subject_dir):
        total += len([f for f in files if not f.startswith(".")])
    return total


def verify_subjects(subjects: List = None):
    if subjects is None:
        subjects = SUBJECTS

    results = {}
    for s in subjects:
        subj_dir = REPO_DIR / "A-Levels" / s.directory_name
        if subj_dir.exists():
            file_count = count_files(subj_dir)
            results[s.code] = {"exists": True, "file_count": file_count}
            console.print(f"  [green]{s.code} {s.name}:[/green] {file_count} files found")
        else:
            results[s.code] = {"exists": False, "file_count": 0}
            console.print(f"  [red]{s.code} {s.name}:[/red] directory not found")
    return results
