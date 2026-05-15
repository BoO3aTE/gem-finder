"""
GitHub Gem Finder — Full Pipeline
Runs all 3 steps in sequence and opens the dashboard.
Usage: py -3 run_all.py
"""

import time
import sys
import os
import subprocess
from scanner import find_gems
from social import enrich_gems
from dashboard import build_dashboard


def main():
    total_start = time.time()

    print("\n" + "=" * 60)
    print("  AI GitHub Gem Finder — Full Pipeline")
    print("=" * 60)

    # Step 1
    print("\n[1/3] GitHub Scanner")
    print("-" * 40)
    gems = find_gems()

    # Step 2
    print("\n[2/3] Social Enrichment (Reddit + HN)")
    print("-" * 40)
    enriched = enrich_gems()

    # Step 3
    print("\n[3/3] Building Dashboard")
    print("-" * 40)
    build_dashboard()

    elapsed = int(time.time() - total_start)
    minutes, seconds = divmod(elapsed, 60)

    print("\n" + "=" * 60)
    print(f"  Done in {minutes}m {seconds}s")
    print(f"  {len(enriched)} gems found")
    print(f"  Dashboard: output/dashboard.html")
    print("=" * 60 + "\n")

    # Auto-open in browser (Windows)
    dashboard_path = os.path.abspath("output/dashboard.html")
    if sys.platform == "win32":
        os.startfile(dashboard_path)


if __name__ == "__main__":
    main()
