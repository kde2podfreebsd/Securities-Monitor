from bot.config import bot


@bot.callback_query_handler(func=lambda call: True)
async def HandlerInlineMiddleware(call):
    if call.data == 'delay':
        pass

    if call.data == 'report':
        pass

    if call.data == 'config':
        pass