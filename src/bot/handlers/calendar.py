import datetime
import json

from src.bot.context import message_context_manager
from telebot import types
from src.monitor.trading_calendar import MOEXTradingCalendar
from src.bot.config import bot

calendar = MOEXTradingCalendar()


@bot.callback_query_handler(func=lambda call: call.data == 'calendar')
async def calendar_inline_handler(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    calendar.load_from_json()
    dates = calendar.trading_calendar

    available_years = []
    for i in dates:
        year, _, _ = i.split('-')
        available_years.append(year)

    available_years = sorted(set(available_years))

    markup = types.InlineKeyboardMarkup()
    for year in available_years:
        markup.add(types.InlineKeyboardButton(text=str(year), callback_data=f"calendar_{year}"))

    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите год",
        reply_markup=markup,
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.split('_')[-1].isdigit() and len(call.data.split('_')) == 2 and call.data.startswith('calendar'))
async def calendar_select_month(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    year = call.data.split('_')[-1]

    calendar.load_from_json()
    dates = calendar.trading_calendar

    available_months = []
    for i in dates:
        y, month, _ = i.split('-')
        if y == year:
            available_months.append(month)

    available_months = sorted(set(available_months))

    markup = types.InlineKeyboardMarkup()
    for month in available_months:
        month_int = int(month)
        markup.add(types.InlineKeyboardButton(text=f"{month_int:02d}", callback_data=f"calendar_{year}_{month}"))

    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите месяц",
        reply_markup=markup,
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: len(call.data.split('_')) == 3 and call.data.startswith('calendar'))
async def calendar_select_day(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    _, year, month = call.data.split('_')

    calendar.load_from_json()
    dates = calendar.trading_calendar

    markup = types.InlineKeyboardMarkup(row_width=3)
    for date_str, status in dates.items():
        y, m, d = date_str.split('-')
        if y == year and m == month:
            day_text = f"{d} {'Рабочий' if status else 'Выходной'}"
            callback_data = f"changestatus_{year}_{month}_{d}_{not status}"
            markup.add(types.InlineKeyboardButton(text=day_text, callback_data=callback_data))

    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text=f"Выберите день ({month}-{year})",
        reply_markup=markup,
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('changestatus'))
async def change_day_status(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    _, year, month, day, new_status = call.data.split('_')

    new_status_bool = json.loads(new_status.lower())
    calendar.change_status(datetime.datetime.strptime(f'{int(year)}-{int(month)}-{int(day)}', '%Y-%m-%d'), new_status_bool)

    calendar.load_from_json()
    dates = calendar.trading_calendar

    markup = types.InlineKeyboardMarkup(row_width=3)
    for date_str, status in dates.items():
        y, m, d = date_str.split('-')
        if y == year and m == month:
            day_text = f"{d} {'Рабочий' if status else 'Выходной'}"
            callback_data = f"changestatus_{year}_{month}_{d}_{not status}"
            markup.add(types.InlineKeyboardButton(text=day_text, callback_data=callback_data))

    msg = await bot.send_message(
        call.message.chat.id,
        f"Статус дня изменен на {'Рабочий' if new_status_bool else 'Выходной'}. Выберите следующий день:",
        reply_markup=markup,
        parse_mode='html'
    )

    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)