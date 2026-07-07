# -*- coding: utf-8 -*-
"""
analiz.py — Merkezi Teknik Analiz Modülü
Kullanım: analiz <sembol> [periyot]
  Örn:  analiz btcusdt
        analiz thyao
        analiz aapl 4h
        analiz eth 1d
"""

import sys
import os

# --- WINDOWS CMD EMOJI VE UNICODE ÇÖKME KORUMASI ---
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# --------------------------------------------------

import json
import math
import urllib.request
import warnings
warnings.filterwarnings("ignore")

# =====================================================================
# 1. SABITLER VE YARDIMCILAR
# =====================================================================

KNOWN_US_STOCKS = {
    "AAPL", "TSLA", "MSFT", "GOOGL", "GOOG", "AMZN", "NVDA", "META", "NFLX",
    "AMD", "INTC", "DIS", "KO", "PEP", "JPM", "BAC", "V", "MA",
    "WMT", "PG", "JNJ", "UNH", "HD", "CRM", "IBM", "CSCO",
    "AVGO", "NVO", "ASML", "UBER", "PYPL", "ADBE", "ORCL",
    "QCOM", "TXN", "SNAP", "SQ", "SHOP", "ROKU", "GME", "AMC",
    "PLTR", "SNOW", "DDOG", "ZM", "CRWD", "SIRI", "F", "GM",
    "BA", "CAT", "GE", "XOM", "CVX", "MCD", "NKE", "SBUX",
    "ABNB", "COIN", "MSTR", "HOOD", "RDDT", "ARM", "DASH",
    "BKNG", "LYFT", "DKNG", "PENN", "CCL", "AAL",
    "LMT", "RTX", "WBD", "WBA", "T", "VZ", "TMUS", "C", "GS",
    "MS", "AXP", "BLK", "SCHW", "SPGI", "MCO", "FI", "BX",
    "AMAT", "MU", "KLAC", "LRCX", "NXPI", "STM",
    "PANW", "FTNT", "ZS", "NET", "OKTA", "CFLT",
}

SHORT_CRYPTO_MAP = {
    "btc": "BTCUSDT", "eth": "ETHUSDT", "sol": "SOLUSDT",
    "xrp": "XRPUSDT", "ada": "ADAUSDT", "doge": "DOGEUSDT",
    "dot": "DOTUSDT", "matic": "POLUSDT", "avax": "AVAXUSDT",
    "link": "LINKUSDT", "uni": "UNIUSDT", "atom": "ATOMUSDT",
    "ltc": "LTCUSDT", "bch": "BCHUSDT",
    "near": "NEARUSDT", "apt": "APTUSDT", "sui": "SUIUSDT",
    "arb": "ARBUSDT", "op": "OPUSDT", "inj": "INJUSDT",
    "fil": "FILUSDT", "ftm": "FTMUSDT", "algo": "ALGOUSDT",
    "rune": "RUNEUSDT", "pendle": "PENDLEUSDT", "ondo": "ONDOUSDT",
    "strk": "STRKUSDT", "tia": "TIAUSDT", "sei": "SEIUSDT",
    "1000pepe": "1000PEPEUSDT", "1000shib": "1000SHIBUSDT",
    "egld": "EGLDUSDT", "imx": "IMXUSDT", "axs": "AXSUSDT",
    "sand": "SANDUSDT", "mana": "MANAUSDT", "gala": "GALAUSDT",
}


def normalise_hisse_symbol(symbol: str) -> str:
    """Hisse senedi sembolünü normalize et: BIST -> .IS, ABD -> olduğu gibi."""
    sym = symbol.upper().strip()
    if "." in sym:
        return sym
    if sym in KNOWN_US_STOCKS:
        return sym
    return sym + ".IS"


