# -*- coding: utf-8 -*-
"""
otosinyal.py — Otomatik Piyasa Tarama Modülü
=============================================
Tum kripto veya tum BIST hisselerini tarar, guclu sinyal buldugunda
sesli alarm verir.

Kullanim:
  otosinyal kripto              # Tum kriptolari tara (Binance)
  otosinyal hisse               # Tum BIST hisselerini tara
  otosinyal kripto 15m          # Kripto — 15dk mumlarla tara
  otosinyal kripto 1h           # Kripto — 1 saatlik mumlarla tara

Durdurmak icin: Ctrl+C
"""

import sys
import os

# --- WINDOWS CMD EMOJI VE UNICODE COKME KORUMASI ---
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
# --------------------------------------------------

import json
import math
import time
import urllib.request
import winsound
import datetime

# =====================================================================
# 1. SABITLER
# =====================================================================

# Kripto: Binance'de taranacak USDT pairleri (top 50+ by volume)
TARANACAK_KRIPTO = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT",
    "DOGEUSDT", "ADAUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
    "MATICUSDT", "SHIBUSDT", "LTCUSDT", "UNIUSDT", "ATOMUSDT",
    "NEARUSDT", "APTUSDT", "SUIUSDT", "ARBUSDT", "OPUSDT",
    "FILUSDT", "INJUSDT", "FTMUSDT", "ALGOUSDT", "RUNEUSDT",
    "AAVEUSDT", "MKRUSDT", "CRVUSDT", "1000PEPEUSDT", "WLDUSDT",
    "SEIUSDT", "TIAUSDT", "PENDLEUSDT", "ONDOUSDT", "JUPUSDT",
    "BONKUSDT", "WIFUSDT", "FLOKIUSDT", "PEPEUSDT", "ENAUSDT",
    "TONUSDT", "STXUSDT", "IMXUSDT", "GALAUSDT", "SANDUSDT",
    "AXSUSDT", "MANAUSDT", "EGLDUSDT", "KAVAUSDT", "ZRXUSDT",
]

# Hisse: Taranacak BIST hisseleri (yuksek likidite, yuksek hacim)
TARANACAK_HISSE = [
    # BIST 30 — Midas'ta islem goren ana hisseler
    "THYAO.IS", "GARAN.IS", "ASELS.IS", "EREGL.IS", "BIMAS.IS",
    "SAHOL.IS", "KCHOL.IS", "TUPRS.IS", "AKBNK.IS", "SISE.IS",
    "HALKB.IS", "TCELL.IS", "PGSUS.IS",
    "TAVHL.IS", "TOASO.IS", "VESTL.IS", "FROTO.IS", "KONTR.IS",
    # BIST 30 ek + populer hisseler
    "SASA.IS", "ODAS.IS", "ENKAI.IS", "KLSER.IS", "PETKM.IS",
    "TTRAK.IS", "DOAS.IS", "FENER.IS", "HEKTS.IS",
    "YKBNK.IS", "VAKBN.IS", "ISCTR.IS",
    "MGROS.IS", "MPARK.IS", "OTKAR.IS", "ARCLK.IS",
    "DOHOL.IS", "TMSN.IS", "ALARK.IS", "SMRTG.IS",
]

# Sinyal esikleri — guvenilir sinyal icin yuksek esik
AL_ESIK = 65       # Bu skorun ustu = guclu AL sinyali
SAT_ESIK = -50     # Bu skorun alti = guclu SAT sinyali
ALERT_COOLDOWN = 120  # Ayni sembol icin minimum bekleme (sn)

# Tarama araliklari (saniye cinsinden)
KONTROL_ARALIK_KRIPTO = 30   # Kripto: 30 sn arayla tara
KONTROL_ARALIK_HISSE = 300   # Hisse: 5 dk arayla tara

# Kripto mum araliklari
KRIPTO_INTERVALS = {
    "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
    "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h",
    "12h": "12h", "1d": "1d",
}
KRIPTO_INTERVAL_LABELS = {
    "1m": "1 Dakikalik", "3m": "3 Dakikalik", "5m": "5 Dakikalik",
    "15m": "15 Dakikalik", "30m": "30 Dakikalik",
    "1h": "1 Saatlik", "2h": "2 Saatlik", "4h": "4 Saatlik",
    "6h": "6 Saatlik", "8h": "8 Saatlik", "12h": "12 Saatlik",
    "1d": "Gunluk",
}


