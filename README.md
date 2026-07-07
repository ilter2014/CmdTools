# CmdTools

CmdTools, Windows komut satırı (CMD) için geliştirilmiş kapsamlı bir araç kutusudur.

Sistem bilgilerinden ağ araçlarına, dosya yönetiminden finansal analize kadar  
30'dan fazla komut ile günlük bilgisayar kullanımını kolaylaştırır.

---

# Özellikler

| Kategori | Komutlar |
|---|---|
| Sistem Araçları | sysinfo, ip, uptime, mac, port |
| Ağ Araçları | pingtest, speedtest, ns (DNS sorgulama) |
| Dosya Araçları | size, hash, tree, emptydirs |
| Güvenlik | passgen, genuuid |
| Dönüştürücüler | b64, url, jsonfmt, timestamp |
| Finans Araçları | alarm, analiz, grafik, haber, sinyal, ytai |
| Diğer | calc, serve |

---

# Kurulum

Projeyi `C:\CmdTools` dizinine kopyalayın.  
Her komut bir `.cmd` dosyası ile çağrılır.

## Örnek Kullanım
| Komut | Açıklama |
|---|---|
| sysinfo | Sistem bilgilerini gösterir |
| ip | IP ve ağ bilgilerini gösterir | 
| pingtest | İnternet gecikmesini ölçer |
| speedtest | İnternet hız testi yapar |
| analiz btcusdt | Teknik analiz yapar (kripto) |
| analiz manas | Teknik analiz yapar (hisse) |
| haber BTC | Finansal haberleri gösterir |
| grafik thyao 1h | Terminalde Türk Hava Yolları hissesinin 1 saatlik grafiğini çizer |
| grafik btcusdt 15m | Terminalde Bitcoin Usdt Kriptosunun 15 dakikalık grafiğini çizer |
| ns google.com | Girilen domainin nameserverlarını verir |
| passgen 24 3 | Tanesi 24 karakterden oluşan 3 adet güçlü şifre üretir |
| genuuid | 1 adet uuid üretir |
| genuuid --upper | 1 adet büyük harflerden oluşan uuid üretir |
| genuuid 8 | 8 adet uuid üretir |
| genuuid 8 --upper | 8 adet büyük harflerden oluşan uuid üretir |
| size C:/CmdTools | C:/CmdTools klasörünün boyutunu gösterir |
| size C:/CmdTools/README.md | C:/CmdTools/README.md dosyasının boyutunu gösterir |

---

# Komut Listesi

| Komut | Açıklama |
|---|---|
| sysinfo | İşletim sistemi, CPU, RAM bilgilerini gösterir |
| ip | Yerel ve genel IP adresini gösterir |
| uptime | Bilgisayarın çalışma süresini gösterir |
| mac | Ağ ve Bluetooth MAC adreslerini gösterir |
| port | Açık portları ve hangi uygulamanın kullandığını gösterir |
| ports | port ile aynı |
| pingtest | İnternet gecikmenizi (ping) ölçer ve değerlendirir |
| speedtest | İnternet hızınızı ölçer (indirme/yükleme) |
| ns | Domain'in nameserver ve DNS görünürlüğünü kontrol eder |
| size | Dosya veya klasörün boyutunu hesaplar |
| hash | Dosyanın MD5/SHA1/SHA256/SHA512 özetini hesaplar |
| tree | Klasör yapısını ağaç şeklinde gösterir |
| emptydirs | Tüm sistemdeki boş klasörleri bulur |
| emptyfolders | emptydirs ile aynı |
| passgen | Güçlü rastgele şifre üretir |
| genuuid | Rastgele UUID (benzersiz kimlik) üretir |
| b64 | Base64 encode/decode yapar |
| url | URL encode/decode yapar |
| jsonfmt | JSON doğrulama, formatlama ve küçültme yapar |
| timestamp | Unix timestamp ve tarih arası dönüşüm yapar |
| calc | Hızlı matematik işlemleri yapar |
| serve | Bulunduğun klasörü HTTP sunucusu yapar |
| alarm | Hisse senedi/kripto için fiyat alarmı kurar |
| analiz | Teknik analiz yapar (hisse/kripto) |
| grafik | Terminalde grafik çizer |
| haber | Finansal haberleri gösterir |
| sinyal | Al/sat sinyali üretir |
| ytai | Yapay zeka ile finansal soruları cevaplar |
| cmdtools | Ana komut (help, list, version, about) |
| help | Yardım bilgisini gösterir |

