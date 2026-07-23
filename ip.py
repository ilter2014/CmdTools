import sys
import socket
import urllib.request
import ssl
import json
import subprocess
import re

# Ici kutuphane uyarilarini sessize al
import warnings
warnings.filterwarnings("ignore")

# Windows SSL kilitlemelerini onleyen SSL context
ssl_context = ssl._create_unverified_context()


def get_public_ipv4():
    """Herkese acik IPv4 adresini whatismyip ve yedek servislerden alir."""
    services = [
        "https://api.ipify.org",
        "https://ipv4.icanhazip.com",
        "https://checkip.amazonaws.com",
        "https://ifconfig.me/ip",
    ]
    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5, context=ssl_context) as resp:
                ip = resp.read().decode("utf-8").strip()
                if ip and re.match(r"^\d+\.\d+\.\d+\.\d+$", ip):
                    return ip
        except Exception:
            continue
    return None


def get_public_ipv6():
    """Herkese acik IPv6 adresini dener."""
    services = [
        "https://api6.ipify.org",
        "https://ipv6.icanhazip.com",
        "https://ifconfig.me/ip",
    ]
    for url in services:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5, context=ssl_context) as resp:
                ip = resp.read().decode("utf-8").strip()
                # IPv6 kontrolu (iki nokta iceriyorsa)
                if ip and ":" in ip:
                    return ip
        except Exception:
            continue
    return None


def get_hostname():
    """Bilgisayar adini ve tam domain adini dondurur."""
    try:
        hostname = socket.gethostname()
        fqdn = socket.getfqdn()
        return hostname, fqdn
    except Exception:
        return None, None


