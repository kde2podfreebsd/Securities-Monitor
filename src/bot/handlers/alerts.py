import datetime
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import date
from telebot import types
from src.bot.config import bot
from src.passport import PassportMOEXAuth

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
            "futoi": "FO | Фьючерсы"
        }
    
    current_time = round_to_nearest_second(datetime.datetime.now())
    
    if endpoint == 'futoi':
        await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"{text_for_market[market]} | {endpoint}\nЗадержка: {delay}. Время запроса: {current_time}",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("ISS", url=url)
        )
    )
    else:
        await bot.send_message(
            chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
            text=f"{text_for_market[market.value]} | {endpoint.value}\nЗадержка: {delay}. Время запроса: {current_time}",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("ISS", url=url)
            )
        )

async def error_alert(market, endpoint):

    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"Проблема с получением данных для маркета {market.value} | {endpoint.value}"
    )

async def send_hi2_alert(status: bool, market):
    message = f"Для маркета {market.value} HI2: {'Значения на сегодняшний день присутствуют' if status else 'Значения на сегодняшний день отсутствуют'}"
    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=message,
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("ISS", url=f"https://iss.moex.com/iss/datashop/algopack/{market.value}/hi2")
        )
    )


async def send_fo_obstats_tickers_count(count: int, trading_time: datetime.time):
    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"Количество уникальных тикеров для FO OBSTATS {trading_time}: {count}"
    )

async def send_plots(files: list, market):
        media_group = []
        i = 0
        for photo in files:
            i += 1
            media_group.append(types.InputMediaPhoto(open(photo, 'rb'), caption=f"{market} delays" if i == 1 else None))
        
        await bot.send_media_group(os.getenv("TELEGRAM_GROUP_CHATID"), media_group)


@bot.message_handler(commands=['info'])
async def get_chat_info(message):
    chat_id = message.chat.id
    chat_type = message.chat.type
    chat_title = message.chat.title
    await bot.send_message(message.chat.id, f'ID чата: {chat_id}\nТип чата: {chat_type}\nНазвание чата: {chat_title}')

