import sys
import os

# --- WINDOWS CMD EMOJI VE UNICODE ÇÖKME KORUMASI ---
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# --------------------------------------------------

import json
import time
import urllib.request
if sys.platform == "win32":
    import winsound

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ALARM_FILE = os.path.join(BASE_DIR, "alarms.json")

# Bilinen ABD hisse senetleri — .IS eklenmez, direkt Yahoo Finance'de sorgulanır.
# BIST hisseleri için kullanıcı THYAO yazarsa arkada .IS eklenir (aşağıdaki set'te
# olmayan tüm noktasız hisse sembolleri BIST kabul edilir).
KNOWN_US_STOCKS = {
    "AAPL", "TSLA", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "NFLX",
    "AMD", "INTC", "DIS", "KO", "PEP", "JPM", "BAC", "V", "MA",
    "WMT", "PG", "JNJ", "UNH", "HD", "CRM", "IBM", "CSCO",
    "AVGO", "NVO", "ASML", "UBER", "PYPL", "ADBE", "ORCL",
    "QCOM", "TXN", "SNAP", "SQ", "SHOP", "ROKU", "GME", "AMC",
    "PLTR", "SNOW", "DDOG", "ZM", "CRWD", "SIRI", "F", "GM",
    "BA", "CAT", "GE", "XOM", "CVX", "MCD", "NKE", "SBUX",
    "ABNB", "COIN", "MSTR", "HOOD", "RDDT", "ARM", "DASH",
    "BKNG", "UBER", "LYFT", "DKNG", "PENN", "CCL", "AAL",
    "LMT", "RTX", "WBD", "WBA", "T", "VZ", "TMUS", "C", "GS",
    "MS", "AXP", "BLK", "SCHW", "SPGI", "MCO", "FI", "BX",
    "AMAT", "MU", "KLAC", "LRCX", "NXPI", "STM",
    "PANW", "FTNT", "ZS", "NET", "OKTA", "CFLT", "DDOG",
}

# --- YARDIMCI FONKSIYONLAR ---

def load_alarms():
    """alarms.json'dan alarm listesini oku. type alanı yoksa coin kabul et (geriye uyum)."""
    if not os.path.exists(ALARM_FILE):
        return []
    try:
        with open(ALARM_FILE, "r", encoding="utf-8") as f:
            alarms = json.load(f)
        # Geriye uyumluluk: type alanı olmayan eski kayıtları coin kabul et
        for alarm in alarms:
            if "type" not in alarm:
                alarm["type"] = "coin"
        return alarms
    except Exception:
        return []


def save_alarms(alarms):
    """Alarm listesini JSON'a kaydet."""
    with open(ALARM_FILE, "w", encoding="utf-8") as f:
        json.dump(alarms, f, indent=4, ensure_ascii=False)


def normalise_hisse_symbol(symbol):
    """
    Hisse senedi sembolünü normalize et.
    - Bilinen ABD hissesi ise olduğu gibi bırak.
    - BIST için .IS ekle (kullanıcı THYAO yazdıysa -> THYAO.IS).
    - Zaten .IS varsa dokunma.
    """
    sym = symbol.upper().strip()
    if "." in sym:
        # Kullanıcı zaten .IS veya başka bir sonek belirtmiş
        return sym
    if sym in KNOWN_US_STOCKS:
        return sym
    # BIST varsay: .IS ekle
    return sym + ".IS"


def get_binance_price(symbol):
    """Binance API'den anlık kripto fiyatı çek."""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode())
            return float(data["price"])
    except Exception:
        return None


def get_hisse_price(symbol):
    """
    yfinance ile hisse senedi güncel fiyatını çek.
    BIST için .IS eklenmiş sembol, ABD için direkt sembol kullanılır.
    """
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        # fast_info en hızlı yöntem — bazen çalışmayabilir
        try:
            price = ticker.fast_info.get("last_price", None)
            if price is not None:
                return float(price)
        except Exception:
            pass
        # Fallback: son 2 günlük kapanış fiyatı
        df = ticker.history(period="2d")
        if not df.empty:
            return float(df["Close"].iloc[-1])
        return None
    except Exception:
        return None


def play_alarm_sound():
    """Alarm sesi: yumusak ve net."""
    if sys.platform == "win32":
        for f, d in [(1200, 200), (1000, 200), (1200, 200)]:
            winsound.Beep(f, d)
            time.sleep(0.08)
        time.sleep(0.15)
        for f, d in [(1400, 300), (1200, 300)]:
            winsound.Beep(f, d)
            time.sleep(0.08)
    else:
        for _ in range(3):
            sys.stdout.write('\a')
            sys.stdout.flush()
            time.sleep(0.2)


# --- KOMUT YÖNETİCİLERİ ---

