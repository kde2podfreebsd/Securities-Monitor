import os
from datetime import date, timedelta
import json
from typing import Dict


class MOEXTradingCalendar:

    def __init__(self, filename: str = "trading_calendar.json"):
        self.filename = os.path.abspath(os.path.join(os.path.dirname(__file__), filename))
        self.trading_calendar = self._load_calendar()

    def _load_calendar(self) -> Dict[str, bool]:
        try:
            with open(self.filename, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def _save_calendar(self) -> None:
        try:
            with open(self.filename, 'w') as file:
                json.dump(self.trading_calendar, file, indent=4)
        except Exception as e:
            raise Exception(f"Ошибка при сохранении календаря: {e}")

    def generate_calendar(self, start_date: date, end_date: date) -> None:
        dates = (start_date + timedelta(days=i) for i in range((end_date - start_date).days + 1))
        for date_ in dates:
            self.trading_calendar[date_.strftime('%Y-%m-%d')] = date_.weekday() < 5
        self._save_calendar()

    def is_working_day(self, date_: date) -> bool:
        return self.trading_calendar.get(date_.strftime('%Y-%m-%d'), False)

    def change_status(self, trading_date: date, status: bool) -> None:
        date_str = trading_date.strftime('%Y-%m-%d')
        if date_str in self.trading_calendar:
            self.trading_calendar[date_str] = status
            self._save_calendar()
        else:
            raise ValueError("Дата не найдена в календаре.")

    def get_status(self, trading_date: date) -> bool:
        return self.trading_calendar.get(trading_date.strftime('%Y-%m-%d'), False)
    

if __name__ == "__main__":
    calendar = MOEXTradingCalendar()
    calendar.generate_calendar(date(2024, 1, 1), date(2030, 12, 31))

