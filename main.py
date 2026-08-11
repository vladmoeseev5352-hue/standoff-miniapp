import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(message: Message):
    await message.answer(
        "🎮 STANDOFF MARKET\n\n"
        "Бот запущен!\n"
        "Здесь будет наш рынок скинов."
    )


@dp.message(Command("market"))
async def market(message: Message):
    await message.answer(
        "🛒 Рынок\n\n"
        "Здесь появятся актуальные скины и цены."
    )


@dp.message(Command("admin"))
async def admin(message: Message):
    await message.answer(
        "🔐 Админ-панель\n\n"
        "Раздел находится в разработке."
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
