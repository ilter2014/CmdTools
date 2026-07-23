import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import subprocess

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    count = 1
    upper = False

    for a in args:
        if a == "-u" or a == "--upper":
            upper = True
        elif a.isdigit():
            count = int(a)
        elif a.startswith("-"):
            print(f"Bilinmeyen parametre: {a}")
            return
        else:
            count = int(a)

    # Python'un uuid modülünü subprocess ile çağır (çakışmayı önlemek için)
    for i in range(count):
        r = subprocess.run(
            [sys.executable, "-c", "import uuid; print(uuid.uuid4())"],
            capture_output=True, text=True, timeout=5
        )
        val = r.stdout.strip()
        if upper:
            val = val.upper()
        print(val)

if __name__ == "__main__":
    main()
