import sys, subprocess, re, json, urllib.request, urllib.error, ssl
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ssl_ctx = ssl._create_unverified_context()

# Dünya çapında DNS sunucuları (dnschecker.org benzeri)
DNS_SERVERS = [
    # Kuzey Amerika
    ("New York, ABD",    "216.239.32.10"),
    ("San Francisco, ABD", "216.239.36.10"),
    ("Chicago, ABD",     "216.239.34.10"),
    ("Dallas, ABD",      "216.239.38.10"),
    ("Toronto, Kanada",  "216.239.36.10"),
    # Avrupa
    ("Londra, UK",       "216.239.32.10"),
    ("Frankfurt, Almanya", "216.239.36.10"),
    ("Amsterdam, Hollanda", "216.239.34.10"),
    ("Paris, Fransa",    "216.239.38.10"),
    ("Stockholm, İsveç", "216.239.32.10"),
    # Asya
    ("Tokyo, Japonya",   "216.239.34.10"),
    ("Singapur",         "216.239.38.10"),
    ("Seul, Güney Kore", "216.239.36.10"),
    ("Mumbai, Hindistan","216.239.32.10"),
    ("Dubai, BAE",       "216.239.34.10"),
    # Okyanusya
    ("Sidney, Avustralya", "216.239.36.10"),
    # Güney Amerika
    ("Sao Paulo, Brezilya", "216.239.38.10"),
]

# Gerçek DNS sunucuları (Google, Cloudflare, Quad9, OpenDNS, Comodo)
REAL_DNS = [
    ("Google DNS",          "8.8.8.8"),
    ("Cloudflare DNS",      "1.1.1.1"),
    ("Quad9",               "9.9.9.9"),
    ("OpenDNS",             "208.67.222.222"),
    ("Comodo Secure DNS",   "8.26.56.26"),
    ("Verisign",            "64.6.64.6"),
    ("DNS.WATCH",           "84.200.69.80"),
    ("SafeDNS",             "195.46.39.39"),
    ("Yandex DNS",          "77.88.8.8"),
    ("Neustar DNS",         "156.154.70.1"),
    ("AdGuard DNS",         "94.140.14.14"),
    ("Norton ConnectSafe",  "199.85.126.10"),
]


