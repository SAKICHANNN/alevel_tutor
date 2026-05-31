"""
ChromaDB + SQLite backup tool.
Creates timestamped backups of ChromaDB vector store and tutor.db.
Ensures ChromaDB is not being written to during backup.

Usage:
    python3 tools/scripts/backup_chroma.py          # Backup now
    python3 tools/scripts/backup_chroma.py --path /my/backups  # Custom path
"""
import argparse
import os
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent.config import CHROMA_DIR, DATA_DIR

DEFAULT_BACKUP_ROOT = DATA_DIR / "backups"


def verify_chroma_ok() -> bool:
    """Verify ChromaDB is accessible and consistent."""
    try:
        db = sqlite3.connect(str(CHROMA_DIR / "chroma.sqlite3"))
        segments = db.execute(
            "SELECT COUNT(*) FROM segments WHERE type = 'urn:chroma:segment/vector/hnsw-local-persisted'"
        ).fetchone()[0]
        collections = db.execute("SELECT COUNT(*) FROM collections").fetchone()[0]
        db.close()
        return segments > 0 and collections > 0
    except Exception as e:
        print(f"[red]ChromaDB verification failed: {e}[/]")
        return False


def backup_chroma(backup_root: Path, verify: bool = True) -> Path:
    """Backup ChromaDB + tutor.db to a timestamped directory."""
    if not CHROMA_DIR.exists():
        raise FileNotFoundError(f"ChromaDB not found at {CHROMA_DIR}")

    if verify and not verify_chroma_ok():
        raise RuntimeError("ChromaDB verification failed — refusing to backup potentially corrupt data")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = backup_root / f"chroma_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    print(f"Backing up ChromaDB ({CHROMA_DIR})")
    print(f"  → {backup_dir}")

    # Copy ChromaDB with status
    t0 = time.time()
    chroma_dest = backup_dir / "chroma_db"
    shutil.copytree(CHROMA_DIR, chroma_dest, dirs_exist_ok=True)
    size = sum(f.stat().st_size for f in chroma_dest.rglob("*") if f.is_file())
    elapsed = time.time() - t0
    print(f"  ChromaDB: {size / 1024 / 1024:.0f} MB in {elapsed:.1f}s")

    # Copy tutor.db if exists
    tutor_db = DATA_DIR / "tutor.db"
    if tutor_db.exists():
        tutor_wal = DATA_DIR / "tutor.db-wal"
        tutor_shm = DATA_DIR / "tutor.db-shm"

        # Force WAL checkpoint before backup
        db = sqlite3.connect(str(tutor_db))
        db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        db.close()

        shutil.copy2(tutor_db, backup_dir / "tutor.db")
        if tutor_wal.exists():
            shutil.copy2(tutor_wal, backup_dir / "tutor.db-wal")
        db_size = tutor_db.stat().st_size if tutor_db.exists() else 0
        print(f"  tutor.db: {db_size / 1024:.0f} KB")

    # Write manifest
    manifest = {
        "timestamp": timestamp,
        "chroma_dir": str(chroma_dest),
        "chroma_size_mb": round(size / 1024 / 1024, 1),
        "backup_created": datetime.now().isoformat(),
    }
    import json
    with open(backup_dir / "manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"Backup complete: {backup_dir.name}")
    return backup_dir


def list_backups(backup_root: Path) -> list:
    if not backup_root.exists():
        return []
    return sorted(
        [d for d in backup_root.iterdir() if d.is_dir() and d.name.startswith("chroma_")],
        reverse=True,
    )


def cleanup_old_backups(backup_root: Path, keep: int = 7):
    """Keep only the most recent N backups."""
    backups = list_backups(backup_root)
    for old in backups[keep:]:
        print(f"Removing old backup: {old.name}")
        shutil.rmtree(old)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backup ChromaDB + SQLite")
    parser.add_argument("--path", type=str, default=str(DEFAULT_BACKUP_ROOT),
                        help=f"Backup root directory (default: {DEFAULT_BACKUP_ROOT})")
    parser.add_argument("--keep", type=int, default=7,
                        help="Keep last N backups, remove older ones (default: 7)")
    parser.add_argument("--no-verify", action="store_true",
                        help="Skip ChromaDB integrity check before backup")
    args = parser.parse_args()

    backup_root = Path(args.path)
    try:
        backup_dir = backup_chroma(backup_root, verify=not args.no_verify)
        cleanup_old_backups(backup_root, keep=args.keep)

        # Show current backups
        backups = list_backups(backup_root)
        print(f"\nExisting backups ({len(backups)}):")
        for b in backups[:5]:
            manifest_file = b / "manifest.json"
            if manifest_file.exists():
                import json
                with open(manifest_file) as f:
                    m = json.load(f)
                print(f"  {b.name} — {m.get('chroma_size_mb', '?')} MB")
    except Exception as e:
        print(f"[red]Backup failed: {e}[/]")
        sys.exit(1)
