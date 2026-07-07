import sys
import os

# --- WINDOWS CMD EMOJI VE UNICODE ÇÖKME KORUMASI ---
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
# --------------------------------------------------

import warnings

warnings.filterwarnings("ignore")

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from g4f.client import Client

def parse_and_convert_date(date_str):
    """GMT tarih stringini TSİ (Turkey Time) formatına çevirir ve eskilik kontrolü yapar."""
    # Örnek girdi: Sun, 05 Jul 2026 08:23:00 GMT
    months_en_tr = {
        "Jan": "Ocak", "Feb": "Şubat", "Mar": "Mart", "Apr": "Nisan",
        "May": "Mayıs", "Jun": "Haziran", "Jul": "Temmuz", "Aug": "Ağustos",
        "Sep": "Eylül", "Oct": "Ekim", "Nov": "Kasım", "Dec": "Aralık"
    }
    try:
        # Sondaki GMT kısmını temizleyip parse edelim
        clean_date = date_str.replace("GMT", "").strip()
        dt = datetime.strptime(clean_date, "%a, %d %b %Y %H:%M:%S")
        
        # GMT'den TSİ'ye (+3 Saat) geçiş
        dt_tsi = dt + timedelta(hours=3)
        
        # 24 saatten eski mi kontrolü
        now = datetime.utcnow() + timedelta(hours=3) # Mevcut TSİ zamanı
        is_old = (now - dt_tsi).total_seconds() > 86400
        age_tag = "⚠️ ESKİ HABER" if is_old else "🔥 GÜNCEL HABER"
        
        month_tr = months_en_tr.get(dt_tsi.strftime("%b"), dt_tsi.strftime("%b"))
        formatted_date = f"{dt_tsi.strftime('%d')} {month_tr} {dt_tsi.strftime('%Y')} - {dt_tsi.strftime('%H:%M')} ({age_tag})"
        return formatted_date
    except Exception:
        return f"{date_str} (Zaman Formatlanamadı)"

def get_google_news(query):
    """Google News RSS servisinden doğrudan canlı haberleri ve linkleri çeker."""
    news_results = []
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=tr&gl=TR&ceid=TR:tr"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        
        with urllib.request.urlopen(req, timeout=7) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        for item in root.findall('.//item'):
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            
            # Tarih dönüşümünü burada hallediyoruz
            display_date = parse_and_convert_date(pub_date)
            
            news_results.append({
                "title": title,
                "body": title,
                "url": link,
                "date": display_date
            })
    except Exception:
        pass
    return news_results[:12]

def analyze_with_ai(news_list, symbol, mode):
    """Haberleri AI'ye gönderip modlara göre süzer ve yorumlar."""
    client = Client()
    news_context = json.dumps(news_list, ensure_ascii=False)
    
    prompt = f"""
    Sen profesyonel bir finans analistisin. Aşağıda {symbol} araması için Google News RSS üzerinden çekilen son haberlerin listesi var:
    {news_context}
    
    Kullanıcı '{mode}' modunu seçti. Senden istenen kurallar:
    
    1. Eğer mod 'sonhaber' ise:
       - Listedeki en güncel ana haberi seç. Haber listesindeki "date" verisini olduğu gibi kullan, tarihe dokunma.
    
    2. Eğer mod 'onemlihaber' ise:
       - Bu haberler arasından fiyatı tavan yaptırabilecek, çakıltabilecek, geleceğini ciddi etkileyecek (büyük ortaklık, dava, hack, regülasyon, büyük veri açıklaması, bilanço vb.) EN KRİTİK haberi seç.
       - EĞER listedeki haberlerin hiçbiri fiyatı sert etkileyecek güçte sıradışı bir haber değilse, doğrudan sadece şu cümleyi yaz: "Kritik/Önemli bir haber bulunamadı." Başka hiçbir şablon veya satır doldurma.

    Seçtiğin haber için TAM olarak şu şablonda Türkçe cevap üret (Asla markdown link formatı olan [text](url) kullanma! URL kısmına sadece düz link metnini yaz! Giriş açıklaması ekleme doğrudan şablonla başla):
    
    📰 Haber Başlığı : [Haberin başlığı]
    🔗 Kaynak Linki : [Haberin listesindeki ham URL adresi]
    🕒 Haber Tarihi : [Haberin listesindeki hazır date verisi]
    
    📊 Fiyata Olası Etkisi: [Tavan Yaptırabilir / Çakıltabilir / Küçük Artış / Küçük Düşüş / Nötr]
    
    💬 AI Analiz & Yorum:
    [Haberin analizini ve piyasa/fiyat yorumunu buraya yaz.]
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content
    except Exception:
        return "❌ Yapay zeka motoruna şu an ulaşılamıyor, lütfen az sonra tekrar deneyin."

def main():
    if len(sys.argv) < 2:
        print("❌ Hata: Eksik argüman girdiniz!\nKullanım: haber [coin/hisse] [sonhaber/onemlihaber]")
        return

    symbol = sys.argv[1].upper()
    
    mode = "sonhaber"
    if len(sys.argv) >= 3:
        user_mode = sys.argv[2].lower()
        if user_mode in ["sonhaber", "onemlihaber"]:
            mode = user_mode

    is_crypto = symbol.endswith("USDT") or symbol in ["BTC", "ETH", "SOL", "XRP", "BITCOIN"]
    
    if is_crypto:
        search_query = f"{symbol.replace('USDT', '')} kripto"
    else:
        search_query = f"{symbol} hisse"

    if symbol in ["BTC", "BTCUSDT", "BITCOIN"]:
        search_query = "Bitcoin kripto fiyat"

    print(f"🔄 {symbol} için Google News üzerinden canlı veriler toplanıyor ve AI analizi yapılıyor ({mode} modu)...")

    raw_news = get_google_news(search_query)
    
    if not raw_news:
        print(f"❌ '{symbol}' ile ilgili Google News üzerinde hiçbir haber kaynağına ulaşılamadı.")
        return

    final_report = analyze_with_ai(raw_news, symbol, mode)
    
    print("\n" + "─" * 60)
    print(f"🔥 {symbol} GÜNCEL HABER VE YAPAY ZEKA ANALİZ PANELİ")
    print("─" * 60)
    print(final_report)
    print("─" * 60)

if __name__ == "__main__":
    main()