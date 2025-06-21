#!/bin/sh

set -e

JADWAL_DEST="/etc/jadwalsholat"
INIT_DEST="/etc/init.d"

echo "🕌 Jadwal Sholat Bot Telegram Installer"
echo "====================================="
echo "1) Install"
echo "2) Uninstall"
echo "0) Keluar"
echo "-------------------------------------"
printf "Pilih opsi [1/2/0]: "
read opsi

if [ "$opsi" = "1" ]; then
    echo ""
    echo "📦 Memastikan dependensi sistem tersedia (python3, pip3, curl, wget, bash)..."
    command -v python3 >/dev/null 2>&1 || {
        echo "⛔ Python3 tidak ditemukan. Harap install Python 3 terlebih dahulu."
        exit 1
    }
    command -v pip3 >/dev/null 2>&1 || {
        echo "📦 pip3 tidak ditemukan. Mencoba menginstall..."
        (apt update && apt install -y python3-pip) || (opkg update && opkg install python3-pip) || {
            echo "⛔ Gagal menginstall pip3. Harap install manual."
            exit 1
        }
    }
    command -v curl >/dev/null 2>&1 || {
        echo "📦 curl tidak ditemukan. Mencoba menginstall..."
        (apt install -y curl) || (opkg install curl) || {
            echo "⛔ Gagal menginstall curl. Harap install manual."
            exit 1
        }
    }
    command -v wget >/dev/null 2>&1 || {
        echo "📦 wget tidak ditemukan. Mencoba menginstall..."
        (apt install -y wget) || (opkg install wget) || {
            echo "⛔ Gagal menginstall wget. Harap install manual."
            exit 1
        }
    }
    command -v bash >/dev/null 2>&1 || {
        echo "📦 bash tidak ditemukan. Mencoba menginstall..."
        (apt install -y bash) || (opkg install bash) || {
            echo "⛔ Gagal menginstall bash. Harap install manual."
            exit 1
        }
    }
    echo "🐍 Menginstall package Python: pyTelegramBotAPI, requests..."
    pip3 install --no-cache-dir pyTelegramBotAPI requests || {
        echo "⛔ Gagal install package Python. Harap cek koneksi atau install manual."
        exit 1
    }

    echo "✅ Semua dependensi terpasang dengan baik."

    echo ""
    echo "📋 Masukkan Konfigurasi Bot Telegram"
    printf "Token Bot Telegram: "
    read TOKEN
    printf "Chat ID (misal: @gruppublik, 1234567890, dan tambahkan -100 didepan untuk super group private): "
    read CHAT_ID
    printf "Thread ID (tekan Enter jika tidak digunakan): "
    read THREAD_ID
    [ -z "$THREAD_ID" ] && THREAD_ID="None"
    printf "Nama Kota (tekan enter untuk Default: Banyumas): "
    read KOTA
    [ -z "$KOTA" ] && KOTA="Banyumas"
    printf "Latitude (tekan enter untuk Default: -7.533912): "
    read LAT
    [ -z "$LAT" ] && LAT="-7.533912"
    printf "Longitude (tekan enter untuk Default: 109.121122): "
    read LON
    [ -z "$LON" ] && LON="109.121122"

    echo "📁 Menyalin file ke sistem..."
    mkdir -p "$JADWAL_DEST"

    base_url="https://raw.githubusercontent.com/ribhy21/Jadwalsholatbot/main/jadwalsholatbot/etc/jadwalsholat"

    wget -qO "$JADWAL_DEST/jadwalsholatbot.py" "$base_url/jadwalsholatbot.py"
    wget -qO "$JADWAL_DEST/updatesholat.txt" "$base_url/updatesholat.txt"
    wget -qO "$JADWAL_DEST/katasholat.txt" "$base_url/katasholat.txt"
    wget -qO "$JADWAL_DEST/penyambutpagi.txt" "$base_url/penyambutpagi.txt"

    echo "📝 Menyimpan konfigurasi..."
    cat > "$JADWAL_DEST/konfirgurasi.txt" <<EOF
# konfigurasi.txt
TOKEN=$TOKEN
CHAT_ID=$CHAT_ID
THREAD_ID=$THREAD_ID
KOTA=$KOTA
LAT=$LAT
LON=$LON
EOF

    echo "📂 Menyalin service init.d"
    wget -qO "$INIT_DEST/jadwalsholatbot" "https://raw.githubusercontent.com/ribhy21/Jadwalsholatbot/main/jadwalsholatbot/etc/init.d/jadwalsholatbot"
    chmod +x "$INIT_DEST/jadwalsholatbot"

    echo "⚙️ Mengaktifkan dan menjalankan service..."
    /etc/init.d/jadwalsholatbot enable
    /etc/init.d/jadwalsholatbot start

    echo ""
    echo "✅ Instalasi selesai!"
    echo "📁 File konfigurasi: $JADWAL_DEST/konfirgurasi.txt"
    echo "▶️  Bot sudah aktif dan berjalan sekarang."

    echo "📨 Mengirim pesan sambutan ke Telegram Anda..."

    WELCOME_MSG="Assalamu'alaikum warahmatullahi wabarakatuh! 👋

🤖 *Bot Jadwal Sholat* berhasil diinstal.

Bot ini akan membantumu mendapatkan jadwal sholat dan pengingat waktu sholat harian secara otomatis.  

Ketik /start untuk memulai dan panduan lainnya."

    if [ "$THREAD_ID" = "None" ]; then
        curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d chat_id="$CHAT_ID" \
            -d text="$WELCOME_MSG" \
            -d parse_mode="Markdown" > /dev/null
    else
        curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
            -d chat_id="$CHAT_ID" \
            -d message_thread_id="$THREAD_ID" \
            -d text="$WELCOME_MSG" \
            -d parse_mode="Markdown" > /dev/null
    fi

    echo "✅ Pesan sambutan berhasil dikirim."

elif [ "$opsi" = "2" ]; then
    echo ""
    echo "⚠️  Uninstall Jadwal Sholat Bot"
    /etc/init.d/jadwalsholatbot stop 2>/dev/null || true
    /etc/init.d/jadwalsholatbot disable 2>/dev/null || true
    rm -rf "$JADWAL_DEST"
    rm -f "$INIT_DEST/jadwalsholatbot"
    echo "✅ Uninstall selesai!"
else
    echo "❎ Keluar dari installer."
fi
