# Copyright (c) 2026 ilter2014
# CmdTools - Windows komut satırı araç kutusu
# GitHub: github.com/ilter2014/CmdTools
#
# Bu dosya CmdTools projesinin bir parçasıdır.
# İzin alınmadan kopyalanması, dağıtılması veya değiştirilmesi yasaktır.
#

# -*- coding: utf-8 -*-
"""
ytai.py — YtAI: Doğal Dil Finansal Yapay Zeka Asistanı
=======================================================
Kullanım: YtAI Soru: [Herhangi bir finansal soru]

Örnek:
  YtAI Soru: Manas hissesi hakkında ne düşünüyorsun?
  YtAI Soru: BTC şuan alınır mı?
  YtAI Soru: THYAO teknik analizi nasıl?
  YtAI Soru: AAPL almak için uygun zaman mı?
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
import re
import math
import urllib.request
import textwrap
import warnings
warnings.filterwarnings("ignore")

# =====================================================================
# 1. SABİTLER VE TANIMLAR
# =====================================================================

# Bilinen ABD hisseleri
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

# Kripto kısa ad → tam sembol eşlemesi
SHORT_CRYPTO_MAP = {
    "btc": "BTCUSDT", "bitcoin": "BTCUSDT",
    "eth": "ETHUSDT", "ethereum": "ETHUSDT",
    "sol": "SOLUSDT", "solana": "SOLUSDT",
    "xrp": "XRPUSDT", "ripple": "XRPUSDT",
    "ada": "ADAUSDT", "cardano": "ADAUSDT",
    "doge": "DOGEUSDT", "dogecoin": "DOGEUSDT",
    "dot": "DOTUSDT", "polkadot": "DOTUSDT",
    "matic": "POLUSDT", "avax": "AVAXUSDT", "avalanche": "AVAXUSDT",
    "link": "LINKUSDT", "chainlink": "LINKUSDT",
    "uni": "UNIUSDT", "uniswap": "UNIUSDT",
    "atom": "ATOMUSDT", "ltc": "LTCUSDT", "litecoin": "LTCUSDT",
    "bch": "BCHUSDT", "near": "NEARUSDT",
    "apt": "APTUSDT", "aptos": "APTUSDT",
    "sui": "SUIUSDT", "arb": "ARBUSDT", "arbitrum": "ARBUSDT",
    "op": "OPUSDT", "optimism": "OPUSDT",
    "inj": "INJUSDT", "injective": "INJUSDT",
    "fil": "FILUSDT", "filecoin": "FILUSDT",
    "ftm": "FTMUSDT", "fantom": "FTMUSDT",
    "algo": "ALGOUSDT", "rune": "RUNEUSDT",
    "pendle": "PENDLEUSDT", "ondo": "ONDOUSDT",
    "tia": "TIAUSDT", "sei": "SEIUSDT",
    "pepe": "1000PEPEUSDT", "shib": "1000SHIBUSDT", "shiba": "1000SHIBUSDT",
}

# Bilinen BIST hisseleri (sık işlem görenler) — sembol tespiti için
KNOWN_BIST_STOCKS = {
    "THYAO", "EREGL", "AKBNK", "GARAN", "ISCTR", "YKBNK", "HALKB", "VAKBN",
    "KCHOL", "SAHOL", "TUPRS", "PGSUS", "TAVHL", "TCELL", "TTKOM",
    "ASELS", "SISE", "BIMAS", "MGROS", "SOKM", "KOZAA", "KOZAL",
    "HEKTS", "KRDMD", "OTKAR", "TOASO", "FROTO", "DOAS", "TTRAK",
    "MANAS", "ALARK", "TRKCM", "GOZDE", "ISGYO", "ECZYT",
    "ENJSA", "ENKAI", "SODA", "ULKER", "VESTL", "ZOREN",
    "AYEN", "AKSA", "ALGYO", "ARCLK", "BRISA", "CCOLA",
    "CEMTS", "CLEBI", "DOGUB", "ECILC", "EGEEN", "GOLTS",
    "GSDHO", "GUSGR", "IHLAS", "IPEKE", "ISFIN", "ISKUR",
    "IZMDC", "KARTN", "KARYE", "KLGYO", "KONYA", "KORDS",
    "LOGO", "MAVI", "METRO", "MIPAZ", "NETAS", "NTHOL",
    "ODAS", "OYAKC", "PETKM", "POLHO", "PRKME", "SASA",
    "SELEC", "SKBNK", "SNGYO", "TATGD", "TMSN", "TSKB",
    "VESBE", "YATAS", "YEOTK",
}


def normalize_and_detect(symbol: str) -> tuple:
    """Sembolü normalize et ve türünü döndür: (normalized_symbol, type, display_name)"""
    s = symbol.upper().strip()

    if s.endswith("USDT"):
        return s, "coin", s
    if s.endswith(".IS"):
        return s, "hisse", s

    if s in SHORT_CRYPTO_MAP or s.lower() in SHORT_CRYPTO_MAP:
        full = SHORT_CRYPTO_MAP.get(s.lower(), SHORT_CRYPTO_MAP.get(s, s + "USDT"))
        return full, "coin", s

    if s in KNOWN_US_STOCKS:
        return s, "hisse", s

    if s in KNOWN_BIST_STOCKS:
        bist = s + ".IS"
        return bist, "hisse", s

    # Varsayılan: BIST olarak dene
    return s + ".IS", "hisse", s


# =====================================================================
# 2. SEMBOL TESPİT (Doğal Dil İçinden)
# =====================================================================

# Türkçe durak kelimeleri
STOP_WORDS = {
    "bir", "bu", "şu", "o", "ve", "veya", "ile", "için", "gibi",
    "kadar", "sonra", "önce", "üzerine", "altında", "arasında",
    "ama", "ancak", "fakat", "çünkü", "eğer", "yani", "oysa",
    "de", "da", "mi", "mu", "mı", "ki", "acaba", "acaba",
    "nasıl", "neden", "niye", "ne", "nerede", "nereden",
    "hakkında", "ile", "göre", "dair", "ilgili",
    "düşünüyorsun", "düşünürsün", "bak", "bakar", "baksana",
    "analizi", "analiz", "teknik", "temel",
    "alınır", "satılır", "alınmalı", "satılmalı", "tutulur",
    "yorumla", "yorum", "değerlendir", "değerlendirme",
    "söyle", "anlat", "açıkla", "izah", "ettir",
    "sence", "size", "sana", "bana", "ona",
    "şuan", "şimdi", "bugün", "yarın", "gelecek",
    "hissesi", "hisse", "coin", "kripto", "parası",
    "soru", "sorun", "cevap", "cevapla",
    "lütfen", "yardım", "yardımcı", "olur", "musun",
    "ben", "sen", "o", "biz", "siz", "onlar",
    "mıyım", "mısın", "mı", "mu", "mi",
    "diyelim", "mesela", "örnek", "örneğin",
}

# Finansal varlık ipuçları — kelimenin yanında "hissesi", "coin" varsa o kelime semboldür
ASSET_HINT_WORDS = {"hissesi", "hisse", "coin", "kripto", "parası", "token", "borsası"}


def extract_symbol_from_question(question: str) -> tuple:
    """
    Doğal dil sorusundan finansal varlık sembolünü tespit et.
    Dönüş: (normalized_symbol, type, display_name, raw_match) veya (None, None, None, None)
    """
    cleaned = re.sub(r'[^\w\s.İÜĞÖÇŞıüğöçş]', ' ', question)
    words = [w.strip().upper() for w in cleaned.split() if w.strip()]

    if not words:
        return None, None, None, None

    # Hint kontrolü: "X hissesi", "X coin" kalıpları
    for i, w in enumerate(words):
        if w.lower() in ASSET_HINT_WORDS and i > 0:
            candidate = words[i - 1]
            # Candidate durak kelimesi değilse sembol olabilir
            if candidate.lower() not in STOP_WORDS and len(candidate) >= 2:
                try:
                    sym, tp, dsp = normalize_and_detect(candidate)
                    return sym, tp, dsp, candidate
                except Exception:
                    pass

    # Doğrudan eşleşme: tüm kelimeleri normalize_and_detect ile dene
    for w in words:
        if w.lower() in STOP_WORDS or len(w) < 2:
            continue
        try:
            sym, tp, dsp = normalize_and_detect(w)
            # Başarılı eşleşme kontrolü
            if tp == "coin" or w in KNOWN_US_STOCKS or w in KNOWN_BIST_STOCKS or w.endswith("USDT") or w.endswith(".IS"):
                return sym, tp, dsp, w
        except Exception:
            pass

    return None, None, None, None


# =====================================================================
# 3. VERİ ÇEKME
# =====================================================================

def fetch_crypto_klines(symbol: str, interval: str = "1h", limit: int = 100):
    """Binance API'den OHLCV mum verileri çek."""
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = json.loads(resp.read().decode("utf-8"))
        closes = [float(k[4]) for k in raw]
        highs = [float(k[2]) for k in raw]
        lows = [float(k[3]) for k in raw]
        volumes = [float(k[5]) for k in raw]
        return closes, highs, lows, volumes
    except Exception:
        return None, None, None, None


