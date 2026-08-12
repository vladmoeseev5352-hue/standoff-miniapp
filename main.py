import os
import asyncio
import sqlite3
import hashlib
import hmac
import json
import random
from urllib.parse import parse_qsl

from aiohttp import web

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder


# =========================================================
# НАСТРОЙКИ
# =========================================================

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN не найден в GitHub Secrets")


WEB_APP_URL = "https://vladmoeseev5352-hue.github.io/standoff-miniapp/"

PORT = int(os.getenv("PORT", "8080"))


bot = Bot(token=TOKEN)
dp = Dispatcher()


# =========================================================
# БАЗА ДАННЫХ
# =========================================================

db = sqlite3.connect(
    "market.db",
    check_same_thread=False
)

db.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    balance INTEGER NOT NULL DEFAULT 1000
)
""")

db.execute("""
CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skin_name TEXT NOT NULL,
    price INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

db.commit()


# =========================================================
# ПОЛЬЗОВАТЕЛИ
# =========================================================

def create_user(
    user_id: int,
    username: str = "",
    full_name: str = ""
):
    db.execute(
        """
        INSERT INTO users (
            user_id,
            username,
            full_name,
            balance
        )
        VALUES (?, ?, ?, 1000)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name
        """,
        (
            user_id,
            username,
            full_name
        )
    )

    db.commit()


def get_balance(user_id: int) -> int:

    create_user(user_id)

    result = db.execute(
        """
        SELECT balance
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    ).fetchone()

    return result[0]


def change_balance(
    user_id: int,
    amount: int
) -> bool:

    create_user(user_id)

    current = get_balance(user_id)

    if current + amount < 0:
        return False

    db.execute(
        """
        UPDATE users
        SET balance = balance + ?
        WHERE user_id = ?
        """,
        (
            amount,
            user_id
        )
    )

    db.commit()

    return True


# =========================================================
# СКИНЫ
# =========================================================

SKINS = [

    {
        "name": "AKR12 Dragon",
        "icon": "🔥",
        "type": "Legendary",
        "price": 350
    },

    {
        "name": "M4A1 Crystal",
        "icon": "💎",
        "type": "Epic",
        "price": 500
    },

    {
        "name": "USP Cyber",
        "icon": "⚡",
        "type": "Rare",
        "price": 250
    },

    {
        "name": "AWM Galaxy",
        "icon": "🌌",
        "type": "Legendary",
        "price": 750
    }

]


ROULETTE_SKINS = [

    {
        "name": "USP Cyber",
        "icon": "⚡",
        "chance": 35
    },

    {
        "name": "AKR12 Dragon",
        "icon": "🔥",
        "chance": 25
    },

    {
        "name": "M4A1 Crystal",
        "icon": "💎",
        "chance": 20
    },

    {
        "name": "AWM Galaxy",
        "icon": "🌌",
        "chance": 12
    },

    {
        "name": "Golden",
        "icon": "👑",
        "chance": 6
    },

    {
        "name": "Dragon",
        "icon": "🐉",
        "chance": 2
    }

]


# =========================================================
# РУЛЕТКА
# =========================================================

def get_random_skin():

    total = sum(
        skin["chance"]
        for skin in ROULETTE_SKINS
    )

    value = random.uniform(
        0,
        total
    )

    current = 0

    for skin in ROULETTE_SKINS:

        current += skin["chance"]

        if value <= current:
            return skin

    return ROULETTE_SKINS[0]


# =========================================================
# TELEGRAM INIT DATA
# =========================================================

def validate_init_data(init_data: str):

    if not init_data:
        return None

    try:

        data = dict(
            parse_qsl(
                init_data,
                keep_blank_values=True
            )
        )

        received_hash = data.pop(
            "hash",
            None
        )

        if not received_hash:
            return None

        data_check_string = "\n".join(
            f"{key}={value}"
            for key, value in sorted(
                data.items()
            )
        )

        secret_key = hmac.new(
            b"WebAppData",
            TOKEN.encode(),
            hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(
            calculated_hash,
            received_hash
        ):
            return None

        user_data = json.loads(
            data.get(
                "user",
                "{}"
            )
        )

        return user_data

    except Exception as error:

        print(
            "InitData validation error:",
            error
        )

        return None


# =========================================================
# API — АВТОРИЗАЦИЯ
# =========================================================

def get_user_from_request(request):

    init_data = request.headers.get(
        "X-Telegram-Init-Data",
        ""
    )

    user = validate_init_data(
        init_data
    )

    if not user:
        return None

    user_id = user.get("id")

    if not user_id:
        return None

    create_user(
        user_id=user_id,
        username=user.get(
            "username",
            ""
        ),
        full_name=(
            user.get("first_name", "")
            + " "
            + user.get("last_name", "")
        ).strip()
    )

    return user


# =========================================================
# API — CORS
# =========================================================

def json_response(
    data,
    status=200
):

    response = web.json_response(
        data,
        status=status
    )

    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = (
        "Content-Type, X-Telegram-Init-Data"
    )
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, OPTIONS"
    )

    return response


async def options(request):

    return json_response({})


# =========================================================
# API — ПОЛЬЗОВАТЕЛЬ
# =========================================================

async def api_me(request):

    user = get_user_from_request(
        request
    )

    if not user:

        return json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            401
        )

    user_id = user["id"]

    balance = get_balance(
        user_id
    )

    purchases = db.execute(
        """
        SELECT
            skin_name,
            price,
            created_at
        FROM purchases
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,)
    ).fetchall()

    purchase_list = []

    for row in purchases:

        purchase_list.append(
            {
                "name": row[0],
                "price": row[1],
                "created_at": row[2]
            }
        )

    return json_response(
        {
            "ok": True,

            "user": {
                "id": user_id,
                "username": user.get(
                    "username",
                    ""
                ),
                "name": (
                    user.get("first_name", "")
                    + " "
                    + user.get("last_name", "")
                ).strip()
            },

            "balance": balance,

            "skins": SKINS,

            "purchases": purchase_list
        }
    )