def detect_and_normalise(raw: str) -> tuple:
    """
    Sembolü analiz edip türünü ve normalize edilmiş halini döndür.
    Dönüş: (normalized_symbol, type)
    """
    raw_lower = raw.strip().lower()

    # 1) Direkt USDT pair
    if raw_lower.endswith("usdt"):
        return raw_lower.upper(), "coin"

    # 2) Kısa kripto adı (btc, eth, sol, ...)
    if raw_lower in SHORT_CRYPTO_MAP:
        return SHORT_CRYPTO_MAP[raw_lower], "coin"

    # 3) BTC/ETH ile biten
    if raw_lower.endswith("btc") or raw_lower.endswith("eth"):
        return raw_lower.upper(), "coin"

    # 4) Hisse senedi
    normalised = normalise_hisse_symbol(raw_lower)
    return normalised, "hisse"


def format_price(price: float) -> str:
    """Fiyatı virgüllü olarak formatla."""
    if price >= 1000:
        return f"{price:,.2f}"
    elif price >= 1:
        return f"{price:.4f}"
    else:
        return f"{price:.8f}"


def format_big_number(n: float) -> str:
    """Büyük sayıları K/M/B olarak formatla."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.2f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.2f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.2f}K"
    else:
        return f"{n:.2f}"


# =====================================================================
# 2. VERI ÇEKME FONKSIYONLARI
# =====================================================================

def fetch_crypto_data(symbol: str, interval: str = "1h", limit: int = 200):
    """Binance API'den OHLCV mum verileri."""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = json.loads(resp.read().decode("utf-8"))

        return {
            "open":   [float(k[1]) for k in raw],
            "high":   [float(k[2]) for k in raw],
            "low":    [float(k[3]) for k in raw],
            "close":  [float(k[4]) for k in raw],
            "volume": [float(k[5]) for k in raw],
            "type":   "coin",
        }
    except Exception:
        return None


def fetch_stock_data(symbol: str):
    """yfinance ile hisse senedi verisi çek. En az 200 mum için 1y periyot."""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1y", interval="1d")
        if df.empty or len(df) < 30:
            return None

        return {
            "open":   df["Open"].tolist(),
            "high":   df["High"].tolist(),
            "low":    df["Low"].tolist(),
            "close":  df["Close"].tolist(),
            "volume": df["Volume"].tolist(),
            "type":   "hisse",
        }
    except Exception:
        return None


def get_24h_change(symbol: str, data_type: str) -> float:
    """24 saatlik fiyat değişim yüzdesi."""
    if data_type == "coin":
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return float(data.get("priceChangePercent", 0))
        except Exception:
            return None
    else:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="5d")
            if len(df) >= 2:
                prev = df["Close"].iloc[-2]
                curr = df["Close"].iloc[-1]
                if prev > 0:
                    return round(((curr - prev) / prev) * 100, 2)
            return None
        except Exception:
            return None


# =====================================================================
# 3. INDİKATÖR HESAPLAMALARI
# =====================================================================

def calculate_ema(prices: list, period: int) -> list:
    """Exponential Moving Average. Dizinin sonuna doğru hizalanmış liste döndürür."""
    if len(prices) < period:
        return None
    k = 2.0 / (period + 1)
    ema = []
    sma = sum(prices[:period]) / period
    ema.append(sma)
    for price in prices[period:]:
        ema.append(price * k + ema[-1] * (1.0 - k))
    return ema  # len = len(prices) - period + 1


def get_latest_ema(ema_list: list) -> float:
    """EMA listesinin son geçerli değerini döndür."""
    if ema_list is None or not ema_list:
        return None
    return ema_list[-1]


def check_ema_price_relation(price: float, ema_last: float) -> str:
    """Fiyatın EMA'ya göre konumu: '▲', '▼' veya '—'"""
    if ema_last is None:
        return "—"
    return "▲" if price >= ema_last else "▼"


