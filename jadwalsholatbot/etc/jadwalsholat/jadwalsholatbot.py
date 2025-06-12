import telebot
import requests
import time
import threading
from datetime import datetime
import random

# === Load konfirgurasi dari file ===
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

config = load_konfirgurasi("/etc/jadwalsholat/konfirgurasi.txt")

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
        url = f"https://api.aladhan.com/v1/timings?latitude={LAT}&longitude={LON}&method=20"
        response = requests.get(url).json()

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
    pesan = f"""Assalamu'alaikum teman-teman!

Bot ini akan bantu kamu untuk selalu tepat waktu dalam menjalankan sholat. ⏰✨

Ketik /jadwal untuk melihat jadwal sholat hari ini.
Saya juga akan mengingatkan saat waktu sholat tiba. 🙏

Semoga harimu penuh kebaikan dan keberkahan! 🌸"""
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
    kirim_sambutan()
    threading.Thread(target=loop_pengingat, daemon=True).start()
    bot.infinity_polling()