# =====================================================================
# 2. TEKNIK INDIKATORLER
# =====================================================================

def calc_ema(prices, p):
    if len(prices) < p:
        return None
    k = 2.0 / (p + 1)
    val = sum(prices[:p]) / p
    for pr in prices[p:]:
        val = pr * k + val * (1.0 - k)
    return val


def calc_rsi(prices, p=14):
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


def calc_macd(prices, fast=12, slow=26, sig=9):
    if len(prices) < slow + sig:
        return None, None, None
    kf = 2.0 / (fast + 1)
    ema_f = [sum(prices[:fast]) / fast]
    for pr in prices[fast:]:
        ema_f.append(pr * kf + ema_f[-1] * (1.0 - kf))
    ks = 2.0 / (slow + 1)
    ema_s = [sum(prices[:slow]) / slow]
    for pr in prices[slow:]:
        ema_s.append(pr * ks + ema_s[-1] * (1.0 - ks))
    offset = len(ema_f) - len(ema_s)
    macd_line = [ema_f[i + offset] - ema_s[i] for i in range(len(ema_s))]
    if len(macd_line) < sig:
        return macd_line[-1], None, None
    ksig = 2.0 / (sig + 1)
    sig_line = [sum(macd_line[:sig]) / sig]
    for i in range(sig, len(macd_line)):
        sig_line.append(macd_line[i] * ksig + sig_line[-1] * (1.0 - ksig))
    hist = macd_line[-1] - sig_line[-1]
    return macd_line[-1], sig_line[-1], hist


def calc_adx(highs, lows, closes, p=14):
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


def calc_bollinger(prices, p=20):
    if len(prices) < p:
        return None, None, None
    r = prices[-p:]
    sma = sum(r) / p
    std = math.sqrt(sum((x - sma) ** 2 for x in r) / p)
    return sma + 2 * std, sma, sma - 2 * std


# =====================================================================
# 2b. SSL HYBRID INDIKATORU
# =====================================================================

def _wma(data, period):
    """Weighted Moving Average."""
    if len(data) < period:
        return []
    weights = list(range(period, 0, -1))
    wsum = sum(weights)
    result = []
    for i in range(period - 1, len(data)):
        window = data[i - period + 1: i + 1]
        result.append(sum(w * v for w, v in zip(weights, window)) / wsum)
    return result


def _hma(data, period):
    """Hull Moving Average — dusuk gecikmeli MA."""
    half = period // 2
    sqrt_p = int(math.sqrt(period))
    wma_half = _wma(data, half)
    wma_full = _wma(data, period)
    if not wma_full or not wma_half:
        return []
    offset = len(wma_half) - len(wma_full)
    raw = [2.0 * wma_half[i + offset] - wma_full[i] for i in range(len(wma_full))]
    return _wma(raw, sqrt_p)


def calc_ssl_hybrid(closes, opens, highs, lows,
                    basis_len=60, ssl_len=10, atr_len=6, atr_mult=3.5):
    """
    SSL Hybrid indikatoru.
    Donus: (ssl_direction, price_vs_basis)
      ssl_direction: 1=bullish, -1=bearish, 0=yetersiz veri
      price_vs_basis: 1=fiyat ustte, -1=fiyat altta, 0=bilinmiyor
    """
    n = len(closes)
    if n < basis_len + ssl_len:
        return 0, 0

    # 1) Basis: HMA of closes
    basis = _hma(closes, basis_len)
    if not basis:
        return 0, 0

    # Hizala: basis dizisi kisa, kapanislara hizala
    basis_offset = n - len(basis)

    # 2) SSL Channel: SMA(close) vs SMA(open)
    if n < ssl_len:
        return 0, 0
    ssl_close = sum(closes[-ssl_len:]) / ssl_len
    ssl_open = sum(opens[-ssl_len:]) / ssl_len
    ssl_dir = 1 if ssl_close > ssl_open else -1

    # 3) ATR for bands
    tr_vals = []
    for i in range(max(1, n - atr_len), n):
        hl = highs[i] - lows[i]
        hc = abs(highs[i] - closes[i - 1])
        lc = abs(lows[i] - closes[i - 1])
        tr_vals.append(max(hl, hc, lc))
    atr_val = sum(tr_vals) / len(tr_vals) if tr_vals else 0

    # 4) Basis son deger
    basis_val = basis[-1]

    # 5) Fiyat vs basis
    price = closes[-1]
    pvb = 1 if price >= basis_val else -1

    return ssl_dir, pvb


