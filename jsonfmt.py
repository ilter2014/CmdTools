import sys, json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        print("Kullanim: jsonfmt <json_dosyasi>")
        print("          jsonfmt \"{...}\"")
        print("          jsonfmt --min <dosya>   (kucult/sikistir)")
        print("          jsonfmt --validate <dosya>  (sadece dogrula)")
        return

    mode = "format"
    source = args

    if args[0] == "--min":
        mode = "minify"
        source = args[1:]
    elif args[0] == "--validate":
        mode = "validate"
        source = args[1:]

    if not source:
        print("Dosya veya JSON metni girin.")
        return

    data_str = " ".join(source)

    # Dosya mı?
    try:
        if os.path.exists(data_str):
            with open(data_str, "r", encoding="utf-8") as f:
                data_str = f.read()
    except:
        pass

    try:
        parsed = json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"Gecersiz JSON! {e}")
        return

    if mode == "validate":
        print("Gecerli JSON!")
        return

    if mode == "minify":
        print(json.dumps(parsed, separators=(",", ":"), ensure_ascii=False))
    else:
        print(json.dumps(parsed, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    import os
    main()
