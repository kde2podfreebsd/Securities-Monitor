import os
import enum
import pandas as pd
from datetime import date, datetime, time
from dotenv import load_dotenv
from src.passport import PassportMOEXAuth
from typing import List
from src.bot.handlers.alerts import send_alert, send_hi2_alert, error_alert
import asyncio
import matplotlib.pyplot as plt

class Market(enum.Enum):

    SHARES = 'eq'
    CURRENCY = 'fx'
    FUTURES = 'fo'


class Endpoint(enum.Enum):

    TRADESTATS = 'tradestats'
    ORDERSTATS = 'orderstats'
    ORDERBOOKSTATS = 'obstats'

class ISSEndpointsFetcher(PassportMOEXAuth):

    def __init__(self) -> None:
        load_dotenv()
        super().__init__(
            username=os.getenv('MOEX_PASSPORT_LOGIN'),
            password=os.getenv('MOEX_PASSPORT_PASSWORD')
        )

    @staticmethod
    def _prepare_dataframe(data: List[List[str]]) -> pd.DataFrame:
        
        dataframe = pd.DataFrame(data['data']['data'], columns=data['data']['columns'])

        columns = ['SYSTIME', 'ts']
        dataframe.rename(columns={'systime': 'SYSTIME'}, inplace=True)
        dataframe['ts'] = pd.to_datetime(dataframe['tradedate'] + ' ' + dataframe['tradetime'])
        dataframe = dataframe[columns].copy()

        return dataframe
    
    async def fetch_data(
            self,
            market: Market,
            endpoint: Endpoint,
            security: str,
            trading_date: date
    ):
        if endpoint == Endpoint.ORDERSTATS and market == Market.FUTURES:
            raise NotImplementedError
        
        formatted_date = trading_date.strftime('%Y-%m-%d')
        url = (
            f'https://iss.moex.com/iss/datashop/algopack/{market.value}/'
            f'{endpoint.value}/{security}.json?from={formatted_date}&till={formatted_date}'
        )
        try:

            data = await self.auth_request(url=url)                    
            df = self._prepare_dataframe(data)
            
            return df, url.replace(".json", "")
        
        except Exception as e:
            print(f'An error occurred: {e}')
            return None, None
    
    async def find_liquid_fo_secid(self) -> str:
        url = f'https://iss.moex.com/iss/datashop/algopack/fo/tradestats.json?iss.only=data'
        data = await self.auth_request(url=url) 
        df = pd.DataFrame(data['data']['data'], columns=data['data']['columns'])
        df['tradedate'] = pd.to_datetime(df['tradedate'])
        grouped = df.groupby('secid')['vol'].sum()
        return grouped.idxmax()

    @staticmethod
    async def send_alert_if_delayed(market: str, endpoint: str, df: pd.DataFrame, url: str) -> None:
        delay = (datetime.now() - df.iloc[-1]['ts']).seconds
        if delay > int(os.getenv('DELAY')):
            await send_alert(market=market, delay=delay, endpoint=endpoint, url=url)

    async def tickers_count_fo_obstats(self) -> int:
        url_obstats = f'https://iss.moex.com/iss/datashop/algopack/fo/obstats.json'
                
        all_data = []
        page_num = 0
        while True:
            page_url = f'{url_obstats}?start={page_num * 1000}'
            data = await self.auth_request(url=page_url)                    
            columns = data['data']['columns']
            page_data = data['data']['data']
            
            if not page_data or page_data is None:
                break
            
            all_data.extend(page_data)
            page_num += 1

        df_obstats = pd.DataFrame(all_data, columns=columns)
        df_obstats['tradedatetime'] = pd.to_datetime(df_obstats['tradedate'] + ' ' + df_obstats['tradetime'])

        #------------------------------------------------#

        url_tradestats = f'https://iss.moex.com/iss/datashop/algopack/fo/tradestats.json'
                
        all_data = []
        page_num = 0
        while True:
            page_url = f'{url_tradestats}?start={page_num * 1000}'
            data = await self.auth_request(url=page_url)                    
            columns = data['data']['columns']
            page_data = data['data']['data']
            
            if not page_data or page_data is None:
                break
            
            all_data.extend(page_data)
            page_num += 1

        df_tradestats = pd.DataFrame(all_data, columns=columns)
        df_tradestats['tradedatetime'] = pd.to_datetime(df_tradestats['tradedate'] + ' ' + df_tradestats['tradetime'])

        now = datetime.now()
        rounded_minutes = (now.minute // 5) * 5
        current_interval = time(now.hour, rounded_minutes, 0)

        df_tradestats = df_tradestats[df_tradestats['tradedatetime'].dt.time == current_interval]
        df_obstats = df_obstats[df_obstats['tradedatetime'].dt.time == current_interval]

        if df_obstats['secid'].nunique() <= df_tradestats['secid'].nunique():
            return df_obstats['secid'].nunique(), current_interval
        else:
            return True, True
    
    async def check_hi2_status(self):
        def check_hi2(df: pd.DataFrame) -> bool:
            if df.shape[0] != 0:
                if 'ts' in df.columns and df.loc[0, 'ts'].date() == date.today():
                    return True
                else:
                    return False
            else:
                return False
        
        for market in Market:
            data = await self.auth_request(url=f'https://iss.moex.com/iss/datashop/algopack/{market.value}/hi2.json')
            df = pd.DataFrame(data['data']['data'], columns=data['data']['columns'])
            df['ts'] = pd.to_datetime(df['tradedate'] + ' ' + df['tradetime'])
            status = check_hi2(df=df)
            await send_hi2_alert(status=status, market=market)

    async def futoi_delay_notifications(self, date: date) -> None:
        formatted_date = date.strftime('%Y-%m-%d')
        url = f"https://iss.moex.com/iss/analyticalproducts/futoi/securities/ri.json?from={formatted_date}&till={formatted_date}&iss.only=futoi&reversed=1"
        data = await self.auth_request(url=url)
        dataframe = pd.DataFrame(data['futoi']['data'], columns=data['futoi']['columns'])
        columns = ['SYSTIME', 'ts']
        dataframe.rename(columns={'systime': 'SYSTIME'}, inplace=True)
        dataframe['ts'] = pd.to_datetime(dataframe['tradedate'] + ' ' + dataframe['tradetime'])
        dataframe = dataframe[columns].copy()
        df_reversed = dataframe.sort_index(ascending=False).reset_index(drop=True)
        await self.send_alert_if_delayed('fo', 'futoi', df_reversed, url=url.replace(".json", ''))
        

    async def process_market_endpoints(self, market: Market, date: date) -> None:
        secid_for_market = {
            "eq": 'SBER',
            "fx": "CNYRUB_TOM",
            "fo": await self.find_liquid_fo_secid()
        }

        async def fetch_and_process_data(endpoint):
            df, url = await self.fetch_data(market, endpoint, secid_for_market[market.value], date)
            if df is None:
                await error_alert(market, endpoint)
            await self.send_alert_if_delayed(market=market, endpoint=endpoint, df=df, url=url)

        tasks = []
        for endpoint in Endpoint:
            if endpoint == Endpoint.ORDERSTATS and market == Market.FUTURES:
                continue
            tasks.append(fetch_and_process_data(endpoint))

        await asyncio.gather(*tasks)

    async def draw_plot(self, market, endpoint, trading_date: date) -> None:

        if endpoint != 'futoi':   
            market = market.value
            endpoint = endpoint.value

        secid_for_market = {
            "eq": 'SBER',
            "fx": "CNYRUB_TOM",
            "fo": await self.find_liquid_fo_secid(),
            "futoi": 'RI'
        }
        
        url = f'https://iss.moex.com/iss/datashop/algopack/{market}/{endpoint}/{secid_for_market[market]}.json'

        if endpoint == 'futoi':
            url='https://iss.moex.com/iss/analyticalproducts/futoi/securities/ri.json'
                
        all_data = []
        page_num = 0
        
        while True:
            page_url = f'{url}?start={page_num * 1000}'
            data = await self.auth_request(url=page_url)
            if endpoint == 'futoi':
                columns = data['futoi']['columns']
                page_data = data['futoi']['data']
            else:                    
                columns = data['data']['columns']
                page_data = data['data']['data']
            
            if not page_data or page_data is None:
                break
            
            all_data.extend(page_data)
            page_num += 1

        df = pd.DataFrame(all_data, columns=columns)

        if endpoint == 'futoi':
            columns = ['SYSTIME', 'ts', 'tradedate', 'tradetime']
            dataframe.rename(columns={'systime': 'SYSTIME'}, inplace=True)
            dataframe['ts'] = pd.to_datetime(dataframe['tradedate'] + ' ' + dataframe['tradetime'])
            dataframe = dataframe[columns].copy()
            df_reversed = dataframe.sort_index(ascending=False).reset_index(drop=True)
            df = df_reversed[df_reversed['tradedate'] == date.today().strftime('%Y-%m-%d')]
            
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

        filename = f'{os.path.abspath(os.path.dirname(__file__))}/static/{market}_{endpoint}_{trading_date}.png'
        plt.savefig(filename)

        print(filename)
        return filename



if __name__ == '__main__':
    import asyncio

    async def test_fetch_data():
        fetcher = ISSEndpointsFetcher()
        trading_date = date.today()
        await fetcher.process_market_endpoints(market=Market.FUTURES, date=trading_date)

    asyncio.run(test_fetch_data())
