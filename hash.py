import sys, os, hashlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ALGOS = ["md5", "sha1", "sha256", "sha512"]

def hash_file(filepath, algo="sha256"):
    try:
        h = hashlib.new(algo)
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return None

def hash_text(text, algo="sha256"):
    h = hashlib.new(algo)
    h.update(text.encode("utf-8"))
    return h.hexdigest()

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    if not args:
        print("Kullanim: hash <dosya>           (varsayilan: sha256)")
        print("          hash <dosya> -a md5")
        print("          hash -t <metin>         (metnin hashini al)")
        print("          hash -a sha512 <dosya>")
        return

    algo = "sha256"
    items = args.copy()

    if "-a" in items:
        idx = items.index("-a")
        if idx + 1 < len(items):
            algo = items[idx + 1].lower()
            if algo not in ALGOS:
                print(f"Desteklenmeyen algoritma: {algo} (md5, sha1, sha256, sha512)")
                return
            items = items[:idx] + items[idx+2:]
        else:
            items.remove("-a")

    if not items:
        print("Dosya veya metin belirtin.")
        return

    if items[0] == "-t":
        text = " ".join(items[1:])
        if not text:
            print("Metin girin.")
            return
        h = hash_text(text, algo)
        print(f"[{algo.upper()}] {text}")
        print(h)
        return

    filepath = items[0]
    if not os.path.exists(filepath):
        print(f"Dosya bulunamadi: {filepath}")
        return

    h = hash_file(filepath, algo)
    if h:
        size = os.path.getsize(filepath)
        print(f"Dosya: {filepath} ({size} byte)")
        print(f"[{algo.upper()}] {h}")
    else:
        print(f"Dosya okunamadi: {filepath}")

if __name__ == "__main__":
    main()
