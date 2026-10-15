import sqlite3
import telebot
import random
import time
import os
from gtts import gTTS
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# የቦት ቶከን
TOKEN = "8944140702:AAHRQf4NUsJG5VJ87Q2tLXLsQdf9RwYDzz0"
bot = telebot.TeleBot(TOKEN)

# 📌 የቴሌግራም ቻናል Username (ቻናል ከሌለህ ወይም ማስገደድ ካልፈለግህ እንደዚሁ ተወው)
CHANNEL_USERNAME = "@YourChannelUsername" 

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

    if not is_user_joined(user_id):
        join_btn = InlineKeyboardMarkup()
        join_btn.add(InlineKeyboardButton("📢 ቻናላችንን ይቀላቀሉ", url=f"https://t.me/{CHANNEL_USERNAME.replace('@', '')}"))
        join_btn.add(InlineKeyboardButton("✅ ተቀላቅያለሁ / Verify", callback_data="check_join"))
        bot.reply_to(message, f"🚀 ቦቱን ለመጠቀም እባክዎን አስቀድመው ቻናላችንን ይቀላቀሉ፦\n\n{CHANNEL_USERNAME}", reply_markup=join_btn)
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
        response_msg = f"🎉 እንኳን ደህና መጡ ወደ <b>SEDOO BINGO</b> {full_name}!\n\nለማስጀመር <b>10 ብር ቦነስ</b> ተሰጥቶዎታል።\n\nለመጫወት ከታች ካሉት አዝራሮች አንዱን ይምረጡ፦"
    else:
        response_msg = f"ሰላም <b>{full_name}</b>! እንኳን ደህና መጡ ወደ <b>SEDOO BINGO</b>።\n\nለመጫወት ከታች ካሉት አዝራሮች አንዱን ይምረጡ፦"

    conn.close()
    bot.reply_to(message, response_msg, parse_mode="HTML", reply_markup=main_keyboard())

def generate_bingo_card():
    col_b = random.sample(range(1, 16), 5)
    col_i = random.sample(range(16, 31), 5)
    col_n = random.sample(range(31, 46), 5)
    col_n[2] = "⭐"
    col_g = random.sample(range(46, 61), 5)
    col_o = random.sample(range(61, 76), 5)

    card_str = "🎰 <b>SEDOO BINGO - CARTELA</b> 🎰\n\n"
    card_str += "<code> B   I   N   G   O </code>\n"
    for r in range(5):
        n_val = f"{col_n[r]:02d}" if col_n[r] != "⭐" else " ⭐ "
        card_str += f"<code>{col_b[r]:02d} | {col_i[r]:02d} | {n_val} | {col_g[r]:02d} | {col_o[r]:02d}</code>\n"
    
    return card_str

def send_number_voice(chat_id, num):
    try:
        text_to_speak = str(num)
        tts = gTTS(text=text_to_speak, lang='en', slow=False)
        voice_filename = f"voice_{num}.ogg"
        tts.save(voice_filename)
        
        with open(voice_filename, 'rb') as audio:
            bot.send_voice(chat_id, audio)
            
        if os.path.exists(voice_filename):
            os.remove(voice_filename)
    except Exception as e:
        print(f"Voice error: {e}")
        bot.send_message(chat_id, f"🎲 የተጠራው ቁጥር፦ <b>{num}</b>", parse_mode="HTML")

@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id

    if call.data == "check_join":
        if is_user_joined(user_id):
            bot.answer_callback_query(call.id, "✅ ማረጋገጡ ተጠናቋል! እንኳን ደህና መጡ።", show_alert=True)
            bot.send_message(chat_id, "🎮 ለመጫወት ከታች ካሉት አዝራሮች ይምረጡ፦", reply_markup=main_keyboard())
        else:
            bot.answer_callback_query(call.id, "❌ አሁንም ቻናሉን አልተቀላቀሉም!", show_alert=True)
        return
    
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
            "Tele birr: <code>0985177839</code>\n"
            "CBE: <code>1000745390448</code>\n"
            "BOA: <code>92707617</code>\n\n"
            "📌 ክፍያ ከፈፀሙ በኋላ ደረሰኙን ለአድሚን ይላኩ።"
        )
        bot.send_message(chat_id, deposit_text, parse_mode="HTML")

    elif call.data == "play_10":
        if balance >= 10:
            new_balance = balance - 10
            cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
            conn.commit()
            
            game_id = random.randint(800, 999)
            bot.answer_callback_query(call.id, "10 ብር ከሂሳብዎ ተቀንሷል።")
            bot.send_message(chat_id, f"🎯 <b>Game ID: {game_id}</b>\nጨዋታው ተጀምሯል, ካርቴላዎ እየወጣ ነው...", parse_mode="HTML")
            
            time.sleep(3)
            card_text = generate_bingo_card()
            bot.send_message(chat_id, card_text, parse_mode="HTML")
            
            time.sleep(2)
            bot.send_message(chat_id, "📢 <b>የቁጥር አጠራር በድምጽ ተጀምሯል!</b>", parse_mode="HTML")
            
            called_numbers = random.sample(range(1, 76), 5)
            for num in called_numbers:
                time.sleep(2)
                send_number_voice(chat_id, num)

            time.sleep(2)
            bot.send_message(chat_id, "🎉 <b>የዚህ ዙር ጨዋታ ተጠናቋል!</b>", parse_mode="HTML", reply_markup=main_keyboard())

        else:
            bot.answer_callback_query(call.id, "❌ በቂ ቀሪ ሂሳብ የለዎትም!", show_alert=True)

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
    print("Sedoo Bingo ቦቱ በሙሉ አሰራር መስራት ጀምሯል...")
    bot.infinity_polling()