def get_local_ips():
    """Yerel agdaki tum IPv4 ve IPv6 adreslerini bulur (127.0.0.1 ve loopback haric)."""
    ipv4_list = []
    ipv6_list = []
    interface_info = []

    # Yontem 1: socket ile ag arayuzlerini tara
    try:
        hostname = socket.gethostname()
        for addr_info in socket.getaddrinfo(hostname, None):
            addr = addr_info[4][0]
            if addr.startswith("127.") or addr == "::1":
                continue
            if ":" in addr:
                # IPv6
                # % ile gelen scope ID'yi temizle
                clean = addr.split("%")[0]
                if clean not in ipv6_list:
                    ipv6_list.append(clean)
            else:
                if addr not in ipv4_list:
                    ipv4_list.append(addr)
    except Exception:
        pass

    # Yontem 2: netifaces kutuphanesi (daha detayli)
    try:
        import netifaces
        if_ips_v4 = []
        if_ips_v6 = []
        for iface in netifaces.interfaces():
            addrs = netifaces.ifaddresses(iface)
            # IPv4
            if netifaces.AF_INET in addrs:
                for a in addrs[netifaces.AF_INET]:
                    ip = a.get("addr", "")
                    netmask = a.get("netmask", "")
                    if ip and not ip.startswith("127."):
                        entry = ip
                        if netmask:
                            entry += f" (mask: {netmask})"
                        if_ip = {"ip": ip, "netmask": netmask, "interface": iface}
                        if_ips_v4.append(if_ip)
            # IPv6
            if netifaces.AF_INET6 in addrs:
                for a in addrs[netifaces.AF_INET6]:
                    ip = a.get("addr", "")
                    if ip and ip != "::1":
                        # scope ID'yi temizle
                        clean_ip = ip.split("%")[0]
                        if_ip6 = {"ip": clean_ip, "interface": iface}
                        if_ips_v6.append(if_ip6)

        # netifaces'ten gelenlerle listeleri guncelle
        for entry in if_ips_v4:
            if entry["ip"] not in ipv4_list:
                ipv4_list.append(entry["ip"])
            interface_info.append(entry)

        for entry in if_ips_v6:
            if entry["ip"] not in [i.split("%")[0] for i in ipv6_list]:
                ipv6_list.append(entry["ip"])
    except ImportError:
        pass

    # Yontem 3: Windows ipconfig (netifaces yoksa)
    if sys.platform == "win32" and not interface_info:
        try:
            output = subprocess.check_output(
                "ipconfig", shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")

            current_iface = None
            for line in output.splitlines():
                line = line.strip()
                # Arayuz adini bul
                if line.endswith(":") and not line.startswith(" ") and not line.startswith("\t"):
                    current_iface = line.rstrip(":").strip("adapter ").strip()

                # IPv4
                ipv4_match = re.search(r"IPv4.*:\s+([\d.]+)", line)
                if ipv4_match:
                    ip = ipv4_match.group(1)
                    if ip not in ipv4_list:
                        ipv4_list.append(ip)

                # IPv6
                ipv6_match = re.search(r"IPv6.*:\s+([\da-f:]+(?:\%\d+)?)", line, re.IGNORECASE)
                if ipv6_match:
                    ip = ipv6_match.group(1).split("%")[0].strip()
                    if ip not in ipv6_list:
                        ipv6_list.append(ip)
        except Exception:
            pass

    # Yontem 3b: Linux ip komutu
    if sys.platform == "linux" and not interface_info:
        try:
            output = subprocess.check_output(
                ["ip", "-4", "addr", "show"], timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            current_iface = None
            for line in output.splitlines():
                iface_match = re.match(r'^\d+:\s+(\S+?):', line)
                if iface_match:
                    current_iface = iface_match.group(1)
                    continue
                ip_match = re.search(r'inet\s+([\d.]+)/\d+', line)
                if ip_match:
                    ip = ip_match.group(1)
                    if ip not in ipv4_list and ip != "127.0.0.1":
                        ipv4_list.append(ip)
                    if current_iface:
                        interface_info.append({"ip": ip, "netmask": "", "interface": current_iface})
        except Exception:
            pass
        try:
            output = subprocess.check_output(
                ["ip", "-6", "addr", "show"], timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            for line in output.splitlines():
                ip_match = re.search(r'inet6\s+([\da-f:]+)/\d+', line)
                if ip_match:
                    ip = ip_match.group(1).split("%")[0]
                    if ip not in ipv6_list and ip != "::1":
                        ipv6_list.append(ip)
        except Exception:
            pass

    return ipv4_list, ipv6_list


def get_default_gateway():
    """Varsayilan ag geçidini (gateway) bulur."""
    try:
        import netifaces
        gws = netifaces.gateways()
        if "default" in gws and netifaces.AF_INET in gws["default"]:
            return gws["default"][netifaces.AF_INET][0]
    except ImportError:
        if sys.platform == "win32":
            try:
                output = subprocess.check_output(
                    "ipconfig", shell=True, timeout=5, stderr=subprocess.DEVNULL
                ).decode("utf-8", errors="replace")
                match = re.search(r"Varsay\305\261lan A\351 Ge\347idi.*:\s+([\d.]+)", output)
                if match:
                    return match.group(1)
                match = re.search(r"Default Gateway.*:\s+([\d.]+)", output)
                if match:
                    return match.group(1)
            except Exception:
                pass
        elif sys.platform == "linux":
            try:
                output = subprocess.check_output(
                    ["ip", "route", "show", "default"], timeout=5, stderr=subprocess.DEVNULL
                ).decode("utf-8", errors="replace").strip()
                m = re.search(r'default\s+via\s+([\d.]+)', output)
                if m:
                    return m.group(1)
            except Exception:
                pass
    return None


def get_dns_servers():
    """DNS sunucularini bulur."""
    dns_list = []
    try:
        import netifaces
        import dns.resolver
        resolvers = dns.resolver.Resolver()
        for ns in resolvers.nameservers:
            dns_list.append(ns)
        return dns_list
    except ImportError:
        pass

    if sys.platform == "win32":
        try:
            output = subprocess.check_output(
                "ipconfig /all", shell=True, timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            for match in re.finditer(r"DNS\s+Sunucular?.*:\s+([\d.]+)", output):
                ip = match.group(1).strip()
                if ip not in dns_list:
                    dns_list.append(ip)
            for match in re.finditer(r"DNS Servers?.*:\s+([\d.]+)", output):
                ip = match.group(1).strip()
                if ip not in dns_list:
                    dns_list.append(ip)
        except Exception:
            pass

    if sys.platform == "linux":
        try:
            with open("/etc/resolv.conf", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("nameserver"):
                        parts = line.split()
                        if len(parts) >= 2:
                            ip = parts[1]
                            if ip not in dns_list:
                                dns_list.append(ip)
        except Exception:
            pass

    return dns_list if dns_list else None


def format_output(data):
    """Veriyi okunabilir formatta yazdirir."""
    lines = []
    lines.append("=" * 60)
    lines.append("  [ IP ve AG BILGILERI ]")
    lines.append("=" * 60)

    # Bilgisayar adi
    hostname, fqdn = data.get("hostname"), data.get("fqdn")
    if hostname:
        lines.append("")
        lines.append("  +- BILGISAYAR")
        lines.append(f"  | Ad          : {hostname}")
        if fqdn and fqdn != hostname:
            lines.append(f"  | Tam Ad      : {fqdn}")

    # Herkese acik IP
    lines.append("")
    lines.append("  +- HERKESE ACIK IP")
    pub_ipv4 = data.get("public_ipv4")
    pub_ipv6 = data.get("public_ipv6")

    if pub_ipv4:
        lines.append(f"  | IPv4        : {pub_ipv4}")
    else:
        lines.append(f"  | IPv4        : — (baglanti yok / zaman asimi)")

    if pub_ipv6:
        lines.append(f"  | IPv6        : {pub_ipv6}")

    # Yerel IP'ler
    local_ipv4 = data.get("local_ipv4", [])
    local_ipv6 = data.get("local_ipv6", [])

    if local_ipv4:
        lines.append("")
        lines.append("  +- YEREL AG (IPv4)")
        for ip in local_ipv4:
            lines.append(f"  | {ip}")
    else:
        lines.append("")
        lines.append("  +- YEREL AG (IPv4)")
        lines.append("  | — (bulunamadi)")

    if local_ipv6:
        lines.append("")
        lines.append("  +- YEREL AG (IPv6)")
        for ip in local_ipv6:
            lines.append(f"  | {ip}")

    # Varsayilan ag geçidi
    gateway = data.get("gateway")
    if gateway:
        lines.append("")
        lines.append("  +- AG GEÇIDI")
        lines.append(f"  | Gateway     : {gateway}")

    # DNS sunuculari
    dns = data.get("dns")
    if dns:
        lines.append("")
        lines.append("  +- DNS SUNUCULARI")
        for i, ns in enumerate(dns, 1):
            lines.append(f"  | {i}. {ns}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    # stdout UTF-8 olsun
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    json_mode = "--json" in sys.argv

    hostname, fqdn = get_hostname()

    data = {
        "hostname": hostname,
        "fqdn": fqdn,
        "public_ipv4": get_public_ipv4(),
        "public_ipv6": get_public_ipv6(),
        "local_ipv4": [],
        "local_ipv6": [],
        "gateway": get_default_gateway(),
        "dns": get_dns_servers(),
    }

    local_ipv4, local_ipv6 = get_local_ips()
    data["local_ipv4"] = local_ipv4
    data["local_ipv6"] = local_ipv6

    if json_mode:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_output(data))


if __name__ == "__main__":
    main()
