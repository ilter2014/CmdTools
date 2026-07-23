import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import time


def check_speedtest_cli():
    """speedtest-cli kurulu mu kontrol et, yoksa yükle."""
    try:
        subprocess.run(
            ["speedtest", "--version"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        return True
    except (FileNotFoundError, OSError):
        pass

    print("📦 speedtest-cli kuruluyor... (azami 30 saniye)")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "speedtest-cli"],
            capture_output=True, text=True, timeout=30,
        )
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("   ⚠️  Kurulum zaman aşımı")
        return False


def run_speedtest():
    """Speedtest'i çalıştırır ve çıktıyı satır satır okur."""
    proc = subprocess.Popen(
        ["speedtest", "--secure"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True,
        creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
    )

    output_lines = []
    for line in proc.stdout:
        line = line.strip()
        if line:
            output_lines.append(line)
            # Anlık durumu göster
            if "Testing from" in line:
                print(f"   🌍 {line}")
            elif "Testing" in line or "Download" in line or "Upload" in line or "Latency" in line or "Idle" in line:
                print(f"   {line}")
            elif "Hosted by" in line:
                print(f"   📡 {line}")

    proc.wait()
    return "\n".join(output_lines)


def parse_results(output):
    """Speedtest çıktısını parse edip sözlük döndürür."""
    results = {
        "isp": "N/A",
        "server": "N/A",
        "ping": "N/A",
        "jitter": "N/A",
        "download_bits": "N/A",
        "upload_bits": "N/A",
        "download_mbps": "N/A",
        "upload_mbps": "N/A",
    }

    # ISP
    m = re.search(r'Testing from\s+(.*?)\s+\(', output)
    if m:
        results["isp"] = m.group(1).strip()

    # Server
    m = re.search(r'Hosted by\s+(.*?)(?:\s+\[|$)', output)
    if m:
        results["server"] = m.group(1).strip()

    # Ping / Jitter
    m = re.search(r'Latency:\s*([\d.]+)\s*ms.*?Jitter:\s*([\d.]+)\s*ms', output, re.DOTALL)
    if m:
        results["ping"] = m.group(1)
        results["jitter"] = m.group(2)
    else:
        m = re.search(r'Latency:\s*([\d.]+)\s*ms', output)
        if m:
            results["ping"] = m.group(1)

    # Download (speedtest-cli çıktısı: "Download: X.XX Mbit/s")
    m = re.search(r'Download:\s*([\d.]+)\s*(Mbit|Gbit)/s', output)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit == "Gbit":
            val *= 1000
        results["download_mbps"] = f"{val:.2f}"
        results["download_bits"] = f"{val * 1_000_000:.0f}"

    # Upload
    m = re.search(r'Upload:\s*([\d.]+)\s*(Mbit|Gbit)/s', output)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        if unit == "Gbit":
            val *= 1000
        results["upload_mbps"] = f"{val:.2f}"
        results["upload_bits"] = f"{val * 1_000_000:.0f}"

    return results, output


def classify_speed(dl_mbps, ul_mbps):
    """Hız değerlerine göre sınıflandırma yapar."""
    try:
        dl = float(dl_mbps)
        ul = float(ul_mbps)
    except (ValueError, TypeError):
        return "N/A", "", ""

    if dl >= 1000:
        dl_label = "🔥 FIBER / 5G"
        dl_desc = "1Gbps+ — Her şey için fazlasıyla yeterli"
    elif dl >= 500:
        dl_label = "⚡ ÇOK HIZLI"
        dl_desc = "Ultra HD, bulut oyun, ağır indirmeler"
    elif dl >= 200:
        dl_label = "🚀 HIZLI"
        dl_desc = "4K video, online oyun, aynı anda çok cihaz"
    elif dl >= 100:
        dl_label = "✅ İYİ"
        dl_desc = "HD video, online oyun, günlük kullanım"
    elif dl >= 50:
        dl_label = "🟡 ORTA"
        dl_desc = "HD video, web, tek cihaz için yeterli"
    elif dl >= 25:
        dl_label = "🟠 İDARE EDER"
        dl_desc = "SD video, web gezintisi, çoklu cihazda zorlanır"
    else:
        dl_label = "🔴 DÜŞÜK"
        dl_desc = "Sadece web, e-posta, video bile kasabilir"

    if ul >= 100:
        ul_label = "⚡ ÇOK İYİ"
        ul_desc = "Bulut yedekleme, canlı yayın, büyük dosya gönderme"
    elif ul >= 50:
        ul_label = "✅ İYİ"
        ul_desc = "Canlı yayın, dosya paylaşımı, video konferans"
    elif ul >= 20:
        ul_label = "🟡 ORTA"
        ul_desc = "Video konferans, dosya gönderme"
    elif ul >= 10:
        ul_label = "🟠 DÜŞÜK"
        ul_desc = "Webcam ile görüşme zorlanabilir"
    else:
        ul_label = "🔴 ÇOK DÜŞÜK"
        ul_desc = "Sadece mesajlaşma, dosya göndermek zor"

    return dl_label, dl_desc, ul_label, ul_desc


def main():
    print("=" * 60)
    print("⚡ SPEEDTEST — İnternet Hız Testi")
    print("=" * 60)
    print()

    # Kütüphane kontrolü
    if not check_speedtest_cli():
        print("❌ speedtest-cli kurulamadı. El ile 'pip install speedtest-cli' deneyin.")
        return

    print("   En iyi sunucu bulunuyor...")
    print()

    # Testi çalıştır
    raw_output = run_speedtest()

    # Parse et
    results, _ = parse_results(raw_output)

    print()
    print("=" * 60)
    print("📊 HIZ TESTİ RAPORU")
    print("=" * 60)
    print(f"\n   🌍 Sağlayıcı:    {results['isp']}")
    print(f"   📡 Sunucu:       {results['server']}")
    print(f"\n   🏓 Ping:          {results['ping']} ms")
    if results['jitter'] != 'N/A':
        print(f"   📶 Jitter:        {results['jitter']} ms")
    print(f"\n   ⬇️  İndirme:       {results['download_mbps']} Mbps")
    print(f"   ⬆️  Yükleme:       {results['upload_mbps']} Mbps")
    print()

    # Sınıflandırma
    dl_label, dl_desc, ul_label, ul_desc = classify_speed(
        results['download_mbps'], results['upload_mbps']
    )
    print(f"   ⬇️  İndirme: {dl_label}")
    print(f"       {dl_desc}")
    print(f"   ⬆️  Yükleme: {ul_label}")
    print(f"       {ul_desc}")
    print()

    # Öneri
    print("💡 İpuçları:")
    print("   • Kablolu bağlantı her zaman daha hızlıdır")
    print("   • Modem/router reseti hızı artırabilir")
    print("   • Test sırasında başka uygulamaları kapatın")
    print("   • 5GHz WiFi, 2.4GHz'den daha hızlıdır")


if __name__ == "__main__":
    main()
