from bot.config.bot import bot
from bot.msg_context import message_context_manager


@bot.message_handler(commands=['chat_info'])
async def get_chat_info(message):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=message.chat.id)
    msg = await bot.send_message(message.chat.id, f'ID чата: {message.chat.id}\nТип чата: {message.chat.type}\nНазвание чата: {message.chat.title}')
    message_context_manager.add_msgId_to_help_menu_dict(
        chat_id=message.chat.id,
        msgId=msg.id
    )