def cmd_ekle(args):
    """alarm ekle coin/hisse <sembol> <koşul>"""
    if len(args) < 4:
        print("❌ Eksik argüman! Kullanım:")
        print('  alarm ekle coin  btcusdt ">63000"          # Kripto (Binance)')
        print('  alarm ekle hisse thyao  ">310"             # BIST hissesi')
        print('  alarm ekle hisse aapl   "<170"             # ABD hissesi')
        print('  alarm ekle hisse THYAO.IS ">310"           # Açık BIST (.IS ile)')
        print('')
        print('⚠️  CMD\'de > ve < işaretlerini tırnak içinde yazın: alarm ekle coin btcusdt ">63000"')
        return

    alarm_type = args[1].lower()
    if alarm_type not in ("coin", "hisse"):
        print("❌ Geçersiz tür! 'coin' veya 'hisse' kullanın.")
        return

    raw_symbol = args[2]
    condition_str = " ".join(args[3:]).strip()

    # Operatörü belirle
    operator = ""
    if condition_str.startswith(">"):
        operator = ">"
    elif condition_str.startswith("<"):
        operator = "<"

    if not operator:
        print("❌ Geçersiz koşul! Başlangıç '>' veya '<' olmalı.")
        print('   Örnek: alarm ekle coin btcusdt ">63000"')
        return

    try:
        target_price = float(condition_str.replace(operator, ""))
    except ValueError:
        print("❌ Geçersiz fiyat formatı!")
        return

    # Sembolü normalize et
    if alarm_type == "coin":
        symbol = raw_symbol.upper()
    else:
        symbol = normalise_hisse_symbol(raw_symbol)

    alarms = load_alarms()
    alarms.append({
        "symbol": symbol,
        "type": alarm_type,
        "operator": operator,
        "target": target_price
    })
    save_alarms(alarms)

    tur_etiket = "🪙" if alarm_type == "coin" else "📈"
    print(f"{tur_etiket} Alarm kuruldu: {symbol} {operator} {target_price} ({alarm_type.upper()})")


def cmd_liste():
    """alarm liste — tüm alarmları göster."""
    alarms = load_alarms()
    if not alarms:
        print("📭 Kurulu alarm bulunmuyor.")
        return
    print("📋 Mevcut Alarmlar:")
    for idx, alarm in enumerate(alarms, 1):
        tur_etiket = "🪙" if alarm["type"] == "coin" else "📈"
        print(f"  #{idx} {tur_etiket} {alarm['symbol']} {alarm['operator']} {alarm['target']}  ({alarm['type'].upper()})")


def cmd_sil(args):
    """alarm sil <no>"""
    if len(args) < 2:
        print("❌ Alarm numarası girin! Örn: alarm sil 1")
        return
    try:
        target_idx = int(args[1]) - 1
    except ValueError:
        print("❌ Geçersiz numara formatı!")
        return

    alarms = load_alarms()
    if target_idx < 0 or target_idx >= len(alarms):
        print("❌ Geçersiz numara! Mevcut alarm sayısı:", len(alarms))
        return
    removed = alarms.pop(target_idx)
    save_alarms(alarms)
    tur_etiket = "🪙" if removed["type"] == "coin" else "📈"
    print(f"🗑️ Alarm silindi: {tur_etiket} {removed['symbol']} {removed['operator']} {removed['target']}")


def cmd_izle():
    """alarm izle — tüm alarmları sürekli takip et."""
    print("🔍 Canlı alarm takibi başlatıldı... Durdurmak için Ctrl+C yapabilirsin.\n")

    while True:
        alarms = load_alarms()
        if not alarms:
            print("📭 Takip edilecek aktif alarm kalmadı. Çıkılıyor...")
            break

        updated_alarms = []
        triggered_any = False

        for alarm in alarms:
            symbol = alarm["symbol"]
            operator = alarm["operator"]
            target = alarm["target"]
            alarm_type = alarm["type"]

            if alarm_type == "coin":
                current_price = get_binance_price(symbol)
            else:
                current_price = get_hisse_price(symbol)

            if current_price is None:
                # Veri çekilemedi — alarmı koru, döngüye devam et
                tur_etiket = "🪙" if alarm_type == "coin" else "📈"
                print(f"  ⏳ {tur_etiket} {symbol} — veri alınamadı, tekrar denenecek...")
                updated_alarms.append(alarm)
                continue

            triggered = False
            if operator == ">" and current_price >= target:
                triggered = True
            elif operator == "<" and current_price <= target:
                triggered = True

            if triggered:
                triggered_any = True
                tur_etiket = "🪙" if alarm_type == "coin" else "📈"
                print(f"  🚨🚨 ALARM TETİKLENDI! {tur_etiket} {symbol} şu an: {current_price} (Hedef: {operator}{target})")
                play_alarm_sound()
                # Tetiklenen alarm JSON'dan silinir (updated_alarms'a eklenmez)
            else:
                updated_alarms.append(alarm)

        if triggered_any:
            save_alarms(updated_alarms)
            print("")

        time.sleep(3)


# --- ANA GİRİŞ ---

def main():
    args = sys.argv[1:]

    if not args:
        print("💡 Kullanım:")
        print('  alarm ekle  coin  btcusdt ">63000"        # Kripto alarmı')
        print('  alarm ekle  hisse thyao   ">310"          # BIST/ABD hisse alarmı')
        print("  alarm liste                                 # Alarmları listele")
        print("  alarm sil <no>                              # Alarm sil")
        print("  alarm izle                                  # Alarmları canlı izle")
        print("")
        print("📌 Örnekler:")
        print('  alarm ekle coin  btcusdt    ">63000"')
        print('  alarm ekle coin  ethusdt    "<2500"')
        print('  alarm ekle hisse thyoa      ">310"   (BIST -> THYAO.IS)')
        print('  alarm ekle hisse aapl       "<170"   (ABD -> AAPL)')
        print('  alarm ekle hisse THYAO.IS   ">310"   (Açık BIST)')
        print("  alarm liste")
        print("  alarm sil 2")
        print("  alarm izle")
        return

    command = args[0].lower()

    if command == "ekle":
        cmd_ekle(args)
    elif command == "liste":
        cmd_liste()
    elif command == "sil":
        cmd_sil(args)
    elif command == "izle":
        cmd_izle()
    else:
        print(f"❌ Bilinmeyen komut: {command}")
        print("Kullanılabilir komutlar: ekle, liste, sil, izle")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Canlı takip kapatıldı.")
