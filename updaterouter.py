#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CmdTools Updaterouter
----------------------
GitHub'dan version kontrolu yapar ve guncel dosyalari indirir.

Version kaynagi:
  https://raw.githubusercontent.com/ilter2014/CmdTools/refs/heads/main/version

Indirme:
  https://github.com/ilter2014/CmdTools/archive/refs/heads/main.zip

NOT: GitHub'daki surum yerelden farkliysa (buyuk de olsa kucuk de olsa)
     guncelleme yapilir. Boylece surum dusurme de desteklenir.
"""

import os
import sys
import shutil
import tempfile
import zipfile
import urllib.request
import urllib.error
import re

# ============================================================
# AYARLAR
# ============================================================

GITHUB_VERSION_URL = (
    "https://raw.githubusercontent.com/ilter2014/CmdTools/refs/heads/main/version"
)
GITHUB_ZIP_URL = (
    "https://github.com/ilter2014/CmdTools/archive/refs/heads/main.zip"
)

SELF_DIR = os.path.dirname(os.path.abspath(__file__))
LOCAL_VERSION_FILE = os.path.join(SELF_DIR, "version")


# ============================================================
# YARDIMCI FONKSIYONLAR
# ============================================================

def dosyadan_surum_oku(dosya_yolu):
    """Dosyadan surum numarasini okur. (3.3, v3.3, version: 3.3 hepsi calisir)"""
    try:
        with open(dosya_yolu, "r", encoding="utf-8") as f:
            icerik = f.read().strip()
        # "3.3" veya "v3.3" veya "version: 3.3" gibi formatlar
        eslesme = re.search(r"version[:\s]*v?(\d+\.\d+(?:\.\d+)?)", icerik, re.IGNORECASE)
        if eslesme:
            return eslesme.group(1)
        # Dogrudan sayi ara
        eslesme = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", icerik)
        if eslesme:
            return eslesme.group(1)
        return icerik if icerik else None
    except Exception:
        return None


def githubdan_surum_oku(url):
    """GitHub RAW URL'sinden surum numarasini okur."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CmdTools-Updater/3.3", "Accept": "text/plain"},
        )
        with urllib.request.urlopen(req, timeout=15) as yanit:
            icerik = yanit.read().decode("utf-8").strip()
        eslesme = re.search(r"version[:\s]*v?(\d+\.\d+(?:\.\d+)?)", icerik, re.IGNORECASE)
        if eslesme:
            return eslesme.group(1)
        eslesme = re.search(r"v?(\d+\.\d+(?:\.\d+)?)", icerik)
        if eslesme:
            return eslesme.group(1)
        return icerik if icerik else None
    except urllib.error.HTTPError as e:
        print(f"  [!] HTTP {e.code}: {url}")
        return None
    except urllib.error.URLError as e:
        print(f"  [!] Baglanti sorunu: {e.reason}")
        return None
    except Exception as e:
        print(f"  [!] Hata: {e}")
        return None


def surum_karsilastir(a, b):
    """
    Iki surum numarasini karsilastirir.
    Donus: 1 -> a > b,  0 -> a == b,  -1 -> a < b
    Ornek: 9.2 vs 0.1 -> 1 (dusurme),  0.1 vs 3.3 -> -1 (yukseltme)
    """
    try:
        pa = [int(x) for x in a.split(".")]
        pb = [int(x) for x in b.split(".")]
        for i in range(max(len(pa), len(pb))):
            va = pa[i] if i < len(pa) else 0
            vb = pb[i] if i < len(pb) else 0
            if va > vb:
                return 1
            if va < vb:
                return -1
        return 0
    except (ValueError, AttributeError):
        if a == b:
            return 0
        return 1 if (a or "") > (b or "") else -1


# ============================================================
# INDIRME MOTORU
# ============================================================