def fetch_stock_data(symbol: str):
    """yfinance ile hisse verisi çek."""
    import yfinance as yf
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="3mo", interval="1d")
        if df.empty or len(df) < 10:
            return None, None, None, None
        return (
            df["Close"].tolist(),
            df["High"].tolist(),
            df["Low"].tolist(),
            df["Volume"].tolist(),
        )
    except Exception:
        return None, None, None, None


def fetch_summary(symbol: str, data_type: str) -> dict:
    """
    Sembol için özet veri topla: fiyat, değişim, indikatörler.
    Dönüş: dict veya None
    """
    if data_type == "coin":
        # 24hr ticker
        url_ticker = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        try:
            req = urllib.request.Request(url_ticker, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                tdata = json.loads(resp.read().decode("utf-8"))
            price = float(tdata["lastPrice"])
            change_pct = float(tdata["priceChangePercent"])
            high24 = float(tdata["highPrice"])
            low24 = float(tdata["lowPrice"])
            vol24 = float(tdata["volume"])
        except Exception:
            return None

        # Mum verileri
        closes, highs, lows, volumes = fetch_crypto_klines(symbol, "1h", 100)
        currency = "USDT"
    else:
        import yfinance as yf
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="3mo", interval="1d")
            if df.empty:
                return None
            price = float(df["Close"].iloc[-1])
            prev_close = float(df["Close"].iloc[-2]) if len(df) >= 2 else price
            change_pct = round(((price - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0
            high24 = float(df["High"].iloc[-1])
            low24 = float(df["Low"].iloc[-1])
            vol24 = float(df["Volume"].iloc[-1])
            closes = df["Close"].tolist()
            highs = df["High"].tolist()
            lows = df["Low"].tolist()
            volumes = df["Volume"].tolist()
            currency = "TL" if symbol.endswith(".IS") else "USD"
        except Exception:
            return None

    if not closes or len(closes) < 14:
        return None

    # İndikatörler
    ema20 = calculate_ema(closes, 20)
    ema50 = calculate_ema(closes, 50)
    rsi = calculate_rsi(closes, 14)
    macd_v, signal_v, hist_v = calculate_macd(closes)

    ema20_last = ema20[-1] if ema20 else None
    ema50_last = ema50[-1] if ema50 else None

    # Destek/Direnç
    support = min(lows[-20:]) if len(lows) >= 20 else min(lows)
    resistance = max(highs[-20:]) if len(highs) >= 20 else max(highs)

    return {
        "price": price,
        "change_pct": change_pct,
        "high24": high24,
        "low24": low24,
        "vol24": vol24,
        "currency": currency,
        "closes": closes,
        "highs": highs,
        "lows": lows,
        "volumes": volumes,
        "ema20": round(ema20_last, 2) if ema20_last else None,
        "ema50": round(ema50_last, 2) if ema50_last else None,
        "rsi": round(rsi, 1) if rsi else None,
        "macd": round(macd_v, 4) if macd_v else None,
        "macd_signal": round(signal_v, 4) if signal_v else None,
        "support": round(support, 2),
        "resistance": round(resistance, 2),
    }


# =====================================================================
# 4. İNDİKATÖR HESAPLAMALARI
# =====================================================================

def calculate_ema(prices, period):
    if len(prices) < period:
        return None
    k = 2.0 / (period + 1)
    ema = []
    sma = sum(prices[:period]) / period
    ema.append(sma)
    for price in prices[period:]:
        ema.append(price * k + ema[-1] * (1.0 - k))
    return ema


def calculate_rsi(prices, period=14):
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
    return 100.0 - (100.0 / (1.0 + rs))


def calculate_macd(prices, fast=12, slow=26, signal=9):
    if len(prices) < slow + signal:
        return None, None, None
    ema_fast = calculate_ema(prices, fast)
    ema_slow = calculate_ema(prices, slow)
    if ema_fast is None or ema_slow is None:
        return None, None, None
    offset = len(ema_fast) - len(ema_slow)
    ema_fast_aligned = ema_fast[offset:]
    macd_line = [f - s for f, s in zip(ema_fast_aligned, ema_slow)]
    signal_line = calculate_ema(macd_line, signal)
    if signal_line is None:
        return macd_line[-1], None, None
    sig_offset = len(macd_line) - len(signal_line)
    macd_trimmed = macd_line[sig_offset:]
    histogram = [m - s for m, s in zip(macd_trimmed, signal_line)]
    return macd_trimmed[-1], signal_line[-1], histogram[-1]


# =====================================================================
# 5. ASCII GRAFİK (SPARKLINE)
# =====================================================================

def make_sparkline(data, width=50):
    """Sayı dizisinden ters yönde (sağdan sola) sparkline çubuk grafiği oluşturur."""
    if not data or len(data) < 3:
        return ""
    # Son 'width' kadar veriyi al
    segment = data[-width:] if len(data) > width else data
    mn, mx = min(segment), max(segment)
    if mx == mn:
        return "▁" * len(segment)
    chars = "▁▂▃▄▅▆▇█"
    result = ""
    for val in segment:
        idx = int((val - mn) / (mx - mn) * (len(chars) - 1))
        idx = max(0, min(idx, len(chars) - 1))
        result += chars[idx]
    return result


def make_price_sparkline(closes, width=50):
    """
    Fiyat grafiğini fiyat etiketleriyle birlikte çiz.
    Dönüş: (sparkline_text, label_left, label_right)
    """
    if not closes or len(closes) < 3:
        return "", "", ""

    segment = closes[-width:] if len(closes) > width else closes
    mn, mx = min(segment), max(segment)
    mid = (mn + mx) / 2.0

    spark = make_sparkline(closes, width)
    # Fiyat etiketleri
    label_right = f"{mx:.2f}" if mx >= 1 else f"{mx:.6f}"
    label_left = f"{mn:.2f}" if mn >= 1 else f"{mn:.6f}"
    label_mid = f"{mid:.2f}" if mid >= 1 else f"{mid:.6f}"

    full_chart = f" {label_right}  {spark}  {label_left}"
    return full_chart, label_left, label_right


def make_bar_chart(closes, width=40, height=7):
    """
    ASCII çubuk grafiği — plotext alternatifi, hafif ve bağımlılıksız.
    Yukarıdan aşağıya çizilen dikey çubuklar.
    """
    if not closes or len(closes) < 3:
        return ""

    segment = closes[-min(width, len(closes)):]
    mn, mx = min(segment), max(segment)
    if mx == mn:
        return " [" + "▬" * min(len(segment), 40) + "]"

    lines = []
    n = len(segment)
    step = max(1, n // 40)  # max 40 sütun
    sampled = segment[::step][:40]

    for row in range(height, 0, -1):
        threshold = mn + (mx - mn) * (row / height)
        bar = ""
        for val in sampled:
            if val >= threshold:
                bar += "█"
            else:
                bar += " "
        label = f"{mn + (mx - mn) * (row / height):.1f}" if row % 2 == 0 or row == height else ""
        lines.append(f" {label:>8s} │{bar}│")

    # Alt eksen
    lines.append(f"          └{'─' * len(sampled)}┘")
    return "\n".join(lines)


# =====================================================================
# 6. AI MOTORU (ÜCRETSİZ — API ANAHTARI GEREKMEZ)
# =====================================================================

def _query_g4f_provider(model: str, messages: list, client) -> str | None:
    """Tek bir g4f sorgusu dene. Başarılı olursa metin döndür."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            timeout=30,
        )
        if response and response.choices:
            text = response.choices[0].message.content
            if text and text.strip():
                return text.strip()
    except Exception:
        pass
    return None


def query_ai(prompt: str, system_prompt: str = "") -> str:
    """
    Ücretsiz AI sorgulama — hiçbir API anahtarı gerekmez.
    g4f (GPT4Free) kullanır, PollinationsAI ile en hızlı sonuç verir.
    """
    try:
        from g4f.client import Client
        from g4f import Provider

        client = Client()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        # PollinationsAI — sürekli test edilmiş, çalışıyor
        for model in (None, "gpt-4o-mini", "llama"):
            try:
                kwargs = {"messages": messages, "provider": Provider.PollinationsAI, "timeout": 30}
                if model:
                    kwargs["model"] = model
                response = client.chat.completions.create(**kwargs)
                if response and response.choices:
                    text = response.choices[0].message.content
                    if text and text.strip():
                        return text.strip()
            except Exception:
                continue

        # Yedek: otomatik provider
        try:
            response = client.chat.completions.create(
                messages=messages, model="gpt-4o-mini", timeout=30
            )
            if response and response.choices:
                text = response.choices[0].message.content
                if text and text.strip():
                    return text.strip()
        except Exception:
            pass
    except Exception:
        pass

    return None
def generate_fallback_analysis(symbol: str, display_name: str, summary: dict) -> str:
    """AI bağlanamazsa kural tabanlı analiz üret."""
    price = summary["price"]
    change = summary["change_pct"]
    rsi = summary.get("rsi")
    ema20 = summary.get("ema20")
    ema50 = summary.get("ema50")
    support = summary.get("support")
    resistance = summary.get("resistance")
    currency = summary.get("currency", "USD")

    lines = []
    lines.append(f"📊 {display_name} için Teknik Özet (AI Bağlanamadı)")
    lines.append("")

    # Trend yönü
    if price >= (ema20 or price) and price >= (ema50 or price):
        trend = "yükseliş trendi"
        trend_icon = "📈"
    elif price < (ema20 or price) and price < (ema50 or price):
        trend = "düşüş trendi"
        trend_icon = "📉"
    else:
        trend = "karmaşık/yatay piyasa"
        trend_icon = "📊"

    lines.append(f"{trend_icon} {display_name} şu anda {trend} içerisinde.")
    lines.append(f"   Fiyat: {price:.2f} {currency} | 24s Değişim: {change:+.2f}%")

    if rsi is not None:
        if rsi > 70:
            lines.append(f"⚠️  RSI {rsi} ile aşırı alım bölgesinde. Kâr satışı gelebilir.")
        elif rsi < 30:
            lines.append(f"💡 RSI {rsi} ile aşırı satım bölgesinde. Tepki alımı beklenebilir.")
        else:
            lines.append(f"📊 RSI {rsi} ile nötr bölgede.")

    if support and resistance:
        lines.append(f"🔵 Destek: {support:.2f} {currency}")
        lines.append(f"🔴 Direnç: {resistance:.2f} {currency}")

    lines.append("")
    lines.append("💡 Öneri: AI motoru şu an yanıt vermiyor. İnternet bağlantınızı kontrol edin")
    lines.append("   veya 'pip install g4f --upgrade' ile g4f kütüphanesini güncelleyin.")

    return "\n".join(lines)


# =====================================================================
# 7. AI ANALİZİ
# =====================================================================

def build_ai_prompt(question: str, symbol: str, display_name: str, summary: dict) -> str:
    """AI'ya gönderilecek prompt'u teknik verilerle zenginleştirerek oluştur."""
    price = summary["price"]
    change = summary["change_pct"]
    currency = summary.get("currency", "USD")

    spark, _, _ = make_price_sparkline(summary["closes"], 50)
    bar_chart = make_bar_chart(summary["closes"], 40, 6)

    lines = []
    lines.append("📊 **CANLI TEKNİK VERİLER**")
    lines.append(f"Parite/Hisse: {symbol} ({display_name})")
    lines.append(f"Güncel Fiyat: {price:.4f} {currency}")
    lines.append(f"24s Değişim: {change:+.2f}%")
    lines.append(f"24s En Yüksek: {summary['high24']:.4f} {currency}")
    lines.append(f"24s En Düşük: {summary['low24']:.4f} {currency}")
    lines.append("")

    # İndikatörler
    rsi = summary.get("rsi")
    ema20 = summary.get("ema20")
    ema50 = summary.get("ema50")
    macd = summary.get("macd")
    macd_sig = summary.get("macd_signal")
    support = summary.get("support")
    resistance = summary.get("resistance")

    if ema20:
        ema20_dir = "▲" if price >= ema20 else "▼"
        lines.append(f"EMA20: {ema20:.2f} {ema20_dir}")
    if ema50:
        ema50_dir = "▲" if price >= ema50 else "▼"
        lines.append(f"EMA50: {ema50:.2f} {ema50_dir}")
    if rsi is not None:
        lines.append(f"RSI(14): {rsi}")
    if macd is not None and macd_sig is not None:
        macd_dir = "🟢" if macd >= macd_sig else "🔴"
        lines.append(f"MACD: {macd:.4f} (Sinyal: {macd_sig:.4f}) {macd_dir}")
    if support:
        lines.append(f"Destek: {support:.2f}")
    if resistance:
        lines.append(f"Direnç: {resistance:.2f}")
    lines.append("")

    # ASCII grafik
    if spark:
        lines.append("📈 **Fiyat Grafiği (Sparkline):**")
        lines.append(f"  {spark}")
    if bar_chart:
        lines.append("📊 **Fiyat Grafiği (ASCII):**")
        lines.append(bar_chart)
    lines.append("")

    # Kullanıcı sorusu
    lines.append("---")
    lines.append(f"**Kullanıcı Sorusu:** {question}")
    lines.append("---")
    lines.append("")
    lines.append("Yukarıdaki verilere göre profesyonel bir finansal analiz çıkart.")

    return "\n".join(lines)


def get_ai_analysis(question: str, symbol: str, display_name: str, summary: dict) -> str:
    """AI'dan analiz al, başarısız olursa kural tabanlı fallback kullan."""

    system_prompt = (
        "Sen profesyonel bir algoritmik trade ve yatırım yapay zekasısın. "
        "Sana gönderilen teknik verileri, fiyatı, grafiği ve kullanıcı sorusunu analiz ederek "
        "tamamen rasyonel, destek/direnç içeren, gelecek tahminleri sunan bir finansal rapor yaz. "
        "Cevabını Türkçe yaz. Kısa ve öz ol. Maddeler halinde yaz. "
        "Altın, döviz, BIST ve kripto paralar hakkında genel bilgiye sahipsin. "
        "Finansal bir ürünün değerlendirmesini yaparken teknik verilere dayan. "
        "Risk uyarısı eklemeyi unutma. Cevabının sonuna "
        "'⚠️ Bu bir yatırım tavsiyesi değildir, sadece teknik analiz amaçlıdır.' ekle."
    )

    prompt = build_ai_prompt(question, symbol, display_name, summary)

    ai_result = query_ai(prompt, system_prompt)

    if ai_result:
        return ai_result

    return generate_fallback_analysis(symbol, display_name, summary)


# =====================================================================
# 8. ÇIKTI / FORMAT
# =====================================================================

def print_welcome():
    hat = "─" * 52
    print(f"\n{hat}")
    print(f"   🧠 YtAI YATIRIM YAPAY ZEKASI ANALİZİ")
    print(f"{hat}")
    print("   Doğal dil ile finansal analiz.")
    print(f"   Örn: YtAI Soru: BTC alınır mı?\n")


def print_result(symbol: str, display_name: str, summary: dict, ai_text: str):
    """Analiz sonucunu formatlı şekilde terminale bas."""
    price = summary["price"]
    change = summary["change_pct"]
    currency = summary.get("currency", "USD")

    change_icon = "📈" if change >= 0 else "📉"
    hat = "─" * 52

    print(f"\n{hat}")
    print(f"   🧠 YtAI YATIRIM YAPAY ZEKASI ANALİZİ")
    print(f"{hat}")
    print()

    # ASCII grafik (bar chart)
    bar_chart = make_bar_chart(summary["closes"], 40, 6)
    if bar_chart:
        print(f"{bar_chart}")
        print()

    # Sparkline
    spark, _, _ = make_price_sparkline(summary["closes"], 50)
    if spark:
        print(f"   {spark}")
        print()

    # Özet bilgi
    change_str = f"{change:+.2f}%" if change is not None else "Veri Yok"
    print(f"   Parite/Hisse : {symbol}")
    print(f"   Güncel Fiyat : {price:.4f} {currency}")
    print(f"   24s Değişim  : {change_str} {change_icon}")

    # İndikatör snippet
    rsi = summary.get("rsi")
    ema20 = summary.get("ema20")
    ema50 = summary.get("ema50")
    ind_parts = []
    if ema20:
        ema20_dir = "▲" if price >= ema20 else "▼"
        ind_parts.append(f"EMA20 @ {ema20} {ema20_dir}")
    if rsi is not None:
        ind_parts.append(f"RSI {rsi}")
    if ind_parts:
        print(f"   İndikatörler : {' | '.join(ind_parts)}")
    print()

    # Yapay zeka yorumu
    print(f"   🤖 YAPAY ZEKA YORUMU VE GELECEK ÖNGÖRÜSÜ:")
    print(f"   {'─' * 48}")

    # Metni satırlara böl ve girintile
    for line in ai_text.strip().split("\n"):
        if line.strip():
            wrapped = textwrap.fill(line.strip(), width=80, subsequent_indent="   ")
            print(f"   {wrapped}")
        else:
            print()

    print(f"{hat}\n")


def print_error(msg: str):
    print(f"\n❌ {msg}")
    print("")


# =====================================================================
# 9. ANA GİRİŞ
# =====================================================================

def main():
    raw_input = " ".join(sys.argv[1:]).strip()

    if not raw_input:
        print_welcome()
        print("   Kullanım: YtAI Soru: [finansal sorunuz]")
        print("   Örnekler:")
        print('     YtAI Soru: Manas hissesi hakkında ne düşünüyorsun?')
        print('     YtAI Soru: BTC şuan alınır mı?')
        print('     YtAI Soru: THYAO teknik analizi nasıl?')
        print('     YtAI Soru: AAPL almak için uygun zaman mı?')
        return

    # "YtAI Soru:" ön ekini temizle (büyük/küçük harf duyarsız)
    question = re.sub(
        r'^(?:YTAI|ytai)\s*[Ss]oru\s*[:]\s*',
        '',
        raw_input,
        flags=re.IGNORECASE
    ).strip()

    if not question:
        question = raw_input

    # Sembol tespiti
    symbol, data_type, display_name, raw_match = extract_symbol_from_question(question)

    if not symbol:
        # Sembol bulunamadıysa tüm soruyu AI'ya doğrudan gönder, bilgi amaçlı
        print(f"\n   ℹ️  Finansal varlık tespit edilemedi. Genel soru olarak işleniyor...\n")
        _answer_general(question)
        return

    print(f"   🔍 '{display_name}' tespit edildi → {symbol} ({data_type.upper()})")
    print(f"   📡 Teknik veriler çekiliyor...")

    summary = fetch_summary(symbol, data_type)
    if not summary:
        print_error(f"'{symbol}' için veri alınamadı! Sembolü kontrol edin.")
        return

    print(f"   ✅ Veriler alındı. AI analizi hazırlanıyor...\n")

    ai_text = get_ai_analysis(question, symbol, display_name, summary)
    print_result(symbol, display_name, summary, ai_text)


def _answer_general(question: str):
    """Sembol bulunamadığında genel soruya AI üzerinden cevap ver."""
    hat = "─" * 52
    system_prompt = (
        "Sen profesyonel bir finansal yapay zeka asistanısın. "
        "Kullanıcı sana bir finans sorusu sordu. "
        "Bildiğin kadarıyla genel finans bilgisi çerçevesinde cevap ver. "
        "Cevabını Türkçe ve maddeler halinde yaz. "
        "Eğer soru finansla ilgili değilse, kibarca yalnızca finansal sorulara cevap verebildiğini belirt."
    )

    ai_result = query_ai(question, system_prompt)

    print(f"\n{hat}")
    print(f"   🧠 YtAI GENEL FİNANS YANITI")
    print(f"{hat}\n")

    if ai_result:
        for line in ai_result.strip().split("\n"):
            if line.strip():
                print(f"   {line.strip()}")
            else:
                print()
    else:
        print("   Finansal varlık adı içeren bir soru sormanız önerilir.")
        print("   Örn: YtAI Soru: BTC alınır mı?")
    print(f"{hat}\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 YtAI kapatıldı.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
