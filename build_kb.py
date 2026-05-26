#!/usr/bin/env python3
"""Build the knowledge base from PDFs into ChromaDB."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.kb_builder import build_all

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Build A-Level Tutor Knowledge Base")
    parser.add_argument("--subject", type=str, choices=["9701", "9702", "9708", "9709"], help="Only index specific subject")
    parser.add_argument("--max-papers", type=int, default=50, help="Max past papers per subject to index")
    args = parser.parse_args()

    print("=" * 50)
    print("  Building A-Level Tutor Knowledge Base")
    print("=" * 50)
    print()

    # Check dependencies
    deps_ok = True
    try:
        import chromadb
        print("  ✓ chromadb installed")
    except ImportError:
        print("  ✗ chromadb not installed. Run: pip install chromadb")
        deps_ok = False

    try:
        import fitz
        print("  ✓ PyMuPDF installed")
    except ImportError:
        print("  ✗ PyMuPDF not installed. Run: pip install PyMuPDF")
        deps_ok = False

    if not deps_ok:
        print("\nPlease install missing dependencies and try again.")
        sys.exit(1)

    print()
    build_all(args.subject, args.max_papers)
