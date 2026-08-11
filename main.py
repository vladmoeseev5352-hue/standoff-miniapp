import os
import asyncio

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
# КЛАВИАТУРЫ
# =========================

def main_menu():
    keyboard = InlineKeyboardBuilder()

    keyboard.button(text="🛒 Магазин", callback_data="shop")
    keyboard.button(text="💰 Баланс", callback_data="balance")
    keyboard.button(text="👤 Профиль", callback_data="profile")
    keyboard.button(text="📦 Мои покупки", callback_data="purchases")
    keyboard.button(text="💸 Продать скин", callback_data="sell")
    keyboard.button(text="🆘 Поддержка", callback_data="support")

    keyboard.adjust(2, 2, 2)

    return keyboard.as_markup()


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
    await message.answer(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Добро пожаловать на наш рынок скинов!\n\n"
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
        "🔥 AKR12 — Dragon\n"
        "💰 Цена: 350₽\n\n"
        "💎 M4A1 — Crystal\n"
        "💰 Цена: 500₽\n\n"
        "⚡ USP — Cyber\n"
        "💰 Цена: 250₽\n\n"
        "🌌 AWM — Galaxy\n"
        "💰 Цена: 750₽",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# БАЛАНС
# =========================

@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>МОЙ БАЛАНС</b>\n\n"
        "💳 Баланс: <b>0₽</b>\n\n"
        "Пополнение баланса добавим следующим этапом.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПРОФИЛЬ
# =========================

@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    user = callback.from_user

    await callback.message.edit_text(
        "👤 <b>МОЙ ПРОФИЛЬ</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.full_name}\n\n"
        "💰 Баланс: 0₽",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ПОКУПКИ
# =========================

@dp.callback_query(F.data == "purchases")
async def purchases(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦 <b>МОИ ПОКУПКИ</b>\n\n"
        "У тебя пока нет покупок.",
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
        "Раздел находится в разработке.\n\n"
        "Здесь мы сделаем выставление скинов "
        "на продажу другим пользователям.",
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
        "Раздел поддержки находится в разработке.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================
# ЗАПУСК БОТА
# =========================

async def main():
    print("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
