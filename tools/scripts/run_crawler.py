#!/usr/bin/env python3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.crawler.pipeline import run_full_pipeline
from tools.crawler.config import SUBJECTS


def main():
    print("=" * 60)
    print("  A-Level Past Papers Crawler")
    print("  Downloading: 9701 Chemistry, 9702 Physics,")
    print("               9708 Economics, 9709 Mathematics")
    print("=" * 60)
    print()

    run_full_pipeline(SUBJECTS)


if __name__ == "__main__":
    main()
