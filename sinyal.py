# -*- coding: utf-8 -*-
"""
sinyal.py — Akıllı Sinyal Modülü
=================================
Kullanım: sinyal <sembol> [periyot]
  Örn:  sinyal btcusdt          (1h varsayılan)
        sinyal btcusdt 15m      (15 dakikalık mumlar)
        sinyal btcusdt 4h       (4 saatlik)
        sinyal thyao             (hisse — günlük)
        sinyal aapl
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
import urllib.parse
import xml.etree.ElementTree as ET
import textwrap
import warnings
warnings.filterwarnings("ignore")

# =====================================================================
# 1. SABİTLER VE TANIMLAR
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
    "btc": "BTCUSDT", "bitcoin": "BTCUSDT",
    "eth": "ETHUSDT", "ethereum": "ETHUSDT",
    "sol": "SOLUSDT", "solana": "SOLUSDT",
    "xrp": "XRPUSDT", "ripple": "XRPUSDT",
    "ada": "ADAUSDT", "doge": "DOGEUSDT", "dogecoin": "DOGEUSDT",
    "dot": "DOTUSDT", "link": "LINKUSDT", "uni": "UNIUSDT",
    "avax": "AVAXUSDT", "avalanche": "AVAXUSDT", "ltc": "LTCUSDT",
    "bch": "BCHUSDT", "near": "NEARUSDT", "apt": "APTUSDT",
    "sui": "SUIUSDT", "ftm": "FTMUSDT", "inj": "INJUSDT",
    "pepe": "1000PEPEUSDT", "shib": "1000SHIBUSDT",
}


def detect_and_normalise(raw: str) -> tuple:
    """(normalized_symbol, type)"""
    s = raw.strip().lower()
    if s.endswith("usdt"):
        return s.upper(), "coin"
    if s in SHORT_CRYPTO_MAP:
        return SHORT_CRYPTO_MAP[s], "coin"
    if "." in s:
        return s.upper(), "hisse"
    up = s.upper()
    if up in KNOWN_US_STOCKS:
        return up, "hisse"
    return up + ".IS", "hisse"


VALID_INTERVALS = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M"}


def parse_interval_label(interval: str) -> str:
    """Interval kodunu insan okunur hale getir: '15m' -> '15 Dakikalık'"""
    labels = {
        "1m": "1 Dakikalık", "3m": "3 Dakikalık", "5m": "5 Dakikalık",
        "15m": "15 Dakikalık", "30m": "30 Dakikalık",
        "1h": "1 Saatlik", "2h": "2 Saatlik", "4h": "4 Saatlik",
        "6h": "6 Saatlik", "8h": "8 Saatlik", "12h": "12 Saatlik",
        "1d": "Günlük", "3d": "3 Günlük", "1w": "Haftalık", "1M": "Aylık",
    }
    return labels.get(interval, interval)


# =====================================================================
# 2. VERİ ÇEKME
# =====================================================================

def fetch_crypto_data(symbol: str, interval: str = "1h"):
    """Binance 24h ticker + son mum verileri (istenen periyotta)"""
    try:
        req = urllib.request.Request(
            f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            t = json.loads(resp.read().decode("utf-8"))
        price = float(t["lastPrice"])
        change = float(t["priceChangePercent"])
        high24 = float(t["highPrice"])
        low24 = float(t["lowPrice"])
        vol = float(t["volume"])

        # İstenen periyotta mum verisi — 100 mum yeterli indikatör için
        req2 = urllib.request.Request(
            f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100",
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urllib.request.urlopen(req2, timeout=5) as resp2:
            klines = json.loads(resp2.read().decode("utf-8"))
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        volumes = [float(k[5]) for k in klines]
        return {"price": price, "change": change, "high24": high24, "low24": low24, "vol24": vol,
                "closes": closes, "highs": highs, "lows": lows, "volumes": volumes,
                "type": "coin", "currency": "USDT"}
    except Exception:
        return None


def fetch_stock_data(symbol: str):
    """yfinance 6 aylık günlük veri"""
    try:
        import yfinance as yf
    except ImportError:
        print("Hata: 'yfinance' kutuphanesi bulunamadi. Kurmak icin: cmdtools install")
        return None
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="6mo", interval="1d")
        if df.empty or len(df) < 10:
            return None
        price = float(df["Close"].iloc[-1])
        prev = float(df["Close"].iloc[-2]) if len(df) >= 2 else price
        change = round(((price - prev) / prev) * 100, 2)
        currency = "TL" if symbol.endswith(".IS") else "USD"
        return {"price": price, "change": change, "high24": float(df["High"].iloc[-1]),
                "low24": float(df["Low"].iloc[-1]), "vol24": float(df["Volume"].iloc[-1]),
                "closes": df["Close"].tolist(), "highs": df["High"].tolist(), "lows": df["Low"].tolist(),
                "volumes": df["Volume"].tolist(), "type": "hisse", "currency": currency}
    except Exception:
        return None


# =====================================================================
# 3. İNDİKATÖRLER
# =====================================================================

def ema(prices, p):
    if len(prices) < p:
        return None
    k = 2.0 / (p + 1)
    ema_arr = []
    sma = sum(prices[:p]) / p
    ema_arr.append(sma)
    for pr in prices[p:]:
        ema_arr.append(pr * k + ema_arr[-1] * (1.0 - k))
    return ema_arr[-1]


def rsi(prices, p=14):
    if len(prices) < p + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        c = prices[i] - prices[i - 1]
        gains.append(c if c > 0 else 0)
        losses.append(abs(c) if c < 0 else 0)
    ag = sum(gains[:p]) / p
    al = sum(losses[:p]) / p
    for i in range(p, len(gains)):
        ag = (ag * (p - 1) + gains[i]) / p
        al = (al * (p - 1) + losses[i]) / p
    if al == 0:
        return 100.0
    return round(100.0 - (100.0 / (1.0 + ag / al)), 1)


def macd_full(prices, fast=12, slow=26, signal=9):
    """
    Tam MACD: (macd_line, signal_line, histogram) son değerler.
    """
    if len(prices) < slow + signal:
        return None, None, None

    # fast EMA
    if len(prices) < fast:
        return None, None, None
    kf = 2.0 / (fast + 1)
    ema_fast = []
    sma_f = sum(prices[:fast]) / fast
    ema_fast.append(sma_f)
    for pr in prices[fast:]:
        ema_fast.append(pr * kf + ema_fast[-1] * (1.0 - kf))

    # slow EMA
    ks = 2.0 / (slow + 1)
    ema_slow = []
    sma_s = sum(prices[:slow]) / slow
    ema_slow.append(sma_s)
    for pr in prices[slow:]:
        ema_slow.append(pr * ks + ema_slow[-1] * (1.0 - ks))

    # MACD line = fast - slow (hizala)
    offset = len(ema_fast) - len(ema_slow)
    macd_line = [ema_fast[i + offset] - ema_slow[i] for i in range(len(ema_slow))]

    # Signal line = EMA of MACD line
    if len(macd_line) < signal:
        return macd_line[-1], None, None
    ksig = 2.0 / (signal + 1)
    sig_line = []
    sma_sig = sum(macd_line[:signal]) / signal
    sig_line.append(sma_sig)
    for i in range(signal, len(macd_line)):
        sig_line.append(macd_line[i] * ksig + sig_line[-1] * (1.0 - ksig))

    # Histogram = MACD - Signal (en son)
    hist = macd_line[-1] - sig_line[-1]

    return macd_line[-1], sig_line[-1], hist


def adx(highs, lows, closes, p=14):
    n = len(closes)
    if n < p * 2:
        return None, 0, 0
    tr, plus, minus = [0.0] * n, [0.0] * n, [0.0] * n
    for i in range(1, n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr[i] = max(hl, hc, lc)
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        if up > down and up > 0:
            plus[i] = up
        if down > up and down > 0:
            minus[i] = down
    atr = sum(tr[1:p + 1]) / p
    ps = sum(plus[1:p + 1]) / p
    ms = sum(minus[1:p + 1]) / p
    for i in range(p + 1, n):
        atr = (atr * (p - 1) + tr[i]) / p
        ps = (ps * (p - 1) + plus[i]) / p
        ms = (ms * (p - 1) + minus[i]) / p
    dp = 100.0 * ps / atr if atr else 0
    dm = 100.0 * ms / atr if atr else 0
    dx = 100.0 * abs(dp - dm) / (dp + dm) if (dp + dm) else 0
    return round(dx, 1), round(dp, 1), round(dm, 1)


def bb(prices, p=20):
    if len(prices) < p:
        return None, None, None
    r = prices[-p:]
    sma = sum(r) / p
    std = math.sqrt(sum((x - sma) ** 2 for x in r) / p)
    return sma + 2 * std, sma, sma - 2 * std


def sr(highs, lows):
    return round(min(lows[-20:]), 2), round(max(highs[-20:]), 2)


def qqe(closes, rsi_period=14, sf=5, qqe_factor=3.0):
    """QQE: RSI uzerinde ATR trailing stop. Donus: trend (1=bull, -1=bear)"""
    n = len(closes)
    if n < rsi_period * 3:
        return 0

    gains, losses = [], []
    for i in range(1, n):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))

    ag = sum(gains[:rsi_period]) / rsi_period
    al = sum(losses[:rsi_period]) / rsi_period
    rsi_vals = [50.0] * rsi_period
    for i in range(rsi_period, len(gains)):
        ag = (ag * (rsi_period - 1) + gains[i]) / rsi_period
        al = (al * (rsi_period - 1) + losses[i]) / rsi_period
        rsi_vals.append(100.0 - (100.0 / (1.0 + ag / al)) if al else 100.0)

    alpha = 1.0 / sf
    rsi_ma = [rsi_vals[0]]
    for i in range(1, len(rsi_vals)):
        rsi_ma.append(rsi_ma[-1] * (1 - alpha) + rsi_vals[i] * alpha)

    wilders_p = 2 * rsi_period - 1
    alpha_w = 1.0 / wilders_p
    atr_rsi = [0.0]
    for i in range(1, len(rsi_ma)):
        atr_rsi.append(abs(rsi_ma[i - 1] - rsi_ma[i]))

    ma_atr_rsi = [atr_rsi[0]]
    for i in range(1, len(atr_rsi)):
        ma_atr_rsi.append(ma_atr_rsi[-1] * (1 - alpha_w) + atr_rsi[i] * alpha_w)

    dar = [ma_atr_rsi[0] * qqe_factor]
    for i in range(1, len(ma_atr_rsi)):
        val = dar[-1] * (1 - alpha_w) + ma_atr_rsi[i] * alpha_w
        dar.append(val * qqe_factor)

    start = rsi_period + 1
    if start >= len(rsi_ma):
        return 0

    longband = [0.0] * len(rsi_ma)
    shortband = [0.0] * len(rsi_ma)
    trend = [0] * len(rsi_ma)
    longband[start] = rsi_ma[start] - dar[start]
    shortband[start] = rsi_ma[start] + dar[start]
    trend[start] = 1

    for i in range(start + 1, len(rsi_ma)):
        newlong = rsi_ma[i] - dar[i]
        newshort = rsi_ma[i] + dar[i]
        if rsi_ma[i - 1] > longband[i - 1] and longband[i - 1] > newlong:
            longband[i] = longband[i - 1]
        else:
            longband[i] = newlong
        if rsi_ma[i - 1] < shortband[i - 1] and shortband[i - 1] < newshort:
            shortband[i] = shortband[i - 1]
        else:
            shortband[i] = newshort
        if trend[i - 1] == 1:
            trend[i] = -1 if rsi_ma[i] < longband[i] else 1
        else:
            trend[i] = 1 if rsi_ma[i] > shortband[i] else -1

    return trend[-1]


# =====================================================================
# 4. KISA ASCII GRAFİK
# =====================================================================

def sparkline(data, w=40):
    if not data or len(data) < 3:
        return ""
    seg = data[-w:]
    mn, mx = min(seg), max(seg)
    if mx == mn:
        return "▬" * len(seg)
    c = "▁▂▃▄▅▆▇█"
    return "".join(c[int((v - mn) / (mx - mn) * (len(c) - 1))] for v in seg)


# =====================================================================
# 5. AL/SAT/NÖTR SİNYAL KARARI
# =====================================================================

def signal_decision(ind) -> tuple:
    """
    Dönüş: (karar, skor, gerekçeler_listesi)
    """
    p = ind["price"]
    e20, e50, e200 = ind.get("ema20"), ind.get("ema50"), ind.get("ema200")
    r = ind.get("rsi")
    macd_v, macd_sig, hist = ind.get("macd"), ind.get("macd_signal"), ind.get("histogram")
    adx_v, dp, dm = ind.get("adx"), ind.get("plus_di"), ind.get("minus_di")
    bb_u, bb_l = ind.get("bb_upper"), ind.get("bb_lower")
    sup, res = ind.get("support"), ind.get("resistance")

    reasons = []
    score = 0

    # EMA (max 30 puan)
    ema_count = 0
    for ema_val in [e20, e50, e200]:
        if ema_val is not None:
            if p >= ema_val:
                score += 10
                ema_count += 1
            else:
                score -= 5
    if ema_count >= 2:
        reasons.append(f"Fiyat {ema_count}/3 EMA üzerinde, yükseliş destekli")
    elif ema_count <= 1:
        reasons.append(f"Fiyat sadece {ema_count}/3 EMA üzerinde, zayıf")

    # RSI (max 20 puan)
    if r is not None:
        if r < 30:
            score += 20
            reasons.append(f"RSI {r} aşırı satım, tepki alımı potansiyeli")
        elif r < 40:
            score += 10
            reasons.append(f"RSI {r} düşük bölgede")
        elif r < 45:
            score += 5
        elif r < 55:
            reasons.append(f"RSI {r} nötr")
        elif r < 60:
            score -= 5
        elif r < 70:
            score -= 10
            reasons.append(f"RSI {r} yüksek bölgede")
        else:
            score -= 20
            reasons.append(f"RSI {r} aşırı alım, satış baskısı gelebilir")

    # MACD (max 15 puan)
    if macd_v is not None and macd_sig is not None:
        if macd_v > 0 and macd_v > macd_sig:
            score += 15
            reasons.append("MACD pozitif ve sinyal üstünde, al momentumu")
        elif macd_v > 0:
            score += 8
            reasons.append("MACD pozitif, al baskısı var")
        elif macd_v < macd_sig:
            score -= 12
            reasons.append("MACD negatif ve sinyal altında, sat baskısı")
        else:
            score -= 5

    # ADX + DI (max 20 puan)
    if adx_v is not None:
        if adx_v >= 25:
            if dp >= dm:
                score += 20
                reasons.append(f"ADX {adx_v} güçlü yükseliş trendi")
            else:
                score -= 15
                reasons.append(f"ADX {adx_v} güçlü düşüş trendi")
        elif adx_v >= 20:
            if dp >= dm:
                score += 8
            else:
                score -= 5
        else:
            reasons.append(f"ADX {adx_v} trendsiz piyasa")

    # Bollinger (max 15 puan)
    if bb_l is not None and bb_u is not None:
        if p <= bb_l * 1.02:
            score += 15
            reasons.append("Fiyat Bollinger alt bandında, destek bölgesi")
        elif p >= bb_u * 0.98:
            score -= 15
            reasons.append("Fiyat Bollinger üst bandında, direnç bölgesi")

    # Destek/Direnç (bonus)
    if sup is not None and res is not None and res > sup:
        pos = (p - sup) / (res - sup) * 100
        if pos < 15:
            score += 8
            reasons.append("Desteğe yakın, yukarı potansiyel yüksek")
        elif pos > 85:
            score -= 8
            reasons.append("Direnç yakınında, geri çekilme riski var")

    # QQE (max 15 puan)
    closes_data = ind.get("closes", [])
    if closes_data:
        qqe_trend = qqe(closes_data)
        if qqe_trend == 1:
            score += 15
            reasons.append("QQE: bullish")
        elif qqe_trend == -1:
            score -= 15
            reasons.append("QQE: bearish")

    score = max(-100, min(100, score))

    if score >= 35:
        karar = "AL 🟢"
    elif score >= 10:
        karar = "BEKLE 🔵"
    elif score >= -15:
        karar = "NÖTR 🟡"
    else:
        karar = "SAT 🔴"

    return karar, score, reasons


# =====================================================================
# 6. AI YORUM + HABER
# =====================================================================

def get_ai_comment(symbol, periyot_adi, karar, score, reasons, haber_metni=""):
    prompt = (
        f"{symbol} ({periyot_adi}) icin sinyal: {karar} (skor: {score}/100).\n"
        f"Gerekceler: {'; '.join(reasons)}.\n"
        + (f"Haber: {haber_metni}\n" if haber_metni else "")
        + "\n1-2 cumle ile neden bu sinyali verdigini acikla. Risk uyarisi ekle. Kisa ve oz."
    )
    system = "Sen bir finansal analistsin. Kisa, oz, anlasilir yorum yap. Turkiye piyasalarini bilirsin."

    try:
        from g4f.client import Client
        from g4f import Provider
        c = Client()
        for model in (None, "gpt-4o-mini", "llama"):
            try:
                kwargs = {
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": prompt},
                    ],
                    "provider": Provider.PollinationsAI,
                    "timeout": 25,
                }
                if model:
                    kwargs["model"] = model
                r = c.chat.completions.create(**kwargs)
                if r and r.choices:
                    t = r.choices[0].message.content
                    if t and t.strip():
                        return t.strip()
            except Exception:
                continue
    except Exception:
        pass
    return None


def get_haber(symbol):
    """Google News RSS'den son 1 haber başlığını çek."""
    try:
        query = urllib.parse.quote(f"{symbol} finans")
        url = f"https://news.google.com/rss/search?q={query}&hl=tr&gl=TR"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            root = ET.fromstring(resp.read())
        items = root.findall(".//item")
        if items:
            title = items[0].find("title")
            if title is not None and title.text:
                return title.text[:200]
    except Exception:
        pass
    return ""


