import asyncio
import os
from src.bot.config import bot
from src.bot.handlers import *
from telebot.asyncio_filters import (
    ForwardFilter,
    IsDigitFilter,
    IsReplyFilter,
    StateFilter,
)


class Bot:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        bot.add_custom_filter(IsReplyFilter())
        bot.add_custom_filter(ForwardFilter())
        bot.add_custom_filter(StateFilter(bot))
        bot.add_custom_filter(IsDigitFilter())

        bot.setup_middleware(FloodingMiddleware(1))
        # self.scheduled_tasks = scheduled_tasks

    async def polling(self):
        task1 = asyncio.create_task(bot.infinity_polling())
        # self.scheduled_tasks.run()
        await task1


if __name__ == "__main__":
    asyncio.run(Bot().polling())