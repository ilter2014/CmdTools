import os
import sys
import subprocess
import importlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============ SURUM ============

def _surum_oku():
    """version dosyasindan surum numarasini okur."""
    try:
        import re
        dosya = os.path.join(os.path.dirname(os.path.abspath(__file__)), "version")
        with open(dosya, "r", encoding="utf-8") as f:
            icerik = f.read().strip()
        eslesme = re.search(r"version[:\s]*v?(\d+\.\d+(?:\.\d+)?)", icerik, re.IGNORECASE)
        if eslesme:
            return eslesme.group(1)
        eslesme = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", icerik)
        if eslesme:
            return eslesme.group(1)
        return icerik or "?"
    except Exception:
        return "?"

SURUM = _surum_oku()

KATEGORILER = {
    "Sistem": ["sysinfo", "ip", "uptime", "mac", "port", "ports"],
    "Ag": ["pingtest", "speedtest", "ns"],
    "Dosya": ["size", "hash", "tree", "emptydirs", "emptyfolders"],
    "Guvenlik": ["passgen", "genuuid"],
    "Donusturucu": ["b64", "url", "jsonfmt", "timestamp"],
    "Diger": ["calc", "serve", "alarm", "analiz", "grafik", "haber", "sinyal", "otosinyal", "ytai"],
    "Yonetici": ["cmdtools", "install", "indir"],
}

KOMUT_ACIKLAMA = {
    "sysinfo": "Isletim sistemi, CPU, RAM bilgilerini gosterir.",
    "ip": "Yerel ve genel IP adresini gosterir.",
    "uptime": "Bilgisayarin ne kadar suredir acik oldugunu gosterir.",
    "mac": "Ag ve Bluetooth MAC adreslerini gosterir.",
    "port": "Acik portlari ve hangi uygulamanin kullandigini gosterir.",
    "ports": "port ile ayni.",
    "pingtest": "Internet gecikmenizi (ping) olcer ve degerlendirir.",
    "speedtest": "Internet hizinizi olcer (indirme/yukleme).",
    "ns": "Domainin nameserver ve DNS gorunurlugunu kontrol eder.",
    "size": "Dosya veya klasorun boyutunu hesaplar.",
    "hash": "Dosyanin MD5/SHA1/SHA256/SHA512 ozetini hesaplar.",
    "tree": "Klasor yapisini agac seklinde gosterir.",
    "emptydirs": "Tum sistemdeki bos klasorleri bulur.",
    "emptyfolders": "emptydirs ile ayni.",
    "passgen": "Guclu rastgele sifre uretir.",
    "genuuid": "Rastgele UUID (benzersiz kimlik) uretir.",
    "b64": "Base64 encode/decode yapar.",
    "url": "URL encode/decode yapar.",
    "jsonfmt": "JSON dogrulama, formatlama ve kucultme yapar.",
    "timestamp": "Unix timestamp ve tarih arasi donusum yapar.",
    "calc": "Hizli matematik islemleri yapar.",
    "serve": "Bulundugun klasoru HTTP sunucusu yapar.",
    "alarm": "Hisse senedi/kripto icin fiyat alarmi kurar.",
    "analiz": "Teknik analiz yapar (hisse/kripto).",
    "grafik": "Terminalde grafik cizer.",
    "haber": "Finansal haberleri gosterir.",
    "sinyal": "Al/sat sinyali uretir.",
    "otosinyal": "Tum kripto veya BIST hisselerini tarar, sinyalde sesli uyarir.",
    "ytai": "Yapay zeka ile finansal sorulari cevaplar.",
    "cmdtools": "CmdTools ana komutu (yardim, list, version, about).",
    "help": "Yardim bilgisini gosterir (cmdtools help ile ayni).",
    "yardim": "help ile ayni (Turkce).",
    "bilgi": "about ile ayni (Turkce).",
    "list": "Tum komutlari listeler.",
    "version": "CmdTools surumunu gosterir.",
    "about": "CmdTools hakkinda bilgi verir.",
    "install": "Gereken kutuphaneleri tara ve kur (cmdtools install).",
    "indir": "install ile ayni (Turkce).",
}

