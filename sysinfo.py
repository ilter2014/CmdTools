import platform
import os
import sys
import subprocess
import re
import json
from datetime import datetime, timedelta

# İç kütüphane uyarılarını sessize al
import warnings
warnings.filterwarnings("ignore")


def get_cpu_info():
    """CPU bilgilerini toplar."""
    info = {}

    # Temel platform bilgileri
    info["islemci"] = platform.processor()

    # WMIC ile detaylı CPU bilgisi (Windows)
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                'wmic cpu get Name,NumberOfCores,NumberOfLogicalProcessors,MaxClockSpeed /format:csv',
                shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace").strip()

            lines = [l.strip() for l in output.splitlines() if l.strip()]
            for line in lines[1:]:  # İlk satır başlık
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 5:
                    info["model"] = parts[2]
                    info["cekirdek"] = parts[3]
                    info["mantiksal_islemci"] = parts[4]
                    info["max_hiz_mhz"] = parts[5]
        except Exception:
            pass

        try:
            usage = subprocess.check_output(
                'wmic cpu get LoadPercentage /format:csv',
                shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace").strip()
            lines = [l.strip() for l in usage.splitlines() if l.strip()]
            if len(lines) > 1:
                parts = [p.strip() for p in lines[1].split(",")]
                if len(parts) >= 2 and parts[1]:
                    info["kullanim_yuzde"] = parts[1]
        except Exception:
            pass

    elif sys.platform == "linux":
        try:
            with open("/proc/cpuinfo", "r") as f:
                cpuinfo = f.read()
            cores = cpuinfo.count("processor")
            info["mantiksal_islemci"] = str(cores)
            model_match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
            if model_match:
                info["model"] = model_match.group(1).strip()
            mhz_match = re.search(r"cpu MHz\s*:\s*([\d.]+)", cpuinfo)
            if mhz_match:
                info["max_hiz_mhz"] = str(int(float(mhz_match.group(1))))
            # CPU load from /proc/loadavg
            with open("/proc/loadavg", "r") as f:
                loadavg = f.read().strip().split()
            if loadavg:
                cores_int = cores if cores > 0 else 1
                info["kullanim_yuzde"] = f"{float(loadavg[0]) / cores_int * 100:.1f}"
        except Exception:
            pass

    # psutil varsa daha detaylı
    try:
        import psutil
        info["fiziksel_cekirdek"] = psutil.cpu_count(logical=False)
        info["toplam_mantiksal"] = psutil.cpu_count(logical=True)
        info["kullanim_yuzde"] = f"{psutil.cpu_percent(interval=0.5)}%"
        info["frekans_mhz"] = f"{psutil.cpu_freq().current:.0f}" if psutil.cpu_freq() else "—"
    except ImportError:
        pass

    return info


def get_ram_info():
    """RAM bilgilerini toplar."""
    info = {}

    # psutil ile detaylı RAM bilgisi
    try:
        import psutil
        mem = psutil.virtual_memory()
        total_gb = mem.total / (1024**3)
        available_gb = mem.available / (1024**3)
        used_gb = mem.used / (1024**3)
        info["toplam"] = f"{total_gb:.2f} GB"
        info["kullanilan"] = f"{used_gb:.2f} GB"
        info["bos"] = f"{available_gb:.2f} GB"
        info["kullanim_yuzde"] = f"{mem.percent}%"

        # Swap
        swap = psutil.swap_memory()
        info["takas_toplam"] = f"{swap.total / (1024**3):.2f} GB"
        info["takas_kullanim_yuzde"] = f"{swap.percent}%"
    except ImportError:
        # WMIC fallback
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(
                    'wmic memorychip get Capacity /format:csv',
                    shell=True, timeout=5, stderr=subprocess.DEVNULL
                ).decode("utf-8", errors="replace").strip()
                total_bytes = 0
                for line in output.splitlines()[1:]:
                    line = line.strip()
                    if line and "," in line:
                        try:
                            total_bytes += int(line.split(",")[1])
                        except (ValueError, IndexError):
                            pass
                if total_bytes > 0:
                    info["toplam"] = f"{total_bytes / (1024**3):.2f} GB"
            except Exception:
                pass
        elif sys.platform == "linux":
            try:
                with open("/proc/meminfo", "r") as f:
                    meminfo = f.read()
                mem_data = {}
                for line in meminfo.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = parts[1].strip().split()[0]  # kB value
                        mem_data[key] = int(val)
                total_kb = mem_data.get("MemTotal", 0)
                avail_kb = mem_data.get("MemAvailable", 0)
                free_kb = mem_data.get("MemFree", 0)
                if total_kb > 0:
                    info["toplam"] = f"{total_kb / (1024**2):.2f} GB"
                    used_kb = total_kb - avail_kb if avail_kb else total_kb - free_kb
                    info["kullanilan"] = f"{used_kb / (1024**2):.2f} GB"
                    info["bos"] = f"{avail_kb / (1024**2):.2f} GB" if avail_kb else f"{free_kb / (1024**2):.2f} GB"
                    info["kullanim_yuzde"] = f"{(total_kb - avail_kb) / total_kb * 100:.1f}" if avail_kb else "—"
                swap_total = mem_data.get("SwapTotal", 0)
                swap_free = mem_data.get("SwapFree", 0)
                if swap_total > 0:
                    info["takas_toplam"] = f"{swap_total / (1024**2):.2f} GB"
                    info["takas_kullanim_yuzde"] = f"{(swap_total - swap_free) / swap_total * 100:.1f}"
            except Exception:
                pass

    return info


def get_os_info():
    """İşletim sistemi bilgilerini toplar."""
    info = {}

    info["sistem"] = platform.system()
    info["surum"] = platform.version()
    info["release"] = platform.release()
    info["makine"] = platform.machine()
    info["node"] = platform.node()
    info["platform"] = platform.platform()

    # Windows için detaylı sürüm
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                'wmic os get Caption,InstallDate,LastBootUpTime,OSArchitecture /format:csv',
                shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace").strip()
            lines = [l.strip() for l in output.splitlines() if l.strip()]
            if len(lines) > 1:
                parts = [p.strip() for p in lines[1].split(",")]
                if len(parts) >= 5:
                    info["windows_surum"] = parts[2]
                    info["mimari"] = parts[5]
        except Exception:
            pass

    elif sys.platform == "linux":
        try:
            with open("/etc/os-release", "r") as f:
                osrel = f.read()
            os_data = {}
            for line in osrel.splitlines():
                parts = line.split("=", 1)
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().strip('"').strip("'")
                    os_data[key] = val
            if "PRETTY_NAME" in os_data:
                info["linux_surum"] = os_data["PRETTY_NAME"]
            elif "NAME" in os_data:
                ver = os_data.get("VERSION_ID", "")
                info["linux_surum"] = f"{os_data['NAME']} {ver}".strip()
            if "ARCHITECTURE" in os_data:
                info["mimari"] = os_data["ARCHITECTURE"]
        except Exception:
            pass

    # Windows aktivasyon durumu
    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                'cscript //nologo "%windir%\\system32\\slmgr.vbs" /xpr',
                shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace").strip()
            info["lisans_durumu"] = output.strip()
        except Exception:
            pass

    return info


def get_disk_info():
    """Disk bilgilerini toplar."""
    info = {}

    try:
        import psutil
        partitions = []
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "birim": part.device,
                    "baglanti_noktasi": part.mountpoint,
                    "dosya_sistemi": part.fstype,
                    "toplam": f"{usage.total / (1024**3):.2f} GB",
                    "kullanilan": f"{usage.used / (1024**3):.2f} GB",
                    "bos": f"{usage.free / (1024**3):.2f} GB",
                    "kullanim_yuzde": f"{usage.percent}%"
                })
            except Exception:
                pass
        info["bolumler"] = partitions
    except ImportError:
        pass

    return info


