import datetime
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import date
from telebot import types
from src.bot.config import bot
from src.passport import PassportMOEXAuth
from datetime import date, timedelta

load_dotenv()

def round_to_nearest_second(dt):
    return dt.replace(microsecond=0)

def round_to_nearest_minute(dt):
    if dt.second >= 30:
        dt += datetime.timedelta(minutes=1)
    return dt.replace(second=0, microsecond=0)

async def send_alert(market, delay, endpoint, url):

    text_for_market = {
            "eq": 'EQ | Акции',
            "fx": "FX | Валюта",
            "fo": "FO | Фьючерсы",
            "futoi": "FUTOI"
        }
    
    current_time = round_to_nearest_second(datetime.datetime.now())
    
    if endpoint == 'futoi':
        await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"❗️Alert\n{text_for_market[market]} | {endpoint}\nЗадержка: {delay} секунд.\nВремя запроса: {current_time}",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(f"FUTOI ISS", url=url)
        )
    )
        
    else:
        await bot.send_message(
            chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
            text=f"❗️Alert\n{text_for_market[market.value]} | {endpoint.value}\nЗадержка: {delay} секунд.\nВремя запроса: {current_time}",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton(f"{text_for_market[market.value]} ISS", url=url)
            )
        )

async def error_alert(market, endpoint):

    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"Проблема с получением данных для маркета {market.value} | {endpoint if endpoint == 'futoi' else endpoint.value}"
    )

async def send_hi2_alert(status: dict):

    message = ''

    for key, value in status.items():
        if value:
            message += f'{date.today()} {key} hi2 - ✅\n'
        else:
            message += f'{date.today()} {key} hi2 - ❌\n'

    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=message,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton(f"EQ HI2 ISS", url=f"https://iss.moex.com/iss/datashop/algopack/eq/hi2"),
            types.InlineKeyboardButton(f"FX HI2 ISS", url=f"https://iss.moex.com/iss/datashop/algopack/fx/hi2"),
            types.InlineKeyboardButton(f"FO HI2 ISS", url=f"https://iss.moex.com/iss/datashop/algopack/fo/hi2")
        )
    )


async def send_fo_obstats_tickers_count(fo_obstats_count_tickers: int, fo_obstats_count_tickers_prev_day: int, trading_time: datetime.time):
    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"❗️Alert\nКоличество уникальных тикеров для FO OBstats на {date.today().strftime('%d.%m.%Y')} {trading_time}: {fo_obstats_count_tickers}.\nКоличество уникальных тикеров для FO OBstats на {(date.today() - timedelta(days=1)) .strftime('%d.%m.%Y')}: {fo_obstats_count_tickers_prev_day}."
    )

async def send_missing_intervals_alert(missing_intervals: str):

    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"❗️Alert | Пропущенные интервалы\n{missing_intervals}"
    )

async def send_plots(files: list, market):
        media_group = []
        i = 0
        for photo in files:
            i += 1
            media_group.append(types.InputMediaPhoto(open(photo, 'rb'), caption=f"Дневные задержки для {market} на {date.today()}" if i == 1 else None))
        
        await bot.send_media_group(os.getenv("TELEGRAM_GROUP_CHATID"), media_group)


@bot.message_handler(commands=['info'])
async def get_chat_info(message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    chat_title = message.chat.title
    await bot.send_message(message.chat.id, f'ID чата: {chat_id}\nТип чата: {chat_type}\nНазвание чата: {chat_title}')



