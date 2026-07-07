import subprocess
import re
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime


def get_netstat_output():
    """netstat -ano çalıştır ve ham çıktıyı döndür."""
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            errors="replace",
        )
        return result.stdout
    except Exception as e:
        print(f"❌ netstat çalıştırılamadı: {e}")
        return ""


def parse_netstat(output):
    """
    netstat çıktısını parse eder.
    LISTENING durumundaki her bağlantıdan (port, pid) çıkarır.
    """
    connections = []
    for line in output.splitlines():
        line = line.strip()
        if "LISTENING" not in line:
            continue

        parts = line.split()
        if len(parts) < 5:
            continue

        local_addr = parts[1]
        pid_str = parts[-1]

        if not pid_str.isdigit():
            continue

        # Port numarasını ayıkla — IPv4 (0.0.0.0:135) veya IPv6 ([::]:135)
        if "[" in local_addr:
            # IPv6: [::1]:5040
            m = re.search(r'\[.*?\]:(\d+)', local_addr)
        else:
            # IPv4: 0.0.0.0:135  veya  *:135
            m = re.search(r':(\d+)$', local_addr)

        if m:
            connections.append((int(m.group(1)), int(pid_str)))

    # Aynı (port, pid) ikililerini tekle
    seen = set()
    unique = []
    for port, pid in connections:
        key = (port, pid)
        if key not in seen:
            seen.add(key)
            unique.append((port, pid))

    return unique


def get_process_info(pid):
    """
    PID'ye ait işlem adı ve oluşturulma zamanını döndürür.
    Dönen: (işlem_adı, oluşturulma_zamanı_raw | "")
    """
    name = "N/A"
    creation_raw = ""

    try:
        # 1. İşlem adı — tasklist ile
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(",")
            if parts:
                candidate = parts[0].strip('"')
                if candidate:
                    name = candidate

        # 2. Oluşturulma zamanı — WMIC ile
        result2 = subprocess.run(
            ["wmic", "process", "where", f"processid={pid}",
             "get", "name,creationdate", "/FORMAT:CSV"],
            capture_output=True,
            text=True,
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        for line in result2.stdout.splitlines():
            line = line.strip()
            if not line or "CreationDate" in line or "Node" in line:
                continue
            cols = line.split(",")
            if len(cols) >= 3:
                candidate_name = cols[1].strip()
                candidate_creation = cols[2].strip()
                if candidate_name:
                    name = candidate_name
                if candidate_creation:
                    creation_raw = candidate_creation
                break

    except Exception:
        pass

    return name, creation_raw


def calc_uptime(creation_raw):
    """
    WMIC CreationDate'inden (YYYYMMDDHHMMSS.mmmmmm±UUU) geçen süreyi hesaplar.
    Dönen: "2 saat 35 dakika" | "45 dakika" | "N/A"
    """
    if not creation_raw:
        return "N/A"

    try:
        # Ondalıklı kısım ve saat dilimini at
        base = creation_raw.split(".")[0].split("+")[0].split("-")[0]
        created = datetime.strptime(base, "%Y%m%d%H%M%S")
        delta = datetime.now() - created
        total_sec = int(delta.total_seconds())

        if total_sec < 0:
            return "N/A"

        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60

        if hours > 0 and minutes > 0:
            return f"{hours} saat {minutes} dakika"
        elif hours > 0:
            return f"{hours} saat"
        else:
            return f"{minutes} dakika"
    except Exception:
        return "N/A"


def main():
    """Ana fonksiyon — dışarıdan da import edilebilir."""
    print("🔍 Açık portlar taranıyor...\n")

    output = get_netstat_output()
    if not output:
        print("❌ Port bilgisi alınamadı. Yetkili (Admin) olarak çalıştırmayı deneyin.")
        return

    connections = parse_netstat(output)
    if not connections:
        print("❌ Açık port bulunamadı.")
        return

    # Port'a göre sırala
    connections.sort(key=lambda x: x[0])

    print(f"{'PORT':<10} {'UYGULAMA':<35} {'AÇIK KALMA SÜRESİ':<25}")
    print("-" * 70)

    for port, pid in connections:
        name, creation = get_process_info(pid)
        uptime = calc_uptime(creation)
        print(f"{port:<10} {name:<35} {uptime:<25}")

    print(f"\n📊 Toplam {len(connections)} adet açık port bulundu.")
    print("💡 İpucu: Bazı portlar için admin yetkisi gerekebilir.")


if __name__ == "__main__":
    main()