# =====================================================================
# 2c. QQE INDIKATORU (Quantitative Qualitative Estimation)
# =====================================================================

def calc_qqe(closes, rsi_period=14, sf=5, qqe_factor=3.0):
    """
    QQE: RSI uzerinde ATR trailing stop.
    Donus: (trend, rsi_ma_val)
      trend: 1=bullish, -1=bearish, 0=yetersiz veri
      rsi_ma_val: son smoothing RSI degeri (0-100)
    """
    n = len(closes)
    if n < rsi_period * 3:
        return 0, 50.0

    # 1) Wilder RSI
    gains, losses = [], []
    for i in range(1, n):
        d = closes[i] - closes[i - 1]
        gains.append(max(d, 0))
        losses.append(max(-d, 0))

    ag = sum(gains[:rsi_period]) / rsi_period
    al = sum(losses[:rsi_period]) / rsi_period

    rsi_vals = [50.0] * rsi_period  # seed
    for i in range(rsi_period, len(gains)):
        ag = (ag * (rsi_period - 1) + gains[i]) / rsi_period
        al = (al * (rsi_period - 1) + losses[i]) / rsi_period
        if al == 0:
            rsi_vals.append(100.0)
        else:
            rsi_vals.append(100.0 - (100.0 / (1.0 + ag / al)))

    # 2) RSI smoothing (EMA with sf)
    alpha = 1.0 / sf
    rsi_ma = [rsi_vals[0]]
    for i in range(1, len(rsi_vals)):
        rsi_ma.append(rsi_ma[-1] * (1 - alpha) + rsi_vals[i] * alpha)

    # 3) ATR of RSI (Wilder smooth)
    wilders_p = 2 * rsi_period - 1
    alpha_w = 1.0 / wilders_p
    atr_rsi = [0.0]
    for i in range(1, len(rsi_ma)):
        atr_rsi.append(abs(rsi_ma[i - 1] - rsi_ma[i]))

    ma_atr_rsi = [atr_rsi[0]]
    for i in range(1, len(atr_rsi)):
        ma_atr_rsi.append(ma_atr_rsi[-1] * (1 - alpha_w) + atr_rsi[i] * alpha_w)

    # Double smooth + scale
    dar = [ma_atr_rsi[0] * qqe_factor]
    for i in range(1, len(ma_atr_rsi)):
        val = dar[-1] * (1 - alpha_w) + ma_atr_rsi[i] * alpha_w
        dar.append(val * qqe_factor)

    # 4) Trailing stop bands
    start = rsi_period + 1
    if start >= len(rsi_ma):
        return 0, 50.0

    longband = [0.0] * len(rsi_ma)
    shortband = [0.0] * len(rsi_ma)
    trend = [0] * len(rsi_ma)

    longband[start] = rsi_ma[start] - dar[start]
    shortband[start] = rsi_ma[start] + dar[start]
    trend[start] = 1

    for i in range(start + 1, len(rsi_ma)):
        newlong = rsi_ma[i] - dar[i]
        newshort = rsi_ma[i] + dar[i]

        # Long band ratchet
        if rsi_ma[i - 1] > longband[i - 1] and longband[i - 1] > newlong:
            longband[i] = longband[i - 1]
        else:
            longband[i] = newlong

        # Short band ratchet
        if rsi_ma[i - 1] < shortband[i - 1] and shortband[i - 1] < newshort:
            shortband[i] = shortband[i - 1]
        else:
            shortband[i] = newshort

        # Trend
        if trend[i - 1] == 1:
            trend[i] = -1 if rsi_ma[i] < longband[i] else 1
        else:
            trend[i] = 1 if rsi_ma[i] > shortband[i] else -1

    return trend[-1], rsi_ma[-1]


# =====================================================================
# 3. SINYAL DEGERLENDIRME
# =====================================================================

