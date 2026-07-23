#!/bin/bash
# ============================================================
# CmdTools v0.3 — Linux Otomatik Kurulum
# ============================================================
# Tek komutla kurulum:
#   bash <(curl -s https://raw.githubusercontent.com/ilter2014/CmdTools/main/install.sh)
#
# veya indirip çalıştırma:
#   chmod +x install.sh
#   ./install.sh
# ============================================================

set -e

KURULUM_DIR="$HOME/CmdTools"
REPO_URL="https://github.com/ilter2014/CmdTools/archive/refs/heads/main.zip"
RENK_YESIL='\033[0;32m'
RENK_KIRMIZI='\033[0;31m'
RENK_SARI='\033[1;33m'
RENK_NORMAL='\033[0m'

basarili() { echo -e "${RENK_YESIL}  ✓ $1${RENK_NORMAL}"; }
hata() { echo -e "${RENK_KIRMIZI}  ✗ $1${RENK_NORMAL}"; }
bilgi() { echo -e "${RENK_SARI}  → $1${RENK_NORMAL}"; }

echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║     CmdTools v0.3 Linux Kurulumu        ║"
echo "  ║     github.com/ilter2014/CmdTools        ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""

# ─── 1. BAGLANTI KONTROLU ───
echo "  1/6  Internet baglantisi kontrol ediliyor..."
if ! curl -s --max-time 5 https://github.com > /dev/null 2>&1; then
    hata "Internet baglantisi yok!"
    echo "         Internet baglantisi olmadan kurulum yapilamaz."
    exit 1
fi
basarili "Internet baglantisi OK"

# ─── 2. PYTHON KONTROLU ───
echo ""
echo "  2/6  Python kontrol ediliyor..."
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    hata "Python bulunamadi!"
    echo "         Kurulum icin Python 3.8+ gereklidir."
    echo "         sudo apt install python3 python3-pip"
    exit 1
fi
PY_VER=$($PYTHON_CMD --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
basarili "Python $PY_VER bulundu ($PYTHON_CMD)"

# ─── 3. MEVCUT KURULUM KONTROLU ───
echo ""
echo "  3/6  Mevcut kurulum kontrol ediliyor..."
if [ -d "$KURULUM_DIR" ]; then
    bilgi "Mevcut kurulum bulundu: $KURULUM_DIR"
    bilgi "Guncelleniyor..."
    rm -rf "$KURULUM_DIR"
fi

# ─── 4. INDIRME ───
echo ""
echo "  4/6  Indiriliyor..."
GEÇICI_DOSYA=$(mktemp /tmp/cmdtools-XXXXXX.zip)
curl -L --progress-bar -o "$GEÇICI_DOSYA" "$REPO_URL"
basarili "Indirme tamamlandi"

# ─── 5. CIKARMA VE KURULUM ───
echo ""
echo "  5/6  Kuruluyor..."
GEÇICI_DIZIN=$(mktemp -d)
unzip -q -o "$GEÇICI_DOSYA" -d "$GEÇICI_DIZIN"
KAYNAK=$(find "$GEÇICI_DIZIN" -maxdepth 1 -type d -name "CmdTools-*" | head -1)
if [ -z "$KAYNAK" ]; then
    KAYNAK="$GEÇICI_DIZIN"
fi
mv "$KAYNAK" "$KURULUM_DIR"
chmod +x "$KURULUM_DIR"/{about,alarm,analiz,b64,bilgi,calc,cmdhash,cmdtools,emptydirs,emptyfolders,genuuid,grafik,haber,ip,jsonfmt,list,mac,ns,otosinyal,passgen,pingtest,port,ports,serve,sinyal,size,speedtest,sysinfo,timestamp,tree,uptime,url,yardim,ytai} 2>/dev/null || true

# Gecik temizle
rm -f "$GEÇICI_DOSYA"
rm -rf "$GEÇICI_DIZIN"

basarili "$KURULUM_DIR konumuna kuruldu"

# ─── 6. PATH KAYDI ───
echo ""
echo "  6/6  PATH guncelleniyor..."
BASHRC="$HOME/.bashrc"
BAŞLIK="# CmdTools"
if grep -q "$BAŞLIK" "$BASHRC" 2>/dev/null; then
    bilgi "PATH zaten ekli"
else
    echo "" >> "$BASHRC"
    echo "$BAŞLIK" >> "$BASHRC"
    echo "export PATH=\"$KURULUM_DIR:\$PATH\"" >> "$BASHRC"
    echo "alias hash='cmdhash'" >> "$BASHRC"
    basarili "PATH'e eklendi (yeni terminalde aktif olur)"
fi

# ─── KUTUPHANE KURULUMU ───
echo ""
echo "  Kütüphaneler kuruluyor..."
"$PYTHON_CMD" "$KURULUM_DIR/updaterouter.py" --cmdname cmdtools install 2>/dev/null || {
    bilgi "Kütüphane kurulumu atlandi (sonra: cmdtools install)"
}

# ─── SONUC ───
echo ""
echo "  ╔══════════════════════════════════════════╗"
echo "  ║         KURULUM BASARILI!               ║"
echo "  ╠══════════════════════════════════════════╣"
echo "  ║  Konum: ~/CmdTools                      ║"
echo "  ║                                          ║"
echo "  ║  Yeni terminal acarak baslayabilirsiniz: ║"
echo "  ║    sysinfo                              ║"
echo "  ║    calc 25*8+10                         ║"
echo "  ║    cmdtools help                        ║"
echo "  ╚══════════════════════════════════════════╝"
echo ""
