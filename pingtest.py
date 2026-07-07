import subprocess
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import re
import statistics


TARGETS = [
    ("Google DNS", "8.8.8.8"),
    ("Cloudflare DNS", "1.1.1.1"),
    ("Yerel Gateway", "192.168.1.1"),
]


def ping_host(host, count=4):
    """Bir hosta ping atar, ms değerlerini döndürür."""
    try:
        result = subprocess.run(
            ["ping", "-n", str(count), host],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        # "time=10ms" veya "süresi=10ms" yakala
        times = []
        for line in result.stdout.splitlines():
            m = re.search(r'(?:time|süresi)[=<]\s*(\d+)', line, re.IGNORECASE)
            if m:
                times.append(int(m.group(1)))
        return times
    except (subprocess.TimeoutExpired, OSError):
        return []


def classify_ping(avg_ms):
    """Ping değerine göre kullanım önerisi ver."""
    if avg_ms < 0:
        return "N/A", ""
    elif avg_ms <= 15:
        return "MÜKEMMEL", "Premium oyun, rekabetçi FPS, canlı yayın, 4K video"
    elif avg_ms <= 30:
        return "İYİ", "Online oyun, HD video, video konferans, her şey için uygun"
    elif avg_ms <= 50:
        return "ORTA", "Video izleme, web gezintisi, casual oyunlar uygun"
    elif avg_ms <= 80:
        return "İDARE EDER", "Video izlenir, rekabetçi oyun için gecikmeli"
    elif avg_ms <= 120:
        return "DÜŞÜK", "Video akıcı olmayabilir, oyun zorlayıcı"
    else:
        return "KÖTÜ", "Sadece web gezintisi, video bile kasabilir"


def main():
    print("🌐 Ping Testi Başlatılıyor...\n")

    all_times = []

    for name, host in TARGETS:
        print(f"   📡 {name} ({host}) ölçülüyor...", end="", flush=True)
        times = ping_host(host)
        if times:
            avg = statistics.mean(times)
            min_t = min(times)
            max_t = max(times)
            packet_loss = 4 - len(times)
            all_times.extend(times)
            print(f"  {avg:.0f}ms (min:{min_t}ms / max:{max_t}ms) {'⚠️ ' + str(packet_loss) + ' kayıp' if packet_loss > 0 else '✅'}")
        else:
            print(f"  ⚠️  Yanıt alınamadı")
        print()

    if not all_times:
        print("❌ Hiçbir hedefe ping atılamadı. İnternet bağlantınızı kontrol edin.")
        return

    overall_avg = statistics.mean(all_times)
    overall_min = min(all_times)
    overall_max = max(all_times)

    print("=" * 60)
    print("📊 PİNG TEST RAPORU")
    print("=" * 60)
    print(f"\n   Ortalama: {overall_avg:.0f} ms")
    print(f"   En düşük: {overall_min} ms")
    print(f"   En yüksek: {overall_max} ms")
    print(f"   Test sayısı: {len(all_times)}")

    status, desc = classify_ping(overall_avg)
    print(f"\n   📈 Durum: {status}")
    print(f"   💡 {desc}")

    print()
    print("💡 İpucu: Kablosuz bağlantı kullanıyorsanız kabloya geçmek")
    print("   pinginizi 10-30ms düşürebilir.")
    print("   Kesintisiz bir bağlantı için modem/router reset atabilirsiniz.")


if __name__ == "__main__":
    main()
