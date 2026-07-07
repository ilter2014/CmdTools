import sys, secrets, string
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def gen_password(length=16, use_symbols=True):
    chars = string.ascii_letters + string.digits
    if use_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"
    password = "".join(secrets.choice(chars) for _ in range(length))
    return password

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    length = 16
    count = 1
    no_symbols = False

    for a in args:
        if a == "--no-symbols" or a == "-ns":
            no_symbols = True
        elif a.isdigit():
            if count == 1 and length == 16:
                length = int(a)
            else:
                count = int(a)

    if length < 4:
        print("⚠️  Minimum 4 karakter.")
        length = 4
    if length > 128:
        print("⚠️  Maksimum 128 karakter.")
        length = 128

    for i in range(count):
        print(gen_password(length, not no_symbols))

if __name__ == "__main__":
    main()