def check_ema_direction(ema_list: list) -> str:
    """EMA'nın son 3 değerine bakarak yön tahmini."""
    if ema_list is None or len(ema_list) < 4:
        return "—"
    # Son 3 değerin ortalaması vs önceki
    recent = ema_list[-4:]
    if recent[-1] > recent[-2] and recent[-2] > recent[-3]:
        return "↗"
    elif recent[-1] < recent[-2] and recent[-2] < recent[-3]:
        return "↘"
    return "→"


def calculate_rsi(prices: list, period: int = 14) -> float:
    """Relative Strength Index (14)."""
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i - 1]
        gains.append(change if change > 0 else 0.0)
        losses.append(abs(change) if change < 0 else 0.0)

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return round(100.0 - (100.0 / (1.0 + rs)), 1)


def rsi_signal(rsi: float) -> tuple:
    """RSI yorumu: (etiket, durum)"""
    if rsi is None:
        return "—", "Veri Yok"
    if rsi >= 70:
        return "🟥", "Aşırı Alım (SAT Sinyali)"
    elif rsi >= 55:
        return "🟨", "Alım Bölgesi (Temkinli)"
    elif rsi >= 45:
        return "⬜", "Nötr Bölge"
    elif rsi >= 30:
        return "🟩", "Satım Bölgesi (Temkinli)"
    else:
        return "🟩", "Aşırı Satım (AL Sinyali)"


def calculate_macd(prices: list, fast: int = 12, slow: int = 26, signal: int = 9) -> tuple:
    """
    MACD hesaplaması.
    Dönüş: (macd_line, signal_line, histogram) — son değerler veya tuple None
    """
    if len(prices) < slow + signal:
        return None, None, None

    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    if ema_fast is None or ema_slow is None:
        return None, None, None

    # Hizala: fast EMA slow'dan daha erken başlar, kırp
    offset = len(ema_fast) - len(ema_slow)
    ema_fast_aligned = ema_fast[offset:]

    macd_line = [f - s for f, s in zip(ema_fast_aligned, ema_slow)]
    signal_line = calculate_ema(macd_line, signal)
    if signal_line is None:
        return macd_line[-1], None, None

    # Hizala
    sig_offset = len(macd_line) - len(signal_line)
    macd_trimmed = macd_line[sig_offset:]

    histogram = [m - s for m, s in zip(macd_trimmed, signal_line)]
    return macd_trimmed[-1], signal_line[-1], histogram[-1]


def macd_signal(macd_val: float, signal_val: float, hist_val: float) -> tuple:
    """MACD yorumu: (etiket, sinyal)"""
    if macd_val is None or signal_val is None:
        return "—", "Veri Yok"

    if macd_val > signal_val:
        if hist_val > 0 and hist_val > abs(macd_val - signal_val) * 0.1:
            return "🟢 AL", "Güçlü Pozitif Kesişim"
        return "🟢 AL", "Pozitif Kesişim"
    else:
        if hist_val < 0 and abs(hist_val) > abs(macd_val - signal_val) * 0.1:
            return "🔴 SAT", "Güçlü Negatif Kesişim"
        return "🔴 SAT", "Negatif Kesişim"


