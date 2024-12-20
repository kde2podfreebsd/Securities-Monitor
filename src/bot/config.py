from dotenv import load_dotenv
import os

from dotenv import load_dotenv
from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_storage import StateMemoryStorage

load_dotenv()

bot = AsyncTeleBot(
    os.getenv("TELEGRAM_BOT_TOKEN"),
    state_storage=StateMemoryStorage(),
    disable_notification=False,
    colorful_logs=True
)