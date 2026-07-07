import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# ============ KOMUT LISTESI (her update'de guncelle) ============

SURUM = "3.3"

KATEGORILER = {
    "Sistem": ["sysinfo", "ip", "uptime", "mac", "port", "ports"],
    "Ag": ["pingtest", "speedtest", "ns"],
    "Dosya": ["size", "hash", "tree", "emptydirs", "emptyfolders"],
    "Guvenlik": ["passgen", "genuuid"],
    "Donusturucu": ["b64", "url", "jsonfmt", "timestamp"],
    "Diger": ["calc", "serve", "alarm", "analiz", "grafik", "haber", "sinyal", "ytai"],
}

KOMUT_ACIKLAMA = {
    "sysinfo": "Isletim sistemi, CPU, RAM bilgilerini gosterir.",
    "ip": "Yerel ve genel IP adresini gosterir.",
    "uptime": "Bilgisayarin ne kadar suredir acik oldugunu gosterir.",
    "mac": "Ag ve Bluetooth MAC adreslerini gosterir.",
    "port": "Acik portlari ve hangi uygulamanin kullandigini gosterir.",
    "ports": "port ile ayni.",
    "pingtest": "Internet gecikmenizi (ping) olcer ve degerlendirir.",
    "speedtest": "Internet hizinizi olcer (indirme/yukleme).",
    "ns": "Domainin nameserver ve DNS gorunurlugunu kontrol eder.",
    "size": "Dosya veya klasorun boyutunu hesaplar.",
    "hash": "Dosyanin MD5/SHA1/SHA256/SHA512 ozetini hesaplar.",
    "tree": "Klasor yapisini agac seklinde gosterir.",
    "emptydirs": "Tum sistemdeki bos klasorleri bulur.",
    "emptyfolders": "emptydirs ile ayni.",
    "passgen": "Guclu rastgele sifre uretir.",
    "genuuid": "Rastgele UUID (benzersiz kimlik) uretir.",
    "b64": "Base64 encode/decode yapar.",
    "url": "URL encode/decode yapar.",
    "jsonfmt": "JSON dogrulama, formatlama ve kucultme yapar.",
    "timestamp": "Unix timestamp ve tarih arasi donusum yapar.",
    "calc": "Hizli matematik islemleri yapar.",
    "serve": "Bulundugun klasoru HTTP sunucusu yapar.",
    "alarm": "Hisse senedi/kripto icin fiyat alarmi kurar.",
    "analiz": "Teknik analiz yapar (hisse/kripto).",
    "grafik": "Terminalde grafik cizer.",
    "haber": "Finansal haberleri gosterir.",
    "sinyal": "Al/sat sinyali uretir.",
    "ytai": "Yapay zeka ile finansal sorulari cevaplar.",
    "cmdtools": "CmdTools ana komutu (yardim, list, version, about).",
    "help": "Yardim bilgisini gosterir (cmdtools help ile ayni).",
    "yardim": "help ile ayni (Turkce).",
    "bilgi": "about ile ayni (Turkce).",
    "list": "Tum komutlari listeler.",
    "version": "CmdTools surumunu gosterir.",
    "about": "CmdTools hakkinda bilgi verir.",
}

KOMUT_KULLANIM = {
    "sysinfo": "sysinfo",
    "ip": "ip",
    "uptime": "uptime",
    "mac": "mac",
    "port": "port [port_numarasi]",
    "ports": "port ile ayni",
    "pingtest": "pingtest",
    "speedtest": "speedtest",
    "ns": "ns <domain>",
    "size": "size [dizin/dosya]",
    "hash": "hash <dosya> [-a md5|sha1|sha256|sha512]",
    "tree": "tree [dizin] [--depth N] [--max N] [--no-size]",
    "emptydirs": "emptydirs",
    "emptyfolders": "emptydirs ile ayni",
    "passgen": "passgen [uzunluk] [adet] [--no-symbols]",
    "genuuid": "genuuid [adet] [--upper]",
    "b64": "b64 encode <metin> | b64 decode <metin>",
    "url": "url encode <metin> | url decode <metin>",
    "jsonfmt": "jsonfmt <json> | jsonfmt --min <json> | jsonfmt --validate <json>",
    "timestamp": "timestamp [timestamp|tarih]",
    "calc": "calc <islem>",
    "serve": "serve [port] [--all]",
    "alarm": "alarm <sembol> <fiyat>",
    "analiz": "analiz <sembol> [timeframe]",
    "grafik": "grafik <sembol> [timeframe]",
    "haber": "haber [sembol]",
    "sinyal": "sinyal <sembol> [timeframe]",
    "ytai": "ytai <soru>",
    "cmdtools": "cmdtools help | list | version | about | bilgi",
    "help": "help [komut]",
    "yardim": "yardim [komut]",
    "bilgi": "bilgi",
    "list": "list",
    "version": "version",
    "about": "about",
}

