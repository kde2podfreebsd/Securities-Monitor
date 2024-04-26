import asyncio
from bot.config.bot import bot
from bot.filters import (
    FloodingMiddleware,
    reply_filter,
    forward_filter
)
from telebot.asyncio_filters import (
    ForwardFilter,
    IsDigitFilter,
    IsReplyFilter,
    StateFilter,
)

from bot.handlers import *

from scheduler import scheduled_tasks
from database.session import create_all


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
        self.scheduled_tasks = scheduled_tasks

    async def polling(self):
        # await create_all()
        task1 = asyncio.create_task(bot.infinity_polling())
        self.scheduled_tasks.run()
        await task1


if __name__ == "__main__":
    b = Bot()
    asyncio.run(b.polling())