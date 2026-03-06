import telebot
from telebot import types
import yt_dlp
import os

API_TOKEN = '8629231101:AAHTuIZfokyWRZysZ79NdLQHDZq8zOqou5k'
bot = telebot.TeleBot(API_TOKEN)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_name = message.from_user.first_name
    welcome_text = (f"أهلاً بك يا {user_name}! 🌟\n\n"
                    "أرسل اسم الأغنية للبحث في يوتيوب، أو رابط إنستغرام للتحميل.")
    bot.send_message(message.chat.id, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    text = message.text
    chat_id = message.chat.id
    if "instagram.com" in text:
        bot.reply_to(message, "جاري تحميل إنستغرام... ⏳")
        download_insta(message, text)
    else:
        bot.reply_to(message, "جاري البحث في يوتيوب... 🔎")
        search_and_ask(message, text)

def search_and_ask(message, query):
    ydl_opts = {'format': 'bestaudio/best', 'noplaylist': True, 'quiet': True}
    if "youtube.com" not in query and "youtu.be" not in query:
        query = f"ytsearch1:{query}"
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(query, download=False)
            if 'entries' in info: info = info['entries'][0]
            user_data[message.chat.id] = info['webpage_url']
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🎵 صوت MP3", callback_data="audio"),
                       types.InlineKeyboardButton("🎬 فيديو MP4", callback_data="video"))
            bot.send_message(message.chat.id, f"📌 {info['title']}\n\nاختر الصيغة:", reply_markup=markup)
        except Exception: bot.send_message(message.chat.id, "❌ لم يتم العثور على الفيديو.")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    url = user_data.get(call.message.chat.id)
    if not url: return
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="جاري التحميل... 📥")
    mode = 'mp3' if call.data == "audio" else 'mp4'
    download_yt(call.message, url, mode)

def download_yt(message, url, mode):
    chat_id = message.chat.id
    ydl_opts = {
        'format': 'bestaudio/best' if mode == 'mp3' else 'best',
        'postprocessors': [{'key': 'FFmpegExtractAudio','preferredcodec': 'mp3','preferredquality': '192'}] if mode == 'mp3' else [],
        'outtmpl': f'file_{chat_id}.%(ext)s',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if mode == 'mp3': filename = filename.rsplit('.', 1)[0] + '.mp3'
        with open(filename, 'rb') as f:
            if mode == 'mp3': bot.send_audio(chat_id, f)
            else: bot.send_video(chat_id, f)
        os.remove(filename)
    except Exception as e: bot.send_message(chat_id, f"❌ خطأ: {e}")

def download_insta(message, url):
    ydl_opts = {'format': 'best', 'outtmpl': f'insta_{message.chat.id}.mp4'}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        with open(ydl_opts['outtmpl'], 'rb') as f:
            bot.send_video(message.chat.id, f)
        os.remove(ydl_opts['outtmpl'])
    except Exception: bot.send_message(message.chat.id, "❌ فشل تحميل إنستا.")

bot.polling()
