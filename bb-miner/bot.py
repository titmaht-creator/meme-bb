import asyncio
import os
import sqlite3
import time
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN", "").strip()
DB_PATH = os.getenv("DB_PATH", "bb_miner.sqlite3")
CAP_HOURS = 24

# Sample rates/thresholds only. Confirm tokenomics before any public launch.
LEVELS = [
    ("Bronze", 0, 1.0),
    ("Silver", 500, 1.5),
    ("Gold", 2500, 2.0),
    ("Platinum", 10000, 3.0),
    ("Diamond", 50000, 5.0),
]

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            points REAL NOT NULL DEFAULT 0,
            pending REAL NOT NULL DEFAULT 0,
            last_tick REAL NOT NULL,
            invited_by INTEGER
        )""")

def level_for(points):
    selected = LEVELS[0]
    for level in LEVELS:
        if points >= level[1]:
            selected = level
    return selected

def get_user(user_id, username=None, invited_by=None):
    now = time.time()
    with db() as con:
        row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            con.execute(
                "INSERT INTO users(user_id,username,last_tick,invited_by) VALUES(?,?,?,?)",
                (user_id, username, now, invited_by if invited_by != user_id else None),
            )
            row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        else:
            con.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))
        return dict(row)

def accrue(user_id):
    now = time.time()
    with db() as con:
        row = con.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if row is None:
            return 0.0
        elapsed = max(0, min(now - row["last_tick"], CAP_HOURS * 3600))
        rate = level_for(row["points"] + row["pending"])[2]
        earned = elapsed / 3600 * rate
        con.execute(
            "UPDATE users SET pending=pending+?, last_tick=? WHERE user_id=?",
            (earned, now, user_id),
        )
        return earned

def main_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛏️ Start / Claim", callback_data="claim")],
        [InlineKeyboardButton(text="👤 My Account", callback_data="account"),
         InlineKeyboardButton(text="🤝 Invite", callback_data="invite")],
    ])

dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    referrer = None
    if len(parts) > 1 and parts[1].startswith("ref_"):
        try:
            referrer = int(parts[1][4:])
        except ValueError:
            pass
    get_user(message.from_user.id, message.from_user.username, referrer)
    accrue(message.from_user.id)
    await message.answer(
        "⛏️ Welcome to BB MINER\n\n"
        "Earn in-app points over time and claim them manually. "
        "These points are not cryptocurrency and have no cash value or guaranteed redemption.",
        reply_markup=main_keyboard(),
    )

@dp.callback_query(F.data == "claim")
async def claim(callback: CallbackQuery):
    get_user(callback.from_user.id, callback.from_user.username)
    accrue(callback.from_user.id)
    with db() as con:
        row = con.execute("SELECT points,pending FROM users WHERE user_id=?",
                          (callback.from_user.id,)).fetchone()
        amount = float(row["pending"])
        con.execute("UPDATE users SET points=points+?, pending=0 WHERE user_id=?",
                    (amount, callback.from_user.id))
        total = float(row["points"]) + amount
    level = level_for(total)
    await callback.message.edit_text(
        f"✅ Claimed: {amount:.2f} points\n"
        f"💰 Total: {total:.2f} points\n"
        f"🏅 Level: {level[0]}",
        reply_markup=main_keyboard(),
    )
    await callback.answer()

@dp.callback_query(F.data == "account")
async def account(callback: CallbackQuery):
    get_user(callback.from_user.id, callback.from_user.username)
    accrue(callback.from_user.id)
    with db() as con:
        row = con.execute("SELECT points,pending FROM users WHERE user_id=?",
                          (callback.from_user.id,)).fetchone()
    total = float(row["points"])
    level = level_for(total + float(row["pending"]))
    await callback.message.edit_text(
        f"👤 BB MINER Account\n"
        f"💰 Claimed: {total:.2f}\n"
        f"⏳ Pending: {float(row['pending']):.2f}\n"
        f"🏅 Level: {level[0]}\n"
        f"⚡ Rate: {level[2]:.1f} points/hour",
        reply_markup=main_keyboard(),
    )
    await callback.answer()

@dp.callback_query(F.data == "invite")
async def invite(callback: CallbackQuery, bot: Bot):
    me = await bot.get_me()
    link = f"https://t.me/{me.username}?start=ref_{callback.from_user.id}"
    await callback.message.edit_text(
        f"🤝 Your invite link:\n{link}\n\n"
        "Referral rewards are not enabled in this starter version.",
        reply_markup=main_keyboard(),
    )
    await callback.answer()

@dp.message(Command("help"))
async def help_cmd(message: Message):
    await message.answer(
        "/start — Open BB MINER\n"
        "/help — Show help\n\n"
        "Points are internal demo points, not a blockchain asset."
    )

async def main():
    if not TOKEN or TOKEN == "PASTE_YOUR_BOTFATHER_TOKEN_HERE":
        raise RuntimeError("Set BOT_TOKEN in your local .env file. Do not share it.")
    init_db()
    bot = Bot(TOKEN)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
