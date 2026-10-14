
import sqlite3
import telebot
import random
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8944140702:AAH7lpwfvrYuCPiCBwLc3cll7VMhU_YiYHg"
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
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("🎮 በ 10 ብር ተጫወት", callback_data="play_10"),
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
        response_msg = f"🎉 እንኳን ደህና መጡ {full_name}!\n\nለማስጀመር <b>10 ብር ቦነስ</b> ተሰጥቶዎታል።\n\nለመጫወት ከታች ካሉት አዝራሮች አንዱን ይምረጡ፦"
    else:
        response_msg = f"ሰላም <b>{full_name}</b>! እንኳን ደህና መጡ።\n\nለመጫወት ከታች ካሉት አዝራሮች አንዱን ይምረጡ፦"

    conn.close()
    bot.reply_to(message, response_msg, parse_mode="HTML", reply_markup=main_keyboard())

def generate_bingo_card():
    card = random.sample(range(1, 76), 15)
    card_str = "🎰 <b>የእርስዎ የቢንጎ ካርቴላ</b> 🎰\n\n"
    card_str += f" | {card[0]:02d} | {card[1]:02d} | {card[2]:02d} |\n"
    card_str += f" | {card[3]:02d} | {card[4]:02d} | {card[5]:02d} |\n"
    card_str += f" | {card[6]:02d} | {card[7]:02d} | {card[8]:02d} |\n"
    card_str += f" | {card[9]:02d} | {card[10]:02d} | {card[11]:02d} |\n"
    card_str += f" | {card[12]:02d} | {card[13]:02d} | {card[14]:02d} |\n"
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
            "💳 <b>የባንክ አማራጮች፦</b>\n"
            "<i>(Tap to copy)</i>👇👇👇\n\n"
            "Tele birr: <code>0985177839</code>\n"
            "CBE: <code>1000745390448</code>\n"
            "BOA: <code>92707617</code>\n"
            "Amhara Bank: <code>9900039885356</code>\n"
            "Tsedey Bank: 0544470000669\n"
            "Abay Bank: 4151013046984015\n"
            "Hibret Bank: 2710415626399014\n"
            "Awash Bank: 014251726692000\n\n"
            "📌 ክፍያ ከፈፀሙ በኋላ ደረሰኙን ለአድሚን ይላኩ።"
        )
        bot.send_message(chat_id, deposit_text, parse_mode="HTML")

    elif call.data == "play_10":
        if balance >= 10:
            new_balance = balance - 10
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            
            bot.answer_callback_query(call.id, "10 ብር ከሂሳብዎ ተቀንሷል።")
            bot.send_message(chat_id, "🎯 <b>በ 10 ብር ጨዋታ ተመዝግበዋል!</b>\n\nጨዋታው በ 5 ሰከንድ ውስጥ ይጀምራል...", parse_mode="HTML")
            
            time.sleep(3)
            card_text = generate_bingo_card()
            bot.send_message(chat_id, card_text, parse_mode="HTML")
            
            time.sleep(2)
            bot.send_message(chat_id, "📢 <b>የቁጥር አጠራር ተጀምሯል!</b>", parse_mode="HTML")
            
            called_numbers = random.sample(range(1, 76), 5)
            for num in called_numbers:
                time.sleep(2)
                bot.send_message(chat_id, f"🎲 የተጠራው ቁጥር፦ <b>{num}</b>", parse_mode="HTML")

            time.sleep(2)
            bot.send_message(chat_id, "🎉 <b>የዚህ ዙር ጨዋታ ተጠናቋል!</b>\n\nእንደገና ለመጫወት ከታች ያለውን አዝራር ይጫኑ።", parse_mode="HTML", reply_markup=main_keyboard())

        else:
            bot.answer_callback_query(call.id, "❌ በቂ ቀሪ ሂሳብ የለዎትም! እባክዎን ሂሳብ ይሙሉ/ዴፖዚት ያድርጉ።", show_alert=True)

    elif call.data == "bonus":
        if has_claimed == 0:
            new_balance = balance + 10.0
            cursor.execute("UPDATE users SET balance = ?, has_claimed_bonus = 1 WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            bot.answer_callback_query(call.id, "🎉 የ 10 ብር ቦነስ ተጨምሮልዎታል!", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ ቦነስ የወሰዱት አንድ ጊዜ ብቻ ነው! ቀድመው ወስደዋል።", show_alert=True)

    conn.close()

if __name__ == "__main__":
    init_db()
    print("ቦቱ በሙሉ አሰራር መስራት ጀምሯል...")
    bot.infinity_polling()
