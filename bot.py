import sqlite3
import telebot
import random
import time
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template
from threading import Thread

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

TOKEN = os.environ.get("BOT_TOKEN","8944140702:AAF_J8e_saDp1gVtGA-WJC4f0mtu4xFl3DI")
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
        InlineKeyboardButton("💳 ቀሪ ሂሳብ (Balance)", callback_data="balance"),
        InlineKeyboardButton("📥 ዴፖዚት (Deposit)", callback_data="deposit"),
        InlineKeyboardButton("🎁 ቦነስ ይውሰዱ", callback_data="bonus")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    full_name = message.from_user.first_name

    if not is_user_joined(user_id):
        join_btn = InlineKeyboardMarkup()
        join_btn.add(InlineKeyboardButton("📢 ቻናላችንን ይቀላቀሉ", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        join_btn.add(InlineKeyboardButton("✅ ተቀላቅያለሁ / Verify", callback_data="check_join"))
        bot.reply_to(message, f"🚀 ቦቱን ለመጠቀም እባክዎን አስቀድመው የቴሌግራም ቻናላችንን ይቀላቀሉ፦\n\n{CHANNEL_USERNAME}", reply_markup=join_btn)
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
        response_msg = f"🎉 እንኳን ደህና መጡ ወደ <b>SEDOO BINGO</b> {full_name}!\n\nለማስጀመር <b>10 ብር ቦነስ</b> ተሰጥቶዎታል።"
    else:
        response_msg = f"ሰላም <b>{full_name}</b>! እንኳን ደህና መጡ ወደ <b>SEDOO BINGO</b>።"

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
        bot.answer_callback_query(call.id, f"የእርስዎ ቀሪ ሂሳብ፦ {balance:.1f} ብር ነው", show_alert=True)

    elif call.data == "deposit":
        deposit_text = (
            "💳 <b>የSEDOO BINGO የባንክ አማራጮች፦</b>\n\n"
            "Telebirr: <code>0985177839</code>\n"
            "CBE: <code>1000745390448</code>\n"
        )
        bot.send_message(chat_id, deposit_text, parse_mode="HTML")

    elif call.data == "bonus":
        if has_claimed == 0:
            new_balance = balance + 10.0
            cursor.execute("UPDATE users SET balance = ?, has_claimed_bonus = 1 WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, "🎉 የ 10 ብር ቦነስ ተጨምሮልዎታል!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ ቦነስ የወሰዱት አንድ ጊዜ ብቻ ነው!", show_alert=True)

    conn.close()

if __name__ == "__main__":
    init_db()
    keep_alive()
    print("Sedoo Bingo ቦቱ በሙሉ አሰራር መስራት ጀምሯል...")
    bot.infinity_polling()
