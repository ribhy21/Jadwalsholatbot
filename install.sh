#!/bin/sh

set -e

BASE_DIR=$(dirname "$0")
JADWAL_SRC="$BASE_DIR/etc/jadwalsholat"
INIT_SRC="$BASE_DIR/etc/init.d"
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
    echo "📋 Masukkan Konfigurasi Bot Telegram"
    printf "Token Bot Telegram: "
    read TOKEN
    printf "Chat ID (misal: -1001234567890): "
    read CHAT_ID
    printf "Thread ID (tekan Enter jika tidak digunakan): "
    read THREAD_ID
    [ -z "$THREAD_ID" ] && THREAD_ID="None"
    printf "Nama Kota (misal: Banyumas): "
    read KOTA
    printf "Latitude (misal: -7.5467668): "
    read LAT
    printf "Longitude (misal: 109.0899219): "
    read LON

    echo "📁 Menyalin file ke sistem..."

    mkdir -p "$JADWAL_DEST"
    cp "$JADWAL_SRC"/*.py "$JADWAL_DEST/"
    cp "$JADWAL_SRC"/*.txt "$JADWAL_DEST/"

    cp "$INIT_SRC/jadwalsholatbot" "$INIT_DEST/"
    chmod +x "$INIT_DEST/jadwalsholatbot"

    echo "📝 Menyimpan konfigurasi..."
    cat > "$JADWAL_DEST/konfirgurasi.txt" <<EOF
# konfigurasi.txt

# Masukkan token bot Telegram Anda
TOKEN=$TOKEN

# Masukkan chat ID (contoh: -1001234567890 untuk supergroup, atau ID user pribadi)
CHAT_ID=$CHAT_ID

# Masukkan thread ID jika menggunakan fitur forum thread di Telegram
# Jika tidak digunakan, isi dengan None
THREAD_ID=$THREAD_ID

# Nama kota (opsional, hanya untuk info di jadwal)
KOTA=$KOTA

# Koordinat lokasi (jika ingin menentukan lokasi jadwal salat)
# Anda bisa menggunakan Google Maps atau situs seperti latlong.net untuk mencarinya
LAT=$LAT
LON=$LON
EOF

    echo "⚙️ Mengaktifkan dan menjalankan service..."
    /etc/init.d/jadwalsholatbot enable
    /etc/init.d/jadwalsholatbot start

    echo ""
    echo "✅ Instalasi selesai!"
    echo "📁 File konfigurasi: $JADWAL_DEST/konfirgurasi.txt"
    echo "▶️  Bot sudah aktif dan berjalan sekarang."

elif [ "$opsi" = "2" ]; then
    echo ""
    echo "⚠️  Uninstall Jadwal Sholat Bot"

    /etc/init.d/jadwalsholatbot stop 2>/dev/null || true
    /etc/init.d/jadwalsholatbot disable 2>/dev/null || true

    echo "🧹 Menghapus file..."
    rm -rf "$JADWAL_DEST"
    rm -f "$INIT_DEST/jadwalsholatbot"

    echo "✅ Uninstall selesai!"
elif [ "$opsi" = "0" ]; then
    echo "❎ Keluar dari installer."
else
    echo "❌ Pilihan tidak valid."
fi