def nslookup_from(domain, dns_ip, timeout=4):
    """Belirli bir DNS sunucusundan domain sorgula."""
    try:
        result = subprocess.run(
            ["nslookup", domain, dns_ip],
            capture_output=True, text=True, timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        output = result.stdout
        # Başarılı yanıt mı?
        if "Address" in output and ("Name" in output or "Name:" in output):
            # IP çözümlenmiş mi?
            ips = re.findall(r'Address(?:es)?:\s+([\d.]+)', output)
            ips = [ip for ip in ips if not ip.startswith("127.") and ip != dns_ip]
            if ips:
                return True, ips
        if "can't find" in output.lower() or "can't resolve" in output.lower() or "NXDOMAIN" in output:
            return False, []
        return False, []
    except (subprocess.TimeoutExpired, OSError):
        return None, []  # timeout = belirsiz


def get_ns_records(domain):
    """Domain'in nameserver'larını sorgula."""
    try:
        result = subprocess.run(
            ["nslookup", "-type=NS", domain],
            capture_output=True, text=True, timeout=8,
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        ns_list = []
        for m in re.finditer(r'primary name server = (.+)', result.stdout):
            ns_list.append(m.group(1).strip())
        for m in re.finditer(r'nameserver = (.+)', result.stdout):
            ns_list.append(m.group(1).strip())
        return ns_list if ns_list else []
    except:
        return []


def get_authoritative_ns(domain):
    """whois benzeri yetkili NS'leri bul."""
    ns_list = get_ns_records(domain)
    # Türkçe karakterleri düzelt
    if not ns_list:
        # Alternatif: dig benzeri
        try:
            result = subprocess.run(
                ["nslookup", "-type=NS", domain],
                capture_output=True, text=True, timeout=8, errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
            )
            for m in re.finditer(r'=(.+)\r?$', result.stdout):
                ns_list.append(m.group(1).strip())
        except:
            pass
    return ns_list


def check_dnschecker_style(domain, ns_servers):
    """DNS sunucularından domain'in görünürlüğünü kontrol et."""
    all_results = {}

    # Gerçek DNS sağlayıcıları
    for name, ip in REAL_DNS:
        status, ips = nslookup_from(domain, ip)
        if status is True:
            all_results[name] = ("✅", ips, ip)
        elif status is None:
            all_results[name] = ("⏱️", [], ip)
        else:
            all_results[name] = ("❌", [], ip)

    return all_results


def whois_ns_lookup(domain):
    """Ek olarak whois benzeri NS sorgusu."""
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             f"Resolve-DnsName -Name {domain} -Type NS | Select-Object NameHost | Format-Table -HideTableHeader"],
            capture_output=True, text=True, timeout=8, errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
        )
        nss = [l.strip() for l in result.stdout.splitlines() if l.strip() and not l.startswith("NameHost") and "." in l]
        return nss
    except:
        return []


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        print("❌ Kullanım: ns <domain>")
        print("   Örnek:   ns google.com")
        print("            ns datadev.com.tr")
        return

    domain = args[0].lower().strip()
    domain = re.sub(r'^https?://', '', domain).split('/')[0]

    print("=" * 65)
    print(f"🌐 NS Lookup — {domain}")
    print("=" * 65)
    print()

    # 1. Yetkili Name Server'ları bul
    print("📋 Yetkili Name Server'lar sorgulanıyor...")
    ns_servers = get_authoritative_ns(domain)
    ps_ns = whois_ns_lookup(domain)

    all_ns = list(set(ns_servers + ps_ns))

    if all_ns:
        print(f"\n   Yetkili Name Server'lar ({len(all_ns)}):")
        for ns in all_ns:
            print(f"      • {ns}")
    else:
        print("   ⚠️  Name Server bilgisi alınamadı. Yine de DNS kontrolleri yapılıyor...")
    print()

    # 2. dnschecker.org tarzı DNS kontrolü
    print("🔍 Küresel DNS Görünürlük Kontrolü")
    print(f"   ({len(REAL_DNS)} DNS sunucusu taranıyor...)\n")

    results = check_dnschecker_style(domain, all_ns)

    succeeded = [k for k, v in results.items() if v[0] == "✅"]
    failed = [k for k, v in results.items() if v[0] == "❌"]
    timeout = [k for k, v in results.items() if v[0] == "⏱️"]

    # Sonuçları yazdır
    print(f"   {'SUNUCU':<25} {'DURUM':<10} {'ÇÖZÜMLENEN IP'}")
    print(f"   {'-'*60}")
    for name, (status, ips, _) in sorted(results.items(), key=lambda x: (0 if x[1][0] == "✅" else 1 if x[1][0] == "⏱️" else 2)):
        ip_str = ", ".join(ips[:3]) if ips else ""
        if status == "✅":
            print(f"   ✅ {name:<23} ✓ Görünüyor       {ip_str}")
        elif status == "⏱️":
            print(f"   ⏱️  {name:<23} ? Zaman aşımı")
        else:
            print(f"   ❌ {name:<23} ✗ Görünmüyor")

    print()
    print("=" * 65)
    print("📊 RAPOR")
    print("=" * 65)
    print(f"\n   ✅ Görünen DNS:     {len(succeeded)}/{len(results)}")
    print(f"   ❌ Görünmeyen:      {len(failed)}/{len(results)}")
    if timeout:
        print(f"   ⏱️  Zaman aşımı:     {len(timeout)}/{len(results)}")

    if len(succeeded) == len(results):
        print(f"\n   ✅ {domain} tüm küresel DNS sunucularında görünüyor!")
    elif len(failed) == len(results):
        print(f"\n   ❌ {domain} hiçbir DNS sunucusunda görünmüyor!")
        print(f"      Domain kayıtlı olmayabilir veya çok yeni eklenmiş.")
    else:
        print(f"\n   ⚠️  {domain} bazı sunucularda görünmüyor.")
        print(f"      DNS yayılımı (propagation) henüz tamamlanmamış olabilir.")
        print(f"      Yeni bir domain ise 24-48 saat bekleyin.")

    print()
    print("💡 Detaylı kontrol için: https://dnschecker.org")
    print(f"   https://dnschecker.org/#A/{domain}" if domain else "")


if __name__ == "__main__":
    main()
