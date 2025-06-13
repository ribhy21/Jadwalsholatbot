import telebot
import requests
import time
import threading
from datetime import datetime
import random
import os

# === Load konfigurasi dari file ===
def load_konfirgurasi(file_path):
    config = {}
    try:
        with open(file_path, "r") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    if value == "None":
                        config[key] = None
                    elif value.replace('.', '', 1).replace('-', '', 1).isdigit():
                        config[key] = float(value) if '.' in value else int(value)
                    else:
                        config[key] = value
    except Exception as e:
        print("Gagal baca konfirgurasi:", e)
    return config

def get_config():
    return load_konfirgurasi("/etc/jadwalsholat/konfirgurasi.txt")

config = get_config()  # <=== tambahkan ini

# Pakai variabel dari konfirgurasi
TOKEN = config.get("TOKEN")
CHAT_ID = config.get("CHAT_ID")
THREAD_ID = config.get("THREAD_ID")
KOTA = config.get("KOTA")  # Tanpa default
LAT = config.get("LAT")
LON = config.get("LON")


DIR_BASE = "/etc/jadwalsholat"
FILE_UPDATE = f"{DIR_BASE}/updatesholat.txt"
FILE_KATA = f"{DIR_BASE}/katasholat.txt"
FILE_PAGI = f"{DIR_BASE}/penyambutpagi.txt"

bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

def get_pesan_acak(file_path):
    try:
        with open(file_path, "r") as f:
            baris = [bar.strip() for bar in f if bar.strip()]
            return random.choice(baris)
    except:
        return None

def kirim_telegram(pesan):
    try:
        if THREAD_ID:
            bot.send_message(chat_id=CHAT_ID, message_thread_id=THREAD_ID, text=pesan)
        else:
            bot.send_message(chat_id=CHAT_ID, text=pesan)
    except Exception as e:
        print("Gagal kirim pesan:", e)

def ambil_jadwal():
    try:
        config = get_config()
        LAT = config.get("LAT")
        LON = config.get("LON")
        KOTA = config.get("KOTA")
        print(f"[DEBUG] Baca LAT: {LAT}, LON: {LON}, KOTA: {KOTA}")  # Ini wajib ada

        url = f"https://api.aladhan.com/v1/timings?latitude={LAT}&longitude={LON}&method=20"
        response = requests.get(url)
        print("[DEBUG] Raw response:", response.text)  # Tambahkan ini
        response = response.json()

        tgl = response['data']['date']['readable']
        hijri = response['data']['date']['hijri']
        hijri_tanggal = hijri['date']
        hijri_bulan = hijri['month']['en']
        hijri_tahun = hijri['year']

        waktu = response['data']['timings']
        imsak = waktu['Imsak']
        subuh = waktu['Fajr']
        terbit = waktu['Sunrise']
        dzuhur = waktu['Dhuhr']
        ashar = waktu['Asr']
        maghrib = waktu['Maghrib']
        isya = waktu['Isha']

        with open(FILE_UPDATE, "w") as f:
            f.write(f"""📅 Tanggal: <b>{tgl}</b>
🕋 Kalender Hijriyah: <b>{hijri_tanggal} ({hijri_bulan} {hijri_tahun} AH)</b>
🕌 Jadwal Sholat <b>{KOTA}, ID</b> dan Sekitarnya

🕓 <code>Imsak     : {imsak}</code>
🕌 <code>Subuh     : {subuh}</code>
🌄 <code>Terbit    : {terbit}</code>
☀️ <code>Dzuhur    : {dzuhur}</code>
🌤 <code>Asar      : {ashar}</code>
🌇 <code>Maghrib   : {maghrib}</code>
🌙 <code>Isya      : {isya}</code>

<b><i>💡 Semoga harimu penuh berkah dan semangat! 💫</i></b>""")

        return {
            "Imsak": imsak,
            "Subuh": subuh,
            "Dzuhur": dzuhur,
            "Asar": ashar,
            "Maghrib": maghrib,
            "Isya": isya
        }

    except Exception as e:
        print("Gagal ambil data:", e)
        return None

def kirim_jadwal():
    try:
        with open(FILE_UPDATE, "r") as f:
            kirim_telegram(f.read())
    except:
        kirim_telegram("Jadwal sholat belum tersedia.")

def kirim_sambutan():
    pesan = f"""<b>Terima kasih telah menggunakan Bot Jadwal Sholat!</b> 🙌

Berikut beberapa perintah yang bisa kamu gunakan:
• <b>/jadwal</b> – Lihat jadwal sholat hari ini sesuai lokasi kamu.
• <b>/update</b> – Perbarui jadwal sholat secara manual.
• <b>/setlokasi</b> – Ganti lokasi agar jadwal sesuai tempat kamu berada.

Bot ini akan mengingatkanmu secara otomatis saat waktu sholat tiba.
Semoga harimu penuh keberkahan dan ketenangan. 🌤🕌"""
    kirim_telegram(pesan)

@bot.message_handler(commands=['start'])
def handle_start(message):
    if message.chat.id == CHAT_ID and message.message_thread_id == THREAD_ID:
        kirim_sambutan()

@bot.message_handler(commands=['jadwal'])
def handle_jadwal(message):
    if message.chat.id == CHAT_ID and message.message_thread_id == THREAD_ID:
        kirim_jadwal()

@bot.message_handler(commands=['update'])
def handle_update(message):
    if message.chat.id == CHAT_ID and message.message_thread_id == THREAD_ID:
        ambil_jadwal()
        waktu = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        kirim_telegram(f"""✅ Jadwal sholat berhasil diperbarui pada <b>{waktu}</b>.
Ketik <b>/jadwal</b> untuk melihat jadwal terbaru.""")