def indir_ve_cikart():
    """
    GitHub'dan main.zip'i indirir, gecici klasore acar ve
    tum dosyalari CmdTools klasorune kopyalar.
    updaterouter.py kendini ezmez (guvenlik).
    """
    print("  [1/4] Zip indiriliyor...")

    gecici_zip = None
    gecici_cikti = None

    try:
        gecici_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
        gecici_zip.close()

        req = urllib.request.Request(
            GITHUB_ZIP_URL,
            headers={"User-Agent": "CmdTools-Updater/3.3", "Accept": "application/zip"},
        )

        with urllib.request.urlopen(req, timeout=120) as yanit:
            toplam_boyut = int(yanit.headers.get("Content-Length", 0))
            indirilen = 0
            with open(gecici_zip.name, "wb") as f:
                while True:
                    chunk = yanit.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    indirilen += len(chunk)
                    if toplam_boyut > 0:
                        yuzde = int(indirilen / toplam_boyut * 100)
                        sys.stdout.write(
                            f"\r  Indirme: {yuzde}% ({indirilen:,}/{toplam_boyut:,} bayt)"
                        )
                    else:
                        sys.stdout.write(f"\r  Indirme: {indirilen:,} bayt")
                    sys.stdout.flush()
                print()

        if indirilen == 0:
            print("  [!] Hic veri indirilemedi!")
            return False

        print(f"  -> {indirilen:,} bayt alindi.")

        print("  [2/4] Zip aciliyor...")
        gecici_cikti = tempfile.mkdtemp()

        with zipfile.ZipFile(gecici_zip.name, "r") as zf:
            zf.extractall(gecici_cikti)

        kaynak = os.path.join(gecici_cikti, "CmdTools-main")
        if not os.path.isdir(kaynak):
            elemanlar = os.listdir(gecici_cikti)
            for e in elemanlar:
                tam_yol = os.path.join(gecici_cikti, e)
                if os.path.isdir(tam_yol):
                    kaynak = tam_yol
                    break
            else:
                print("  [!] Zip icinde klasor bulunamadi!")
                return False

        icindekiler = os.listdir(kaynak)
        print(f"  -> {len(icindekiler)} dosya/klasor bulundu.")

        print("  [3/4] Dosyalar kopyalaniyor...")

        sayac = 0
        atlanan = 0

        for eleman in sorted(icindekiler):
            kaynak_yol = os.path.join(kaynak, eleman)
            hedef_yol = os.path.join(SELF_DIR, eleman)

            # updaterouter.py'yi ATLA (kendimizi koru)
            if eleman.lower() == "updaterouter.py":
                atlanan += 1
                continue

            try:
                if os.path.isdir(kaynak_yol):
                    if os.path.exists(hedef_yol):
                        shutil.rmtree(hedef_yol, ignore_errors=True)
                    shutil.copytree(kaynak_yol, hedef_yol)
                    sayac += 1
                else:
                    shutil.copy2(kaynak_yol, hedef_yol)
                    sayac += 1
            except PermissionError:
                print(f"  [!] Yetki hatasi: {eleman} (atlandi)")
                atlanan += 1
            except Exception as e:
                print(f"  [!] {eleman} kopyalanamadi: {e}")
                atlanan += 1

        print(f"  -> {sayac} dosya/klasor guncellendi.", end="")
        if atlanan:
            print(f" ({atlanan} atlandi)")
        else:
            print()

        print("  [4/4] Gecici dosyalar temizleniyor...")
        return True

    except urllib.error.HTTPError as e:
        print(f"\n  [!] HTTP {e.code} - GitHub'a erisilemiyor!")
        return False
    except urllib.error.URLError as e:
        print(f"\n  [!] Baglanti sorunu: {e.reason}")
        return False
    except zipfile.BadZipFile:
        print("\n  [!] Bozuk zip dosyasi indirildi!")
        return False
    except Exception as e:
        print(f"\n  [!] Beklenmeyen hata: {e}")
        return False
    finally:
        try:
            if gecici_zip and os.path.exists(gecici_zip.name):
                os.unlink(gecici_zip.name)
        except Exception:
            pass
        try:
            if gecici_cikti and os.path.exists(gecici_cikti):
                shutil.rmtree(gecici_cikti, ignore_errors=True)
        except Exception:
            pass


# ============================================================
# KOMUT YONLENDIRME
# ============================================================

def komutu_calistir(komut_adi, komut_args):
    """
    --cmdname ile gelen komutu ilgili Python betigine yonlendirir.
    Ornek: 'sysinfo' -> sysinfo modulunu import eder, cmd_sysinfo() fonksiyonuna yonlendirir.
    """
    modul_adi = f"{komut_adi}"
    try:
        # Dinamik olarak modulu import et
        import importlib
        modul = importlib.import_module(modul_adi)

        # Fonksiyon adini bul: cmd_<komut> veya main veya dogrudan calistir
        fonk_adi = f"cmd_{komut_adi}"
        if hasattr(modul, fonk_adi):
            fonk = getattr(modul, fonk_adi)
            fonk()
        elif hasattr(modul, "main"):
            # Modulu sys.argv ile tekrar calistir (args'lar ile)
            eski_argv = list(sys.argv)
            sys.argv = [modul_adi + ".py"] + komut_args
            try:
                modul.main()
            finally:
                sys.argv = eski_argv
        else:
            print(f"Hata: {komut_adi}.py icinde uygun fonksiyon bulunamadi.")
            sys.exit(1)
    except ImportError as e:
        print(f"Hata: {komut_adi}.py dosyasi bulunamadi veya yuklenemedi!")
        print(f"  Detay: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Hata: {komut_adi} calistirilirken sorun olustu!")
        print(f"  Detay: {e}")
        sys.exit(1)


