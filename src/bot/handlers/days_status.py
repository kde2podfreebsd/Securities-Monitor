import datetime
import json

from src.bot.handlers.context import message_context_manager
from telebot import types
from src.trading_calendar import MOEXTradingCalendar
from src.bot.config import bot

calendar = MOEXTradingCalendar()

@bot.message_handler(commands=["calendar"])
async def calendar_inline_handler(message):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=message.chat.id)
    calendar._load_calendar()
    dates = calendar.trading_calendar

    available_years = sorted(set(date.split('-')[0] for date in dates))

    markup = types.InlineKeyboardMarkup()
    for year in available_years:
        markup.add(types.InlineKeyboardButton(text=str(year), callback_data=f"calendar_{year}"))

    msg = await bot.send_message(
        chat_id=message.chat.id,
        text="Выберите год",
        reply_markup=markup,
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_') and len(call.data.split('_')) == 2)
async def calendar_select_month(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    year = call.data.split('_')[1]

    calendar._load_calendar()
    dates = calendar.trading_calendar

    available_months = sorted(set(date.split('-')[1] for date in dates if date.startswith(year)))

    markup = types.InlineKeyboardMarkup()
    for month in available_months:
        markup.add(types.InlineKeyboardButton(text=f"{int(month):02d}", callback_data=f"calendar_{year}_{month}"))
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data="back_to_year"))

    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text="Выберите месяц",
        reply_markup=markup,
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('calendar_') and len(call.data.split('_')) == 3)
async def calendar_select_day(call):
    await message_context_manager.delete_msgId_from_help_menu_dict(chat_id=call.message.chat.id)
    _, year, month = call.data.split('_')

    calendar._load_calendar()
    dates = calendar.trading_calendar

    markup = types.InlineKeyboardMarkup(row_width=3)
    for date_str, status in dates.items():
        y, m, d = date_str.split('-')
        if y == year and m == month:
            day_text = f"{d} {'Рабочий' if status else 'Выходной'}"
            callback_data = f"changestatus_{year}_{month}_{d}_{not status}"
            markup.add(types.InlineKeyboardButton(text=day_text, callback_data=callback_data))
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data=f"back_to_month_{year}"))

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
    calendar.change_status(datetime.datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d'), new_status_bool)

    calendar._load_calendar()
    dates = calendar.trading_calendar

    markup = types.InlineKeyboardMarkup(row_width=3)
    for date_str, status in dates.items():
        y, m, d = date_str.split('-')
        if y == year and m == month:
            day_text = f"{d} {'Рабочий' if status else 'Выходной'}"
            callback_data = f"changestatus_{year}_{month}_{d}_{not status}"
            markup.add(types.InlineKeyboardButton(text=day_text, callback_data=callback_data))
    markup.add(types.InlineKeyboardButton(text="Назад", callback_data=f"back_to_month_{year}"))

    msg = await bot.send_message(
        chat_id=call.message.chat.id,
        text=f"Статус дня изменен на {'Рабочий' if new_status_bool else 'Выходной'}. Выберите следующий день:",
        reply_markup=markup,
        parse_mode='html'
    )
    message_context_manager.add_msgId_to_help_menu_dict(chat_id=call.message.chat.id, msgId=msg.message_id)


@bot.callback_query_handler(func=lambda call: call.data.startswith('back_to_'))
async def back_handler(call):
    parts = call.data.split('_')
    action = parts[2]
    year = parts[3] if len(parts) == 4 else None

    if action == "year":
        await calendar_inline_handler(call.message)
    elif action == "month":
        call.message.text = f"/calendar_{year}"
        await calendar_select_month(call)
