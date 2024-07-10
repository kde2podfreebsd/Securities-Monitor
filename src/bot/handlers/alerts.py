import datetime
import os
from dotenv import load_dotenv
import pandas as pd
from datetime import date
from telebot import types
from src.bot.config import bot
from src.passport import PassportMOEXAuth
import matplotlib.pyplot as plt

load_dotenv()

async def send_alert(market, delay, endpoint, url):

    text_for_market = {
            "eq": 'EQ | Акции',
            "fx": "FX | Валюта",
            "fo": "FO | Фьючерсы"
        }
    
    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"{text_for_market[market.value]} | {endpoint.value}\nЗадержка: {delay}",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("ISS", url=url)
        )
    )


async def send_fo_obstats_tickers_count(count: int, trading_time: datetime.time):
    await bot.send_message(
        chat_id=os.getenv('TELEGRAM_GROUP_CHATID'),
        text=f"Количество уникальных тикеров для {trading_time}: {count}"
    )


async def draw_plot(market, endpoint, trading_date: date) -> None:
        
        market = market.value
        endpoint = endpoint.value
        
        passport_obj = PassportMOEXAuth(os.getenv('MOEX_PASSPORT_LOGIN'), os.getenv('MOEX_PASSPORT_PASSWORD'))
        
        url = f'https://iss.moex.com/iss/datashop/algopack/{market}/{endpoint}.json'
                
        all_data = []
        page_num = 0
        
        while True:
            page_url = f'{url}?start={page_num * 1000}'
            data = await passport_obj.auth_request(url=page_url)                    
            columns = data['data']['columns']
            page_data = data['data']['data']
            
            if not page_data or page_data is None:
                break
            
            all_data.extend(page_data)
            page_num += 1

        df = pd.DataFrame(all_data, columns=columns)
    
        df['tradetime'] = pd.to_datetime(df['tradedate'] + ' ' + df['tradetime'])
        df['SYSTIME'] = pd.to_datetime(df['SYSTIME'])

        df['delay'] = (df['SYSTIME'] - df['tradetime']).dt.total_seconds()

        colors = ['red' if delay > int(os.getenv("DELAY")) else 'blue' for delay in df['delay']]

        plt.figure(figsize=(18, 6))

        bar_width = 0.8

        plt.bar(df['tradetime'].dt.strftime('%H:%M:%S'), df['delay'], color=colors, width=bar_width)
        
        plt.title(f'Задержки для маркета {market} и эндпоинта {endpoint}\n{trading_date.strftime("%Y-%m-%d")}', loc='center', pad=5)
        plt.xlabel('5и минутки')
        plt.ylabel('Задержка (в секундах)')
        plt.xticks(rotation=90)
        plt.ylim(0, df['delay'].max() + 50)

        median_delay = df['delay'].median()
        mean_delay = df['delay'].mean()
        max_delay = df['delay'].max()
        min_delay = df['delay'].min()

        table_data = [[max_delay, min_delay, mean_delay, median_delay]]
        table_columns = ["Max", "Min", "Mean", "Median"]

        table = plt.table(
            cellText=table_data,
            colLabels=table_columns,
            cellLoc='center', loc='bottom', bbox=[0, -1, 1, 0.5]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        plt.subplots_adjust(bottom=0.3)

        plt.tight_layout()

        filename = f'{os.path.abspath(os.path.dirname(__file__))}/../../static/{market}_{endpoint}_{trading_date}.png'
        plt.savefig(filename)

        print(filename)
        return filename

async def send_plots(files: list, market):
        media_group = []
        i = 0
        for photo in files:
            i += 1
            media_group.append(types.InputMediaPhoto(open(photo, 'rb'), caption=f"{market} delays" if i == 1 else None))
        
        await bot.send_media_group(os.getenv("TELEGRAM_GROUP_CHATID"), media_group)

