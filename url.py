import sys, urllib.parse
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if len(args) < 2:
        print("❌ Kullanim: url encode <metin>")
        print("             url decode <metin>")
        print("   Ornek:   url encode Merhaba Dunya")
        print("             url decode Merhaba+Dunya")
        return

    mode = args[0].lower()
    text = " ".join(args[1:])

    if mode == "encode":
        print(urllib.parse.quote(text))
    elif mode == "decode":
        try:
            print(urllib.parse.unquote(text))
        except Exception as e:
            print(f"❌ Decode hatasi: {e}")
    else:
        print(f"❌ Bilinmeyen mod: {mode} (encode/decode kullanin)")

if __name__ == "__main__":
    main()