# =====================================================================
# 7. ÇIKTI
# =====================================================================

def format_price(p):
    if p >= 1000:
        return f"{p:,.2f}"
    elif p >= 1:
        return f"{p:.4f}"
    return f"{p:.8f}"


def main():
    if len(sys.argv) < 2:
        print("Kullanım: sinyal <sembol> [periyot]")
        print("Örn: sinyal btcusdt, sinyal btcusdt 15m, sinyal thyao")
        print("Periyotlar: 1m, 5m, 15m, 30m, 1h, 4h, 1d (varsayılan: 1h)")
        return

    raw = sys.argv[1].strip()
    symbol, data_type = detect_and_normalise(raw)

    # Periyot kontrolü
    interval = "1h"
    periyot_adi = "1 Saatlik"
    if len(sys.argv) >= 3:
        user_int = sys.argv[2].strip().lower()
        if user_int in VALID_INTERVALS:
            interval = user_int
            periyot_adi = parse_interval_label(user_int)

    print(f"🔍 {symbol} ({periyot_adi}) analiz ediliyor...")

    if data_type == "coin":
        data = fetch_crypto_data(symbol, interval)
    else:
        data = fetch_stock_data(symbol)
        periyot_adi = "Günlük"

    if not data:
        print(f"❌ '{symbol}' için veri alınamadı! Sembolü veya periyodu kontrol edin.")
        return

    closes = data["closes"]
    p = data["price"]

    # İndikatör hesapla
    ind = {"price": p, "closes": closes}
    ind["ema20"] = ema(closes, 20)
    ind["ema50"] = ema(closes, 50)
    ind["ema200"] = ema(closes, 200)
    ind["rsi"] = rsi(closes, 14)
    macd_v, macd_sig, hist = macd_full(closes)
    ind["macd"] = macd_v
    ind["macd_signal"] = macd_sig
    ind["histogram"] = hist
    adx_v, dp, dm = adx(data["highs"], data["lows"], closes)
    ind["adx"], ind["plus_di"], ind["minus_di"] = adx_v, dp, dm
    ind["bb_upper"], _, ind["bb_lower"] = bb(closes)
    ind["support"], ind["resistance"] = sr(data["highs"], data["lows"])

    # Sinyal kararı
    karar, score, reasons = signal_decision(ind)

    # Grafik
    spark = sparkline(closes, 40)

    # Haber + AI
    haber = get_haber(symbol)
    ai_yorum = get_ai_comment(symbol, periyot_adi, karar, score, reasons, haber)

    # ===== ÇIKTI =====
    hat = "─" * 50
    print()
    print(hat)
    print(f"  📊 SİNYAL RAPORU — {symbol}  |  {periyot_adi}")
    print(hat)
    print()

    # Sparkline
    if spark:
        mn = min(closes[-40:]) if len(closes) >= 40 else min(closes)
        mx = max(closes[-40:]) if len(closes) >= 40 else max(closes)
        print(f"   {mn:>10.2f}  {spark}  {mx:.2f}")
        print()

    # Fiyat bilgisi
    degisim = f"{data['change']:+.2f}%" if data['change'] is not None else "—"
    print(f"   Fiyat     : {format_price(p):>10s} {data['currency']}")
    print(f"   Değişim   : {degisim:>10s}")
    print(f"   Destek    : {format_price(ind['support']):>10s}")
    print(f"   Direnç    : {format_price(ind['resistance']):>10s}")
    print()

    # Sinyal
    print(f"   ╔═══ SİNYAL ═══╗")
    print(f"   ║   {karar:^16s}   ║")
    print(f"   ╚═══════════════╝")
    print(f"   Skor: {score:>+3d}/100")
    print()

    # Gerekçeler
    print(f"   📋 Gerekçeler:")
    for r in reasons:
        print(f"     • {r}")
    print()

    # AI yorumu
    print(f"   🤖 AI Yorumu:")
    print(f"   {'─' * 46}")
    if ai_yorum:
        for line in ai_yorum.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")
    else:
        if score >= 35:
            print("   Teknik göstergeler al sinyali üretiyor. Yükseliş trendinde.")
        elif score <= -15:
            print("   Teknik göstergeler sat sinyali üretiyor. Düşüş trendinde.")
        else:
            print("   Teknik göstergeler karışık sinyaller veriyor. Beklemede kalınmalı.")
    print()

    # Haber
    if haber:
        print(f"   📰 Son Haber:")
        print(f"     {haber}")
        print()

    # Özet
    print(f"   💡 Özet: {symbol} ({periyot_adi}) skor {score}/100 → {karar}")
    print(f"   ⚠️ Bu bir yatırım tavsiyesi değildir.")
    print(hat)
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Sinyal kapatıldı.")
