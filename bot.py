import os
import sqlite3
import random
import threading
import logging
from flask import Flask
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# Demo bingo using points only. No real-money deposits, wagers, or cash-outs.
TOKEN = "8944140702:AAF_J8e_saDp1gVtGA-WJC4f0mtu4xFl3DI"
DB_PATH = os.getenv("DB_PATH", "bingo_users.db")
PLAY_COST = 10
STARTING_POINTS = 100

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing. Add your Telegram bot token in Render Environment Variables.")

logging.basicConfig(level=logging.INFO)
bot = telebot.TeleBot(TOKEN, parse_mode="HTML")
app = Flask(__name__)

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                points INTEGER NOT NULL DEFAULT 100,
                games_played INTEGER NOT NULL DEFAULT 0,
                games_won INTEGER NOT NULL DEFAULT 0
            )
        """)

def register_user(user):
    full_name = " ".join(x for x in [user.first_name, user.last_name] if x)
    with db() as conn:
        conn.execute("""
            INSERT INTO users (user_id, username, full_name, points)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                full_name=excluded.full_name
        """, (user.id, user.username, full_name, STARTING_POINTS))

def get_user(user_id):
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()

def change_points(user_id, delta):
    with db() as conn:
        conn.execute("UPDATE users SET points=points+? WHERE user_id=?", (delta, user_id))

def main_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎱 Play Bingo (10 points)", callback_data="play"),
        InlineKeyboardButton("💰 My Points", callback_data="balance"),
    )
    kb.add(
        InlineKeyboardButton("📊 My Stats", callback_data="stats"),
        InlineKeyboardButton("ℹ️ How to Play", callback_data="help"),
    )
    return kb

def make_card():
    columns = [
        random.sample(range(1, 16), 5),
        random.sample(range(16, 31), 5),
        random.sample(range(31, 46), 5),
        random.sample(range(46, 61), 5),
        random.sample(range(61, 76), 5),
    ]
    card = [[columns[c][r] for c in range(5)] for r in range(5)]
    card[2][2] = "★"
    return card

def render_card(card, called):
    labels = ["B", "I", "N", "G", "O"]
    lines = ["<b>B   I   N   G   O</b>"]
    for row in card:
        cells = []
        for value in row:
            if value == "★":
                cells.append("★")
            elif value in called:
                cells.append(f"<b>✓{value}</b>")
            else:
                cells.append(str(value))
        lines.append("  ".join(f"{v:>3}" for v in cells))
    return "<pre>" + "\n".join(lines) + "</pre>"

def has_bingo(card, called):
    def marked(v):
        return v == "★" or v in called
    for row in card:
        if all(marked(v) for v in row):
            return True
    for c in range(5):
        if all(marked(card[r][c]) for r in range(5)):
            return True
    if all(marked(card[i][i]) for i in range(5)):
        return True
    if all(marked(card[i][4-i]) for i in range(5)):
        return True
    return False

def new_game_text(card, called, latest=None):
    msg = "🎱 <b>Your Bingo Card</b>\n"
    if latest is not None:
        msg += f"\n🔢 Number drawn: <b>{latest}</b>\n"
    msg += "\n" + render_card(card, called)
    msg += "\nNumbers are drawn one at a time. Complete a row, column, or diagonal to win 20 points."
    return msg

@bot.message_handler(commands=["start"])
def start(message):
    register_user(message.from_user)
    bot.send_message(
        message.chat.id,
        "🎉 <b>Welcome to Adwa Bingo!</b>\n\n"
        "Play with free demo points only. Points have no cash value and cannot be deposited or withdrawn.\n"
        f"You start with <b>{STARTING_POINTS} points</b>.\n\nChoose an option:",
        reply_markup=main_keyboard()
    )

@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "🎱 <b>How to play</b>\n"
        f"• Each game costs {PLAY_COST} points.\n"
        "• A random number is drawn each turn.\n"
        "• Complete a row, column, or diagonal to win 20 points.\n"
        "• If you run out of points, use /daily to claim 20 free points once every 24 hours.\n"
        "• Demo points have no cash value and cannot be exchanged for money."
    )

@bot.message_handler(commands=["daily"])
def daily(message):
    register_user(message.from_user)
    with db() as conn:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "last_daily" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN last_daily INTEGER NOT NULL DEFAULT 0")
        user = conn.execute("SELECT points, last_daily FROM users WHERE user_id=?", (message.from_user.id,)).fetchone()
        import time
        now = int(time.time())
        if now - user["last_daily"] < 86400:
            remaining = 86400 - (now - user["last_daily"])
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            bot.send_message(message.chat.id, f"⏳ Daily points already claimed. Try again in about {hours}h {minutes}m.")
            return
        conn.execute("UPDATE users SET points=points+20, last_daily=? WHERE user_id=?", (now, message.from_user.id))
    bot.send_message(message.chat.id, "🎁 You received 20 free demo points!", reply_markup=main_keyboard())

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    user_id = call.from_user.id
    register_user(call.from_user)
    user = get_user(user_id)

    if call.data == "balance":
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"💰 You have <b>{user['points']} demo points</b>.")
    elif call.data == "stats":
        bot.answer_callback_query(call.id)
        bot.send_message(
            call.message.chat.id,
            f"📊 <b>Your stats</b>\nGames played: {user['games_played']}\nBingo wins: {user['games_won']}\nPoints: {user['points']}"
        )
    elif call.data == "help":
        bot.answer_callback_query(call.id)
        help_command(call.message)
    elif call.data == "play":
        bot.answer_callback_query(call.id)
        if user["points"] < PLAY_COST:
            bot.send_message(call.message.chat.id, "You need 10 demo points to play. Use /daily to claim free points.")
            return
        change_points(user_id, -PLAY_COST)
        with db() as conn:
            conn.execute("UPDATE users SET games_played=games_played+1 WHERE user_id=?", (user_id,))
        card = make_card()
        called = []
        game_kb = InlineKeyboardMarkup()
        game_kb.add(InlineKeyboardButton("🔢 Draw next number", callback_data="draw"))
        game_kb.add(InlineKeyboardButton("🏠 Main menu", callback_data="menu"))
        active_games[user_id] = {"card": card, "called": called}
        bot.send_message(call.message.chat.id, new_game_text(card, called), reply_markup=game_kb)
    elif call.data == "draw":
        bot.answer_callback_query(call.id)
        game = active_games.get(user_id)
        if not game:
            bot.send_message(call.message.chat.id, "No active game. Press Play Bingo to start a new game.", reply_markup=main_keyboard())
            return
        remaining = [n for n in range(1, 76) if n not in game["called"]]
        if not remaining:
            bot.send_message(call.message.chat.id, "All numbers were drawn. Start a new game from the menu.", reply_markup=main_keyboard())
            active_games.pop(user_id, None)
            return
        number = random.choice(remaining)
        game["called"].append(number)
        card = game["card"]
        called = game["called"]
        if has_bingo(card, called):
            change_points(user_id, 20)
            with db() as conn:
                conn.execute("UPDATE users SET games_won=games_won+1 WHERE user_id=?", (user_id,))
            active_games.pop(user_id, None)
            bot.send_message(
                call.message.chat.id,
                "🏆 <b>BINGO! You won 20 demo points!</b>\n\n" + new_game_text(card, called, number),
                reply_markup=main_keyboard()
            )
        elif len(called) >= 50:
            active_games.pop(user_id, None)
            bot.send_message(call.message.chat.id, new_game_text(card, called, number) + "\n\nGame ended. Try again!", reply_markup=main_keyboard())
        else:
            game_kb = InlineKeyboardMarkup()
            game_kb.add(InlineKeyboardButton("🔢 Draw next number", callback_data="draw"))
            game_kb.add(InlineKeyboardButton("🏠 Main menu", callback_data="menu"))
            bot.send_message(call.message.chat.id, new_game_text(card, called, number), reply_markup=game_kb)
    elif call.data == "menu":
        bot.answer_callback_query(call.id)
        active_games.pop(user_id, None)
        bot.send_message(call.message.chat.id, "🏠 Main menu:", reply_markup=main_keyboard())
    else:
        bot.answer_callback_query(call.id, "Unknown option")

active_games = {}

@app.get("/")
def health():
    return "Adwa Bingo bot is running (demo points only).", 200

@app.get("/health")
def health_check():
    return {"status": "ok"}, 200

def run_web():
    port = int(os.getenv("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    init_db()
    with db() as conn:
        cols = [r["name"] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "last_daily" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN last_daily INTEGER NOT NULL DEFAULT 0")
    threading.Thread(target=run_web, daemon=True).start()
    logging.info("Starting Adwa Bingo polling bot")
    bot.infinity_polling(skip_pending=True, timeout=30, long_polling_timeout=30)
