import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re


def get_uptime_seconds():
    """
    Sistem çalışma süresini saniye cinsinden döndürür.
    Linux'ta /proc/uptime, Windows'ta wmic/net statistics server kullanılır.
    """
    # Linux: /proc/uptime
    if sys.platform == "linux":
        try:
            with open("/proc/uptime", "r") as f:
                uptime_sec = float(f.read().split()[0])
            return int(uptime_sec)
        except Exception:
            pass

    # Yöntem 1: wmic ile
    try:
        result = subprocess.run(
            ["wmic", "os", "get", "lastbootuptime"],
            capture_output=True,
            text=True,
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if line and line.isdigit():
                boot_raw = line.strip()
                import datetime
                boot = datetime.datetime.strptime(boot_raw.split(".")[0], "%Y%m%d%H%M%S")
                delta = datetime.datetime.now() - boot
                return int(delta.total_seconds())
    except Exception:
        pass

    # Yöntem 2: systeminfo ile
    try:
        result = subprocess.run(
            ["systeminfo", "|", "find", "System Boot Time"],
            capture_output=True,
            text=True,
            errors="replace",
            shell=True,
        )
        for line in result.stdout.splitlines():
            m = re.search(r'(\d+/\d+/\d+\s+\d+:\d+:\d+)', line)
            if m:
                import datetime
                boot = datetime.datetime.strptime(m.group(1), "%m/%d/%Y %H:%M:%S")
                delta = datetime.datetime.now() - boot
                return int(delta.total_seconds())
    except Exception:
        pass

    # Yöntem 3: net statistics server (İngilizce Windows)
    try:
        result = subprocess.run(
            ["net", "statistics", "server"],
            capture_output=True,
            text=True,
            errors="replace",
        )
        for line in result.stdout.splitlines():
            if "Statistics since" in line:
                m = re.search(r'(\d+/\d+/\d+\s+\d+:\d+:\d+)', line)
                if m:
                    import datetime
                    boot = datetime.datetime.strptime(m.group(1), "%m/%d/%Y %H:%M:%S")
                    delta = datetime.datetime.now() - boot
                    return int(delta.total_seconds())
    except Exception:
        pass

    return None


def format_uptime(total_sec):
    """Saniyeyi 'X saat Y dakika' formatına çevir."""
    if total_sec is None:
        return "N/A"

    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60

    if hours > 0 and minutes > 0:
        return f"{hours} saat {minutes} dakika"
    elif hours > 0:
        return f"{hours} saat"
    else:
        return f"{minutes} dakika"


def main():
    print("⏱️  Sistem çalışma süresi hesaplanıyor...\n")

    sec = get_uptime_seconds()
    if sec is None:
        print("❌ Uptime bilgisi alınamadı.")
        return

    text = format_uptime(sec)

    # Gün varsa ekle
    days = sec // 86400
    hours = (sec % 86400) // 3600
    minutes = (sec % 3600) // 60

    if days > 0:
        print(f"🖥️  Bilgisayar {days} gün {hours} saat {minutes} dakikadır açık.")
    elif hours > 0:
        print(f"🖥️  Bilgisayar {hours} saat {minutes} dakikadır açık.")
    else:
        print(f"🖥️  Bilgisayar {minutes} dakikadır açık.")

    print(f"\n📊 Toplam: {sec} saniye")


if __name__ == "__main__":
    main()
