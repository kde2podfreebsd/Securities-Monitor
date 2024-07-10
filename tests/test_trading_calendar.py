import pytest
from src.trading_calendar import MOEXTradingCalendar
from datetime import date

@pytest.mark.asyncio
async def test_trading_calendar():
    calendar = MOEXTradingCalendar(filename="../tests/test_trading_calendar.json")
    calendar.generate_calendar(date(2024, 1, 1), date(2024, 12, 31))
    assert calendar.is_working_day(date(2024, 5, 9))
    assert calendar.get_status(date(2024, 6, 18))
    calendar.change_status(date(2024, 5, 9), False)
    assert not calendar.get_status(date(2024, 5, 9))