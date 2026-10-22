import os
import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from flask import Flask, send_from_directory
import threading

TOKEN = "8944140702:AAF_J8e_saDp1gVtGA-WJC4f0mtu4xFl3DI"
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")

app = Flask(__name__, static_folder='.')

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/health')
def health():
    return "OK", 200

DB_PATH = "bingo_users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 140.0
        )
    """)
    conn.commit()
    conn.close()

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    full_name = message.from_user.first_name or "Player"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, full_name) VALUES (?, ?, ?)",
                   (user_id, username, full_name))
    conn.commit()
    conn.close()

    web_app_url = os.environ.get("RENDER_EXTERNAL_URL", "https://addis-bingo-1-4zld.onrender.com")

    markup = InlineKeyboardMarkup()
    play_button = InlineKeyboardButton(
        text="🎰 ADWA BINGO ተጫወት (Open Mini App)",
        web_app=WebAppInfo(url=web_app_url)
    )
    markup.add(play_button)

    welcome_msg = (
        f"🎉 <b>እንኳን ደህና መጡ ወደ ADWA BINGO Mini App, {full_name}!</b>\n\n"
        "በቀጥታ በቴሌግራም ሚኒ አፕ የካርቴላ መምረጫ እና ጨዋታ ለመጀመር ከታች ያለውን አዝራር ይጫኑ፦"
    )

    bot.send_message(message.chat.id, welcome_msg, reply_markup=markup)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    
    # የድሮ ዌብሁኮችን እና ማጣሪያዎችን ለማጥፋት
    bot.remove_webhook()
    print("Adwa Bingo Bot & Mini App backend running smoothly...")
    bot.infinity_polling(skip_pending=True)
