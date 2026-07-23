# Changelog

All notable changes to **CmdTools** will be documented in this file.

---

## CmdTools v0.3 Alpha - July 23, 2026

### Added

* `cmdtools install` / `cmdtools indir` komutu eklendi.
* Eksik kutuphaneler icin akilli tespit ve kurulum sistemi.
* Tum komutlarda ImportError yakalama: eksik kutuphane varsa kullaniciyi `cmdtools install` yonlendirir.
* Linux destegi: sysinfo, ip, mac, uptime, port, emptydirs, pingtest, ns icin Linux alternatifleri.
* 35 adet .sh bash launcher dosyasi olusturuldu.

### Changed

* Surum 0.2 -> 0.3.
* Kutuphane hatalari yerine anlamli kullanici mesajlari.
* Windows-specific yollar platform-neutral hale getirildi.

### Fixed

* passgen 16 3 gibi argumanlarin dogru ayrismasi.
* mac komutunun Linux regex hatasi duzeltildi.
* calc.py 'e' sabitinin bilimsel notasyonu bozma hatasi.
* grafik.py kripto tespitinde operator oncelik hatasi.
* sinyal.py AI fallback'te skor->score degisken hatasi.
* haber.py g4f importu graceful hale getirildi.
* alarm.py winsound ve sabit Windows yolu kaldirildi.
* updaterouter.py yerel surum GitHub'dan buyukse geri dusurmeyi atlar.

## CmdTools v0.1 Alpha - July 7, 2026

### Added

* Initial public alpha release.
* Basic command system.
* Core project structure.
* Documentation.
* Custom License.
* Security Policy.
* Contributing Guide.
* Code of Conduct.
* GitHub project configuration.

### Changed

* Initial implementation.

### Fixed

* Initial stability improvements.

---

## Versioning

CmdTools uses the following version format:

* **Alpha** – Early development versions.
* **Beta** – Feature-complete versions undergoing testing.
* **Release Candidate (RC)** – Final testing before stable release.
* **Stable** – Production-ready releases.

Example release history:

* CmdTools v0.1 Alpha
* CmdTools v0.2 Alpha
* CmdTools v0.3 Beta
* CmdTools v0.9 RC
* CmdTools v1.0
* CmdTools v1.1
* CmdTools v1.2

---

Thank you for using CmdTools!
