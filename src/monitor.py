import os
import enum
import pandas as pd
from datetime import date, datetime, time
from dotenv import load_dotenv
from src.passport import PassportMOEXAuth
from typing import List
from src.bot.handlers.alerts import send_alert, send_hi2_alert, error_alert, send_missing_intervals_alert
import asyncio
import matplotlib.pyplot as plt
from datetime import datetime, time, timedelta

eq_sessions = [
    (time(10, 5, 0), time(18, 40, 0)),
    (time(19, 5, 0), time(23, 50, 0))
]

fx_sessions = [
    (time(10, 5, 0), time(19, 0, 0))
]

fo_sessions = [
    (time(10, 5, 0), time(14, 0, 0)),
    (time(14, 10, 0), time(18, 50, 0)),
    (time(19, 10, 0), time(23, 50, 0))
]

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

        self.previously_alerted_intervals = {
            'eq': set(),
            'fx': set(),
            'fo': set()
        }

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
        error_count = 0
        while error_count < 3:
            try:
                data = await self.auth_request(url=url)                    
                df = self._prepare_dataframe(data)
                if df.equals(self._prepare_dataframe(data)):
                    return df, url.replace(".json", "")
            except Exception as e:
                print(f'An error occurred: {e}')
                error_count += 1
                if error_count == 3:
                    print('Max number of retries reached')
                    return None, None
            await asyncio.sleep(1)
        print('Max number of retries reached')
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
                
        all_data = []
        page_num = 0
        while True:
            page_url = f'{url_obstats}?date={(date.today() - timedelta(days=1)).strftime("%Y-%m-%d")}&start={page_num * 1000}'
            data = await self.auth_request(url=page_url)                    
            columns = data['data']['columns']
            page_data = data['data']['data']
            
            if not page_data or page_data is None:
                break
            
            all_data.extend(page_data)
            page_num += 1

        df_obstats_prev_day = pd.DataFrame(all_data, columns=columns)
        df_obstats_prev_day['tradedatetime'] = pd.to_datetime(df_obstats_prev_day['tradedate'] + ' ' + df_obstats_prev_day['tradetime'])

        now = datetime.now()
        rounded_minutes = (now.minute // 5) * 5
        current_interval = time(now.hour, rounded_minutes, 0)

        df_obstats = df_obstats[df_obstats['tradedatetime'].dt.time == current_interval]
        
        return df_obstats['secid'].nunique(), df_obstats_prev_day['secid'].nunique(), current_interval
    
    async def check_hi2_status(self):
        def check_hi2(df: pd.DataFrame) -> bool:
            if df.shape[0] != 0 and df is not None:
                if 'ts' in df.columns and df.loc[0, 'ts'].date() == date.today():
                    return True
                else:
                    return False
            else:
                return False
            
        hi2_status = {
            "eq": False,
            "fx": False,
            "fo": False
        }
        
        for market in Market:
            data = await self.auth_request(url=f'https://iss.moex.com/iss/datashop/algopack/{market.value}/hi2.json')
            df = pd.DataFrame(data['data']['data'], columns=data['data']['columns'])
            df['ts'] = pd.to_datetime(df['tradedate'] + ' ' + df['tradetime'])
            hi2_status[market.value] = check_hi2(df=df)

        await send_hi2_alert(status=hi2_status)

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
        if df_reversed is None:
            await error_alert(market='fo', endpoint='futoi')
            return 
        else:
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
                await self.error_alert(market=market, endpoint=endpoint)
                return ""
            else:
                await self.send_alert_if_delayed(market=market, endpoint=endpoint, df=df, url=url)

            if market.value == 'eq':
                current_intervals = set(self.find_missing_intervals(df, eq_sessions))
            elif market.value == 'fx':
                current_intervals = set(self.find_missing_intervals(df, fx_sessions))
            elif market.value == 'fo':
                current_intervals = set(self.find_missing_intervals(df, fo_sessions))
            else:
                current_intervals = set()

            new_intervals = current_intervals - self.previously_alerted_intervals[market.value]
            self.previously_alerted_intervals[market.value].update(new_intervals)

            return "\n".join(str(interval) for interval in new_intervals)

        tasks = []
        for endpoint in Endpoint:
            if endpoint == Endpoint.ORDERSTATS and market == Market.FUTURES:
                continue
            tasks.append(fetch_and_process_data(endpoint))

        results = await asyncio.gather(*tasks)
        results = [result for result in results if result]
        results = "\n".join(results)
        if results:
            await send_missing_intervals_alert(results)

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

        if endpoint == 'futoi':
            url=f'https://iss.moex.com/iss/analyticalproducts/futoi/securities/ri.json?from={date.today().strftime("%Y-%m-%d")}&till={date.today().strftime("%Y-%m-%d")}'
            data = await self.auth_request(url=url)
            columns = data['futoi']['columns']
            all_data = data['futoi']['data']

        else:
            url = f'https://iss.moex.com/iss/datashop/algopack/{market}/{endpoint}/{secid_for_market[market]}.json'
                
            all_data = []
            page_num = 0
            
            while True:
                page_url = f'{url}?start={page_num * 1000}'
                data = await self.auth_request(url=page_url)     
                columns = data['data']['columns']
                page_data = data['data']['data']
                
                if not page_data or page_data is None:
                    break
                
                all_data.extend(page_data)
                page_num += 1

        df = pd.DataFrame(all_data, columns=columns)

        if endpoint == 'futoi':
            columns = ['SYSTIME', 'ts', 'tradedate', 'tradetime']
            df.rename(columns={'systime': 'SYSTIME'}, inplace=True)
            df['ts'] = pd.to_datetime(df['tradedate'] + ' ' + df['tradetime'])
            df = df[columns].copy()
            df_reversed = df.sort_index(ascending=False).reset_index(drop=True)
            df = df_reversed[df_reversed['tradedate'] == date.today().strftime('%Y-%m-%d')]
            
        df['tradetime'] = pd.to_datetime(df['tradedate'] + ' ' + df['tradetime'])
        df['SYSTIME'] = pd.to_datetime(df['SYSTIME'])

        df['delay'] = (df['SYSTIME'] - df['tradetime']).dt.total_seconds()

        colors = ['red' if delay > int(os.getenv("DELAY")) else 'blue' for delay in df['delay']]

        plt.figure(figsize=(12, 6))

        bar_width = 0.8

        plt.bar(df['tradetime'].dt.strftime('%H:%M:%S'), df['delay'], color=colors, width=bar_width)
        
        plt.title(f'Задержки для маркета {market} и эндпоинта {endpoint}\n{trading_date.strftime("%Y-%m-%d")}', loc='center', pad=5)
        plt.xlabel('5и минутки')
        plt.ylabel('Задержка (в секундах)')
        plt.xticks(rotation=90)
        plt.ylim(0, df['delay'].max() + 50)

        median_delay = df['delay'].median()
        mean_delay = round(df['delay'].mean(), 2)
        max_delay = df['delay'].max()
        min_delay = df['delay'].min()

        table_data = [[max_delay, min_delay, mean_delay, median_delay]]
        table_columns = ["Max", "Min", "Mean", "Median"]

        table = plt.table(
            cellText=table_data,
            colLabels=table_columns,
            cellLoc='center', loc='bottom', bbox=[0, -0.95, 1, 0.5]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 1.5)

        plt.subplots_adjust(bottom=0.4)

        plt.tight_layout()

        filename = f'{os.path.abspath(os.path.dirname(__file__))}/static/{market}_{endpoint}_{trading_date}.png'
        plt.savefig(filename)

        print(filename)
        return filename

    def generate_expected_intervals(self, start_time, end_time):
        intervals = []
        current_time = datetime.combine(datetime.today(), start_time)
        end_time = datetime.combine(datetime.today(), end_time)
        while current_time <= end_time:
            intervals.append(current_time.time())
            current_time += timedelta(minutes=5)
        return intervals

    def find_missing_intervals(self, df, session_times):
        df['time_only'] = pd.to_datetime(df['ts']).dt.time
        
        current_time = datetime.now().time()
        missing_intervals = []

        for start_time, end_time in session_times:
            expected_intervals = self.generate_expected_intervals(start_time, end_time)
            
            past_intervals = [interval for interval in expected_intervals if interval <= current_time]
            
            for interval in past_intervals:
                if interval not in df['time_only'].values:
                    missing_intervals.append(interval)
        
        return missing_intervals



if __name__ == '__main__':
    import asyncio

    async def test_fetch_data():
        fetcher = ISSEndpointsFetcher()
        trading_date = date.today()
        #await fetcher.process_market_endpoints(market=Market.CURRENCY, date=date.today())
        #await fetcher.draw_plot(market=Market.SHARES, endpoint=Endpoint.TRADESTATS, trading_date=trading_date)
        #print(await fetcher.tickers_count_fo_obstats())

    asyncio.run(test_fetch_data())
