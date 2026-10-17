import sqlite3
import telebot
import random
import time
import os
from gtts import gTTS
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template
from threading import Thread

# 📌 1. Flask Web Server ngam udditde index.html (Mini App)
app = Flask('', template_folder='.')

@app.route('/')
def home():
    return render_template('index.html')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.start()

# 📌 2. Telegram Bot Token
TOKEN = os.environ.get("BOT_TOKEN","8944140702:AAEvwvINJqTS5sVmVryGPdjx5g6YPNUfx-0 ")
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "@sedoobingo" 

def init_db():
    conn = sqlite3.connect("bingo_users.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            balance REAL DEFAULT 10.0,
            has_claimed_bonus INTEGER DEFAULT 1
        )
    """)
    conn.commit()
    conn.close()

def is_user_joined(user_id):
    if CHANNEL_USERNAME == "@YourChannelUsername":
        return True
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        if member.status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception as e:
        print(f"Channel Check Error: {e}")
        return True

def main_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("💳 Balance", callback_data="balance"),
        InlineKeyboardButton("📥 Deposit", callback_data="deposit"),
        InlineKeyboardButton("🎁 Bonus", callback_data="bonus")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    full_name = message.from_user.first_name

    if not is_user_joined(user_id):
        join_btn = InlineKeyboardMarkup()
        join_btn.add(InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        join_btn.add(InlineKeyboardButton("✅ Verify", callback_data="check_join"))
        bot.reply_to(message, f"🚀 Naatu e channel amen adan:\n\n{CHANNEL_USERNAME}", reply_markup=join_btn)
        return

    conn = sqlite3.connect("bingo_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    existing_user = cursor.fetchone()

    if not existing_user:
        cursor.execute(
            "INSERT INTO users (user_id, username, full_name, balance, has_claimed_bonus) VALUES (?, ?, ?, ?, 1)",
            (user_id, username, full_name, 10.0)
        )
        conn.commit()
        response_msg = f"🎉 Bisimillaama <b>SEDOO BINGO</b> {full_name}!\n\nA heɓii <b>10 ETB Bonus</b>."
    else:
        response_msg = f"Jam waali <b>{full_name}</b>! Bisimillaama e <b>SEDOO BINGO</b>."

    conn.close()
    bot.reply_to(message, response_msg, parse_mode="HTML", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    conn = sqlite3.connect("bingo_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT balance, has_claimed_bonus FROM users WHERE user_id = ?", (user_id,))
    res = cursor.fetchone()
    
    balance = res[0] if res else 0.0
    has_claimed = res[1] if res else 1

    if call.data == "balance":
        bot.answer_callback_query(call.id, f"Kaalis ma: {balance:.1f} ETB", show_alert=True)

    elif call.data == "deposit":
        deposit_text = (
            "💳 <b>SEDOO BINGO Bank Options:</b>\n\n"
            "Telebirr: <code>0985177839</code>\n"
            "CBE: <code>1000745390448</code>\n"
        )
        bot.send_message(chat_id, deposit_text, parse_mode="HTML")

    elif call.data == "bonus":
        if has_claimed == 0:
            new_balance = balance + 10.0
            cursor.execute("UPDATE users SET balance = ?, has_claimed_bonus = 1 WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, "🎉 A heɓii 10 ETB bonus!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ A ƴettii bonus ma gila adan!", show_alert=True)

    conn.close()

if __name__ == "__main__":
    init_db()
    keep_alive()
    print("Sedoo Bingo Bot ina gollora no feewi...")
    bot.infinity_polling()
