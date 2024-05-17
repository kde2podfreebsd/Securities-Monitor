from src.bot.config import bot
from src.bot.context import message_context_manager
from src.bot.markup import InlineMarkup


@bot.message_handler(commands=["start", "menu"])
async def welcome_handler(message) -> None:
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=message.chat.id)
    msg = await bot.send_message(
        chat_id=message.chat.id,
        text="Выберите действие",
        reply_markup=InlineMarkup.main_user_menu(),
        parse_mode='html'
    )

    message_context_manager.add_msgId_to_help_menu_dict(chat_id=message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_main_menu')
async def back_to_main_menu(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите действие",
        reply_markup=InlineMarkup.main_user_menu(),
        parse_mode='html'
    )

    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)