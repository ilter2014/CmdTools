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
    """Bluetooth durumunu hciconfig ile al."""
    if sys.platform != "linux":
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
                status = "Acik" if parts[1].strip('"') == "OK" else "Kapali"
                devices.append((name, status))
        return devices
    else:
        devices = []
        try:
            out = subprocess.check_output(
                ["hciconfig"], timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            for block in out.split("hci"):
                block = block.strip()
                if not block:
                    continue
                dev_match = re.match(r'(\d+)', block)
                name = f"hci{dev_match.group(1)}" if dev_match else "Bluetooth"
                if "UP RUNNING" in block:
                    devices.append((name, "Acik"))
                else:
                    devices.append((name, "Kapali"))
        except Exception:
            pass
        return devices

def get_bt_mac():
    """Bluetooth MAC adresini al."""
    if sys.platform != "linux":
        out = run(["getmac"], timeout=5)
        macs = []
        for line in out.splitlines():
            m = re.match(r'([\da-fA-F-]{17})\s+(.+)', line)
            if m:
                mac, conn = m.group(1).upper(), m.group(2).strip()
                if "bluetooth" in conn.lower() and "N/A" not in conn and "N/A" not in mac:
                    macs.append((mac, conn.strip('"')))
        return macs
    else:
        macs = []
        try:
            out = subprocess.check_output(
                ["hciconfig"], timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            for block in out.split("hci"):
                block = block.strip()
                if not block:
                    continue
                dev_match = re.match(r'(\d+)', block)
                name = f"hci{dev_match.group(1)}" if dev_match else "Bluetooth"
                mac_match = re.search(r'BD Address:\s+([\da-fA-F:]{17})', block)
                if mac_match:
                    mac = mac_match.group(1).upper()
                    macs.append((mac, name))
        except Exception:
            pass
        return macs

def main():
    print("🔍 Ag ve Bluetooth MAC Adresleri taranıyor...\n")

    bt_devices = get_bt_status()
    bt_macs = get_bt_mac()

    any_active = False

    # Bluetooth
    if bt_devices:
        print("Bluetooth:")
        for name, status in bt_devices:
            icon = "+" if status == "Acik" else "-"
            print(f"   {icon} {name}: {status}")
            if status == "Acik": any_active = True
        print()

    # Ag baglanticilari
    print("Ag Baglanticilari:")
    adapter_count = 0

    if sys.platform == "linux":
        # Linux: ip -o link show
        try:
            output = subprocess.check_output(
                ["ip", "-o", "link", "show"], timeout=5, stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            for line in output.splitlines():
                # Format: "2: eth0: <BROADCAST,...> ..."
                m = re.match(r'^(\d+):\s+(\S+?):', line)
                if not m:
                    continue
                iface = m.group(2)
                if iface == "lo":
                    continue
                adapter_count += 1

                # Check if UP
                up = "UP" in line or "state UP" in line

                # Get MAC from ip link
                mac = "N/A"
                try:
                    link_out = subprocess.check_output(
                        ["ip", "link", "show", iface], timeout=5, stderr=subprocess.DEVNULL
                    ).decode("utf-8", errors="replace")
                    mac_match = re.search(r'link/ether\s+([\da-fA-F:]{17})', link_out)
                    if mac_match:
                        mac = mac_match.group(1).upper()
                except Exception:
                    pass

                # Get IP
                ip_addr = "N/A"
                try:
                    ip_out = subprocess.check_output(
                        ["ip", "-4", "addr", "show", iface], timeout=5, stderr=subprocess.DEVNULL
                    ).decode("utf-8", errors="replace")
                    ip_match = re.search(r'inet\s+([\d.]+)/\d+', ip_out)
                    if ip_match:
                        ip_addr = ip_match.group(1)
                except Exception:
                    pass

                icon = "+" if up else "-"
                if up:
                    any_active = True
                print(f"   {icon} {iface}")
                print(f"      Durum: {'Acik' if up else 'Kapali'}")
                print(f"      MAC:   {mac}")
                print(f"      IP:    {ip_addr}")
                print()
        except Exception:
            pass
    else:
        # Windows: ipconfig
        ipconfig = run(["ipconfig", "/all"], timeout=10)
        blocks = parse_ipconfig_blocks(ipconfig)

        for block in blocks:
            nm = re.search(r'^(Ethernet|Wireless LAN|Bluetooth|Unknown) adapter (.+?):', block, re.MULTILINE)
            if not nm: continue
            atype = nm.group(1)
            aname = nm.group(2).strip()
            adapter_count += 1

            mm = re.search(r'(?:Physical Address|Fiziksel Adres)[.\s]*:[\s]*([\da-fA-F-]{17})', block)
            mac = mm.group(1).upper() if mm else "N/A"
            if mac == "N/A": continue

            status = "Acik"
            med = re.search(r'(?:Media State|Medya Durumu)[.\s]*:[\s]*(.+)', block)
            if med:
                ms = med.group(1).strip().lower()
                if "disconnected" in ms or "baglanti" in ms or "media disconnected" in ms:
                    status = "Kapali"

            icon = "+" if status == "Acik" else "-"
            label = atype.replace("Wireless LAN", "WiFi").replace("adapter", "").strip()

            if status == "Acik":
                any_active = True
            print(f"   {icon} {aname} ({label})")
            print(f"      Durum: {status}")
            print(f"      MAC:   {mac}")
            print()

    # getmac / hciconfig ekstra BT MAC
    if bt_macs:
        print("Bluetooth MAC Adresleri:")
        for mac, conn in bt_macs:
            print(f"   * {mac}  ({conn})")
        print()

    if not any_active:
        print("   - Acik ag baglantisi veya Bluetooth bulunamadi.")
        print("   * MAC adresi aranabilecek aktif bir ag veya Bluetooth baglantisi yok.")
        print("   Kablolu/kablosuz bir aga baglanin veya Bluetooth'u acin.\n")
        return

    print(f"Ozet: {adapter_count} bagdastrici tarandi.")

if __name__ == "__main__":
    main()
