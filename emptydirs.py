import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import string
import time
import concurrent.futures


def get_all_drives():
    """Sistemdeki tüm sürücü harflerini döndürür."""
    drives = []
    # Linux'ta ortak dizinleri tara
    if sys.platform == "linux":
        linux_paths = ["/home", "/tmp", "/var/tmp"]
        for p in linux_paths:
            if os.path.exists(p):
                drives.append(p)
        return drives
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            drives.append(drive)
    return drives


def format_duration(seconds):
    """Saniyeyi insanın okuyabileceği formata çevir."""
    if seconds < 60:
        return f"{seconds:.1f} saniye"
    elif seconds < 3600:
        return f"{seconds / 60:.1f} dakika"
    else:
        return f"{seconds / 3600:.1f} saat"


def scan_drive_for_empty_folders(drive, timeout_sec=15):
    """
    Bir sürücüdeki tüm boş klasörleri bulur.
    Boş = içinde hiç dosya veya alt klasör olmayan.
    """
    empty_dirs = []
    start = time.time()
    total_folders = 0

    try:
        for root, dirs, files in os.walk(drive):
            if time.time() - start > timeout_sec:
                break

            total_folders += 1

            # Eğer bu klasörde hiç dosya yoksa ve hiç alt klasör yoksa = boş
            if not dirs and not files:
                try:
                    empty_dirs.append(root)
                except (OSError, PermissionError):
                    pass

    except (OSError, PermissionError):
        pass

    elapsed = time.time() - start
    return empty_dirs, total_folders, elapsed


def main():
    print("🔍 Boş klasörler taranıyor...\n")

    drives = get_all_drives()
    all_empty = []
    total_folders_scanned = 0
    total_time = 0
    scanned_drives = 0
    errors = []

    for drive in drives:
        print(f"   Taranıyor: {drive}")
        try:
            empty, folder_count, elapsed = scan_drive_for_empty_folders(drive)
            all_empty.extend(empty)
            total_folders_scanned += folder_count
            total_time += elapsed
            scanned_drives += 1
            print(f"   → {len(empty)} boş klasör bulundu ({elapsed:.1f}s)")
        except Exception as e:
            errors.append(f"   ⚠️ {drive} taranamadı: {e}")

    if errors:
        print()
        for err in errors:
            print(err)

    print()
    print("=" * 70)
    print(f"📊 TARAMA RAPORU")
    print("=" * 70)

    if not all_empty:
        print("\n✅ Hiç boş klasör bulunamadı!")
        print(f"📁 Taranan {scanned_drives} sürücüde toplam {total_folders_scanned} klasör kontrol edildi")
        print(f"⏱️  Toplam süre: {format_duration(total_time)}")
        return

    print(f"\n📁 {'KLASÖR':<60} {'DURUM':<10}")
    print("-" * 70)

    for folder_path in sorted(all_empty):
        # Klasör adını kısaltma
        display_name = folder_path
        if len(display_name) > 57:
            display_name = "..." + display_name[-54:]
        print(f"   {display_name:<60} {'BOŞ':<10}")

    print()
    print(f"📊 Toplam: {len(all_empty)} boş klasör bulundu")
    print(f"📁 Taranan {scanned_drives} sürücüde toplam {total_folders_scanned} klasör kontrol edildi")
    print(f"⏱️  Toplam süre: {format_duration(total_time)}")


if __name__ == "__main__":
    main()
