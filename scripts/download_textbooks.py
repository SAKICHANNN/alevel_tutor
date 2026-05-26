#!/usr/bin/env python3
"""Download Cambridge A-Level textbooks from indexed sources."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.textbooks import list_available, download_all, download_direct_pdfs


def main():
    print("=" * 60)
    print("  A-Level Textbook Downloader")
    print("=" * 60)
    print()

    print("Available textbook PDFs:")
    list_available()
    print()

    print("Step 1: Downloading direct PDF links...")
    download_direct_pdfs()
    print()

    print("Step 2: Downloading from pdfdrive.to & other sources...")
    download_all()
    print()

    print("Done! Check data/textbooks/")


if __name__ == "__main__":
    main()
