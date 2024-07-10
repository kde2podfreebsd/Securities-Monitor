from typing import Dict, Union
from datetime import datetime

from telebot import types
from src.bot.config import bot
from telebot.asyncio_handler_backends import BaseMiddleware
from telebot.asyncio_handler_backends import CancelUpdate
from telebot.asyncio_handler_backends import ContinueHandling

class FloodingMiddleware(BaseMiddleware):
    def __init__(self, limit: float) -> None:
        super().__init__()
        self.last_time: Dict[int, datetime] = {}
        self.limit = limit
        self.update_types = ["message"]

    async def pre_process(self, message: types.Message, data: Dict[str, str]) -> Union[ContinueHandling, CancelUpdate]:
        try:
            if message.from_user.id not in self.last_time:
                self.last_time[message.from_user.id] = message.date
                return ContinueHandling()
            if (message.date - self.last_time[message.from_user.id]).total_seconds() < self.limit:
                await bot.send_message(message.chat.id, "Вы делаете запросы слишком часто")
                return CancelUpdate()
            self.last_time[message.from_user.id] = message.date
            return ContinueHandling()
        except Exception as e:
            return CancelUpdate()

    async def post_process(self, message: types.Message, data: Dict[str, str], exception: Exception) -> ContinueHandling:
        return ContinueHandling()


@bot.message_handler(is_forwarded=True)
async def forward_filter(message: types.Message):
    try:
        await bot.send_message(message.chat.id, "Бот не принимает пересланые сообщения!")
    except Exception:
        pass

