import asyncio
import sqlite3
import logging
import sys
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

# --- SOZLAMALAR (LOYIHA MA'LUMOTLARI) ---
API_TOKEN = '8512126860:AAEvguhPUtgmua8Z8WitHXi5_35l2dQfH2U'
ADMIN_ID = 5670469794  

# SHU YERGA O'Z LOYIHANGIZ LINKINI NUSXALAB QO'YING
LOYIHA_LINKI = "https://openbudget.uz/uz/boards/view/123456" # <--- O'zgartiring!

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# --- BAZA VA PAPKALAR ---
if not os.path.exists('skrinshotlar'):
    os.makedirs('skrinshotlar')

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                  (user_id INTEGER PRIMARY KEY, 
                   full_name TEXT,
                   referrer_id INTEGER, 
                   points INTEGER DEFAULT 0,
                   verified_photos INTEGER DEFAULT 0)''')
conn.commit()

# --- ASOSIY MENYU ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🗳 Ovoz berish")
    builder.button(text="👤 Mening profilim")
    builder.button(text="📢 Taklifnoma")
    builder.button(text="🏆 Reyting")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- FOYDALANUVCHI QISMI ---

@dp.message(CommandStart())
async def start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name
    args = message.text.split()
    referrer_id = args[1] if len(args) > 1 else None

    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()

    if not user:
        cursor.execute("INSERT INTO users (user_id, full_name, referrer_id, points, verified_photos) VALUES (?, ?, ?, 0, 0)", 
                       (user_id, name, referrer_id))
        if referrer_id and referrer_id.isdigit() and int(referrer_id) != user_id:
            cursor.execute("UPDATE users SET points = points + 1 WHERE user_id=?", (int(referrer_id),))
        conn.commit()
    else:
        cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (name, user_id))
        conn.commit()

    await message.answer(
        f"👋 **Assalomu alaykum, {name}!**\n\n"
        "O'z mahallangiz obodonchiligi uchun ovoz yig'ish botiga xush kelibsiz! 🚀\n"
        "Ovoz bering, skrinshot yuboring va sovg'alar yutib oling!",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )

@dp.message(F.text == "🗳 Ovoz berish")
async def vote_info(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Loyihaga o'tish (Ovoz berish) 🌐", url=LOYIHA_LINKI))
    
    text = (
        "🚀 **Ovoz berish bo'yicha yo'riqnoma:**\n\n"
        "1️⃣ Pastdagi tugma orqali loyihaga o'ting.\n"
        "2️⃣ Sahifadagi 'Ovoz berish' tugmasini bosing.\n"
        "3️⃣ SMS kodni kiriting.\n"
        "4️⃣ **Muvaffaqiyatli ovoz berilgani haqidagi xabarni skrinshot qilib shu botga yuboring!**\n\n"
        "🎁 Har bir tasdiqlangan skrinshot uchun ball beriladi!"
    )
    await message.answer(text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.message(F.text == "👤 Mening profilim")
async def my_profile(message: types.Message):
    cursor.execute("SELECT points, verified_photos FROM users WHERE user_id=?", (message.from_user.id,))
    data = cursor.fetchone()
    points, photos = data if data else (0, 0)
    
    text = (
        "📋 **Sizning ma'lumotlaringiz:**\n\n"
        f"👤 Ism: **{message.from_user.full_name}**\n"
        f"🌟 Jami ballar: **{points}**\n"
        f"📸 Tasdiqlangan ovozlar: **{photos}**"
    )
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "🏆 Reyting")
async def ranking(message: types.Message):
    cursor.execute("SELECT full_name, user_id, points FROM users ORDER BY points DESC LIMIT 10")
    top = cursor.fetchall()
    
    text = "🏆 **Eng faol foydalanuvchilar (Top 10):**\n\n"
    for i, (name, uid, p) in enumerate(top, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"{i}."
        text += f"{medal} **{name}**\n   └ ID: `{uid}` — **{p} ball**\n\n"
    
    await message.answer(text, parse_mode="Markdown")

@dp.message(F.text == "📢 Taklifnoma")
async def invite(message: types.Message):
    bot_info = await bot.get_me()
    link = f"https://t.me/{bot_info.username}?start={message.from_user.id}"
    await message.answer(
        f"🔗 **Sizning shaxsiy havolangiz:**\n\n`{link}`\n\n"
        "Do'stlaringizga yuboring va har bir taklif uchun 1 ball oling!",
        parse_mode="Markdown"
    )

# --- SKRINSHOTLARNI QABUL QILISH ---

@dp.message(F.photo)
async def handle_screenshot(message: types.Message):
    photo = message.photo[-1]
    user_id = message.from_user.id
    
    file = await bot.get_file(photo.file_id)
    file_name = f"skrinshotlar/{user_id}_{photo.file_id[:10]}.jpg"
    await bot.download_file(file.file_path, file_name)
    
    await message.reply("📥 **Skrinshot qabul qilindi!**\nAdmin tasdiqlashini kuting...")
    
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="Tasdiqlash ✅", callback_data=f"verify_{user_id}"))
    
    await bot.send_photo(
        ADMIN_ID, 
        photo.file_id, 
        caption=f"⚡️ **Yangi skrinshot!**\nKimdan: {message.from_user.full_name}\nID: `{user_id}`",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("verify_"))
async def approve(callback: types.CallbackQuery):
    if callback.from_user.id == ADMIN_ID:
        target_id = int(callback.data.split("_")[1])
        cursor.execute("UPDATE users SET points = points + 1, verified_photos = verified_photos + 1 WHERE user_id=?", (target_id,))
        conn.commit()
        try:
            await bot.send_message(target_id, "🎉 **Tabriklaymiz!**\nSkrinshotingiz tasdiqlandi. Hisobingizga 1 ball qo'shildi!")
        except: pass
        await callback.message.edit_caption(caption=callback.message.caption + "\n\n✅ **TASDIQLANDI**", parse_mode="Markdown")
        await callback.answer("Ball berildi!")

# --- ADMIN ---
@dp.message(Command("stat"), F.from_user.id == ADMIN_ID)
async def stats(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    await message.answer(f"📊 **Jami foydalanuvchilar:** {count} ta")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
