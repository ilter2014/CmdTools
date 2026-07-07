import subprocess, re, sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run(cmd, timeout=10):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
        return r.stdout or ""
    except: return ""

def parse_ipconfig_blocks(text):
    """ipconfig /all çıktısını adaptör bloklarına ayır."""
    blocks = []
    current = []
    for line in text.splitlines():
        if re.match(r'^(Ethernet|Wireless LAN|Bluetooth|Unknown)', line) and current:
            blocks.append("\n".join(current))
            current = [line]
        else:
            current.append(line)
    if current: blocks.append("\n".join(current))
    return blocks

def get_bt_status():
    """Bluetooth durumunu PowerShell ile al."""
    out = run(["powershell", "-Command",
        "Get-PnpDevice | Where-Object {$_.Class -eq 'Bluetooth'} | "
        "Select-Object FriendlyName, Status | ConvertTo-Csv -NoTypeInformation"],
        timeout=8)
    devices = []
    for line in out.splitlines():
        if "," not in line or "FriendlyName" in line: continue
        parts = line.strip('"').split('","')
        if len(parts) >= 2:
            name = parts[0].strip('"')
            status = "Açık" if parts[1].strip('"') == "OK" else "Kapalı"
            devices.append((name, status))
    return devices

def get_bt_mac():
    """Bluetooth MAC'ini getmac'den al."""
    out = run(["getmac"], timeout=5)
    macs = []
    for line in out.splitlines():
        m = re.match(r'([\da-fA-F-]{17})\s+(.+)', line)
        if m:
            mac, conn = m.group(1).upper(), m.group(2).strip()
            if "bluetooth" in conn.lower() and "N/A" not in conn and "N/A" not in mac:
                macs.append((mac, conn.strip('"')))
    return macs

def main():
    print("🔍 Ağ ve Bluetooth MAC Adresleri taranıyor...\n")

    ipconfig = run(["ipconfig", "/all"], timeout=10)
    bt_devices = get_bt_status()
    bt_macs = get_bt_mac()
    getmac_all = run(["getmac"], timeout=5)

    any_active = False

    # Bluetooth
    if bt_devices:
        print("📶 Bluetooth:")
        for name, status in bt_devices:
            icon = "🟢" if status == "Açık" else "🔴"
            print(f"   {icon} {name}: {status}")
            if status == "Açık": any_active = True
        print()

    # Ağ bağdaştırıcıları
    print("🌐 Ağ Bağdaştırıcıları:")
    blocks = parse_ipconfig_blocks(ipconfig)
    adapter_count = 0

    for block in blocks:
        # Adaptör adı
        nm = re.search(r'^(Ethernet|Wireless LAN|Bluetooth|Unknown) adapter (.+?):', block, re.MULTILINE)
        if not nm: continue
        atype = nm.group(1)
        aname = nm.group(2).strip()
        adapter_count += 1

        # MAC
        mm = re.search(r'(?:Physical Address|Fiziksel Adres)[.\s]*:[\s]*([\da-fA-F-]{17})', block)
        mac = mm.group(1).upper() if mm else "—"
        if mac == "—": continue  # MAC yoksa geç

        # Durum
        status = "Açık"
        med = re.search(r'(?:Media State|Medya Durumu)[.\s]*:[\s]*(.+)', block)
        if med:
            ms = med.group(1).strip().lower()
            if "disconnected" in ms or "bağlantı" in ms or "media disconnected" in ms:
                status = "Kapalı"

        icon = "🟢" if status == "Açık" else "🔴"
        ticon = "🔌" if "Ethernet" in atype else "📶" if "Wireless" in atype else "🦷"
        label = atype.replace("Wireless LAN", "WiFi").replace("adapter", "").strip()

        if status == "Açık":
            any_active = True
            print(f"   {icon} {ticon} {aname} ({label})")
            print(f"      Durum: {status}")
            print(f"      MAC:   {mac}")
        else:
            print(f"   {icon} {ticon} {aname} ({label})")
            print(f"      Durum: {status}")
        print()

    # getmac'ten ekstra BT MAC
    if bt_macs:
        print("🦷 Bluetooth MAC Adresleri:")
        for mac, conn in bt_macs:
            print(f"   • {mac}  ({conn})")
        print()

    if not any_active:
        print("   ❌ Açık ağ bağlantısı veya Bluetooth bulunamadı.")
        print("   💡 MAC adresi aranabilecek aktif bir ağ veya Bluetooth bağlantısı yok.")
        print("   Kablolu/kablosuz bir ağa bağlanın veya Bluetooth'u açın.\n")
        return

    print(f"📊 Özet: {adapter_count} bağdaştırıcı tarandı.")
    print("💡 İpucu: Bluetooth gözükmüyorsa sürücü yüklü olmayabilir.")

if __name__ == "__main__":
    main()
