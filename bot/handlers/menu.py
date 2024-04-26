from bot.config.bot import bot
from bot.msg_context import message_context_manager
from bot.markup import (TextMarkup, InlineMarkup)


async def _menu(message):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=message.chat.id)
    msg = await bot.send_message(
        chat_id=message.chat.id,
        text=TextMarkup.menu,
        reply_markup=InlineMarkup.menu(),
        parse_mode="html"
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=message.chat.id, msgId=msg.message_id)


@bot.message_handler(commands=["menu"])
async def welcome_handler(message) -> None:
    await _menu(message)