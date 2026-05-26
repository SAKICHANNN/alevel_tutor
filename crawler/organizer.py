import json
import os
import shutil
from collections import defaultdict
from pathlib import Path
from typing import List

from rich.console import Console

from .config import (
    SUBJECTS,
    REPO_DIR,
    PAPERS_DIR,
    classify_file,
    SESSION_CODES,
)

console = Console()


def organize_papers(subjects: List = None):
    if subjects is None:
        subjects = SUBJECTS

    PAPERS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}

    for s in subjects:
        console.print(f"\n[bold cyan]Organizing {s.code} - {s.name}...[/bold cyan]")
        source_dir = REPO_DIR / "A-Levels" / s.directory_name
        if not source_dir.exists():
            console.print(f"  [red]Source directory not found: {source_dir}[/red]")
            continue

        target_root = PAPERS_DIR / f"{s.code}_{s.name.lower()}"
        stats = {
            "qp": 0,
            "ms": 0,
            "er": 0,
            "gt": 0,
            "in": 0,
            "other": 0,
            "unclassified": 0,
        }
        years = set()
        files_by_year_type = defaultdict(lambda: defaultdict(list))

        for dirpath, dirnames, filenames in os.walk(source_dir):
            for filename in filenames:
                if filename.startswith(".") or filename == "README.md":
                    continue

                filepath = Path(dirpath) / filename
                info = classify_file(filename)

                if info:
                    year = info["full_year"]
                    ftype = info["type"]
                    years.add(year)

                    target_dir = target_root / year / ftype
                    target_dir.mkdir(parents=True, exist_ok=True)

                    target_path = target_dir / filename
                    try:
                        shutil.copy2(filepath, target_path)
                    except OSError as e:
                        console.print(f"    [red]Failed to copy {filename}: {e}[/red]")
                        continue

                    if ftype in stats:
                        stats[ftype] += 1
                    else:
                        stats["other"] += 1

                    files_by_year_type[year][ftype].append(filename)
                else:
                    stats["unclassified"] += 1
                    other_dir = target_root / "other"
                    other_dir.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(filepath, other_dir / filename)
                    except OSError:
                        pass

        manifest[s.code] = {
            "name": s.name,
            "total_files": sum(v for k, v in stats.items() if k != "unclassified"),
            "by_type": stats,
            "years": sorted(years),
            "year_count": len(years),
            "files": {year: {ftype: files for ftype, files in type_map.items()} for year, type_map in files_by_year_type.items()},
        }

        console.print(f"  [green]Total:[/green] {manifest[s.code]['total_files']} files across {len(years)} years")
        console.print(f"  Question Papers: {stats['qp']} | Mark Schemes: {stats['ms']} | Examiner Reports: {stats['er']} | Grade Thresholds: {stats['gt']}")

    manifest_path = PAPERS_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    console.print(f"\n[bold green]Manifest saved to {manifest_path}[/bold green]")

    return manifest
