import os
import enum
import pandas as pd
from datetime import date, datetime, time
from dotenv import load_dotenv
from src.passport import PassportMOEXAuth
from typing import List
from src.bot.handlers.alerts import send_alert
import asyncio

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
        
        async def fetch_page_data(page_url):
            data = await self.auth_request(url=page_url)                    
            return data['data']['data'], data['data.cursor']['data'][0], data['data']['columns']

        try:
            first_page_url = f'{url}&start=0'
            first_page_data, cursor_info, columns = await fetch_page_data(first_page_url)
            all_data = first_page_data

            total_records = cursor_info[1]
            page_size = cursor_info[2]

            if total_records > page_size:
                last_page_num = (total_records // page_size) * page_size
                last_page_url = f'{url}&start={last_page_num}'
                last_page_data, _, _ = await fetch_page_data(last_page_url)
                all_data.extend(last_page_data)

            df = self._prepare_dataframe({'data': {'data': all_data, 'columns': columns}})
            
            return df, url.replace(".json", "")
        
        except Exception as e:
            print(f'An error occurred: {e}')
            return None
    
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
        url = f'https://iss.moex.com/iss/datashop/algopack/fo/obstats.json'
                
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
        df['tradedatetime'] = pd.to_datetime(df['tradedate'] + ' ' + df['tradetime'])

        now = datetime.now()
        rounded_minutes = (now.minute // 5) * 5
        current_interval = time(now.hour, rounded_minutes, 0)

        df = df[df['tradedatetime'].dt.time == current_interval]

        return df['secid'].nunique(), current_interval

    async def process_market_endpoints(self, market: Market, date: date) -> None:
        secid_for_market = {
            "eq": 'SBER',
            "fx": "CNYRUB_TOM",
            "fo": await self.find_liquid_fo_secid()
        }

        async def fetch_and_process_data(endpoint):
            df, url = await self.fetch_data(market, endpoint, secid_for_market[market.value], date)
            await self.send_alert_if_delayed(market=market, endpoint=endpoint, df=df, url=url)

        tasks = []
        for endpoint in Endpoint:
            if endpoint == Endpoint.ORDERSTATS and market == Market.FUTURES:
                continue
            tasks.append(fetch_and_process_data(endpoint))

        await asyncio.gather(*tasks)



if __name__ == '__main__':
    import asyncio

    async def test_fetch_data():
        fetcher = ISSEndpointsFetcher()
        trading_date = date.today()
        await fetcher.process_market_endpoints(market=Market.FUTURES, date=trading_date)

    asyncio.run(test_fetch_data())
