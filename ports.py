"""
ports.py — port.py ile aynı işi yapar.
İkisi de "açık port ve süreç bilgisi" gösterir.
Fark: sadece çağrıldığı komut adı değişir, işlev aynıdır.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from port import main

if __name__ == "__main__":
    main()