def calculate_adx(highs: list, lows: list, closes: list, period: int = 14) -> tuple:
    """
    Average Directional Index (14).
    Dönüş: (adx, plus_di, minus_di) veya (None, None, None)
    """
    n = len(closes)
    if n < period * 2:
        return None, None, None

    tr = [0.0] * n
    plus_dm = [0.0] * n
    minus_dm = [0.0] * n

    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)

        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        if up > down and up > 0:
            plus_dm[i] = up
        if down > up and down > 0:
            minus_dm[i] = down

    # Wilder smoothing (ilk SMA, sonra k = 1/period)
    atr = [0.0] * n
    pdi_s = [0.0] * n
    mdi_s = [0.0] * n

    atr[period] = sum(tr[1:period + 1]) / period
    pdi_s[period] = sum(plus_dm[1:period + 1]) / period
    mdi_s[period] = sum(minus_dm[1:period + 1]) / period

    for i in range(period + 1, n):
        atr[i] = (atr[i - 1] * (period - 1) + tr[i]) / period
        pdi_s[i] = (pdi_s[i - 1] * (period - 1) + plus_dm[i]) / period
        mdi_s[i] = (mdi_s[i - 1] * (period - 1) + minus_dm[i]) / period

    # DI hesapla
    di_plus_series = [0.0] * n
    di_minus_series = [0.0] * n
    dx_series = [0.0] * n

    for i in range(period, n):
        if atr[i] != 0:
            di_plus_series[i] = 100.0 * pdi_s[i] / atr[i]
            di_minus_series[i] = 100.0 * mdi_s[i] / atr[i]
        di_sum = di_plus_series[i] + di_minus_series[i]
        if di_sum != 0:
            dx_series[i] = 100.0 * abs(di_plus_series[i] - di_minus_series[i]) / di_sum

    # ADX: SMA of last (period) DX values
    adx = sum(dx_series[n - period:n]) / period if period > 0 else 0.0

    return round(adx, 1), round(di_plus_series[-1], 1), round(di_minus_series[-1], 1)


def adx_signal(adx: float, plus_di: float, minus_di: float) -> tuple:
    """ADX yorumu: (etiket, metin)"""
    if adx is None:
        return "—", "Veri Yok"
    if adx >= 25:
        yon = "🔼 Yükseliş" if plus_di > minus_di else "🔽 Düşüş"
        return f"⚡ Güçlü", f"Güçlü Trend ({yon})"
    elif adx >= 20:
        yon = "Yükseliş" if plus_di > minus_di else "Düşüş"
        return "📊 Zayıf", f"Zayıf {yon} Eğilimi"
    else:
        return "⬜ Zayıf", "Trendsiz / Yatay Piyasa"


def calculate_bollinger(prices: list, period: int = 20, std_dev: float = 2.0) -> tuple:
    """Bollinger Bantları: (üst, orta, alt)"""
    if len(prices) < period:
        return None, None, None
    recent = prices[-period:]
    sma = sum(recent) / period
    variance = sum((p - sma) ** 2 for p in recent) / period
    std = math.sqrt(variance)
    upper = sma + std_dev * std
    lower = sma - std_dev * std
    return upper, sma, lower


def bollinger_signal(price: float, bb_upper: float, bb_middle: float, bb_lower: float) -> str:
    """Bollinger sinyali."""
    if bb_upper is None:
        return "Veri Yok"
    if price >= bb_upper * 0.98:
        return "🟥 Direnç Bölgesi (SAT)"
    elif price >= bb_middle:
        return "🟡 Üst Bant (Temkinli)"
    elif price >= bb_lower * 1.02:
        return "🟩 Alt Bant (Temkinli)"
    else:
        return "🟢 Destek Bölgesi (AL)"


def find_support_resistance(highs: list, lows: list, closes: list) -> tuple:
    """Basit pivot bazlı destek/direnç seviyeleri."""
    recent = min(200, len(closes))
    if recent < 10:
        return None, None
    resistance = max(highs[-recent:])
    support = min(lows[-recent:])
    # Ek olarak pivot noktası
    pivot = (resistance + support + closes[-1]) / 3.0
    # R1, S1
    r1 = 2 * pivot - support
    s1 = 2 * pivot - resistance
    return round(s1, 2), round(r1, 2)


def analyze_volume(volumes: list, closes: list) -> str:
    """Hacim analizi: son mum hacmi vs 20 mum ortalaması."""
    if len(volumes) < 20:
        return "Yetersiz Veri"
    avg_vol = sum(volumes[-20:]) / 20
    if avg_vol == 0:
        return "Normal"
    latest = volumes[-1]
    ratio = latest / avg_vol
    if ratio > 2.0:
        return "🔥 Ortalamanın Çok Üstü (Yüksek Hacim)"
    elif ratio > 1.5:
        return "📊 Ortalama Üstü"
    elif ratio > 0.7:
        return "📊 Normal"
    else:
        return "💤 Ortalama Altı (Düşük Hacim)"


