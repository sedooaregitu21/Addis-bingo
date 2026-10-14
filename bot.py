import sqlite3
import telebot
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8944140702:AAHRQf4NUsJG5VJ87Q2tLXLsQdf9RwYDzz0"
bot = telebot.TeleBot(TOKEN)

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

def main_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("🎮 በ 10 ብር ተጫወት", callback_data="play_10"),
        InlineKeyboardButton("🎮 በ 20 ብር ተጫወት", callback_data="play_20"),
        InlineKeyboardButton("💳 ቀሪ ሂሳብ", callback_data="balance"),
        InlineKeyboardButton("📥 ዴፖዚት (Deposit)", callback_data="deposit"),
        InlineKeyboardButton("🎁 ቦነስ ይውሰዱ", callback_data="bonus")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    full_name = message.from_user.first_name

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
        response_msg = f"🎉 እንኳን ደህና መጡ {full_name}!\n\nለማስጀመር <b>10 ብር ቦነስ</b> ተሰጥቶዎታል።\n\nADWA Bingo ለመጫወት ከታች ካሉት አማራጮች ይምረጡ፦"
    else:
        response_msg = f"ሰላም <b>{full_name}</b>!\n\nወደ ADWA Bingo እንኳን ደህና መጡ። ለመጫወት ከታች ይምረጡ፦"

    conn.close()
    bot.reply_to(message, response_msg, parse_mode="HTML", reply_markup=main_keyboard())

def generate_adwa_bingo_card():
    # ትክክለኛ የቢንጎ አምድ ስንጥቀት (B I N G O)
    col_b = random.sample(range(1, 16), 5)
    col_i = random.sample(range(16, 31), 5)
    col_n = random.sample(range(31, 46), 5)
    col_n[2] = "⭐" # መሀል ላይ ፍሪ ስፔስ (Free Space)
    col_g = random.sample(range(46, 61), 5)
    col_o = random.sample(range(61, 76), 5)

    card_str = "🎰 <b>ADWA BINGO - CARTELA #3</b> 🎰\n\n"
    card_str += "<code> B   I   N   G   O </code>\n"
    for r in range(5):
        n_val = f"{col_n[r]:02d}" if col_n[r] != "⭐" else " ⭐ "
        card_str += f"<code>{col_b[r]:02d} | {col_i[r]:02d} | {n_val} | {col_g[r]:02d} | {col_o[r]:02d}</code>\n"
    
    return card_str

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
            "💳 <b>የባንክ አማራጮች (ADWA Bingo):</b>\n\n"
            "Tele birr: <code>0985177839</code>\n"
            "CBE: <code>1000745390448</code>\n"
            "BOA: <code>92707617</code>\n\n"
            "📌 ክፍያ ከፈፀሙ በኋላ ደረሰኙን ለአድሚን ይላኩ።"
        )
        bot.send_message(chat_id, deposit_text, parse_mode="HTML")

    elif call.data in ["play_10", "play_20"]:
        stake = 10 if call.data == "play_10" else 20
        
        if balance >= stake:
            new_balance = balance - stake
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            
            game_id = random.randint(800, 999)
            bot.answer_callback_query(call.id, f"{stake} ብር ከሂሳብዎ ተቀንሷል።")
            bot.send_message(chat_id, f"🎯 <b>Game ID: {game_id}</b>\nጨዋታው ተጀምሯል, ካርቴላዎ እየወጣ ነው...", parse_mode="HTML")
            
            time.sleep(2)
            card_text = generate_adwa_bingo_card()
            bot.send_message(chat_id, card_text, parse_mode="HTML")
            
            time.sleep(2)
            bot.send_message(chat_id, "📢 <b>ቁጥሮች መጥራት ጀምረዋል...</b>", parse_mode="HTML")
            
            called_numbers = random.sample(range(1, 76), 5)
            for num in called_numbers:
                time.sleep(2)
                bot.send_message(chat_id, f"🎲 የተጠራው ቁጥር፦ <b>{num}</b>", parse_mode="HTML")

            time.sleep(2)
            bot.send_message(chat_id, "🎉 <b>ይህ ዙር ተጠናቋል!</b>", parse_mode="HTML", reply_markup=main_keyboard())

        else:
            bot.answer_callback_query(call.id, "❌ በቂ ቀሪ ሂሳብ የለዎትም! እባክዎን ዴፖዚት ያድርጉ።", show_alert=True)

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
    print("ADWA Bingo ቦት በሙሉ አሰራር መስራት ጀምሯል...")
    bot.infinity_polling()
