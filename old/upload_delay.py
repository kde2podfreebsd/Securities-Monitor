# coding: utf-8

import time
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime, date
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

chat_id = -318342503
token = '785216782:AAEYXe6zNsbOv-t4zELnt9Ng_gvV2m58guo'

mybot = Updater(token).bot

today_date = datetime.now().strftime('%Y-%m-%d')

endpoints = ['tradestats', 'orderstats', 'obstats', 'futoi']

def preproc(df):
    columns = ['tradedate', 'tradetime', 'SYSTIME']
    df.rename(columns={'systime': 'SYSTIME'}, inplace=True)
    df = df[columns].copy()
    
    df['ts'] = df['tradedate'] + ' ' + df['tradetime']
    df['ts'] = pd.to_datetime(df['ts'])
	
    df['SYSTIME'] = pd.to_datetime(df['SYSTIME'])
    return df


if date.today().weekday() < 5:
	for ep in endpoints:
		if ep == 'futoi':
			url = f'https://iss.moex.com/iss/analyticalproducts/futoi/securities/ri.csv?from={today_date}&till={today_date}&iss.only=futoi'
		else:
			url = f'https://iss.moex.com/iss/datashop/algopack/eq/{ep}/sber.csv?from={today_date}&till={today_date}&iss.only=data'
		
		X = pd.read_csv(url, sep=';', skiprows=2)
		X = preproc(X)
		X['delay'] = (X['SYSTIME'] - X['ts']).dt.seconds
		X.set_index('tradetime', inplace=True)

		res = X['delay'].plot.bar(figsize=(15, 6), ylim=[0, 300]).get_figure()
		res.savefig(f'{ep}.png')
		res.clear()
		time.sleep(1)

		cap = f'{ep}\nmax: ' + str(X['delay'].max()) + ' sec.\nmed: ' + str(X['delay'].median()) + ' sec.'

		mybot.send_photo(chat_id=chat_id, photo=open(f'{ep}.png', 'rb'), caption=cap, parse_mode=telegram.ParseMode.MARKDOWN)
