import sys, re, operator, math

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OPS = {
    "+": operator.add, "-": operator.sub,
    "*": operator.mul, "/": operator.truediv,
    "//": operator.floordiv, "%": operator.mod,
    "**": operator.pow,
}

def calc(expr):
    # Güvenli matematik - sadece sayılar ve operatörler
    expr = expr.strip()
    # Önce parantezleri çöz (iç içe destek)
    while "(" in expr:
        m = re.search(r'\(([^()]+)\)', expr)
        if not m: break
        expr = expr.replace(f"({m.group(1)})", str(calc(m.group(1))), 1)

    # PI ve e sabitleri
    expr = expr.replace("pi", str(math.pi)).replace("PI", str(math.pi))
    expr = expr.replace("e", str(math.e))

    # Tek tek token işle
    tokens = re.findall(r'[\d.]+|[+\-*/%()]|\*\*|//', expr)
    if not tokens:
        return None, "Gecersiz ifade"

    # Operatör önceliği: ** önce, sonra */% sonra +-
    # 1. **
    i = 0
    while i < len(tokens):
        if tokens[i] == "**":
            if i == 0 or i == len(tokens)-1:
                return None, "Hatali kullanim"
            try:
                r = float(tokens[i-1]) ** float(tokens[i+1])
                tokens[i-1:i+2] = [str(r)]
                i = 0
            except: i += 1
        else: i += 1

    # 2. * / // %
    i = 0
    while i < len(tokens):
        if tokens[i] in ("*", "/", "//", "%"):
            if i == 0 or i == len(tokens)-1:
                return None, "Hatali kullanim"
            try:
                a, b = float(tokens[i-1]), float(tokens[i+1])
                if tokens[i] == "/" and b == 0:
                    return None, "Sifira bolme hatasi"
                r = OPS[tokens[i]](a, b)
                tokens[i-1:i+2] = [str(r)]
                i = 0
            except: i += 1
        else: i += 1

    # 3. + -
    i = 0
    while i < len(tokens):
        if tokens[i] in ("+", "-"):
            if i == 0 or i == len(tokens)-1:
                return None, "Hatali kullanim"
            try:
                a, b = float(tokens[i-1]), float(tokens[i+1])
                r = OPS[tokens[i]](a, b)
                tokens[i-1:i+2] = [str(r)]
                i = 0
            except: i += 1
        else: i += 1

    if len(tokens) == 1:
        try: return float(tokens[0]), None
        except: return None, "Hata"
    return None, "Ifade cozulemedi"

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    if not args:
        print("Kullanim: calc <islem>")
        print("  Ornek:  calc 25*8+10")
        print("          calc (12+8)*3-5")
        print("          calc 2**8")
        print("          calc 100/4%3")
        return

    expr = " ".join(args)
    result, err = calc(expr)
    if err:
        print(f"Hata: {err}")
    else:
        # Tam sayıysa .0'sız göster
        if result == int(result):
            print(f"{expr} = {int(result)}")
        else:
            print(f"{expr} = {result:.4f}".rstrip("0").rstrip("."))

if __name__ == "__main__":
    main()
