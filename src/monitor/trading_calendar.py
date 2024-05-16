import datetime
import json
from datetime import timedelta, date


class MOEXTradingCalendar:
    def __init__(self):
        self.trading_calendar = {}
        self.filename = 'calendar.json'

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

    def get_status(self, date):
        self.load_from_json()
        return self.trading_calendar.get(date, None)

    def change_status(self, date: datetime.date, status):
        if date in self.trading_calendar:
            self.load_from_json()
            self.trading_calendar[date] = status
            self.save_to_json()
        else:
            print("Date not found in the calendar.")


if __name__ == "__main__":
    calendar = MOEXTradingCalendar()
    calendar.generate_calendar(date(2024, 1, 1), date(2024, 12, 31))
    print("Status for 2024-05-20:", calendar.get_status('2024-05-20'))
