"""
emptyfolders.py — emptydirs.py ile aynı işi yapar.
emptydirs / emptyfolders — ikisi de boş klasörleri tarar.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from emptydirs import main

if __name__ == "__main__":
    main()