# =====================================================================
# 4. İŞLEM SKORU ALGORITMASI
# =====================================================================

def calculate_trade_score(ind: dict) -> tuple:
    """
    Ağırlıklı işlem skoru (0-100).
    ind dict'i şunları içerir: price, ema20, ema50, ema200, rsi,
    macd_val, signal_val, histogram, adx, plus_di, minus_di,
    bb_upper, bb_middle, bb_lower, support, resistance
    """
    score = 0.0
    details = []

    # --- 1) EMA Skoru (%30) ---
    price = ind["price"]
    ema_values = [ind.get("ema20"), ind.get("ema50"), ind.get("ema200")]
    valid_emas = [e for e in ema_values if e is not None]
    if valid_emas:
        above = sum(1 for e in valid_emas if price >= e)
        ema_pct = (above / len(valid_emas)) * 100.0
        ema_score = ema_pct  # 0-100
        score += ema_score * 0.30
        details.append(f"EMA({above}/{len(valid_emas)} üst): {ema_score:.0f}/100")
    else:
        details.append("EMA: Veri Yok")

    # --- 2) RSI Skoru (%20) ---
    rsi = ind.get("rsi")
    if rsi is not None:
        if rsi < 25:
            rsi_score = 95  # Aşırı satış — güçlü al
        elif rsi < 30:
            rsi_score = 85
        elif rsi < 40:
            rsi_score = 70
        elif rsi < 45:
            rsi_score = 60
        elif rsi < 55:
            rsi_score = 50  # Nötr
        elif rsi < 60:
            rsi_score = 40
        elif rsi < 70:
            rsi_score = 30
        elif rsi < 75:
            rsi_score = 15
        else:
            rsi_score = 5   # Aşırı alım — güçlü sat
        score += rsi_score * 0.20
        details.append(f"RSI({rsi}): {rsi_score:.0f}/100")
    else:
        details.append("RSI: Veri Yok")

    # --- 3) MACD Skoru (%20) ---
    macd_val = ind.get("macd_val")
    signal_val = ind.get("signal_val")
    if macd_val is not None and signal_val is not None:
        if macd_val > signal_val:
            macd_score = 80
        else:
            macd_score = 20
        score += macd_score * 0.20
        details.append(f"MACD: {macd_score:.0f}/100")
    else:
        details.append("MACD: Veri Yok")

    # --- 4) ADX/Trend Skoru (%30) ---
    adx = ind.get("adx")
    plus_di = ind.get("plus_di") or 0
    minus_di = ind.get("minus_di") or 0
    if adx is not None:
        if adx >= 25:
            base = 85 if plus_di >= minus_di else 15
            # ADX ne kadar yüksekse o kadar güvenli
            adx_boost = min(adx - 25, 15) * (1 if plus_di >= minus_di else -1)
            adx_score = max(5, min(95, base + adx_boost))
        elif adx >= 20:
            adx_score = 65 if plus_di >= minus_di else 35
        else:
            adx_score = 50  # Trendsiz
        score += adx_score * 0.30
        details.append(f"ADX({adx}): {adx_score:.0f}/100")
    else:
        details.append("ADX: Veri Yok")

    total = round(score)
    if total >= 70:
        signal_text = "🟢 GÜÇLÜ AL / Bullish"
    elif total <= 35:
        signal_text = "🔴 GÜÇLÜ SAT / Bearish"
    else:
        signal_text = "🟡 KARARSIZ / Yatay Piyasa"

    return total, signal_text, details


# =====================================================================
# 5. KURAL TABANLI AI YORUM MOTORU
# =====================================================================

