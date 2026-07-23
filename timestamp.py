import sys, time, datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        now = time.time()
        print(f"Suan: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Unix Timestamp: {int(now)}")
        print(f"Milisaniye:     {int(now * 1000)}")
        return

    val = args[0]

    try:
        val_num = float(val)
        if val_num > 1e12:
            val_num /= 1000
        dt = datetime.datetime.fromtimestamp(val_num)
        print(f"Timestamp: {int(val_num)}")
        print(f"Tarih:     {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"ISO:       {dt.isoformat()}")
    except ValueError:
        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y %H:%M:%S"]:
            try:
                dt = datetime.datetime.strptime(val, fmt)
                ts = int(dt.timestamp())
                print(f"Tarih:     {val}")
                print(f"Timestamp: {ts}")
                return
            except ValueError:
                continue
        print("Cozelemedi. Format: YYYY-MM-DD HH:MM:SS")
        print("  Orn: timestamp 1704067200")
        print("       timestamp 2024-01-01")

if __name__ == "__main__":
    main()
