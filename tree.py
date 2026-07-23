import sys, os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def format_size(size):
    if size < 1024: return f"{size} B"
    if size < 1024**2: return f"{size/1024:.1f} KB"
    return f"{size/1024**2:.1f} MB"

def walk_dir(path, prefix="", max_depth=5, current_depth=0, show_size=True, max_items=50):
    """Klasor yapisini agac seklinde goster."""
    if current_depth > max_depth:
        return 0

    try:
        items = sorted(os.listdir(path))
    except (PermissionError, OSError):
        return 0

    # Klasorleri ve dosyalari ayir
    dirs = []
    files = []
    for item in items:
        full = os.path.join(path, item)
        if os.path.isdir(full):
            dirs.append(item)
        elif os.path.isfile(full):
            files.append(item)

    all_items = dirs + files
    count = 0

    for i, item in enumerate(all_items):
        if count >= max_items:
            # Kalan sayisini goster
            remaining = len(all_items) - count
            if remaining > 0:
                print(f"{prefix}{'   ' if i == 0 else ''}[... {remaining} oge daha]")
            break

        is_last = (i == len(all_items) - 1)
        connector = "+-- " if is_last else "|-- "
        full_path = os.path.join(path, item)

        if os.path.isdir(full_path):
            size_info = ""
            if show_size:
                try:
                    total = 0
                    for root, dirs, files in os.walk(full_path):
                        for f in files:
                            try: total += os.path.getsize(os.path.join(root, f))
                            except: pass
                    size_info = f" ({format_size(total)})"
                except: pass
            print(f"{prefix}{connector}{item}/{size_info}")
            sub_prefix = prefix + ("    " if is_last else "|   ")
            count += walk_dir(full_path, sub_prefix, max_depth, current_depth+1, show_size, max_items)
        else:
            size_info = ""
            if show_size:
                try:
                    fsize = os.path.getsize(full_path)
                    size_info = f" ({format_size(fsize)})"
                except: pass
            print(f"{prefix}{connector}{item}{size_info}")
            count += 1

    return count

def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    path = "."
    max_depth = 3
    show_size = True
    max_items = 30

    i = 0
    while i < len(args):
        if args[i] == "--depth" and i+1 < len(args):
            max_depth = int(args[i+1])
            i += 2
        elif args[i] == "--no-size":
            show_size = False
            i += 1
        elif args[i] == "--max" and i+1 < len(args):
            max_items = int(args[i+1])
            i += 2
        elif not args[i].startswith("-"):
            path = args[i]
            i += 1
        else:
            i += 1

    if not os.path.exists(path):
        print(f"Klasor bulunamadi: {path}")
        return

    abs_path = os.path.abspath(path)
    print(abs_path)
    total = walk_dir(path, "", max_depth, 0, show_size, max_items)
    print(f"\nToplam: {total} oge")

if __name__ == "__main__":
    main()
