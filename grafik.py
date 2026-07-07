import sys
import os

# --- WINDOWS CMD EMOJI VE UNICODE ÇÖKME KORUMASI ---
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# --------------------------------------------------

import requests
import plotext as plt
import yfinance as yf
from datetime import datetime, timedelta

def get_crypto_data(symbol, interval):
    """Binance API'den kripto mum verilerini çeker."""
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol.upper(), "interval": interval, "limit": 100}
    try:
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 400: return None
        data = response.json()
        
        # Panel için genel 24s hacim ve değişim bilgilerini de ek çekelim
        ticker_url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}"
        t_res = requests.get(ticker_url, timeout=5).json()
        
        closes = [float(c[4]) for c in data]
        volumes = [float(c[5]) for c in data]
        
        return {
            "type": "CRYPTO",
            "currency": "USDT",
            "klines": data,
            "closes": closes,
            "change_24h": float(t_res.get("priceChangePercent", 0)),
            "high_24h": float(t_res.get("highPrice", max(closes[-40:]))),
            "low_24h": float(t_res.get("lowPrice", min(closes[-40:]))),
            "volume_24h": float(t_res.get("volume", sum(volumes[-40:])))
        }
    except Exception:
        return None

def get_bist_data(symbol, interval):
    """Yahoo Finance üzerinden BİST verilerini çeker."""
    ticker_symbol = f"{symbol.upper()}.IS"
    
    # Binance interval'lerini yfinance formatına eşleme
    interval_map = {"1m":"1m", "5m":"5m", "15m":"15m", "30m":"30m", "1h":"60m", "1d":"1d", "1w":"1wk", "1M":"1mo"}
    yf_interval = interval_map.get(interval, "15m")
    
    # Geçmiş veri limiti belirleme
    period = "5d" if yf_interval in ["1m", "5m", "15m", "30m"] else "1mo"
    if yf_interval in ["1d", "60m"]: period = "6mo"

    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=yf_interval)
        if df.empty or len(df) < 2: return None
        
        # Son 100 veriyi al (RSI ve EMA için)
        df = df.tail(100)
        
        # Günlük değişim hesabı
        info = ticker.fast_info
        prev_close = info.get('previous_close', df['Close'].iloc[-2])
        current_price = df['Close'].iloc[-1]
        change_pct = ((current_price - prev_close) / prev_close) * 100
        
        return {
            "type": "BIST",
            "currency": "TRY",
            "df": df,
            "closes": df['Close'].tolist(),
            "change_24h": change_pct,
            "high_24h": df['High'].iloc[-1], # Son periyodun yüksek/düşük/hacim değerleri
            "low_24h": df['Low'].iloc[-1],
            "volume_24h": df['Volume'].iloc[-1]
        }
    except Exception:
        return None

def calculate_ema(prices, period):
    if len(prices) < period: return [prices[-1]] * len(prices)
    k = 2 / (period + 1)
    ema = []
    sma = sum(prices[:period]) / period
    ema.append(sma)
    for price in prices[period:]:
        ema.append((price * k) + (ema[-1] * (1 - k)))
    return ([prices[0]] * (len(prices) - len(ema))) + ema

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1: return 50.0
    gains, losses = [], []
    for i in range(1, len(prices)):
        change = prices[i] - prices[i-1]
        gains.append(change if change > 0 else 0)
        losses.append(abs(change) if change < 0 else 0)
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0: return 100.0
    return 100 - (100 / (1 + (avg_gain / avg_loss)))

