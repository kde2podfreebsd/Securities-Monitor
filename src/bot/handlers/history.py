from src.bot.config import bot
from src.bot.context import message_context_manager
from src.bot.markup import InlineMarkup
from telebot import types
from src.database.session import async_session
from src.database.dal import EndpointsDelayDal
import calendar


@bot.callback_query_handler(func=lambda call: call.data == 'history')
async def history_inline_handler(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите маркет",
        reply_markup=InlineMarkup.select_market(),
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'eq')
async def history_inline_handler(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите эндпоинт",
        reply_markup=InlineMarkup.eq_endpoints()
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'fo')
async def history_inline_handler(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите эндпоинт",
        reply_markup=InlineMarkup.fo_endpoints()
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'fx')
async def history_inline_handler(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите эндпоинт",
        reply_markup=InlineMarkup.fx_endpoints()
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_select_market')
async def back_to_select_market(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите маркет",
        reply_markup=InlineMarkup.select_market(),
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.endswith('_eq') or call.data.endswith('_fx') or call.data.endswith('_fo') or call.data.endswith('_hi2'))
async def handle_endpoint_market_buttons(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    market = call.data.split('_')[-1]
    endpoint = call.data[:-3]

    async with async_session() as session:
        dal = EndpointsDelayDal(session)
        available_years = await dal.get_available_years(market, endpoint)

        markup = types.InlineKeyboardMarkup()
        for year in available_years:
            markup.add(types.InlineKeyboardButton(text=str(year), callback_data=f"{market}_{endpoint}_{year}"))

        if len(available_years) == 0:
            msg = await bot.send_message(call.message.chat.id, "Нет данных", reply_markup=markup)
            message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)
        else:
            msg = await bot.send_message(call.message.chat.id, "Выберите год:", reply_markup=markup)
            message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[-1].isdigit() and len(call.data.split('_')) == 3 and (call.data.startswith('eq') or call.data.startswith('fx') or call.data.startswith('fo') or call.data.startswith('hi2')))
async def handle_year_selection(call):

    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    market, endpoint, selected_year = call.data.split('_')

    async with async_session() as session:
        dal = EndpointsDelayDal(session)
        available_months = await dal.get_available_months_by_year(int(selected_year), market, endpoint)

        markup = types.InlineKeyboardMarkup()
        for month_num in available_months:
            month_name = calendar.month_name[month_num]
            markup.add(types.InlineKeyboardButton(text=month_name, callback_data=f"{market}_{endpoint}_{selected_year}_{month_num}"))

        msg = await bot.send_message(call.message.chat.id, "Выберите месяц:", reply_markup=markup)
        message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[-1].isdigit() and len(call.data.split('_')) == 4 and (call.data.startswith('eq') or call.data.startswith('fx') or call.data.startswith('fo') or call.data.startswith('hi2')))
async def handle_month_selection(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    market, endpoint, selected_year, selected_month = call.data.split('_')

    async with async_session() as session:
        dal = EndpointsDelayDal(session)
        available_days = await dal.get_available_days_by_year_month(int(selected_year), int(selected_month), market, endpoint)

        markup = types.InlineKeyboardMarkup(row_width=7)
        row = []
        for day in available_days:
            row.append(types.InlineKeyboardButton(text=str(day), callback_data=f"{market}_{endpoint}_{selected_year}_{selected_month}_{day}"))
            if len(row) == 3:
                markup.add(*row)
                row = []

        if row:
            markup.add(*row)

        msg = await bot.send_message(call.message.chat.id, "Выберите день:", reply_markup=markup)
        message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(
    func=lambda call: call.data.split('_')[-1].isdigit() and len(call.data.split('_')) == 5 and (call.data.startswith('eq') or call.data.startswith('fx') or call.data.startswith('fo') or call.data.startswith('hi2')))
async def handle_day_selection(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    market, endpoint, selected_year, selected_month, selected_day = call.data.split('_')

    async with async_session() as session:
        dal = EndpointsDelayDal(session)
        output = await dal.get_delay_periods(
            market=market,
            endpoint=endpoint,
            year=int(selected_year),
            month=int(selected_month),
            day=int(selected_day)
        )

        print(output)
    # message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)

