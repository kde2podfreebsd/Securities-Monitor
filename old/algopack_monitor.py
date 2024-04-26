
# coding: utf-8

import time
import pandas as pd
from datetime import datetime, date
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

# TODO расширить для fx и fo + hi2(расчет раз в день)
# TODO доработать выходной текст (если идет поломка, агрегация в одно сообщение)
# TODO поиграться с графиком
# TODO определять пропуски в данных (наличие 5и минуток) - лучше определять в конце дня

chat_id = -318342503
token = '785216782:AAEYXe6zNsbOv-t4zELnt9Ng_gvV2m58guo'

mybot = Updater(token).bot

today_date = datetime.now().strftime('%Y-%m-%d')

def push(text):
    mybot.send_message(chat_id, text, parse_mode=telegram.ParseMode.MARKDOWN)

endpoints = ['tradestats', 'orderstats', 'obstats', 'futoi']

def preproc(df):
    columns = ['tradedate', 'tradetime', 'SYSTIME']
    df.rename(columns={'systime': 'SYSTIME'}, inplace=True)
    df = df[columns].copy()
    
    df['ts'] = df['tradedate'] + ' ' + df['tradetime']
    df['ts'] = pd.to_datetime(df['ts'])
    
    return df

def message(arr):
    txt = '*algopack delay*\n'
    for el in arr:
        txt += el['ep'] + ': ' + str(el['delta']//60) + ' min\n'
        
    return txt


if date.today().weekday() < 5:
	while True:
		delays = []
		for ep in endpoints:
			if ep == 'futoi':
				url = f'https://iss.moex.com/iss/analyticalproducts/futoi/securities/ri.csv?from={today_date}&till={today_date}&iss.only=futoi'
			else:
				url = f'https://iss.moex.com/iss/datashop/algopack/eq/{ep}/sber.csv?from={today_date}&till={today_date}&latest=1&iss.only=data'
			
			X = pd.read_csv(url, sep=';', skiprows=2)
			df = preproc(X)

			ts = df.loc[0, 'ts']
			systime = df.loc[0, 'SYSTIME']

			delta = (datetime.now() - ts).seconds
			if delta > 10*60:
				delays.append({'ep': ep, 'delta': delta})

			time.sleep(1)

		if len(delays) > 0:
			push(message(delays))

		if (datetime.now().hour >= 19) | ((datetime.now().hour == 18) & (datetime.now().minute >= 45)):
			break

		time.sleep(297)