# =========================================================
# API — ПОКУПКА
# =========================================================

async def api_buy(request):

    user = get_user_from_request(
        request
    )

    if not user:

        return json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            401
        )

    try:

        body = await request.json()

        skin_name = body.get(
            "skin"
        )

    except Exception:

        return json_response(
            {
                "ok": False,
                "error": "Invalid JSON"
            },
            400
        )

    skin = next(
        (
            item
            for item in SKINS
            if item["name"] == skin_name
        ),
        None
    )

    if not skin:

        return json_response(
            {
                "ok": False,
                "error": "Skin not found"
            },
            404
        )

    user_id = user["id"]

    price = skin["price"]

    if not change_balance(
        user_id,
        -price
    ):

        return json_response(
            {
                "ok": False,
                "error": "Недостаточно токенов",
                "balance": get_balance(
                    user_id
                )
            },
            400
        )

    db.execute(
        """
        INSERT INTO purchases (
            user_id,
            skin_name,
            price
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            skin["name"],
            price
        )
    )

    db.commit()

    return json_response(
        {
            "ok": True,

            "message": "Покупка успешна",

            "skin": skin,

            "balance": get_balance(
                user_id
            )
        }
    )


# =========================================================
# API — РУЛЕТКА
# =========================================================

async def api_spin(request):

    user = get_user_from_request(
        request
    )

    if not user:

        return json_response(
            {
                "ok": False,
                "error": "Unauthorized"
            },
            401
        )

    user_id = user["id"]

    price = 30

    balance = get_balance(
        user_id
    )

    if balance < price:

        return json_response(
            {
                "ok": False,
                "error": "Недостаточно токенов",
                "balance": balance
            },
            400
        )

    # Списываем 30 токенов
    change_balance(
        user_id,
        -price
    )

    # Определяем выигрыш
    winning_skin = get_random_skin()

    # Добавляем выигрыш в покупки
    db.execute(
        """
        INSERT INTO purchases (
            user_id,
            skin_name,
            price
        )
        VALUES (?, ?, ?)
        """,
        (
            user_id,
            winning_skin["name"],
            30
        )
    )

    db.commit()

    return json_response(
        {
            "ok": True,

            "cost": price,

            "skin": {
                "name": winning_skin["name"],
                "icon": winning_skin["icon"]
            },

            "balance": get_balance(
                user_id
            )
        }
    )


# =========================================================
# API — SKINS
# =========================================================

async def api_skins(request):

    return json_response(
        {
            "ok": True,
            "skins": SKINS,
            "roulette": ROULETTE_SKINS
        }
    )


# =========================================================
# TELEGRAM BOT
# =========================================================

def main_menu():

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="🎰 Открыть STANDOFF MARKET",
        web_app={
            "url": WEB_APP_URL
        }
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

    keyboard.adjust(
        1,
        2,
        2,
        2
    )

    return keyboard.as_markup()


def back_button():

    keyboard = InlineKeyboardBuilder()

    keyboard.button(
        text="⬅️ Главное меню",
        callback_data="home"
    )

    return keyboard.as_markup()


@dp.message(CommandStart())
async def start(message: Message):

    user = message.from_user

    create_user(
        user.id,
        user.username or "",
        user.full_name
    )

    await message.answer(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Добро пожаловать на рынок скинов!\n\n"
        "🎰 Открывай Mini App.\n"
        "🛒 Покупай скины.\n"
        "🎁 Испытывай удачу в рулетке.\n\n"
        "🪙 Стартовый баланс: <b>1000 токенов</b>",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )


@dp.callback_query(F.data == "home")
async def home(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🎮 <b>STANDOFF MARKET</b>\n\n"
        "Выбери нужный раздел 👇",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "shop")
async def shop(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🛒 <b>МАГАЗИН</b>\n\n"
        "Открой Mini App для покупки скинов.",
        reply_markup=main_menu(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "balance")
async def balance(
    callback: CallbackQuery
):

    value = get_balance(
        callback.from_user.id
    )

    await callback.message.edit_text(
        "💰 <b>МОЙ БАЛАНС</b>\n\n"
        f"🪙 Токены: <b>{value}</b>",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "profile")
async def profile(
    callback: CallbackQuery
):

    user = callback.from_user

    create_user(
        user.id,
        user.username or "",
        user.full_name
    )

    value = get_balance(
        user.id
    )

    await callback.message.edit_text(
        "👤 <b>МОЙ ПРОФИЛЬ</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.full_name}\n"
        f"🪙 Токены: <b>{value}</b>",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "purchases")
async def purchases(
    callback: CallbackQuery
):

    rows = db.execute(
        """
        SELECT skin_name, price
        FROM purchases
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (
            callback.from_user.id,
        )
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
                f"🎨 {skin_name} — {price} 🪙"
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


@dp.callback_query(F.data == "sell")
async def sell(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "💸 <b>ПРОДАЖА СКИНА</b>\n\n"
        "Раздел подключим следующим этапом.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


@dp.callback_query(F.data == "support")
async def support(
    callback: CallbackQuery
):

    await callback.message.edit_text(
        "🆘 <b>ПОДДЕРЖКА</b>\n\n"
        "Раздел подключим следующим этапом.",
        reply_markup=back_button(),
        parse_mode="HTML"
    )

    await callback.answer()


# =========================================================
# HTTP SERVER
# =========================================================

async def start_api():

    app = web.Application()

    app.router.add_route(
        "OPTIONS",
        "/{path:.*}",
        options
    )

    app.router.add_get(
        "/api/me",
        api_me
    )

    app.router.add_get(
        "/api/skins",
        api_skins
    )

    app.router.add_post(
        "/api/buy",
        api_buy
    )

    app.router.add_post(
        "/api/spin",
        api_spin
    )

    runner = web.AppRunner(
        app
    )

    await runner.setup()

    site = web.TCPSite(
        runner,
        "0.0.0.0",
        PORT
    )

    await site.start()

    print(
        f"API server started on port {PORT}"
    )

    return runner


# =========================================================
# ЗАПУСК
# =========================================================

async def main():

    print(
        "Starting Telegram bot..."
    )

    api_runner = await start_api()

    try:

        await dp.start_polling(
            bot
        )

    finally:

        await api_runner.cleanup()

        await bot.session.close()


if __name__ == "__main__":

    asyncio.run(
        main()
    )