def generate_commentary(ind: dict) -> list:
    """İndikatörlere göre dinamik yorum cümleleri üret."""
    comments = []
    price = ind["price"]

    # --- EMA yorumu ---
    up_names = []
    for name, val in [("EMA20", ind.get("ema20")), ("EMA50", ind.get("ema50")),
                       ("EMA200", ind.get("ema200"))]:
        if val is not None and price >= val:
            up_names.append(name)
    if len(up_names) >= 2:
        comments.append(f"Fiyat {', '.join(up_names)} seviyelerinin üzerinde, yükseliş trendi güçlü.")
    elif len(up_names) == 1:
        comments.append(f"Fiyat {up_names[0]} üzerinde, diğer ortalamaların altında. Trend net değil.")
    else:
        comments.append("Fiyat tüm EMA ortalamalarının altında, düşüş baskısı mevcut.")

    # --- RSI yorumu ---
    rsi = ind.get("rsi")
    if rsi is not None:
        if rsi < 30:
            comments.append(f"RSI {rsi} ile aşırı satış bölgesinde. Teknik tepki alımı gelebilir, dip arayışı sürebilir.")
        elif rsi > 70:
            comments.append(f"RSI {rsi} ile aşırı alım bölgesinde. Kâr satışı yaşanabilir, tepe bölgesine yaklaşılıyor.")
        elif rsi > 55:
            comments.append(f"RSI {rsi} ile alım baskısı pozitif, yükseliş momentumu korunuyor.")
        elif rsi < 45:
            comments.append(f"RSI {rsi} ile satım baskısı devam ediyor, momentum negatif bölgede.")
        else:
            comments.append(f"RSI {rsi} ile nötr bölgede, net bir yön sinyali yok.")

    # --- MACD yorumu ---
    macd_val = ind.get("macd_val")
    signal_val = ind.get("signal_val")
    if macd_val is not None and signal_val is not None:
        if macd_val > signal_val:
            comments.append("MACD sinyal çizgisinin üzerinde, al sinyali aktif.")
        else:
            comments.append("MACD sinyal çizgisinin altında, sat sinyali aktif.")

    # --- ADX yorumu ---
    adx = ind.get("adx")
    plus_di = ind.get("plus_di") or 0
    minus_di = ind.get("minus_di") or 0
    if adx is not None:
        if adx >= 25:
            yon = "yükseliş" if plus_di >= minus_di else "düşüş"
            comments.append(f"ADX {adx} ile güçlü {yon} trendi var. Trend takip edilmeli.")
        elif adx >= 20:
            yon = "yükseliş" if plus_di >= minus_di else "düşüş"
            comments.append(f"ADX {adx} ile zayıf {yon} eğilimi var, teyit beklenmeli.")
        else:
            comments.append(f"ADX {adx} ile trend gücü zayıf, yatay piyasa koşulları hakim.")

    # --- Bollinger yorumu ---
    bb_upper = ind.get("bb_upper")
    bb_lower = ind.get("bb_lower")
    if bb_upper is not None and bb_lower is not None:
        band_width = bb_upper - bb_lower
        if price >= bb_upper * 0.99:
            comments.append("Fiyat Bollinger üst bandına dayandı, direnç bölgesinde. Geri çekilme riski var.")
        elif price <= bb_lower * 1.01:
            comments.append("Fiyat Bollinger alt bandına yakın, destek bölgesinde. Tepki alımı beklenebilir.")
        elif bb_upper - price < band_width * 0.15:
            comments.append("Fiyat Bollinger üst banda yakın, direnç test ediliyor.")
        elif price - bb_lower < band_width * 0.15:
            comments.append("Fiyat Bollinger alt banda yakın, destek bölgesi test ediliyor.")

    # --- Destek/Direnç yorumu ---
    support = ind.get("support")
    resistance = ind.get("resistance")
    if support and resistance and resistance > support:
        price_pos = (price - support) / (resistance - support) * 100
        if price_pos > 85:
            comments.append(f"Direnç seviyesine ({format_price(resistance)}) yaklaşıldı, dikkatli olunmalı.")
        elif price_pos < 15:
            comments.append(f"Destek seviyesine ({format_price(support)}) yakın, tepki alımı potansiyeli yüksek.")

    # En fazla 5 cümle
    return comments[:5]


