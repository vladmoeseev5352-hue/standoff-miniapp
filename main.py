import os
import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в Secrets")


bot = Bot(token=TOKEN)
dp = Dispatcher()


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
    keyboard.button(text="⬅️ Главное меню", callback_data="home")
    return keyboard.as_markup()


@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Добро пожаловать на наш рынок скинов!\n\n"
        "Выбери нужный раздел 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "home")
async def home(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Выбери нужный раздел 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "shop")
async def shop(callback: CallbackQuery):
    await callback.message.edit_text(
        "🛒 <b>МАГАЗИН</b>\n\n"
        "Здесь будут находиться скины и их цены.\n\n"
        "🔥 AKR12 — Dragon — 350₽\n"
        "💎 M4A1 — Crystal — 500₽\n"
        "⚡ USP — Cyber — 250₽\n"
        "🌌 AWM — Galaxy — 750₽",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "balance")
async def balance(callback: CallbackQuery):
    await callback.message.edit_text(
        "💰 <b>БАЛАНС</b>\n\n"
        "💳 Ваш баланс: 0₽\n\n"
        "Пополнение сделаем следующим этапом.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile(callback: CallbackQuery):
    await callback.message.edit_text(
        "👤 <b>ПРОФИЛЬ</b>\n\n"
        f"🆔 ID: <code>{callback.from_user.id}</code>\n"
        f"👤 Имя: {callback.from_user.full_name}",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "purchases")
async def purchases(callback: CallbackQuery):
    await callback.message.edit_text(
        "📦 <b>МОИ ПОКУПКИ</b>\n\n"
        "Пока покупок нет.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "sell")
async def sell(callback: CallbackQuery):
    await callback.message.edit_text(
        "💸 <b>ПРОДАЖА СКИНА</b>\n\n"
        "Этот раздел пока в разработке.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


@dp.callback_query(F.data == "support")
async def support(callback: CallbackQuery):
    await callback.message.edit_text(
        "🆘 <b>ПОДДЕРЖКА</b>\n\n"
        "По вопросам работы магазина обращайтесь к администратору.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )
    await callback.answer()


async def main():
    print("Starting Telegram bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