def skor_hesapla(closes, opens, highs, lows, price):
    """Tek bir sembol icin sinyal skoru hesapla. Donus: (skor, karar, gerekceler)"""
    if len(closes) < 30:
        return 0, "BEKLE", ["Yetersiz veri"]

    e20 = calc_ema(closes, 20)
    e50 = calc_ema(closes, 50)
    e200 = calc_ema(closes, 200) if len(closes) >= 200 else None
    r = calc_rsi(closes, 14)
    macd_v, macd_sig, hist = calc_macd(closes)
    adx_v, dp, dm = calc_adx(highs, lows, closes)
    bb_u, bb_mid, bb_l = calc_bollinger(closes)

    # Yeni indikatorler: SSL Hybrid ve QQE
    ssl_dir, pvb = calc_ssl_hybrid(closes, opens, highs, lows)
    qqe_trend, qqe_rsi = calc_qqe(closes)

    reasons = []
    score = 0

    # EMA (max 25)
    ema_above = 0
    for ev in [e20, e50, e200]:
        if ev is not None:
            if price >= ev:
                score += 8
                ema_above += 1
            else:
                score -= 4
    if ema_above >= 2:
        reasons.append(f"EMA {ema_above}/3 ustunde")
    elif ema_above <= 1:
        reasons.append(f"EMA {ema_above}/3 ustunde")

    # RSI (max 15)
    if r is not None:
        if r < 30:
            score += 15
            reasons.append(f"RSI {r} asiri satis")
        elif r < 40:
            score += 8
            reasons.append(f"RSI {r} dusuk")
        elif r < 45:
            score += 4
        elif r < 55:
            pass  # notr bolge — puan yok
        elif r > 70:
            score -= 15
            reasons.append(f"RSI {r} asiri alim")
        elif r > 60:
            score -= 8
            reasons.append(f"RSI {r} yuksek")

    # MACD (max 12)
    if macd_v is not None and macd_sig is not None:
        if macd_v > 0 and macd_v > macd_sig:
            score += 12
            reasons.append("MACD guclu al")
        elif macd_v > macd_sig:
            score += 6
        elif macd_v < macd_sig:
            score -= 10
            reasons.append("MACD sat baskisi")

    # ADX (max 15)
    if adx_v is not None:
        if adx_v >= 25:
            if dp >= dm:
                score += 15
                reasons.append(f"ADX {adx_v} guclu yukselis")
            else:
                score -= 12
                reasons.append(f"ADX {adx_v} guclu dusus")
        elif adx_v >= 20 and dp >= dm:
            score += 6

    # Bollinger (max 12)
    if bb_l is not None and bb_u is not None:
        if price <= bb_l * 1.02:
            score += 12
            reasons.append("Bollinger alt bandi — destek")
        elif price >= bb_u * 0.98:
            score -= 12
            reasons.append("Bollinger ust bandi — direnc")

    # SSL Hybrid (max 15 — yeni)
    if ssl_dir != 0:
        if ssl_dir == 1 and pvb == 1:
            score += 15
            reasons.append("SSL Hybrid: bullish + fiyat ustte")
        elif ssl_dir == 1:
            score += 6
            reasons.append("SSL Hybrid: bullish")
        elif ssl_dir == -1 and pvb == -1:
            score -= 15
            reasons.append("SSL Hybrid: bearish + fiyat altta")
        elif ssl_dir == -1:
            score -= 6
            reasons.append("SSL Hybrid: bearish")

    # QQE (max 15 — yeni)
    if qqe_trend != 0:
        if qqe_trend == 1:
            score += 15
            reasons.append(f"QQE: bullish (RSI:{qqe_rsi:.0f})")
        else:
            score -= 15
            reasons.append(f"QQE: bearish (RSI:{qqe_rsi:.0f})")

    score = max(-100, min(100, score))

    if score >= AL_ESIK:
        karar = "AL"
    elif score <= SAT_ESIK:
        karar = "SAT"
    else:
        karar = "BEKLE"

    return score, karar, reasons


# =====================================================================
# 4. VERI CEKME — KRIPTO
# =====================================================================

def fetch_all_binance_24hr():
    """Binance tum 24hr ticker verisini tek istekte cek (cok hizli)."""
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None


def fetch_klines(symbol, interval="15m", limit=100):
    """Tek sembol icin mum verisi cek. Donus: (closes, opens, highs, lows)"""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        closes = [float(k[4]) for k in raw]
        opens = [float(k[1]) for k in raw]
        highs = [float(k[2]) for k in raw]
        lows = [float(k[3]) for k in raw]
        return closes, opens, highs, lows
    except Exception:
        return None, None, None, None


