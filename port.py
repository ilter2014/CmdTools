import subprocess
import re
import sys
import os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from datetime import datetime

# Try to set LANG for Turkish locale on Linux
if sys.platform == "linux":
    for var in ("LANG", "LC_ALL"):
        os.environ.setdefault(var, "tr_TR.UTF-8")


def get_netstat_output():
    """netstat -ano (Windows) veya ss -tlnp (Linux) çalıştır ve ham çıktıyı döndür."""
    if sys.platform == "linux":
        try:
            result = subprocess.run(
                ["ss", "-tlnp"],
                capture_output=True,
                text=True,
                errors="replace",
            )
            return result.stdout
        except Exception as e:
            print(f"❌ ss çalıştırılamadı: {e}")
            return ""
    else:
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
    netstat (Windows) veya ss (Linux) çıktısını parse eder.
    LISTENING / LISTEN durumundaki her bağlantıdan (port, pid) çıkarır.
    """
    connections = []
    for line in output.splitlines():
        line = line.strip()

        if sys.platform == "linux":
            # ss -tlnp çıktısı: "LISTEN  0  128  0.0.0.0:22  0.0.0.0:*  users:(("sshd",pid=1234,fd=3))"
            if not line.startswith("LISTEN"):
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            local_addr = parts[3]
            # Port bul: 0.0.0.0:22  veya  [::]:22
            m = re.search(r':(\d+)$', local_addr)
            if not m:
                continue
            port = int(m.group(1))
            # PID bul: users:((...pid=1234...))
            pid_match = re.search(r'pid=(\d+)', line)
            if pid_match:
                pid = int(pid_match.group(1))
            else:
                pid = 0
            connections.append((port, pid))
        else:
            if "LISTENING" not in line:
                continue
            parts = line.split()
            if len(parts) < 5:
                continue
            local_addr = parts[1]
            pid_str = parts[-1]
            if not pid_str.isdigit():
                continue
            if "[" in local_addr:
                m = re.search(r'\[.*?\]:(\d+)', local_addr)
            else:
                m = re.search(r':(\d+)$', local_addr)
            if m:
                connections.append((int(m.group(1)), int(pid_str)))

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
    PID'ye ait isim ve olusturulma zamanini dondurur.
    Donen: (isim, olusturma_zamani_raw | "")  (Linux'ta creation_raw her zaman "")
    """
    name = "N/A"
    creation_raw = ""

    if sys.platform == "linux":
        # /proc/pid/comm dosyasından isim al
        try:
            comm_path = f"/proc/{pid}/comm"
            if os.path.exists(comm_path):
                with open(comm_path, "r") as f:
                    name = f.read().strip()
        except Exception:
            pass
        return name, creation_raw

    try:
        # 1. Isim — tasklist ile (Windows)
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

        # 2. Olusturulma zamani — WMIC ile (Windows)
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