def get_boot_time():
    """Sistem açılış süresini ve çalışma süresini hesaplar."""
    try:
        import psutil
        boot_ts = psutil.boot_time()
        boot_time = datetime.fromtimestamp(boot_ts)
        now = datetime.now()
        uptime = now - boot_time

        gun = uptime.days
        saat = uptime.seconds // 3600
        dakika = (uptime.seconds % 3600) // 60

        return {
            "acilis_zamani": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
            "calisma_suresi": f"{gun} gün, {saat} saat, {dakika} dakika"
        }
    except (ImportError, Exception):
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(
                    'wmic os get LastBootUpTime /format:csv',
                    shell=True, timeout=5, stderr=subprocess.DEVNULL
                ).decode("utf-8", errors="replace").strip()
                lines = [l.strip() for l in output.splitlines() if l.strip()]
                if len(lines) > 1:
                    parts = [p.strip() for p in lines[1].split(",")]
                    if len(parts) >= 2 and parts[1]:
                        from datetime import datetime
                        boot_str = parts[1].split(".")[0]
                        boot_time = datetime.strptime(boot_str, "%Y%m%d%H%M%S")
                        now = datetime.now()
                        uptime = now - boot_time
                        gun = uptime.days
                        saat = uptime.seconds // 3600
                        dakika = (uptime.seconds % 3600) // 60
                        return {
                            "acilis_zamani": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                            "calisma_suresi": f"{gun} gün, {saat} saat, {dakika} dakika"
                        }
            except Exception:
                pass
        elif sys.platform == "linux":
            try:
                with open("/proc/uptime", "r") as f:
                    uptime_sec = float(f.read().split()[0])
                boot_time = datetime.now() - timedelta(seconds=uptime_sec)
                gun = int(uptime_sec // 86400)
                saat = int((uptime_sec % 86400) // 3600)
                dakika = int((uptime_sec % 3600) // 60)
                return {
                    "acilis_zamani": boot_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "calisma_suresi": f"{gun} gun, {saat} saat, {dakika} dakika"
                }
            except Exception:
                pass
    return {}


def format_output(data):
    """Veriyi okunabilir formatta yazdırır."""
    lines = []
    lines.append("=" * 60)
    lines.append("  [ SISTEM BILGILERI ]")
    lines.append("=" * 60)

    # OS Bilgileri
    os_info = data.get("os", {})
    lines.append("")
    lines.append("  +- ISLETIM SISTEMI")
    lines.append(f"  | Sistem      : {os_info.get('sistem', '-')} {os_info.get('release', '-')}")
    if "linux_surum" in os_info:
        lines.append(f"  | Surum       : {os_info['linux_surum']}")
    elif "windows_surum" in os_info:
        lines.append(f"  | Surum       : {os_info['windows_surum']}")
    lines.append(f"  | Mimari      : {os_info.get('mimari', os_info.get('makine', '-'))}")
    lines.append(f"  | Bilgisayar  : {os_info.get('node', '-')}")
    if "lisans_durumu" in os_info:
        lines.append(f"  | Lisans      : {os_info['lisans_durumu']}")

    # CPU Bilgileri
    cpu = data.get("cpu", {})
    lines.append("")
    lines.append("  +- ISLEMCI (CPU)")
    if cpu.get("model"):
        lines.append(f"  | Model       : {cpu['model']}")
    elif cpu.get("islemci"):
        lines.append(f"  | Islemci     : {cpu['islemci']}")
    if "fiziksel_cekirdek" in cpu:
        lines.append(f"  | Fiziksel    : {cpu['fiziksel_cekirdek']} cekirdek")
    if "cekirdek" in cpu:
        lines.append(f"  | Cekirdek    : {cpu['cekirdek']}")
    if "toplam_mantiksal" in cpu:
        lines.append(f"  | Mantiksal   : {cpu['toplam_mantiksal']} islemci")
    if "mantiksal_islemci" in cpu:
        lines.append(f"  | Mantiksal   : {cpu['mantiksal_islemci']}")
    if cpu.get("frekans_mhz", "").replace(",", "").replace(".", "").isdigit():
        hiz = float(cpu['frekans_mhz'].replace(",", ""))
        lines.append(f"  | Frekans     : {hiz:.0f} MHz ({hiz/1000:.2f} GHz)")
    if "max_hiz_mhz" in cpu:
        lines.append(f"  | Max Frekans : {cpu['max_hiz_mhz']} MHz")
    if "kullanim_yuzde" in cpu:
        lines.append(f"  | Kullanim    : %{cpu['kullanim_yuzde']}")

    # RAM Bilgileri
    ram = data.get("ram", {})
    lines.append("")
    lines.append("  +- BELLEK (RAM)")
    if "toplam" in ram:
        lines.append(f"  | Toplam      : {ram['toplam']}")
    if "kullanilan" in ram:
        lines.append(f"  | Kullanilan  : {ram['kullanilan']}")
    if "bos" in ram:
        lines.append(f"  | Bos         : {ram['bos']}")
    if "kullanim_yuzde" in ram:
        lines.append(f"  | Kullanim    : %{ram['kullanim_yuzde']}")
    if "takas_toplam" in ram:
        lines.append(f"  | Takas (Swap): {ram['takas_toplam']} (%{ram.get('takas_kullanim_yuzde', '-')})")

    # Disk Bilgileri
    disk = data.get("disk", {})
    bolumler = disk.get("bolumler", [])
    if bolumler:
        lines.append("")
        lines.append("  +- DISK BOLUMLERI")
        for bolum in bolumler:
            lines.append(f"  | {bolum['birim']} ({bolum['baglanti_noktasi']})")
            lines.append(f"  |   Boyut : {bolum['toplam']}  Kullanim: %{bolum['kullanim_yuzde']}")
            lines.append(f"  |   Bos   : {bolum['bos']} / {bolum['kullanim_yuzde']} dolu")

    # Çalışma Süresi
    boot = data.get("boot", {})
    if boot:
        lines.append("")
        lines.append("  +- CALISMA SURESI")
        lines.append(f"  | Acilis      : {boot.get('acilis_zamani', '-')}")
        lines.append(f"  | Calisiyor   : {boot.get('calisma_suresi', '-')}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    # stdout UTF-8 olsun ki Türkçe karakterler sorun çıkarmasın
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    # JSON çıktı istendi mi?
    json_mode = "--json" in sys.argv

    data = {
        "os": get_os_info(),
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "disk": get_disk_info(),
        "boot": get_boot_time(),
    }

    if json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_output(data))


if __name__ == "__main__":
    main()
