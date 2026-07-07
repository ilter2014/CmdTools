import sys
import os
import urllib.request
import time
import ssl
import subprocess

# stdout UTF-8 zorlaması (cp1254 Unicode hatası için)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# İç kütüphane uyarılarını sessize al
import warnings
warnings.filterwarnings("ignore")

# === UPDATEROUTER VERSION ===
UPDATEROUTER_VERSION = "2.0"

# === SABİTLER ===
BASE_DIR = r"C:\CmdTools"
VERSION_FILE = os.path.join(BASE_DIR, "version")
SELF_VERSION_FILE = os.path.join(BASE_DIR, "updaterouterversion")
GITHUB_BASE_URL = "https://raw.githubusercontent.com/ilter2014/CmdTools/refs/heads/main"
GITHUB_VERSION_URL = f"{GITHUB_BASE_URL}/version"
GITHUB_SELF_URL = f"{GITHUB_BASE_URL}/updaterouterversion"
GITHUB_MANIFEST_URL = f"{GITHUB_BASE_URL}/manifest.txt"

# Windows SSL kilitlenmelerini önleyen hızlı SSL context'i
ssl_context = ssl._create_unverified_context()


def parse_version_only(content):
    """Read version number from 'version: X.Y' format. Tolerant of extra content for backward compat."""
    for line in content.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            if key.strip().lower() == "version":
                return val.strip()
    return ""


def parse_self_version(content):
    """
    updaterouterversion dosyasını parse eder.
    Format:
        updaterouter_version: X.X
        ---SOURCE---
        [updaterouter.py kodunun tamamı]
    """
    version = ""
    source = ""
    lines = content.splitlines()
    found_source = False
    source_lines = []
    for line in lines:
        if line.strip() == "---SOURCE---":
            found_source = True
            continue
        if not found_source:
            if ":" in line:
                key, _, val = line.partition(":")
                if key.strip().lower() == "updaterouter_version":
                    version = val.strip()
        else:
            source_lines.append(line)
    source = "\n".join(source_lines)
    return version, source


def parse_version_tuple(ver_str):
    """'3.0' → (3, 0), '3.10' → (3, 10) gibi bir tuple döndürür."""
    try:
        parts = str(ver_str).strip().split(".")
        return tuple(int(p) for p in parts if p)
    except (ValueError, AttributeError):
        return (0,)


def is_newer_version(remote_ver, local_ver):
    """
    remote_ver > local_ver ise True döndürür.
    ÖNEMLİ: remote_ver <= local_ver ise False döndürür (sürüm düşürme yok).
    Örnek: local 0.7, remote 0.6 → False (güncelleme değil, düşürme)
    """
    if not remote_ver or not local_ver:
        return False
    return parse_version_tuple(remote_ver) > parse_version_tuple(local_ver)


def fetch_remote_file(file_url, timeout=10):
    """GitHub'dan dosya çeker, bytes döndürür; hata durumunda None."""
    try:
        req = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context) as response:
            return response.read()
    except Exception:
        return None