def main():
    if len(sys.argv) < 3:
        print("❌ Hata: Eksik argüman girdiniz!\nKullanım: grafik [sembol] [zaman_dilimi] (Örn: grafik thya0 15m)")
        return

    symbol = sys.argv[1].lower()
    interval = sys.argv[2].lower()

    # Kripto mu BİST mi tespiti
    is_crypto = symbol.endswith("usdt") or symbol.endswith("btc") or symbol.endswith("try") and len(symbol) > 5
    # Eğer sonu usdt bitmiyorsa ve kullanıcı düz girdiyle btc yazdıysa otomatik usdt bağlayalım kolaylık olsun
    if symbol == "btc" or symbol == "eth" or symbol == "sol":
        symbol += "usdt"
        is_crypto = True

    print(f"🔄 {symbol.upper()} için {interval} verileri analiz ediliyor...")

    if is_crypto:
        res = get_crypto_data(symbol, interval)
    else:
        res = get_bist_data(symbol, interval)

    if not res:
        print(f"❌ Hata: '{symbol.upper()}' bulunamadı veya veri çekilemedi!")
        return

    # Fiyat listesi ve İndikatörler
    closes = res["closes"]
    ema20_list = calculate_ema(closes, 20)
    ema50_list = calculate_ema(closes, 50)
    rsi_value = calculate_rsi(closes, 14)

    current_price = closes[-1]
    last_ema20 = ema20_list[-1]
    last_ema50 = ema50_list[-1]

    ema20_dir = "↑" if current_price > last_ema20 else "↓"
    ema50_dir = "↑" if current_price > last_ema50 else "↓"

    if current_price > last_ema20 and last_ema20 > last_ema50 and rsi_value > 50:
        trend_status = "Bullish 🐂"
    elif current_price < last_ema20 and last_ema20 < last_ema50 and rsi_value < 50:
        trend_status = "Bearish 🐻"
    else:
        trend_status = "Neutral ⚖️"

    # Mum Listelerini Grafik İçin Hazırlama (Son 40 Mum)
    dates_plot = list(range(40))
    open_plot, high_plot, low_plot, close_plot = [], [], [], []

    if res["type"] == "CRYPTO":
        for candle in res["klines"][-40:]:
            open_plot.append(float(candle[1]))
            high_plot.append(float(candle[2]))
            low_plot.append(float(candle[3]))
            close_plot.append(float(candle[4]))
        source_name = "Binance"
        vol_suffix = "BTC" if "BTC" in symbol.upper() else "UNIT"
        vol_formatted = f"{res['volume_24h']/1000:.2f}K {vol_suffix}" if res['volume_24h'] > 1000 else f"{res['volume_24h']:.2f}"
    else:
        df_plot = res["df"].tail(40)
        open_plot = df_plot['Open'].tolist()
        high_plot = df_plot['High'].tolist()
        low_plot = df_plot['Low'].tolist()
        close_plot = df_plot['Close'].tolist()
        source_name = "BIST / Yahoo"
        vol_formatted = f"{res['volume_24h']/1e6:.2f}M Lot" if res['volume_24h'] > 1e6 else f"{res['volume_24h']/1e3:.2f}K Lot"

    # Grafik Çizimi
    plt.clf()
    plt.theme("dark")
    plt.candlestick(dates_plot, {"Open": open_plot, "High": high_plot, "Low": low_plot, "Close": close_plot})
    plt.plotsize(80, 15)
    
    # Çıktı Paneli
    print("\n" + "─" * 52)
    print(f"{symbol.upper()} | {interval} | {source_name}")
    print("─" * 52)
    print(f"Price      : {current_price:,.2f} {res['currency']}")
    print(f"Change     : {res['change_24h']:+.2f}%")
    print(f"High       : {res['high_24h']:,.2f}")
    print(f"Low        : {res['low_24h']:,.2f}")
    print(f"Volume     : {vol_formatted}")
    print(f"EMA20      : {last_ema20:,.2f} {ema20_dir}")
    print(f"EMA50      : {last_ema50:,.2f} {ema50_dir}")
    print(f"RSI        : {rsi_value:.1f}")
    print(f"Trend      : {trend_status}")
    print("─" * 52)
    
    # Grafiği en alta basıyoruz
    plt.show()

if __name__ == "__main__":
    main()