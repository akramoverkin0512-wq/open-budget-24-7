import asyncio
import sqlite3
import logging
import sys
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# --- SOZLAMALAR ---
API_TOKEN = os.getenv('API_TOKEN', '8512126860:AAEvguhPUtgmua8Z8WitHXi5_35l2dQfH2U')
ADMIN_ID = int(os.getenv('ADMIN_ID', '5670469794'))
LOYIHA_LINKI = "https://openbudget.uz/uz/boards/view/123456" # O'zingiznikiga almashtiring

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Baza va papka
if not os.path.exists('skrinshotlar'): os.makedirs('skrinshotlar')
conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, full_name TEXT, referrer_id INTEGER, 
                   points INTEGER DEFAULT 0, verified_photos INTEGER DEFAULT 0)''')
conn.commit()

def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🗳 Ovoz berish")
    builder.button(text="👤 Mening profilim")
    builder.button(text="📢 Taklifnoma")
    builder.button(text="🏆 Reyting")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name
    args = message.text.split()
    ref_id = args[1] if len(args) > 1 else None
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (user_id, full_name, referrer_id) VALUES (?, ?, ?)", (user_id, name, ref_id))
        if ref_id and ref_id.isdigit() and int(ref_id) != user_id:
            cursor.execute("UPDATE users SET points = points + 1 WHERE user_id=?", (int(ref_id),))
        conn.commit()
    await message.answer(f"👋 Salom, {name}!", reply_markup=main_menu())

@dp.message(F.text == "🗳 Ovoz berish")
async def vote(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="Ovoz berish sahifasi 🌐", url=LOYIHA_LINKI))
    await message.answer("Ovoz bering va skrinshot yuboring!", reply_markup=kb.as_markup())

@dp.message(F.photo)
async def handle_photo(message: types.Message):
    photo = message.photo[-1]
    file_name = f"skrinshotlar/{message.from_user.id}_{photo.file_id[:10]}.jpg"
    await bot.download(photo, destination=file_name)
    await message.reply("✅ Qabul qilindi! Admin tasdiqlashini kuting.")
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="Tasdiqlash ✅", callback_data=f"verify_{message.from_user.id}"))
    await bot.send_photo(ADMIN_ID, photo.file_id, caption=f"ID: {message.from_user.id}", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("verify_"))
async def approve(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        uid = int(callback.data.split("_")[1])
        cursor.execute("UPDATE users SET points = points + 1, verified_photos = verified_photos + 1 WHERE user_id=?", (uid,))
        conn.commit()
        await bot.send_message(uid, "🎉 Skrinshotingiz tasdiqlandi!")
        await callback.answer("Tasdiqlandi!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())