KOMUT_ORNEK = {
    "sysinfo": "sysinfo",
    "ip": "ip",
    "uptime": "uptime",
    "mac": "mac",
    "port": "port",
    "pingtest": "pingtest",
    "speedtest": "speedtest",
    "ns": "ns google.com",
    "size": "size C:\\Projeler",
    "hash": "hash C:\\Users\\ilter\\dosya.zip -a md5",
    "tree": "tree C:\\CmdTools --depth 2",
    "emptydirs": "emptydirs",
    "passgen": "passgen 24 3",
    "genuuid": "genuuid 5 --upper",
    "b64": "b64 encode Merhaba Dunya",
    "url": "url encode Merhaba Dunya",
    "jsonfmt": "jsonfmt '{\"ad\":\"Ali\"}'",
    "timestamp": "timestamp 1704067200",
    "calc": "calc 25*8+10",
    "serve": "serve 8080",
}


def cmd_version():
    print(f"CmdTools v{SURUM}")


def cmd_about():
    print(f"CmdTools v{SURUM}")
    print()
    print("CmdTools, Windows komut satiri icin")
    print("gelistirilmis bir arac kutusudur.")
    print()
    print("Amac: Gunluk bilgisayar kullaniminda")
    print("isleri kolaylastirmak, ag, dosya, sistem")
    print("ve finans araclarina hizli erisim saglamak.")
    print()
    print(f"Toplam {len(KOMUT_ACIKLAMA)} komut")
    print(f"Surum: {SURUM}")
    print("Gelistirici: ilter2014")
    print("GitHub: github.com/ilter2014/CmdTools")


def cmd_list():
    print(f"CmdTools v{SURUM} - Kullanilabilir Komutlar")
    print()
    for kat, komutlar in KATEGORILER.items():
        print(f"  {kat}:")
        for k in komutlar:
            aciklama = KOMUT_ACIKLAMA.get(k, "")
            print(f"    - {k:<15} {aciklama}")
        print()


def cmd_help(konu=None):
    if not konu:
        cmd_list()
        print("  Yardim:")
        print("    help <komut>     Belirli bir komut hakkinda detayli yardim")
        print("    cmdtools help    Bu yardim ekrani")
        print("    cmdtools list    Komut listesi")
        print("    cmdtools version Surum bilgisi")
        print("    cmdtools about   Proje hakkind")
        print()
        return

    komut = konu.lower()
    if komut not in KOMUT_ACIKLAMA:
        print(f"Bilinmeyen komut: {konu}")
        print("Gecerli komutlari gormek icin: cmdtools help")
        return

    aciklama = KOMUT_ACIKLAMA.get(komut, "Aciklama yok.")
    kullanim = KOMUT_KULLANIM.get(komut, komut)
    ornek = KOMUT_ORNEK.get(komut, "-")

    print(f"Komut: {komut}")
    print()
    print(f"Aciklama:")
    print(f"  {aciklama}")
    print()
    print(f"Kullanim:")
    print(f"  {kullanim}")
    print()
    print(f"Ornek:")
    print(f"  {ornek}")


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    if not args:
        cmd_version()
        print()
        print("Kullanilan: cmdtools <komut>")
        print("  cmdtools help       Yardim")
        print("  cmdtools list       Komut listesi")
        print("  cmdtools version    Surum bilgisi")
        print("  cmdtools about      Proje hakkind")
        return

    komut = args[0].lower()

    if komut in ("version", "--version", "-v"):
        cmd_version()
    elif komut in ("about", "bilgi"):
        cmd_about()
    elif komut in ("list", "--list", "-l"):
        cmd_list()
    elif komut in ("help", "yardim"):
        konu = args[1] if len(args) > 1 else None
        cmd_help(konu)
    else:
        print(f"Bilinmeyen komut: {komut}")
        print("Kullanilan: cmdtools help | list | version | about")


if __name__ == "__main__":
    main()
