from telebot.asyncio_handler_backends import BaseMiddleware
from telebot.asyncio_handler_backends import CancelUpdate
from telebot.asyncio_handler_backends import ContinueHandling

from src.bot.config import bot


class FloodingMiddleware(BaseMiddleware):
    def __init__(self, limit) -> None:
        super().__init__()
        self.last_time = {}
        self.limit = limit
        self.update_types = ["message"]

    async def pre_process(self, message, data):
        if message.from_user.id not in self.last_time:
            self.last_time[message.from_user.id] = message.date
            return
        if message.date - self.last_time[message.from_user.id] < self.limit:
            await bot.send_message(message.chat.id, "Вы делаете запросы слишком часто")
            return CancelUpdate()
        self.last_time[message.from_user.id] = message.date

    async def post_process(self, message, data, exception):
        return ContinueHandling()


@bot.message_handler(is_forwarded=True)
async def forward_filter(message):
    await bot.send_message(message.chat.id, "Бот не принимает пересланые сообщения!")


@bot.message_handler(is_reply=True)
async def reply_filter(message):
    await bot.send_message(message.chat.id, "Бот не принимает ответы на сообщения!")