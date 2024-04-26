from datetime import datetime, date, timedelta
import pandas as pd
from monitor.utils import Markets, Endpoints


class DelayMonitor:

    def __init__(self):
        self.endpoints = [endpoint.value for endpoint in Endpoints]
        self.markets = [market.value for market in Markets]

    @staticmethod
    def preprocessing(dataframe):
        columns = ['tradedate', 'tradetime', 'SYSTIME']
        dataframe.rename(columns={'systime': 'SYSTIME'}, inplace=True)
        dataframe = dataframe[columns].copy()

        dataframe['ts'] = dataframe['tradedate'] + ' ' + dataframe['tradetime']
        dataframe['ts'] = pd.to_datetime(dataframe['ts'])

        return dataframe

    def calculate_delay(self, url: str):
        try:
            dataframe = pd.read_csv(url, sep=';', skiprows=2)
            dataframe = self.preprocessing(dataframe)
            ts = dataframe.loc[0, 'ts']
            delta = (datetime.now() - ts).seconds
            return delta, dataframe
        except Exception as e:
            print(f"Error occurred while processing {url}: {e}")
            return None, None

    def date_range(self, start_date: date, end_date: date):
        for n in range(int((end_date - start_date).days) + 1):
            yield start_date + timedelta(n)

    def upload_history_delay(self, start_date: date, end_date: date):
        for single_date in self.date_range(start_date=start_date, end_date=end_date):
            print(single_date)
            formatted_date = single_date.strftime('%Y-%m-%d')
            for endpoint in self.endpoints:
                for market in self.markets:
                    url = f'https://iss.moex.com/iss/datashop/algopack/{market}/{endpoint}/sber.csv?from={formatted_date}&till={formatted_date}&iss.only=data'
                    print(url)
                    delta, dataframe = self.calculate_delay(url=url)
                    print(delta)
                    if delta is None:
                        # TODO: обработка что это или выходной или пропуск в данных
                        continue
                    if delta > 10 * 60:
                        print(f"Date: {formatted_date}, Market: {market}, Endpoint: {endpoint}")
                        print(dataframe['ts'], end="\n-------------\n")


if __name__ == "__main__":
    # dm = DelayMonitor()
    # dm.upload_history_delay(start_date=date(2024, 4, 25), end_date=date.today())
    df = pd.read_csv("https://iss.moex.com/iss/datashop/algopack/eq/tradestats/sber.csv?from=2024-04-25&till=2024-04-25&iss.only=data", sep=';', skiprows=2, encoding='utf-8')
    print(df)