# =====================================================================
# 6. ÇIKTI / TABLO
# =====================================================================

def print_analysis(symbol: str, data: dict, change_pct: float, interval: str = ""):
    """Tüm analizi terminal tablosu olarak bas."""
    closes = data["close"]
    highs = data["high"]
    lows = data["low"]
    volumes = data["volume"]
    money = data["type"]

    current_price = closes[-1]
    currency_label = "USDT" if money == "coin" else "TL"

    # --- İndikatörleri hesapla ---
    ema20_raw = calculate_ema(closes, 20)
    ema50_raw = calculate_ema(closes, 50)
    ema200_raw = calculate_ema(closes, 200)

    ema20_last = get_latest_ema(ema20_raw)
    ema50_last = get_latest_ema(ema50_raw)
    ema200_last = get_latest_ema(ema200_raw)

    rsi_val = calculate_rsi(closes, 14)
    macd_v, signal_v, hist_v = calculate_macd(closes)
    adx_v, di_p, di_m = calculate_adx(highs, lows, closes)
    bb_u, bb_m, bb_l = calculate_bollinger(closes)
    sup, res = find_support_resistance(highs, lows, closes)

    ema20_dir = check_ema_price_relation(current_price, ema20_last)
    ema50_dir = check_ema_price_relation(current_price, ema50_last)
    ema200_dir = check_ema_price_relation(current_price, ema200_last)

    ema20_trend = check_ema_direction(ema20_raw)
    ema50_trend = check_ema_direction(ema50_raw)

    rsi_icon, rsi_label = rsi_signal(rsi_val)
    macd_icon, macd_label = macd_signal(macd_v, signal_v, hist_v)
    adx_icon, adx_label = adx_signal(adx_v, di_p, di_m)
    bb_label = bollinger_signal(current_price, bb_u, bb_m, bb_l)
    vol_label = analyze_volume(volumes, closes)

    # --- Trend durumu ---
    up_emas = sum(1 for e in [ema20_last, ema50_last, ema200_last]
                  if e is not None and current_price >= e)
    if rsi_val is not None:
        if up_emas >= 2 and rsi_val > 50:
            trend_text = "🟢 Bullish"
        elif up_emas <= 1 and rsi_val < 50:
            trend_text = "🔴 Bearish"
        else:
            trend_text = "🟡 Nötr / Karmaşık"
    else:
        trend_text = "—"

    change_icon = "📈" if change_pct is not None and change_pct >= 0 else "📉"
    change_display = f"{change_pct:+.2f}%" if change_pct is not None else "Veri Yok"

    # --- İşlem Skoru ---
    indicator_dict = {
        "price": current_price,
        "ema20": ema20_last, "ema50": ema50_last, "ema200": ema200_last,
        "rsi": rsi_val,
        "macd_val": macd_v, "signal_val": signal_v, "histogram": hist_v,
        "adx": adx_v, "plus_di": di_p, "minus_di": di_m,
        "bb_upper": bb_u, "bb_middle": bb_m, "bb_lower": bb_l,
        "support": sup, "resistance": res,
    }

    trade_score, trade_signal, score_details = calculate_trade_score(indicator_dict)
    ai_comments = generate_commentary(indicator_dict)

    # --- TABLO ÇIKTISI ---
    periyot = f" {interval}" if interval else " 1s"
    hat = "─" * 53

    print(f"\n{hat}")
    print(f" {symbol:^12s} | MERKEZİ TEKNİK ANALİZ |{periyot}")
    print(f"{hat}")

    # Fiyat ve trend
    print(f" Fiyat          : {format_price(current_price):>12s} {currency_label}")
    print(f" 24s Değişim    : {change_display:>12s} {change_icon}")
    print(f" Trend          : {trend_text}")
    print()

    # EMA
    ema20_label = f"{ema20_dir} {ema20_trend}" if ema20_last else "—"
    ema50_label = f"{ema50_dir} {ema50_trend}" if ema50_last else "—"
    ema200_label = f"{ema200_dir}" if ema200_last else "—"
    print(f" EMA20          : {ema20_label:<12s}   ({format_price(ema20_last) if ema20_last else 'N/A'})")
    print(f" EMA50          : {ema50_label:<12s}   ({format_price(ema50_last) if ema50_last else 'N/A'})")
    print(f" EMA200         : {ema200_label:<12s}   ({format_price(ema200_last) if ema200_last else 'N/A'})")
    print()

    # RSI, MACD, ADX
    print(f" RSI(14)        : {rsi_val if rsi_val else 'N/A':>8s}  {rsi_icon} {rsi_label}")
    print(f" MACD(12/26/9)  : {macd_icon:<4s} {macd_label}")
    print(f" ADX(14)        : {adx_v if adx_v else 'N/A':>8s}  {adx_icon} {adx_label}")
    print()

    # Bollinger, Destek/Direnç, Hacim
    bb_line = f"Üst: {format_price(bb_u) if bb_u else '—'}  Orta: {format_price(bb_m) if bb_m else '—'}  Alt: {format_price(bb_l) if bb_l else '—'}"
    print(f" Bollinger      : {bb_label}")
    print(f" Destek         : {format_price(sup) if sup else '—':>12s}")
    print(f" Direnç         : {format_price(res) if res else '—':>12s}")
    print(f" Hacim          : {vol_label}")
    print()

    # AI Yorum
    print(f" 📊 AI Özet Yorumu")
    print(f"{hat}")
    if ai_comments:
        for c in ai_comments:
            print(f"  • {c}")
    else:
        print("  • Yorum üretilemedi (yetersiz veri).")
    print()

    # Skor
    print(f"{hat}")
    print(f" İşlem Skoru    : {trade_score:>3d}/100  {trade_signal}")
    print(f"{hat}\n")