def kripto_24hr_ozet(ticker_data, semboller):
    """24hr ticker'dan sembol bilgilerini cikar."""
    sonuclar = {}
    for t in ticker_data:
        s = t.get("symbol", "")
        if s in semboller:
            try:
                sonuclar[s] = {
                    "price": float(t["lastPrice"]),
                    "change": float(t["priceChangePercent"]),
                    "volume": float(t["quoteVolume"]),
                    "high": float(t["highPrice"]),
                    "low": float(t["lowPrice"]),
                }
            except (ValueError, KeyError):
                pass
    return sonuclar


# =====================================================================
# 5. VERI CEKME — HISSE
# =====================================================================

def fetch_hisse_batch(semboleler):
    """yfinance ile toplu hisse verisi cek (batch download)."""
    import yfinance as yf
    import warnings
    import contextlib
    import io
    warnings.filterwarnings("ignore")
    try:
        # yfinance uyarilarini ve hata mesajlarini bastir
        with contextlib.redirect_stderr(io.StringIO()):
            df = yf.download(
                semboleler,
                period="6mo",
                interval="1d",
                group_by="ticker",
                threads=True,
                progress=False,
            )
        return df
    except Exception:
        return None


def hisse_veri_cikar(df, sembol, tek_sembol=False):
    """Batch download sonucu tek sembol icin veri cikar. Donus: (close, open, high, low, price, change)"""
    try:
        if tek_sembol:
            close = df["Close"].dropna().tolist()
            opn = df["Open"].dropna().tolist()
            high = df["High"].dropna().tolist()
            low = df["Low"].dropna().tolist()
        else:
            if sembol not in df.columns.get_level_values(0):
                return None, None, None, None, None, None
            close = df[sembol]["Close"].dropna().tolist()
            opn = df[sembol]["Open"].dropna().tolist()
            high = df[sembol]["High"].dropna().tolist()
            low = df[sembol]["Low"].dropna().tolist()

        if len(close) < 30:
            return None, None, None, None, None, None

        price = close[-1]
        prev = close[-2]
        change = round(((price - prev) / prev) * 100, 2) if prev else 0
        return close, opn, high, low, price, change
    except Exception:
        return None, None, None, None, None, None


# =====================================================================
# 6. SES UYARISI
# =====================================================================

def cal_alarm_sesi():
    """Alarm sesi: yumusak ve net."""
    for f, d in [(1200, 200), (1000, 200), (1200, 200)]:
        winsound.Beep(f, d)
        time.sleep(0.08)
    time.sleep(0.15)
    for f, d in [(1400, 300), (1200, 300)]:
        winsound.Beep(f, d)
        time.sleep(0.08)


# =====================================================================
# 7. FORMAT YARDIMCILARI
# =====================================================================

def fmt_fiyat(p):
    if p >= 1000:
        return f"{p:,.2f}"
    elif p >= 1:
        return f"{p:.4f}"
    elif p >= 0.001:
        return f"{p:.6f}"
    return f"{p:.8f}"


def sparkline(data, w=30):
    if not data or len(data) < 3:
        return ""
    seg = data[-w:]
    mn, mx = min(seg), max(seg)
    if mx == mn:
        return "-" * len(seg)
    c = "_.-o*O@#"
    return "".join(c[int((v - mn) / (mx - mn) * (len(c) - 1))] for v in seg)


# =====================================================================
# 8. KRIPTO TARAMA (CANLI SINYAL BOTU)
# =====================================================================