KOMUT_KULLANIM = {
    "sysinfo": "sysinfo",
    "ip": "ip",
    "uptime": "uptime",
    "mac": "mac",
    "port": "port [port_numarasi]",
    "ports": "port ile ayni",
    "pingtest": "pingtest",
    "speedtest": "speedtest",
    "ns": "ns <domain>",
    "size": "size [dizin/dosya]",
    "hash": "hash <dosya> [-a md5|sha1|sha256|sha512]",
    "tree": "tree [dizin] [--depth N] [--max N] [--no-size]",
    "emptydirs": "emptydirs",
    "emptyfolders": "emptydirs ile ayni",
    "passgen": "passgen [uzunluk] [adet] [--no-symbols]",
    "genuuid": "genuuid [adet] [--upper]",
    "b64": "b64 encode <metin> | b64 decode <metin>",
    "url": "url encode <metin> | url decode <metin>",
    "jsonfmt": "jsonfmt <json> | jsonfmt --min <json> | jsonfmt --validate <json>",
    "timestamp": "timestamp [timestamp|tarih]",
    "calc": "calc <islem>",
    "serve": "serve [port] [--all]",
    "alarm": "alarm <sembol> <fiyat>",
    "analiz": "analiz <sembol> [timeframe]",
    "grafik": "grafik <sembol> [timeframe]",
    "haber": "haber [sembol]",
    "sinyal": "sinyal <sembol> [timeframe]",
    "otosinyal": "otosinyal kripto|hisse [periyot]",
    "ytai": "ytai <soru>",
    "cmdtools": "cmdtools help | list | version | about | bilgi",
    "help": "help [komut]",
    "yardim": "yardim [komut]",
    "bilgi": "bilgi",
    "list": "list",
    "version": "version",
    "about": "about",
    "install": "cmdtools install | cmdtools indir",
    "indir": "cmdtools install ile ayni",
}

KOMUT_ORNEK = {
    "sysinfo": "sysinfo",
    "ip": "ip",
    "uptime": "uptime",
    "mac": "mac",
    "port": "port",
    "pingtest": "pingtest",
    "speedtest": "speedtest",
    "ns": "ns google.com",
    "size": "size ~/Projeler",
    "hash": "hash ~/dosya.zip -a md5",
    "tree": "tree ~/CmdTools --depth 2",
    "emptydirs": "emptydirs",
    "passgen": "passgen 24 3",
    "genuuid": "genuuid 5 --upper",
    "b64": "b64 encode Merhaba Dunya",
    "url": "url encode Merhaba Dunya",
    "jsonfmt": "jsonfmt '{\"ad\":\"Ali\"}'",
    "timestamp": "timestamp 1704067200",
    "calc": "calc 25*8+10",
    "serve": "serve 8080",
    "alarm": "alarm ekle coin btcusdt \">63000\"",
    "analiz": "analiz btcusdt 4h",
    "grafik": "grafik btcusdt 1h",
    "haber": "haber BTC",
    "sinyal": "sinyal ethusdt 1d",
    "ytai": "ytai BTC suan alinir mi?",
    "otosinyal": "otosinyal kripto 15m",
    "install": "cmdtools install",
    "indir": "cmdtools indir",
}


def cmd_version():
    print(f"CmdTools v{SURUM}")


def cmd_about():
    print(f"CmdTools v{SURUM}")
    print()
    print("CmdTools, komut satiri icin")
    print("gelistirilmis bir arac kutusudur.")
    print()
    print("Amac: Gunluk bilgisayar kullaniminda")
    print("isleri kolaylastirmak, ag, dosya, sistem")
    print("ve finans araclarina hizli erisim saglamak.")
    print()
    print(f"Toplam {len(KOMUT_ACIKLAMA)} komut")
    print(f"Surum: {SURUM}")
    print("Gelistirici: ilter2014")
    print("GitHub: github.com/ilter2014/CmdTools")