user_states = {}
user_data = {}

@bot.message_handler(commands=['setlokasi'])
def handle_setlokasi(message):
    if message.chat.id == CHAT_ID and message.message_thread_id == THREAD_ID:
        user_id = message.from_user.id
        user_states[user_id] = "awaiting_lat"
        user_data[user_id] = {}
        bot.reply_to(message, "Silakan masukkan koordinat <b>Latitude</b> Anda:", parse_mode="HTML")

@bot.message_handler(func=lambda msg: msg.chat.id == CHAT_ID and msg.message_thread_id == THREAD_ID)
def handle_user_input(message):
    user_id = message.from_user.id
    state = user_states.get(user_id)

    if not state:
        return  # tidak dalam sesi input /setlokasi

    if state == "awaiting_lat":
        try:
            user_data[user_id]["LAT"] = float(message.text.strip())
            user_states[user_id] = "awaiting_lon"
            bot.reply_to(message, "Sekarang masukkan koordinat <b>Longitude</b> Anda:", parse_mode="HTML")
        except:
            bot.reply_to(message, "Format Latitude tidak valid. Harap masukkan angka, contoh: -7.5467", parse_mode="Markdown")

    elif state == "awaiting_lon":
        try:
            user_data[user_id]["LON"] = float(message.text.strip())
            user_states[user_id] = "awaiting_kota"
            bot.reply_to(message, "Terakhir, masukkan <b>nama kota</b> Anda:", parse_mode="HTML")
        except:
            bot.reply_to(message, "Format Longitude tidak valid. Harap masukkan angka, contoh: 109.0899", parse_mode="Markdown")

    elif state == "awaiting_kota":  # ✅ dipindah ke sini
        user_data[user_id]["KOTA"] = message.text.strip()
        try:
            # Simpan ke konfirgurasi.txt
            with open("/etc/jadwalsholat/konfirgurasi.txt", "r") as f:
                lines = f.readlines()

            new_lines = []
            for line in lines:
                if line.startswith("LAT="):
                    new_lines.append(f'LAT={user_data[user_id]["LAT"]}\n')
                elif line.startswith("LON="):
                    new_lines.append(f'LON={user_data[user_id]["LON"]}\n')
                elif line.startswith("KOTA="):
                    new_lines.append(f'KOTA={user_data[user_id]["KOTA"]}\n')
                else:
                    new_lines.append(line)

            with open("/etc/jadwalsholat/konfirgurasi.txt", "w") as f:
                f.writelines(new_lines)

            # Ambil ulang jadwal sholat
            waktu_sholat = ambil_jadwal()  # panggil API berdasarkan lokasi baru

            bot.reply_to(message, f"""✅ Lokasi berhasil diperbarui!
📍 <b>{user_data[user_id]["KOTA"]}</b>
🌐 Koordinat: <code>{user_data[user_id]["LAT"]}, {user_data[user_id]["LON"]}</code>

Silakan ketik /jadwal untuk melihat jadwal salat terbaru.""", parse_mode="HTML")

        except Exception as e:
            bot.reply_to(message, f"Gagal memperbarui lokasi: {e}")

        # Clear state
        user_states.pop(user_id, None)
        user_data.pop(user_id, None)

def loop_pengingat():
    waktu_sholat = ambil_jadwal()
    terakhir_update = time.time()
    dikirim = set()

    while True:
        now = datetime.now()
        waktu_now = now.strftime("%H:%M")

        if waktu_now == "00:05":
            kirim_jadwal()
            time.sleep(60)

        if waktu_now == "00:01":
            dikirim.clear()

        if time.time() - terakhir_update > 5 * 3600:
            waktu_sholat = ambil_jadwal()
            terakhir_update = time.time()

        if waktu_sholat:
            waktu_imsak = waktu_sholat["Imsak"]
            if waktu_now == waktu_imsak and waktu_now not in dikirim:
                pesan = get_pesan_acak(FILE_PAGI) or "Awali pagi ini dengan semangat dan senyuman terbaikmu."
                kirim_telegram(f"""<b>🕓 {waktu_imsak}</b>
⏰ <b>Waktu Imsak Telah Tiba!</b>

Sudah saatnya bersiap untuk Subuh di wilayah <b>{KOTA}</b> dan sekitarnya.

<b><i>{pesan}</i></b>""")
                dikirim.add(waktu_now)

            mapping = {
                waktu_sholat["Subuh"]: "Subuh",
                waktu_sholat["Dzuhur"]: "Dzuhur",
                waktu_sholat["Asar"]: "Asar",
                waktu_sholat["Maghrib"]: "Maghrib",
                waktu_sholat["Isya"]: "Isya"
            }

            if waktu_now in mapping and waktu_now not in dikirim:
                salat = mapping[waktu_now]
                pesan = get_pesan_acak(FILE_KATA) or "Jangan lewatkan sholatmu, karena itu bekal terbaik untuk hari esok."
                kirim_telegram(f"""<b>🕒 {waktu_now}</b>
Saat ini telah masuk waktu sholat <b>{salat}</b>  
untuk wilayah <b>{KOTA}</b> dan sekitarnya.

<i><b>"{pesan}"</b></i>""")
                dikirim.add(waktu_now)

        time.sleep(61)

# === Mulai Bot ===
if __name__ == "__main__":
    threading.Thread(target=loop_pengingat, daemon=True).start()
    bot.infinity_polling()