def tarama_kripto(interval="15m"):
    """Canli kripto sinyal botu — surekli tara, sinyalde alarm cal."""
    periyot_adi = KRIPTO_INTERVAL_LABELS.get(interval, interval)
    kontrol_sn = KONTROL_ARALIK_KRIPTO
    alert_gecmisi = {}
    toplam_sinyal = 0
    dongu = 0
    baslangic = time.time()

    # === BASLANGIC BANNERI ===
    print()
    print("  ============================================")
    print("       CRYPTO SIGNAL BOT - OTOSINYAL")
    print("  ============================================")
    print(f"   Semboller   : {len(TARANACAK_KRIPTO)} adet (Binance)")
    print(f"   Periyot     : {periyot_adi}")
    print(f"   Tarama      : her {kontrol_sn} sn")
    print(f"   Esik        : AL > {AL_ESIK} (guclu sinyal)")
    print(f"   Indikatorler: EMA/RSI/MACD/ADX/BB/SSL/QQE")
    print(f"   Alarm       : sesli (bip)")
    print("  ============================================")
    print()
    print("  Bot baslatildi. Guclu AL sinyalleri bekleniyor...")
    print("  Durdurmak icin Ctrl+C")
    print()

    while True:
        dongu += 1
        dongu_baslangic = time.time()
        simdi = time.time()
        gecen = int(simdi - baslangic)
        saat = gecen // 3600
        dak = (gecen % 3600) // 60
        san = gecen % 60
        sure = f"{saat:02d}:{dak:02d}:{san:02d}"
        zaman = datetime.datetime.now().strftime("%H:%M:%S")

        # 1) Tum 24hr ticker verisini tek seferde cek
        try:
            ticker = fetch_all_binance_24hr()
        except Exception:
            ticker = None
        if ticker is None:
            print(f"  [{zaman}] Binance baglanti hatasi, {kontrol_sn}s sonra tekrar...")
            time.sleep(kontrol_sn)
            continue

        ozet = kripto_24hr_ozet(ticker, TARANACAK_KRIPTO)

        # 2) Her sembol icin mum cek + skor hesapla
        bulunanlar = []
        basarili = 0
        for sembol in TARANACAK_KRIPTO:
            bilgi = ozet.get(sembol)
            if not bilgi:
                continue

            closes, opens, highs, lows = fetch_klines(sembol, interval, 100)
            if closes is None or len(closes) < 30:
                continue

            basarili += 1
            skor, karar, gerekceler = skor_hesapla(closes, opens, highs, lows, bilgi["price"])

            # Sadece guclu AL sinyallerini topla (SAT gosterme)
            if karar == "AL":
                son_alarm = alert_gecmisi.get(sembol, 0)
                if (simdi - son_alarm) >= ALERT_COOLDOWN:
                    bulunanlar.append({
                        "sembol": sembol,
                        "karar": karar,
                        "skor": skor,
                        "gerekceler": gerekceler,
                        "fiyat": bilgi["price"],
                        "degisim": bilgi["change"],
                        "sparkline": sparkline(closes),
                    })
                    alert_gecmisi[sembol] = simdi
                    toplam_sinyal += 1

            time.sleep(0.05)

        # 3) Sonuclari goster — SADECE AL sinyalleri
        if bulunanlar:
            bulunanlar.sort(key=lambda x: x["skor"], reverse=True)

            for b in bulunanlar:
                print("  ┌──────────────────────────────────────────────┐")
                print(f"  │  🟢 AL SINYALI  —  {b['sembol']:<24s} │")
                print("  ├──────────────────────────────────────────────┤")
                print(f"  │  Fiyat   : {fmt_fiyat(b['fiyat']):>12s} USDT               │")
                deg = f"{b['degisim']:+.1f}%"
                print(f"  │  24s Deg : {deg:>10s}                    │")
                print(f"  │  Skor    : {b['skor']:+4d}/100                     │")
                if b["sparkline"]:
                    print(f"  │  Grafik  : {b['sparkline']:<34s} │")
                print(f"  │  Gerekce : {b['gerekceler'][0]:<34s} │")
                if len(b["gerekceler"]) > 1:
                    print(f"  │            {b['gerekceler'][1]:<34s} │")
                if len(b["gerekceler"]) > 2:
                    print(f"  │            {b['gerekceler'][2]:<34s} │")
                print(f"  │  [{zaman}] Tarama #{dongu} | Toplam: {toplam_sinyal}       │")
                print("  └──────────────────────────────────────────────┘")
                print()

            cal_alarm_sesi()
        else:
            print(f"  [{zaman}] #{dongu} | {basarili} sembol tarandi | Sinyal yok")

        gecen_dongu = time.time() - dongu_baslangic
        bekleme = max(5, kontrol_sn - gecen_dongu)
        time.sleep(bekleme)


# =====================================================================
# 9. HISSE TARAMA (TEK SEFERLIK — sonucu goster, bitir)
# =====================================================================

