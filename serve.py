import sys, os, http.server, socketserver, socket, threading

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    port = 8000
    bind_all = False

    for a in args:
        if a == "--all" or a == "-a":
            bind_all = True
        elif a.isdigit():
            port = int(a)

    if port < 1 or port > 65535:
        print("Port 1-65535 arasinda olmali.")
        return
    if port < 1024:
        print(f"Uyari: {port} portu icin admin yetkisi gerekebilir.")

    cwd = os.getcwd()
    host = "0.0.0.0" if bind_all else "127.0.0.1"
    local_ip = get_local_ip()

    handler = http.server.SimpleHTTPRequestHandler

    print(f"Sunucu baslatildi!")
    print(f"  Klasor: {cwd}")
    print(f"  Yerel:  http://localhost:{port}")
    if bind_all:
        print(f"  Ag:     http://{local_ip}:{port}")
    print()
    print(f"Durdurmak icin Ctrl+C")
    print()

    try:
        with socketserver.TCPServer((host, port), handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        print(f"Port {port} kullaniliyor: {e}")
        print(f"Farkli bir port deneyin: serve 8080")
    except KeyboardInterrupt:
        print(" Sunucu durduruldu.")

if __name__ == "__main__":
    main()