def write_file_utf8(file_path, data):
    """Dosyayı UTF-8 BOM'suz yazar. Veri zaten bytes ise decode edip yazar."""
    if isinstance(data, bytes):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            text = data.decode("utf-8", errors="replace")
    else:
        text = data
    with open(file_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def check_self_update():
    """
    updaterouterversion üzerinden kendini güncelleme.
    - GitHub'daki updaterouterversion'u çeker
    - Versiyon karşılaştırır (remote > local ise günceller, düşürme YASAK)
    - Güncelleme varsa kodu updaterouter.py'ye yazar
    - Yerel updaterouterversion'u da günceller
    """
    try:
        # 1. Yerel updaterouterversion'u oku
        local_content = ""
        if os.path.exists(SELF_VERSION_FILE):
            with open(SELF_VERSION_FILE, "r", encoding="utf-8") as f:
                local_content = f.read()
        else:
            # Bootstrap: dosya yoksa GitHub'dan çek
            remote_data = fetch_remote_file(GITHUB_SELF_URL)
            if remote_data is not None:
                remote_text = remote_data.decode("utf-8").strip()
                write_file_utf8(SELF_VERSION_FILE, remote_text)
                local_content = remote_text

        local_ver, _ = parse_self_version(local_content)
        if not local_ver:
            local_ver = "0.0"

        # 2. GitHub'daki updaterouterversion'u çek
        remote_data = fetch_remote_file(GITHUB_SELF_URL)
        if remote_data is None:
            return False

        remote_text = remote_data.decode("utf-8").strip()
        remote_ver, remote_source = parse_self_version(remote_text)

        if not remote_ver:
            return False

        # 3. Sürüm karşılaştırması: remote > local ise güncelle
        #    (remote <= local: ya eşit ya da düşürme — atla)
        if not is_newer_version(remote_ver, local_ver):
            return False

        # 4. GÜNCELLEME VAR!
        baslangic = time.time()
        surum_eski = local_ver
        surum_yeni = remote_ver
        print(f"🔄 updaterouter.py güncelleniyor: {surum_eski} → {surum_yeni}")

        # Yeni kodu updaterouter.py'ye yaz
        if remote_source and remote_source.strip():
            updaterouter_path = os.path.join(BASE_DIR, "updaterouter.py")
            write_file_utf8(updaterouter_path, remote_source)

        # Yerel updaterouterversion'u güncelle
        write_file_utf8(SELF_VERSION_FILE, remote_text)

        gecen_sure = time.time() - baslangic
        print(f"✅ updaterouter.py güncellendi: {surum_eski} → {surum_yeni} ({gecen_sure:.2f} sn)")
        print("📌 Değişiklikler bir sonraki çalıştırmada etkin olacak.\n")
        return True

    except Exception as e:
        print(f"⚠️ updaterouter.py güncelleme hatası: {e}")
        return False


def check_project_update():
    """Wipe+reload: remote > local ise tüm dosyaları sil, manifest.txt'teki her şeyi yeniden indir."""
    try:
        # 1. Local version oku
        local_ver = ""
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, "r", encoding="utf-8") as f:
                local_ver = parse_version_only(f.read())
        if not local_ver:
            local_ver = "0.0"

        # 2. Remote version çek
        remote_data = fetch_remote_file(GITHUB_VERSION_URL)
        if remote_data is None:
            return
        remote_ver = parse_version_only(remote_data.decode("utf-8"))

        if not remote_ver or not is_newer_version(remote_ver, local_ver):
            return

        # 3. GÜNCELLEME VAR!
        baslangic = time.time()
        surum_eski = local_ver
        surum_yeni = remote_ver
        print(f"\U0001f504 Proje güncelleniyor: {surum_eski} → {surum_yeni}")

        # 4. manifest.txt çek
        manifest_data = fetch_remote_file(GITHUB_MANIFEST_URL)
        if manifest_data is None:
            print("  ⚠️ manifest.txt indirilemedi — güncelleme iptal.")
            return

        manifest_text = manifest_data.decode("utf-8").strip()
        manifest_files = [f.strip() for f in manifest_text.splitlines() if f.strip()]

        if not manifest_files:
            print("  ⚠️ manifest.txt boş — güncelleme iptal.")
            return

        protected = {"updaterouter.py", "updaterouterversion"}

        # 5. Tüm manifest dosyalarını sil (protected hariç)
        for fname in manifest_files:
            if fname in protected:
                continue
            fpath = os.path.join(BASE_DIR, fname)
            if os.path.exists(fpath):
                os.remove(fpath)
                print(f"  \U0001f5d1️ Silindi: {fname}")

        # 6. Her şeyi yeniden indir
        ok = True
        for fname in manifest_files:
            if fname in protected:
                continue
            fpath = os.path.join(BASE_DIR, fname)
            fdir = os.path.dirname(fpath)
            if fdir and not os.path.exists(fdir):
                os.makedirs(fdir, exist_ok=True)

            data = fetch_remote_file(f"{GITHUB_BASE_URL}/{fname}")
            if data is None:
                print(f"  ⚠️ {fname} indirilemedi — atlanıyor.")
                ok = False
            else:
                write_file_utf8(fpath, data)
                print(f"  ✅ İndirildi: {fname}")

        # 7. Temizlik: manifest dışı .cmd/.py dosyalarını sil
        for fname in os.listdir(BASE_DIR):
            fpath = os.path.join(BASE_DIR, fname)
            if not os.path.isfile(fpath):
                continue
            if fname in protected or fname in manifest_files:
                continue
            if fname.endswith(('.cmd', '.py')) or fname == 'version':
                os.remove(fpath)
                print(f"  \U0001f9f9 Temizlik: {fname}")

        # 8. Version dosyasını güncelle
        if ok:
            with open(VERSION_FILE, "w", encoding="utf-8") as f:
                f.write(f"version: {remote_ver}\n")
            gecen_sure = time.time() - baslangic
            print(f"✅ Proje güncellendi: {surum_eski} → {surum_yeni} ({gecen_sure:.2f} sn)\n")
        else:
            print("⚠️ Bazı dosyalar indirilemedi. Version güncellenmedi.\n")

    except Exception as e:
        print(f"❌ Güncelleme hatası: {e}\n")


def main():
    # 1. Önce kendini güncelle (updaterouterversion kontrolü)
    check_self_update()

    # 2. Sonra proje dosyalarını güncelle (version kontrolü)
    check_project_update()

    # 3. Gelen argümanları ayıkla ve komut adını yakala
    user_args = sys.argv[1:]
    cmd_called = "haber"  # Varsayılan fallback

    if "--cmdname" in user_args:
        idx = user_args.index("--cmdname")
        if idx + 1 < len(user_args):
            cmd_called = user_args[idx + 1].lower()
        user_args = user_args[:idx] + user_args[idx + 2:]

    # --cmdcmd parametresi (cmdtools alt komutları için)
    if "--cmdcmd" in user_args:
        idx = user_args.index("--cmdcmd")
        if idx + 1 < len(user_args):
            user_args.append(user_args[idx + 1])
        user_args = user_args[:idx] + user_args[idx + 2:]

    target_py = os.path.join(BASE_DIR, f"{cmd_called}.py")

    if not os.path.exists(target_py):
        print(f"❌ Hata: '{cmd_called}.py' dosyası dizinde bulunamadı!")
        return

    # 4. Süreç yönetimi — UTF-8 uyumlu, errors='replace' ile kilitlenme koruması
    result = subprocess.run(
        [sys.executable, target_py] + user_args,
        text=True,
        errors="replace",
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
