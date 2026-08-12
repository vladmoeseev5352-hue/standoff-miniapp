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
# НАСТРОЙКА MINI APP
# =========================

WEB_APP_URL = "https://vladmoeseev5352-hue.github.io/standoff-miniapp/"


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
# ГЛАВНОЕ МЕНЮ
# =========================

def main_menu():

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🎰 Открыть STANDOFF MARKET",
        web_app={"url": WEB_APP_URL}
    )

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

    keyboard.adjust(1, 2, 2, 2)

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
# /START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    create_user(message.from_user.id)

    await message.answer(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Добро пожаловать на наш рынок скинов!\n\n"
        "🎰 Открой Mini App, чтобы посмотреть "
        "рулетку и магазин.\n\n"
        "💰 Стартовый баланс: 1000₽",
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
        "🛒 <b>МАГАЗИН</b>\n\n"
        "🎰 Для полноценного магазина "
        "открой Mini App.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


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
    value = get_balance(user.id)

    await callback.message.edit_text(
        "👤 <b>МОЙ ПРОФИЛЬ</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.full_name}\n"
        f"💰 Баланс: {value}₽",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПОКУПКИ
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
        "Раздел находится в разработке.",
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
        "Раздел находится в разработке.",
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
