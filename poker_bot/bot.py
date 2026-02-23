"""
Telegram bot entry point for the Poker Mini App.
Sends the /start reply with a WebApp button and sets the menu button.
"""

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    MenuButtonWebApp,
)

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://gafrustam.ru/poker/")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🃏 Играть в покер",
            web_app=WebAppInfo(url=WEBAPP_URL),
        )
    ]])
    await message.answer(
        "♠️ <b>Heads-Up Texas Hold'em</b>\n\n"
        "• Стартовый стек: <b>3 000</b> фишек у каждого\n"
        "• Малый блайнд: <b>50</b> | Большой: <b>100</b>\n"
        "• Соперник — умный AI с Monte Carlo + GPT\n\n"
        "Нажми кнопку ниже, чтобы открыть игру:",
        parse_mode="HTML",
        reply_markup=kb,
    )


async def main():
    # Set menu button globally so the button appears in the chat input bar
    try:
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="🃏 Покер",
                web_app=WebAppInfo(url=WEBAPP_URL),
            )
        )
    except Exception as e:
        print(f"[bot] Could not set menu button: {e}")

    print(f"[bot] Starting polling. WebApp URL: {WEBAPP_URL}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
