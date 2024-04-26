from bot.config.bot import bot
from bot.msg_context import message_context_manager


@bot.message_handler(is_reply=True)
async def reply_filter(message):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=message.chat.id)
    msg = await bot.send_message(message.chat.id, "Бот не принимает ответы на сообщения!")
    message_context_manager.add_msgId_to_help_menu_dict(
        chat_id=message.chat.id,
        msgId=msg.id
    )