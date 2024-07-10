import pytest
from old_monitor import ISSEndpointsFetcher
from old_monitor import Market, Endpoint
from datetime import date
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

@pytest.mark.asyncio
async def test_fetch_data():
    fetcher = ISSEndpointsFetcher()
    trading_date = date(2024, 6, 18)
    secid = 'SBER'
    df, _ = await fetcher.fetch_data(market=Market.SHARES, endpoint=Endpoint.TRADESTATS, security=secid, trading_date=trading_date)
    assert isinstance(df, pd.DataFrame)
    assert 'SYSTIME' in df.columns
    assert 'ts' in df.columns
    assert not df.empty
    assert (pd.to_datetime(df['ts'].dt.date) == pd.Series([trading_date] * len(df))).all()

