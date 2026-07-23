import sys
import base64 as _b64

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if len(args) < 2:
        print("Kullanim: b64 encode <metin>")
        print("          b64 decode <metin>")
        return

    mode = args[0].lower()
    text = " ".join(args[1:])

    if mode == "encode":
        print(_b64.b64encode(text.encode("utf-8")).decode("utf-8"))
    elif mode == "decode":
        try:
            print(_b64.b64decode(text).decode("utf-8"))
        except Exception as e:
            print(f"Hata: {e}")
    else:
        print(f"Bilinmeyen mod: {mode} (encode/decode)")

if __name__ == "__main__":
    main()
