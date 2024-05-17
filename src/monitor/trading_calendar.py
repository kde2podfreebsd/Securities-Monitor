import datetime
import json
from datetime import timedelta, date
import os


class MOEXTradingCalendar:
    def __init__(self):
        self.trading_calendar = {}
        self.filename = f'{os.path.abspath(os.path.dirname(__file__))}/calendar.json'

    def generate_calendar(self, start_date: date, end_date: date):
        while start_date <= end_date:
            self.trading_calendar[start_date.strftime('%Y-%m-%d')] = self.is_working_day(start_date)
            start_date += timedelta(days=1)
        self.save_to_json()

    @staticmethod
    def is_working_day(date):
        return date.weekday() < 5

    def save_to_json(self):
        with open(self.filename, 'w') as file:
            json.dump(self.trading_calendar, file, indent=4)

    def load_from_json(self):
        with open(self.filename, 'r') as file:
            self.trading_calendar = json.load(file)

    def get_status(self, trading_date: datetime.date):
        self.load_from_json()
        return self.trading_calendar.get(trading_date.strftime("%Y-%m-%d"), None)

    def change_status(self, trading_date: datetime.date, status):
        if trading_date.strftime("%Y-%m-%d") in self.trading_calendar:
            self.load_from_json()
            self.trading_calendar[trading_date.strftime("%Y-%m-%d")] = status
            self.save_to_json()
        else:
            print("Date not found in the calendar.")


if __name__ == "__main__":
    calendar = MOEXTradingCalendar()
    # calendar.generate_calendar(date(2024, 1, 1), date(2030, 12, 31))
    # print(calendar.get_status(trading_date=datetime.date.today()))
    # calendar.change_status(trading_date=datetime.date.today(), status=True)
    # print(calendar.get_status(trading_date=datetime.date.today()))