# =====================================================================
# 7. ANA GİRİŞ
# =====================================================================

def main():
    if len(sys.argv) < 2:
        print("Kullanım: analiz <sembol> [periyot]")
        print("")
        print("📌 Örnekler:")
        print("  analiz btcusdt              # BTC 1 saatlik")
        print("  analiz btcusdt 4h           # BTC 4 saatlik")
        print("  analiz thyao                # THYAO (BIST)")
        print("  analiz aapl                 # Apple (ABD)")
        print("  analiz eth                  # ETH/USDT kripto")
        print("  analiz eregl                # EREGL (BIST)")
        return

    raw_symbol = sys.argv[1].strip()
    interval = sys.argv[2].strip().lower() if len(sys.argv) >= 3 else ""

    # Sembolü normalize et
    norm_symbol, data_type = detect_and_normalise(raw_symbol)

    # Periyot: crypto için 1h varsayılan, yoksa parametre
    if data_type == "coin":
        fetch_interval = interval if interval in ("1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M") else "1h"
    else:
        fetch_interval = ""  # stocks always daily with yfinance

    print(f"🔄 {norm_symbol} için teknik analiz hazırlanıyor... (kaynak: {'Binance' if data_type == 'coin' else 'Yahoo Finance'}, periyot: {fetch_interval if data_type == 'coin' else '1d'})")

    # Veri çek
    if data_type == "coin":
        data = fetch_crypto_data(norm_symbol, fetch_interval)
        display_interval = fetch_interval
    else:
        data = fetch_stock_data(norm_symbol)
        display_interval = "1d"

    if data is None:
        print(f"❌ '{norm_symbol}' için veri alınamadı! Sembolü kontrol edin.")
        return

    change_pct = get_24h_change(norm_symbol, data_type)
    print_analysis(norm_symbol, data, change_pct, display_interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Analiz kapatıldı.")
