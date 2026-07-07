import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def format_size(bytes_val):
    """Byte değerini insanın okuyabileceği formata çevirir."""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 ** 2:
        return f"{bytes_val / 1024:.1f} KB"
    elif bytes_val < 1024 ** 3:
        return f"{bytes_val / 1024 ** 2:.1f} MB"
    else:
        return f"{bytes_val / 1024 ** 3:.2f} GB"


def get_dir_size(path):
    """Klasörün toplam boyutunu hesaplar (iç içe tüm dosyalar)."""
    total = 0
    file_count = 0
    folder_count = 0
    try:
        for root, dirs, files in os.walk(path):
            folder_count += len(dirs)
            for f in files:
                try:
                    fp = os.path.join(root, f)
                    total += os.path.getsize(fp)
                    file_count += 1
                except (OSError, PermissionError):
                    pass
    except (OSError, PermissionError) as e:
        print(f"⚠️  Klasör taranırken hata: {e}")
        return None, 0, 0
    return total, file_count, folder_count


def show_file_info(path):
    """Tek dosya bilgisini gösterir."""
    try:
        size = os.path.getsize(path)
        name = os.path.basename(path)
        print(f"📄 {name}")
        print(f"   Boyut: {format_size(size)}")
        print(f"   Tam yol: {os.path.abspath(path)}")
    except OSError as e:
        print(f"❌ Dosya okunamadı: {e}")


def show_dir_info(path):
    """Klasör bilgisini ve içindekileri gösterir."""
    try:
        items = os.listdir(path)
    except (OSError, PermissionError) as e:
        print(f"❌ Klasör okunamadı: {e}")
        return

    abs_path = os.path.abspath(path)
    print(f"📁 {os.path.basename(path) or path}")
    print(f"   Tam yol: {abs_path}")
    print()

    # Önce dosyaları, sonra klasörleri listele
    files = []
    dirs = []
    for item in items:
        try:
            full = os.path.join(path, item)
            if os.path.isfile(full):
                files.append(item)
            elif os.path.isdir(full):
                dirs.append(item)
        except (OSError, PermissionError):
            pass

    # Klasör içindekileri listele
    if items:
        print(f"   İçindekiler ({len(items)} öğe):")
        print()
        for d in sorted(dirs):
            d_path = os.path.join(path, d)
            d_size, _, _ = get_dir_size(d_path)
            d_size_str = format_size(d_size) if d_size is not None else "N/A"
            print(f"   📁 {d:<30} {d_size_str:>10}")
        for f in sorted(files):
            f_path = os.path.join(path, f)
            try:
                f_size = os.path.getsize(f_path)
            except (OSError, PermissionError):
                f_size = 0
            print(f"   📄 {f:<30} {format_size(f_size):>10}")
        print()
    else:
        print("   (boş klasör)")

    # Toplam boyut
    total_size, file_count, folder_count = get_dir_size(path)
    if total_size is not None:
        print(f"   📊 Toplam boyut: {format_size(total_size)}")
        print(f"   📂 {folder_count} alt klasör, {file_count} dosya")
    else:
        print(f"   📊 Toplam boyut: N/A (bazı dosyalar okunamadı)")


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # --cmdname temizlenmiş haliyle gelen arg
    path = args[0] if args else "."

    # Yolu genişlet (tilda vs.)
    path = os.path.expanduser(path)
    path = os.path.expandvars(path)

    if not os.path.exists(path):
        print(f"❌ Hata: '{path}' bulunamadı.")
        return

    print(f"📏 Boyut hesaplanıyor...\n")

    if os.path.isfile(path):
        show_file_info(path)
    elif os.path.isdir(path):
        show_dir_info(path)
    else:
        print(f"❌ Hata: '{path}' tanınamayan bir öğe.")


if __name__ == "__main__":
    main()