def cmd_bilgi():
    return cmd_about()


def cmd_indir():
    return cmd_install()


def cmd_list():
    print(f"CmdTools v{SURUM} - Kullanilabilir Komutlar")
    print()
    for kat, komutlar in KATEGORILER.items():
        print(f"  {kat}:")
        for k in komutlar:
            aciklama = KOMUT_ACIKLAMA.get(k, "")
            print(f"    - {k:<15} {aciklama}")
        print()


def cmd_yardim(konu=None):
    return cmd_help(konu)


def cmd_help(konu=None):
    if not konu:
        cmd_list()
        print("  Hizli Baslangic:")
        print("    sysinfo              Sistem bilgilerini goster")
        print("    ip                   IP ve ag bilgilerini goster")
        print("    calc 25*8+10         Matematik islemi yap")
        print("    passgen 16 3         16 karakterden 3 sifre uret")
        print("    grafik btcusdt       Kripto grafigi ciz")
        print("    analiz THYAO         Hisse teknik analizi")
        print("    cmdtools install     Eksik kutuphaneleri kur")
        print()
        print("  Komut Detayi:")
        print("    cmdtools help <komut>    Belirli bir komut hakkinda bilgi")
        print("    cmdtools list            Tum komutlari listele")
        print("    cmdtools version         Surum bilgisi")
        print("    cmdtools about           Proje hakkinda bilgi")
        print("    cmdtools install         Eksik kutuphaneleri otomatik kur")
        print()
        return

    komut = konu.lower()
    if komut not in KOMUT_ACIKLAMA:
        print(f"Bilinmeyen komut: {konu}")
        print("Gecerli komutlari gormek icin: cmdtools help")
        print()
        print("Komut kategorileri:")
        for kat, kmt in KATEGORILER.items():
            print(f"  {kat}: {', '.join(kmt)}")
        print()
        return

    aciklama = KOMUT_ACIKLAMA.get(komut, "Aciklama yok.")
    kullanim = KOMUT_KULLANIM.get(komut, komut)
    ornek = KOMUT_ORNEK.get(komut, "-")

    print(f"Komut: {komut}")
    print()
    print(f"  {aciklama}")
    print()
    print(f"  Kullanim:  {kullanim}")
    print()
    print(f"  Ornek:     {ornek}")
    print()