def guncelleme_kontrolu(sessiz=False):
    """
    GitHub ile yerel surumu karsilastirir.
    sessiz=True: sadece guncelleme gerekli mi doner, cikti yazmaz.
    Donus: (guncelleme_gerekli, github_version)
    """
    yerel_version = dosyadan_surum_oku(LOCAL_VERSION_FILE)
    if not yerel_version:
        yerel_version = "?"

    if not sessiz:
        print()
        print("=" * 58)
        print(f"  CmdTools Updaterouter")
        print(f"  Yerel surum: v{yerel_version}")
        print("=" * 58)
        print()

    github_version = githubdan_surum_oku(GITHUB_VERSION_URL)

    if not github_version:
        if not sessiz:
            print("  [!] GitHub version alinamadi! Internet baglantisi yok mu?")
            print()
            print("  Bitti. Hicbir sey yapilmadi.")
        return (False, None)

    if not sessiz:
        print(f"  Yerel version: v{yerel_version}")
        print(f"  GitHub version: v{github_version}")
        print()

    if yerel_version == "?":
        return (True, github_version)

    kars = surum_karsilastir(yerel_version, github_version)
    gerekli = (kars != 0)

    if not sessiz:
        if kars > 0:
            print(f"  ! Surum dusurme: v{yerel_version} -> v{github_version}")
        elif kars < 0:
            print(f"  ! Yeni surum: v{yerel_version} -> v{github_version}")
        else:
            print(f"  CmdTools v{yerel_version} zaten guncel.")
        print()

    return (gerekli, github_version)


def guncelleme_yap():
    """GitHub'dan guncel dosyalari indirir ve yukler."""
    print("  Guncelleme baslatiliyor...")
    print()
    basarili = indir_ve_cikart()

    # Linux'ta .cmd dosyalarini temizle (Windows launcher'lari)
    if basarili and sys.platform != "win32":
        _temizle_windows_dosyalari()

    print()
    return basarili


def _temizle_windows_dosyalari():
    """Linux'ta .cmd dosyalarini sil."""
    silinen = 0
    for fname in os.listdir(SELF_DIR):
        if fname.endswith(".cmd"):
            try:
                os.remove(os.path.join(SELF_DIR, fname))
                silinen += 1
            except Exception:
                pass
    if silinen:
        print(f"  {silinen} Windows .cmd dosyasi temizlendi.")


# ============================================================
# ANA MANTIK
# ============================================================

def main():
    # Komut argumanlarini ayristir
    cmdname = "cmdtools"
    cmdcmd = None
    komut_args = []
    gecici_args = list(sys.argv[1:])

    i = 0
    while i < len(gecici_args):
        if gecici_args[i] == "--cmdname" and i + 1 < len(gecici_args):
            cmdname = gecici_args[i + 1]
            i += 2
        elif gecici_args[i] == "--cmdcmd" and i + 1 < len(gecici_args):
            cmdcmd = gecici_args[i + 1]
            i += 2
        else:
            komut_args.append(gecici_args[i])
            i += 1

    # Ana komut cmdtools ise, direkt cmdtools.py'ye yonlendir
    if cmdname == "cmdtools":
        import importlib
        try:
            modul = importlib.import_module("cmdtools")
            # --cmdcmd varsa (about, version vb.) dogrudan calistir
            if cmdcmd:
                fonk_adi = f"cmd_{cmdcmd}"
                if hasattr(modul, fonk_adi):
                    eski_argv = list(sys.argv)
                    sys.argv = [sys.argv[0]] + komut_args
                    try:
                        getattr(modul, fonk_adi)()
                    finally:
                        sys.argv = eski_argv
                    return
            # cmdtools'e kalan argumanlari gonder
            eski_argv = list(sys.argv)
            sys.argv = [sys.argv[0]] + komut_args
            try:
                modul.main()
            finally:
                sys.argv = eski_argv
            return
        except ImportError as e:
            print(f"Hata: cmdtools.py yuklenemedi! {e}")
            sys.exit(1)

    # --- Diger komutlar icin (sysinfo, ip, port vb.) ---

    # Guncelleme kontrolu
    yerel_s = dosyadan_surum_oku(LOCAL_VERSION_FILE) or "0.0"
    github_s = githubdan_surum_oku(GITHUB_VERSION_URL)

    if github_s is None:
        # GitHub erisilemedi → guncelleme yapma, komutu calistir
        pass
    else:
        kars = surum_karsilastir(yerel_s, github_s)
        if kars >= 0:
            # Yerel >= GitHub → guncelleme gerekmiyor (dusurmeyi de atlama)
            pass
        elif kars < 0:
            # GitHub > Yerel → guncelleme yap
            print(f"  Yeni surum mevcut: v{yerel_s} -> v{github_s}")
            print()
            if guncelleme_yap():
                print()
                print("=" * 58)
                print("  OK GUNCELLEME BASARILI!")
                print("=" * 58)
                print()
                print("  Yeni dosyalar indirildi.")
                print()
            else:
                print("  Guncelleme basarisiz. Mevcut surum korunuyor.")
                print()

    # Komutu calistir
    komutu_calistir(cmdname, komut_args)


if __name__ == "__main__":
    main()