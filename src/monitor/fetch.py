import os
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, date, timedelta

from src.monitor.auth import PassportMOEXAuth
from src.logger import logger
from src.database.dal import EndpointsDelayDal
from src.database.session import async_session
from src.types import Endpoints, Markets


class ISSEndpointsFetcher(PassportMOEXAuth):
    _instance = None

    def __new__(cls, *args, **kwargs) -> object:
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        load_dotenv()
        super().__init__(username=os.getenv('MOEX_PASSPORT_LOGIN'), password=os.getenv('MOEX_PASSPORT_PASSWORD'))
        self.endpoints = [endpoint.value for endpoint in Endpoints]
        self.markets = [market.value for market in Markets]
        self.basedir = os.path.abspath(os.path.dirname(__file__))
        logger.info(message="Init ISSEndpointsFetcher object")

    @staticmethod
    def date_range(start_date: date, end_date: date):
        for n in range(int((end_date - start_date).days) + 1):
            yield start_date + timedelta(n)

    @staticmethod
    def is_weekend(some_date: date) -> bool:
        return some_date.weekday() >= 5

    @staticmethod
    def prepare_dataframe(dataframe):
        columns = ['tradedate', 'tradetime', 'SYSTIME']
        dataframe.rename(columns={'systime': 'SYSTIME'}, inplace=True)
        dataframe = dataframe[columns].copy()

        dataframe['ts'] = dataframe['tradedate'] + ' ' + dataframe['tradetime']
        dataframe['ts'] = pd.to_datetime(dataframe['ts'])

        return dataframe

    async def upload_history_delay(self, start_date: date, end_date: date):
        for single_date in self.date_range(start_date=start_date, end_date=end_date):
            formatted_date = single_date.strftime('%Y-%m-%d')
            for endpoint in self.endpoints:
                for market in self.markets:
                    if market == 'fo' and endpoint == 'orderstats':
                        continue
                    # TODO для eq - sber а для других роутов другие тикеры
                    # TODO считать делэи в поставках данных datetime.now() - ts в отдельную бд
                    url = f'https://iss.moex.com/iss/datashop/algopack/{market}/{endpoint}/sber.csv?from={formatted_date}&till={formatted_date}&iss.only=data'
                    filename = f'{self.basedir}/csv/{endpoint}_{market}_{formatted_date}.csv'
                    status = await self.preprocessing(url=url, filename=filename, formatted_date=formatted_date, market=market, endpoint=endpoint)
                    if status is False:
                        continue
            filename = f'{self.basedir}/csv/futoi_fo_{formatted_date}.csv'
            futoi_url = f'https://iss.moex.com/iss/analyticalproducts/futoi/securities/ri.csv?from={formatted_date}&till={formatted_date}&iss.only=futoi'
            status = await self.preprocessing(url=futoi_url, filename=filename, formatted_date=formatted_date, market=Markets.FUTURES, endpoint='futoi')
            if status is False:
                continue

    async def preprocessing(self, url: str, filename: str, formatted_date: str, market: Markets, endpoint: Endpoints):
        output = await self.download_csv(url=url, filename=filename)
        if output is False:
            logger.error(message=f"Error while uploading csv file from ISS: {filename}")
            raise Exception(f"Error while uploading csv file from ISS: {filename}")

        dataframe = pd.read_csv(filename, sep=';', skiprows=2)
        logger.info(f"Read csv by pandas: {filename}")

        if dataframe.shape[0] == 0:
            logger.warning(
                message=f"No data!!! url={url} | date: {formatted_date} | market: {market} | endpoint: {endpoint}")
            self.delete_csv(filename=filename)
            return False

        dataframe = self.prepare_dataframe(dataframe=dataframe)

        async with async_session() as session:
            endpoints_delay_dal = EndpointsDelayDal(session)
            await endpoints_delay_dal.create_from_dataframe(
                dataframe=dataframe,
                date=datetime.strptime(formatted_date, '%Y-%m-%d'),
                endpoint=endpoint,
                market=market
            )

        self.delete_csv(filename=filename)
        del dataframe

        return True


if __name__ == "__main__":
    import asyncio
    dm = ISSEndpointsFetcher()
    asyncio.run(dm.upload_history_delay(start_date=date(2024, 4, 25), end_date=date.today()))