---

# Örnek Çıktılar

## sysinfo

```text
$ sysinfo

============================================================
  [ SISTEM BILGILERI ]
============================================================

  +- ISLETIM SISTEMI
  | Sistem      : Windows 11
  | Bilgisayar  : DESKTOP-ABC123
  ...
```

## calc

```text
$ calc 25*8+10

25*8+10 = 210
```

## passgen

```text
$ passgen 16 3

rF3)I)kwGqJ$*D]#
<&H}P)Pjy0w9?XA3
wbUvb!EMKX#3o^?)
...
```

---

# Gereksinimler

- Python 3.8+
- Windows 10/11
- İnternet bağlantısı (API çağrıları için)
- İntarnet bağlantısı yoksa dışarı ile iletişim kurmayan sistem komutları kullanılabilir ancak güncellemeler yapılamaz

---

# Proje Yapısı

```text
C:\CmdTools\

├── updaterouter.py      # Ana yönlendirici (tüm komutları .py dosyalarına yönlendirir)
├── *.py                 # Diğer tüm komut dosyaları
├── *.cmd                # Çalıştırma kısayolları
├── version              # Sürüm bilgisi
├── updaterouterversion  # Güncelleme bilgisi
└── manifest.txt         # Dosya manifestosu
```

---

# Güncelleme Sistemi

CmdTools, `updaterouter.py` üzerinden kendini güncelleyebilir.

- Her komut çalıştırıldığında GitHub'daki son sürüm kontrol edilir.
- Yeni sürüm varsa tüm proje dosyaları otomatik güncellenir.
- Güncelleme başarısız olursa mevcut sürüm korunur.
- Sistem otomatik olarak ilk installer kurumunda gereken kütüphaneleri kurmaktadır yeni güncellemelerde kütüphaneler updaterouter.py tarafından otomatik olarak kurulmaktadır.

---

# Geri Bildirim ve Destek

CmdTools, kullanıcı geri bildirimlerini önemseyen ve gelen öneriler doğrultusunda sürekli geliştirilen bir projedir.

Kullanıcılarımızın karşılaştığı sorunlar, önerileri ve geliştirme fikirleri bizim için değerlidir.

CmdTools'u kullanıcı yorumları, öneriler ve ihtiyaçlar doğrultusunda; fırsat buldukça geliştirmeye ve daha iyi hale getirmeye devam edeceğimize söz veriyoruz.

## İletişim

Her türlü geri bildirim, öneri ve destek talebi için:

[ilter9047@gmail.com](mailto:ilter9047@gmail.com)

Gönderilen e-postalar incelenir ve uygun şekilde yanıtlanmaya çalışılır.

## Destek Süreci

- Tarafımıza ulaştıktan sonra **6 saatten fazla süre geçmesine rağmen** geri dönüş alamadıysanız, lütfen [ILETISIM.md](./ILETISIM.md) dosyasındaki kurallara uygun şekilde tekrar iletişim kurun.

- [ILETISIM.md](./ILETISIM.md) dosyasına uygun gönderilen destek maillerine **en geç 6 saat içerisinde** geri dönüş sağlanacaktır.

---
# Lisans

Bu proje [LICENSE](./LICENSE) dosyasında belirtilen lisans koşulları ile lisanslanmıştır.

---

# Katkıda Bulunma

Katkıda bulunmak için [CONTRIBUTING.md](./CONTRIBUTING.md) dosyasını inceleyin.

---

# Geliştirici

ilter2014 - [GitHub](https://github.com/ilter2014)
