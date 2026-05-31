"""
Restore ChromaDB from a backup directory.
Replaces the current ChromaDB and tutor.db with the backup version.

Usage:
    python3 tools/scripts/restore_chroma.py <backup_dir>
    python3 tools/scripts/restore_chroma.py --list   # List available backups
    python3 tools/scripts/restore_chroma.py --latest # Restore most recent backup
"""
import argparse
import shutil
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.config import CHROMA_DIR, DATA_DIR

BACKUP_ROOT = DATA_DIR / "backups"


def list_backups() -> list:
    if not BACKUP_ROOT.exists():
        return []
    return sorted(
        [d for d in BACKUP_ROOT.iterdir() if d.is_dir() and d.name.startswith("chroma_")],
        reverse=True,
    )


def verify_backup(backup_dir: Path) -> bool:
    """Verify the backup contains valid data."""
    chroma_dir = backup_dir / "chroma_db"
    if not chroma_dir.exists():
        print(f"[red]No chroma_db in backup: {backup_dir}[/]")
        return False

    chroma_sqlite = chroma_dir / "chroma.sqlite3"
    if not chroma_sqlite.exists():
        print(f"[red]No chroma.sqlite3 in backup[/]")
        return False

    try:
        db = sqlite3.connect(str(chroma_sqlite))
        collections = db.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
        db.close()
        if collections == 0:
            print("[yellow]Warning: backup has 0 collections[/]")
        return True
    except Exception as e:
        print(f"[red]Backup SQLite corrupt: {e}[/]")
        return False


def restore_from(backup_dir: Path, dry_run: bool = False) -> bool:
    """Restore ChromaDB + tutor.db from backup."""
    chroma_src = backup_dir / "chroma_db"
    tutor_src = backup_dir / "tutor.db"

    if not verify_backup(backup_dir):
        return False

    print(f"Restoring from: {backup_dir.name}")
    if dry_run:
        print("  [DRY RUN] No changes made")
        print(f"  Would restore chroma_db → {CHROMA_DIR}")
        if tutor_src.exists():
            print(f"  Would restore tutor.db → {DATA_DIR}")
        return True

    # Backup current ChromaDB first (one-time safety)
    safety_dir = BACKUP_ROOT / "pre_restore_auto"
    if CHROMA_DIR.exists():
        safety_dir.mkdir(parents=True, exist_ok=True)
        safety_target = safety_dir / f"chroma_db_{Path(backup_dir).name}"
        if not safety_target.exists():
            shutil.copytree(CHROMA_DIR, safety_target)
            print(f"  Safety backup saved to: {safety_target}")

    # Remove current ChromaDB and replace
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)
    shutil.copytree(chroma_src, CHROMA_DIR)
    print(f"  ChromaDB restored")

    # Restore tutor.db
    if tutor_src.exists():
        # Close any open connections
        tutor_db = DATA_DIR / "tutor.db"
        if tutor_db.exists():
            tutor_db.unlink()
        shutil.copy2(tutor_src, tutor_db)
        print(f"  tutor.db restored")

    print("Restore complete.")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Restore ChromaDB from backup")
    parser.add_argument("backup", nargs="?", type=str,
                        help="Backup directory name or path")
    parser.add_argument("--list", action="store_true", help="List available backups")
    parser.add_argument("--latest", action="store_true", help="Restore most recent backup")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be restored")
    args = parser.parse_args()

    if args.list:
        backups = list_backups()
        if not backups:
            print("No backups found.")
        else:
            print(f"Available backups ({len(backups)}):")
            for b in backups:
                manifest = b / "manifest.json"
                if manifest.exists():
                    import json
                    with open(manifest) as f:
                        m = json.load(f)
                    print(f"  {b.name} — {m.get('chroma_size_mb', '?')} MB — {m.get('timestamp', '?')}")
                else:
                    print(f"  {b.name} (no manifest)")
        sys.exit(0)

    if args.latest:
        backups = list_backups()
        if not backups:
            print("[red]No backups found[/]")
            sys.exit(1)
        args.backup = str(backups[0])

    if not args.backup:
        parser.print_help()
        sys.exit(1)

    backup_path = Path(args.backup)
    if not backup_path.exists():
        # Try under backup root
        backup_path = BACKUP_ROOT / args.backup
    if not backup_path.exists():
        print(f"[red]Backup not found: {args.backup}[/]")
        sys.exit(1)

    ok = restore_from(backup_path, dry_run=args.dry_run)
    sys.exit(0 if ok else 1)