def tarama_hisse():
    """Tum BIST hisselerini tek seferde tara, tavan yapacaklari goster."""
    semboller = list(dict.fromkeys(TARANACAK_HISSE))
    zaman = datetime.datetime.now().strftime("%H:%M:%S")

    # === BASLANGIC ===
    print()
    print("  ============================================")
    print("       BIST HISSE TARAMA - OTOSINYAL")
    print("  ============================================")
    print(f"   Hisse sayisi : {len(semboller)} adet (BIST)")
    print(f"   Indikatorler : EMA/RSI/MACD/ADX/BB/SSL/QQE")
    print("  ============================================")
    print()
    print(f"  [{zaman}] Tarama baslatiliyor... ({len(semboller)} hisse)")
    print()

    # Toplu veri cek
    df = fetch_hisse_batch(semboller)
    if df is None or df.empty:
        print("  ❌ Veri alinamadi! Internet baglantisi veya Yahoo Finance hatasi.")
        return

    bulunanlar = []
    basarili = 0
    for sembol in semboller:
        close, opn, high, low, price, change = hisse_veri_cikar(df, sembol, tek_sembol=False)
        if close is None:
            continue

        basarili += 1
        skor, karar, gerekceler = skor_hesapla(close, opn, high, low, price)

        # Sadece AL sinyallerini topla (tavan potansiyeli)
        if skor > 0:
            bulunanlar.append({
                "sembol": sembol,
                "skor": skor,
                "gerekceler": gerekceler,
                "fiyat": price,
                "degisim": change,
                "sparkline": sparkline(close),
            })

    bitis = datetime.datetime.now().strftime("%H:%M:%S")

    # Skora gore sirala — en yuksek skor ustte
    bulunanlar.sort(key=lambda x: x["skor"], reverse=True)

    # === RAPOR — SADECE ILK 5 ===
    print()
    print("  ══════════════════════════════════════════════")
    print(f"   TAVAN TARAMA  |  {basarili} hisse tarandi")
    print(f"   Baslama: {zaman}  |  Bitis: {bitis}")
    print("  ══════════════════════════════════════════════")

    if not bulunanlar:
        print()
        print("  ❌ Tavan potansiyeli tespit edilemedi.")
        print("  Tum hisseler durgun.")
        print("  💡 Baska bir zamanda tekrar kontrol edin.")
        print("  ══════════════════════════════════════════════")
        return

    # En guclu 5 hisseyi goster
    top5 = bulunanlar[:5]

    print()
    print("  🟢 TAVAN YAPABILECEK HISSELER (TOP 5)")
    print("  ─────────────────────────────────────")

    for i, b in enumerate(top5, 1):
        sembol_kisa = b["sembol"].replace(".IS", "")
        deg = f"{b['degisim']:+.1f}%"

        # Guven gostergesi
        if b["skor"] >= 70:
            guven = "⭐⭐⭐ GUCLU"
        elif b["skor"] >= 55:
            guven = "⭐⭐ ORTA"
        else:
            guven = "⭐ ZAYIF"

        print()
        print(f"   {i}. {sembol_kisa}  —  {guven}")
        print(f"      Skor  : {b['skor']:+d}/100")
        print(f"      Fiyat : {fmt_fiyat(b['fiyat'])} TL  |  24s: {deg}")
        if b["sparkline"]:
            print(f"      Grafik: {b['sparkline']}")
        for g in b["gerekceler"][:3]:
            print(f"        {g}")

    print()
    print("  ══════════════════════════════════════════════")
    print(f"  💡 {len(bulunanlar)} hissede yuksek alim potansiyeli tespit edildi")
    print("  📌 Strateji: 3 tavan之后 sat")
    print("  ⚠️  Bu bir yatirim tavsiyesi degildir.")
    print("  ══════════════════════════════════════════════")
    print()

    # Alarm sesi
    cal_alarm_sesi()


# =====================================================================
# 10. ANA GIRIS
# =====================================================================

def main():
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help", "-?"):
        print(__doc__.strip())
        return

    mod = args[0].lower()

    if mod == "kripto":
        # Opsiyonel periyot
        interval = "15m"
        if len(args) >= 2:
            user_int = args[1].strip().lower()
            if user_int in KRIPTO_INTERVALS:
                interval = KRIPTO_INTERVALS[user_int]
            else:
                print(f"  Gecersiz periyot: {user_int}. Varsayilan: 15m")
        tarama_kripto(interval)

    elif mod in ("hisse", "bist"):
        tarama_hisse()

    else:
        print(f"  Gecersiz mod: {mod}")
        print()
        print("  Kullanim:")
        print("    otosinyal kripto         # Tum kriptolari tara")
        print("    otosinyal kripto 15m     # Kripto, 15dk mumlarla")
        print("    otosinyal kripto 1h      # Kripto, 1 saatlik")
        print("    otosinyal hisse          # Tum BIST hisselerini tara")
        print("    otosinyal bist           # hisse ile ayni")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  👋 Bot kapatildi. Iyi gunler!")
        sys.exit(0)