def _find_third_party_imports():
    """Tum .py dosyalarini tarayarak ucuncu taraf import'lari bulur."""
    third_party = set()

    # Python 3.10+ stdlib tam liste
    if hasattr(sys, "stdlib_module_names"):
        stdlib = set(sys.stdlib_module_names)
    else:
        stdlib = {
            "__future__", "abc", "aifc", "argparse", "array", "ast", "asynchat",
            "asyncio", "asyncore", "atexit", "audioop", "base64", "bdb", "binascii",
            "binhex", "bisect", "builtins", "bz2", "calendar", "cgi", "cgitb",
            "chunk", "cmath", "cmd", "code", "codecs", "codeop", "collections",
            "colorsys", "compileall", "concurrent", "configparser", "contextlib",
            "contextvars", "copy", "copyreg", "cProfile", "crypt", "csv",
            "ctypes", "curses", "dataclasses", "datetime", "dbm", "decimal",
            "difflib", "dis", "distutils", "doctest", "email", "encodings",
            "enum", "errno", "faulthandler", "fcntl", "filecmp", "fileinput",
            "fnmatch", "formatter", "fractions", "ftplib", "functools",
            "gc", "getopt", "getpass", "gettext", "glob", "grp", "gzip",
            "hashlib", "heapq", "hmac", "html", "http", "idlelib", "imaplib",
            "imghdr", "imp", "importlib", "inspect", "io", "ipaddress",
            "itertools", "json", "keyword", "lib2to3", "linecache", "locale",
            "logging", "lzma", "mailbox", "mailcap", "marshal", "math",
            "mimetypes", "mmap", "modulefinder", "multiprocessing", "netrc",
            "nis", "nntplib", "numbers", "operator", "optparse", "os",
            "ossaudiodev", "pathlib", "pdb", "pickle", "pickletools", "pipes",
            "pkgutil", "platform", "plistlib", "poplib", "posix", "posixpath",
            "pprint", "profile", "pstats", "pty", "pwd", "py_compile",
            "pyclbr", "pydoc", "queue", "quopri", "random", "re", "readline",
            "reprlib", "resource", "rlcompleter", "runpy", "sched", "secrets",
            "select", "selectors", "shelve", "shlex", "shutil", "signal",
            "site", "smtpd", "smtplib", "sndhdr", "socket", "socketserver",
            "spwd", "sqlite3", "sre_compile", "sre_constants", "sre_parse",
            "ssl", "stat", "statistics", "string", "stringprep", "struct",
            "subprocess", "sunau", "symtable", "sys", "sysconfig", "syslog",
            "tabnanny", "tarfile", "telnetlib", "tempfile", "termios",
            "test", "textwrap", "threading", "time", "timeit", "tkinter",
            "token", "tokenize", "tomllib", "trace", "traceback",
            "tracemalloc", "tty", "turtle", "turtledemo", "types",
            "typing", "unicodedata", "unittest", "urllib", "uu", "uuid",
            "venv", "warnings", "wave", "weakref", "webbrowser", "winreg",
            "winsound", "wsgiref", "xdrlib", "xml", "xmlrpc", "zipapp",
            "zipfile", "zipimport", "zlib",
            # Python 3.8-3.9 ek moduller
            "_thread", "antigravity", "appdirs", "chunk", "distutils",
            "email", "html.parser", "markupbase", "parser", "pydoc_data",
            "test", "unittest.mock", "urllib.parse", "xml.dom",
        }

    # Proje icindeki moduller (kendimizi hariç tutuyoruz)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    proj_modulleri = set()
    for f in os.listdir(script_dir):
        if f.endswith(".py"):
            proj_modulleri.add(f[:-3])

    for fname in os.listdir(script_dir):
        if not fname.endswith(".py") or fname == "updaterouter.py":
            continue
        fpath = os.path.join(script_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for line in f:
                    s = line.strip()
                    if s.startswith("#") or s.startswith("except"):
                        continue
                    if s.startswith("import "):
                        # "import sys, os, re" gibi逗cyollu import'lari ayristir
                        parts = s[len("import "):].split(",")
                        for part in parts:
                            # "plotext as plt" → "plotext"
                            mod = part.strip().split()[0].split(".")[0].strip()
                            if mod and mod not in stdlib and mod not in proj_modulleri:
                                third_party.add(mod)
                    elif s.startswith("from ") and " import " in s:
                        mod = s.split()[1].split(".")[0].strip()
                        if mod and mod not in stdlib and mod not in proj_modulleri:
                            third_party.add(mod)
        except Exception:
            pass
    return sorted(third_party)


def _pip_kur():
    """Pip yoksa otomatik kur. Donus: pip komutu listesi veya None."""
    # pip zaten var mi?
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return [sys.executable, "-m", "pip"]
    except Exception:
        pass

    # pip yok, get-pip.py ile kur
    print("    pip bulunamadi, otomatik kuruluyor...")
    try:
        import tempfile, urllib.request
        url = "https://bootstrap.pypa.io/get-pip.py"
        req = urllib.request.Request(url, headers={"User-Agent": "CmdTools/0.3"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="wb") as f:
            f.write(data)
            get_pip_path = f.name
        # PEP 668 kontrolu
        brk = []
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--break-system-packages", "--help"],
                capture_output=True, timeout=5,
            )
            if "--break-system-packages" in (r.stdout or b"").decode(errors="replace"):
                brk = ["--break-system-packages"]
        except Exception:
            pass
        result = subprocess.run(
            [sys.executable, get_pip_path, "--user"] + brk,
            capture_output=True, text=True, timeout=120,
        )
        os.unlink(get_pip_path)
        if result.returncode == 0:
            print("    pip basariyla kuruldu!")
            return [sys.executable, "-m", "pip"]
    except Exception as e:
        print(f"    pip kurulumu basarisiz: {e}")
    return None


def cmd_install():
    """Gereken kutuphaneleri tara ve kur. Tam kurulum: pip + Python kutuphaneleri + sistem araclari."""
    import tempfile as _tempfile

    print()
    print(" CmdTools Kurulum Baslatiliyor")
    print("=" * 50)

    # ─── 1. INTERNET KONTROLU ───
    print()
    print(" 1/4  Internet baglantisi kontrol ediliyor...")
    try:
        import urllib.request as _urllib_req
        _urllib_req.urlopen("https://pypi.org", timeout=5)
        print("      Internet baglantisi OK")
    except Exception:
        print("      Internet baglantisi yok veya PyPI erisilemez!")
        print("      Internet baglantisi olmadan kurulum yapilamaz.")
        return

    # ─── 2. PIP KURULUMU ───
    print()
    print(" 2/4  pip kontrol ediliyor...")
    pip_cmd = _pip_kur()
    if not pip_cmd:
        print("      pip kurulamadi! Manuel olarak pip'i yukleyin.")
        print("     ornek: curl https://bootstrap.pypa.io/get-pip.py | python3")
        return
    print("      pip OK")

    # PEP 668 (--break-system-packages) kontrolu
    brk_flags = []
    try:
        r = subprocess.run(
            pip_cmd + ["install", "--break-system-packages", "--help"],
            capture_output=True, timeout=5,
        )
        if "--break-system-packages" in (r.stdout or b"").decode(errors="replace"):
            brk_flags = ["--break-system-packages"]
    except Exception:
        pass

    # ─── 3. PYTHON KUTUPHANELERI ───
    print()
    print(" 3/4  Python kutuphaneleri kuruluyor...")

    # Tum projedeki import'lari tara
    imports = _find_third_party_imports()

    # pip paket adi eslestirmeleri
    pip_map = {
        "dns": "dnspython",
        "yaml": "pyyaml",
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "sklearn": "scikit-learn",
        "cv": "opencv-python",
    }

    # Tam liste: projenin ihtiyac duydugu tum kutuphaneler
    TAM_LISTE = [
        ("psutil",       "Sistem bilgileri (sysinfo, uptime)"),
        ("requests",     "HTTP istekleri (grafik)"),
        ("plotext",      "Terminal grafikleri (grafik)"),
        ("yfinance",     "Hisse/Kripto verileri (analiz, sinyal, ytai, alarm)"),
        ("dnspython",    "DNS sorgulama (ns)"),
        ("g4f",          "AI yorumlama (haber, sinyal, ytai)"),
        ("netifaces",    "Ag arayuzleri (ip)"),
        ("speedtest-cli", "Hiz testi (speedtest)"),
    ]

    kurulan = []
    kuruldu_sayi = 0
    mevcut_sayi = 0
    basarisiz = []

    for pip_name, aciklama in TAM_LISTE:
        mod_name = pip_name.replace("-", "_").replace("python", "")
        # modul adini dogrula
        try:
            importlib.import_module(mod_name)
            print(f"      {pip_name:<20} zaten kurulu  ({aciklama})")
            mevcut_sayi += 1
            continue
        except ImportError:
            pass

        print(f"      {pip_name:<20} kuruluyor...  ({aciklama})", end=" ", flush=True)
        try:
            # speedtest-cli icin pip paket adi farkli
            actual_pip = "speedtest-cli" if pip_name == "speedtest-cli" else pip_name
            result = subprocess.run(
                pip_cmd + ["install", actual_pip, "-q"] + brk_flags,
                capture_output=True, text=True, timeout=300,
            )
            if result.returncode == 0:
                print("OK")
                kurulan.append(pip_name)
                kuruldu_sayi += 1
            else:
                hata = (result.stderr or "").strip().split("\n")[-1][:50]
                print(f"HATA: {hata}")
                basarisiz.append(pip_name)
        except subprocess.TimeoutExpired:
            print("ZAMAN ASIMI")
            basarisiz.append(pip_name)
        except Exception as e:
            print(f"HATA: {str(e)[:50]}")
            basarisiz.append(pip_name)

    # Taramadan gelen ek kutuphaneler
    for mod in imports:
        pip_name = pip_map.get(mod, mod)
        if pip_name in [x[0] for x in TAM_LISTE] or pip_name in kurulan or pip_name in basarisiz:
            continue
        try:
            importlib.import_module(mod)
            mevcut_sayi += 1
            continue
        except ImportError:
            pass
        print(f"      {pip_name:<20} kuruluyor...", end=" ", flush=True)
        try:
            result = subprocess.run(
                pip_cmd + ["install", pip_name, "-q"] + brk_flags,
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0:
                print("OK")
                kurulan.append(pip_name)
                kuruldu_sayi += 1
            else:
                print("ATLANDI")
                basarisiz.append(pip_name)
        except Exception:
            print("ATLANDI")
            basarisiz.append(pip_name)

    # ─── 4. SISTEM ARACTLARI ───
    print()
    print(" 4/4  Sistem araclari kontrol ediliyor...")
    sistem_komutlari = {
        "dig":       "dnsutils (DNS araclari)",
        "nslookup":  "dnsutils (DNS araclari)",
        "hciconfig": "bluez (Bluetooth)",
        "ss":        "iproute2 (ag araclari)",
        "ping":      "iputils-ping",
    }
    for komut, paket in sistem_komutlari.items():
        sonuc = subprocess.run(
            ["which", komut], capture_output=True, text=True, timeout=5,
        )
        if sonuc.returncode == 0:
            print(f"      {komut:<12} OK")
        else:
            print(f"      {komut:<12} eksik ({paket}) — sudo apt install {paket.split()[0]}")

    # ─── SONUC ───
    print()
    print("=" * 50)
    toplam = kuruldu_sayi + mevcut_sayi
    if basarisiz:
        print(f"  Kurulum tamamlandi: {kuruldu_sayi} kuruldu, {mevcut_sayi} mevcut, {len(basarisiz)} basarisiz")
        print(f"  Basarisiz: {', '.join(basarisiz)}")
        print(f"  Manuel: pip3 install {' '.join(basarisiz)}")
    else:
        print(f"  Tum kutuphaneler hazir! ({kuruldu_sayi} kuruldu, {mevcut_sayi} zaten vardi)")
    print("=" * 50)
    print()


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        cmd_version()
        print()
        print("Kullanilan: cmdtools <komut>")
        print("  cmdtools help       Yardim")
        print("  cmdtools list       Komut listesi")
        print("  cmdtools version    Surum bilgisi")
        print("  cmdtools about      Proje hakkind")
        print("  cmdtools install    Kutuphaneleri kur")
        return

    komut = args[0].lower()

    if komut in ("version", "--version", "-v"):
        cmd_version()
    elif komut in ("about", "bilgi"):
        cmd_about()
    elif komut in ("list", "--list", "-l"):
        cmd_list()
    elif komut in ("help", "yardim"):
        konu = args[1] if len(args) > 1 else None
        cmd_help(konu)
    elif komut in ("install", "indir"):
        cmd_install()
    else:
        print(f"Bilinmeyen komut: {komut}")
        print("Kullanilan: cmdtools help | list | version | about")


if __name__ == "__main__":
    main()
