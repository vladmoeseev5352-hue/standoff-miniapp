import os
import asyncio
import sqlite3

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в GitHub Secrets")


bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================
# БАЗА ДАННЫХ
# =========================

db = sqlite3.connect("market.db")

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER NOT NULL DEFAULT 1000
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skin_name TEXT NOT NULL,
    price INTEGER NOT NULL
)
""")

db.commit()


def create_user(user_id: int):
    db.execute(
        "INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, ?)",
        (user_id, 1000)
    )
    db.commit()


def get_balance(user_id: int):
    create_user(user_id)

    result = db.execute(
        "SELECT balance FROM users WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    return result[0]


# =========================
# СКИНЫ
# =========================

SKINS = [
    {
        "id": 1,
        "name": "🔥 AKR12 — Dragon",
        "price": 350
    },
    {
        "id": 2,
        "name": "💎 M4A1 — Crystal",
        "price": 500
    },
    {
        "id": 3,
        "name": "⚡ USP — Cyber",
        "price": 250
    },
    {
        "id": 4,
        "name": "🌌 AWM — Galaxy",
        "price": 750
    }
]


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

def main_menu():

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🛒 Магазин",
        callback_data="shop"
    )

    keyboard.button(
        text="💰 Баланс",
        callback_data="balance"
    )

    keyboard.button(
        text="👤 Профиль",
        callback_data="profile"
    )

    keyboard.button(
        text="📦 Мои покупки",
        callback_data="purchases"
    )

    keyboard.button(
        text="💸 Продать скин",
        callback_data="sell"
    )

    keyboard.button(
        text="🆘 Поддержка",
        callback_data="support"
    )

    keyboard.adjust(2, 2, 2)

    return keyboard.as_markup()


# =========================
# КНОПКА НАЗАД
# =========================

def back_button():

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="⬅️ Главное меню",
        callback_data="home"
    )

    return keyboard.as_markup()


# =========================
# КНОПКИ МАГАЗИНА
# =========================

def shop_keyboard():

    keyboard = InlineKeyboardBuilder()

    for skin in SKINS:

        keyboard.button(
            text=f"{skin['name']} — {skin['price']}₽",
            callback_data=f"skin:{skin['id']}"
        )

    keyboard.button(
        text="⬅️ Главное меню",
        callback_data="home"
    )

    keyboard.adjust(1)

    return keyboard.as_markup()


# =========================
# /START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    create_user(message.from_user.id)

    await message.answer(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Добро пожаловать на наш рынок скинов!\n\n"
        "💰 На старте тебе начислено 1000₽.\n\n"
        "Выбери нужный раздел 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


# =========================
# ГЛАВНОЕ МЕНЮ
# =========================

@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):

    await callback.message.edit_text(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Выбери нужный раздел 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# МАГАЗИН
# =========================

@dp.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):

    await callback.message.edit_text(
        "🛒 <b>МАГАЗИН STANDOFF MARKET</b>\n\n"
        "Выбери скин:",
        reply_markup=shop_keyboard(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# КАРТОЧКА СКИНА
# =========================

@dp.callback_query(F.data.startswith("skin:"))
async def skin(callback: CallbackQuery):

    skin_id = int(callback.data.split(":")[1])

    skin = next(
        skin for skin in SKINS
        if skin["id"] == skin_id
    )

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text=f"🛒 Купить за {skin['price']}₽",
        callback_data=f"buy:{skin['id']}"
    )

    keyboard.button(
        text="⬅️ Назад в магазин",
        callback_data="shop"
    )

    keyboard.adjust(1)

    await callback.message.edit_text(
        f"🎨 <b>{skin['name']}</b>\n\n"
        f"💰 Цена: <b>{skin['price']}₽</b>\n\n"
        "Нажми кнопку ниже, чтобы купить этот скин.",
        reply_markup=keyboard.as_markup(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПОКУПКА
# =========================

@dp.callback_query(F.data.startswith("buy:"))
async def buy(callback: CallbackQuery):

    user_id = callback.from_user.id

    create_user(user_id)

    skin_id = int(callback.data.split(":")[1])

    skin = next(
        skin for skin in SKINS
        if skin["id"] == skin_id
    )

    balance = get_balance(user_id)

    if balance < skin["price"]:

        await callback.answer(
            "❌ Недостаточно денег!",
            show_alert=True
        )

        return

    new_balance = balance - skin["price"]

    db.execute(
        "UPDATE users SET balance = ? WHERE user_id = ?",
        (new_balance, user_id)
    )

    db.execute(
        """
        INSERT INTO purchases
        (user_id, skin_name, price)
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            skin["name"],
            skin["price"]
        )
    )

    db.commit()

    await callback.message.edit_text(
        "✅ <b>ПОКУПКА УСПЕШНА!</b>\n\n"
        f"🎨 {skin['name']}\n"
        f"💰 Потрачено: {skin['price']}₽\n"
        f"💳 Новый баланс: {new_balance}₽",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer("Покупка совершена! 🎉")


# =========================
# БАЛАНС
# =========================

@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):

    value = get_balance(callback.from_user.id)

    await callback.message.edit_text(
        "💰 <b>МОЙ БАЛАНС</b>\n\n"
        f"💳 Баланс: <b>{value}₽</b>",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПРОФИЛЬ
# =========================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):

    create_user(callback.from_user.id)

    user = callback.from_user
    balance = get_balance(user.id)

    await callback.message.edit_text(
        "👤 <b>МОЙ ПРОФИЛЬ</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.full_name}\n"
        f"💰 Баланс: {balance}₽",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# МОИ ПОКУПКИ
# =========================

@dp.callback_query(F.data == "purchases")
async def purchases(callback: CallbackQuery):

    rows = db.execute(
        """
        SELECT skin_name, price
        FROM purchases
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (callback.from_user.id,)
    ).fetchall()

    if not rows:

        text = (
            "📦 <b>МОИ ПОКУПКИ</b>\n\n"
            "Покупок пока нет."
        )

    else:

        items = []

        for skin_name, price in rows:

            items.append(
                f"🎨 {skin_name} — {price}₽"
            )

        text = (
            "📦 <b>МОИ ПОКУПКИ</b>\n\n"
            + "\n".join(items)
        )

    await callback.message.edit_text(
        text,
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПРОДАЖА
# =========================

@dp.callback_query(F.data == "sell")
async def sell(callback: CallbackQuery):

    await callback.message.edit_text(
        "💸 <b>ПРОДАЖА СКИНА</b>\n\n"
        "Этот раздел сделаем следующим этапом.\n\n"
        "Здесь пользователи смогут выставлять "
        "свои скины на продажу.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПОДДЕРЖКА
# =========================

@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):

    await callback.message.edit_text(
        "🆘 <b>ПОДДЕРЖКА</b>\n\n"
        "По вопросам работы магазина "
        "обращайтесь к администратору.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ЗАПУСК
# =========================

async def main():

    print("Starting Telegram bot...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
