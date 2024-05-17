import datetime
from typing import Union, Dict, List
import matplotlib.pyplot as plt

from sqlalchemy import and_, extract, Integer, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from src.database.models import EndpointsDelay
from src.database.session import DBTransactionStatus, async_session
from src.types import Endpoints, Markets
import pandas as pd
from src.logger import logger


class EndpointsDelayDal:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def check_existence(
            self,
            date: datetime.date,
            ts: datetime.datetime,
            systime: datetime.datetime,
            market: Markets,
            endpoint: Endpoints
    ) -> Union[DBTransactionStatus.SUCCESS, DBTransactionStatus.ALREADY_EXIST]:
        existing_entry = await self.db_session.execute(
            select(EndpointsDelay).where(
                and_(
                    EndpointsDelay.date == date,
                    EndpointsDelay.ts == ts,
                    EndpointsDelay.systime == systime,
                    EndpointsDelay.market == market,
                    EndpointsDelay.endpoint == endpoint,
                )
            )
        )
        existing_entry = existing_entry.scalars().first()

        if existing_entry:
            logger.info("Entry already exists in the database.")
            return DBTransactionStatus.ALREADY_EXIST
        else:
            logger.info("Entry does not exist in the database.")
            return DBTransactionStatus.SUCCESS

    async def create(
            self,
            date: datetime.date,
            ts: datetime.datetime,
            systime: datetime.datetime,
            market: Markets,
            endpoint: Endpoints
    ) -> Union[
        DBTransactionStatus.SUCCESS, DBTransactionStatus.ROLLBACK, DBTransactionStatus.ALREADY_EXIST
    ]:
        if await self.check_existence(
                date=date,
                ts=ts,
                systime=systime,
                market=market,
                endpoint=endpoint
        ) == DBTransactionStatus.ALREADY_EXIST:
            return DBTransactionStatus.ALREADY_EXIST

        new_entry = EndpointsDelay(
            date=date,
            ts=ts,
            systime=systime,
            market=market,
            endpoint=endpoint,
            delay=(systime-ts).seconds
        )

        self.db_session.add(new_entry)

        try:
            await self.db_session.commit()
            logger.info("New entry added to the database.")
            return DBTransactionStatus.SUCCESS

        except IntegrityError as e:
            await self.db_session.rollback()
            logger.error(f"Error occurred while creating new entry: {e}")
            return DBTransactionStatus.ROLLBACK

    async def get_all(
            self,
    ) -> Union[list, None]:
        all_entries = await self.db_session.execute(select(EndpointsDelay).order_by(EndpointsDelay.ts))
        all_entries = all_entries.scalars().all()
        return all_entries

    async def get_by_market(
            self,
            market: Markets
    ) -> Union[list, None]:
        entries_by_market = await self.db_session.execute(
            select(EndpointsDelay).where(EndpointsDelay.market == market).order_by(EndpointsDelay.ts)
        )
        entries_by_market = entries_by_market.scalars().all()
        return entries_by_market

    async def get_by_endpoint(
            self,
            endpoint: Endpoints
    ) -> Union[list, None]:
        entries_by_endpoint = await self.db_session.execute(
            select(EndpointsDelay).where(EndpointsDelay.endpoint == endpoint).order_by(EndpointsDelay.ts)
        )
        entries_by_endpoint = entries_by_endpoint.scalars().all()
        return entries_by_endpoint

    async def create_from_dataframe(
            self,
            dataframe: pd.DataFrame,
            market: Markets,
            endpoint: Endpoints,
            date: datetime.date
    ) -> Union[
        DBTransactionStatus.SUCCESS, DBTransactionStatus.ROLLBACK, DBTransactionStatus.ALREADY_EXIST
    ]:
        for _, row in dataframe.iterrows():
            systime = datetime.datetime.strptime(row['SYSTIME'], '%Y-%m-%d %H:%M:%S')
            ts = row['ts']

            status = await self.create(
                date=date,
                ts=ts,
                systime=systime,
                market=market,
                endpoint=endpoint
            )

            if status == DBTransactionStatus.ROLLBACK:
                return DBTransactionStatus.ROLLBACK

        return DBTransactionStatus.SUCCESS

    async def get_available_years(self, market: Markets, endpoint: Endpoints) -> List[int]:
        years = []
        query = select(
            extract('year', EndpointsDelay.date).cast(Integer).distinct()
        ).where(
            and_(
                EndpointsDelay.market == market,
                EndpointsDelay.endpoint == endpoint
            )
        )
        result = await self.db_session.execute(query)
        for row in result.scalars():
            years.append(row)
        return years

    async def get_available_months_by_year(
            self, year: int, market: Markets, endpoint: Endpoints
    ) -> Dict[int, List[int]]:
        months = {}
        query = select(
            extract('month', EndpointsDelay.date).cast(Integer).distinct()
        ).where(
            and_(
                EndpointsDelay.market == market,
                EndpointsDelay.endpoint == endpoint,
                extract('year', EndpointsDelay.date).cast(Integer) == year
            )
        )
        result = await self.db_session.execute(query)
        for row in result.scalars():
            months[row] = []

        return months

    async def get_available_days_by_year_month(
            self, year: int, month: int, market: Markets, endpoint: Endpoints
    ) -> Dict[int, List[int]]:
        days = {}
        query = select(
            extract('day', EndpointsDelay.date).cast(Integer).distinct()
        ).where(
            and_(
                EndpointsDelay.market == market,
                EndpointsDelay.endpoint == endpoint,
                extract('year', EndpointsDelay.date).cast(Integer) == year,
                extract('month', EndpointsDelay.date).cast(Integer) == month
            )
        )
        result = await self.db_session.execute(query)
        for row in result.scalars():
            days[row] = []

        return days

    async def get_delay_periods(
            self,
            market: Markets,
            endpoint: Endpoints,
            year: int,
            month: int,
            day: int
    ) -> list[pd.DataFrame]:
        start_date = datetime.date(year, month, day)
        end_date = start_date + datetime.timedelta(days=1)

        query = select(EndpointsDelay).where(
            and_(
                EndpointsDelay.market == market,
                EndpointsDelay.endpoint == endpoint,
                EndpointsDelay.date >= start_date,
                EndpointsDelay.date < end_date,
                EndpointsDelay.delay > 600
            )
        ).order_by(EndpointsDelay.ts)

        result = await self.db_session.execute(query)
        entries = result.scalars().all()

        if not entries:
            return []

        df = pd.DataFrame([
            {
                'ts': entry.ts,
                'delay': entry.delay
            }
            for entry in entries
        ])

        delay_threshold = 600
        current_start = None
        current_end = None
        dfs = []

        for index, row in df.iterrows():
            if current_start is None:
                current_start = row['ts']
                current_end = row['ts']
            else:
                if row['delay'] > delay_threshold:
                    current_end = row['ts']
                else:
                    if current_start != current_end:
                        period_df = df[(df['ts'] >= current_start) & (df['ts'] <= current_end)].copy()
                        dfs.append(period_df)

                    current_start = row['ts']
                    current_end = row['ts']

        if current_start != current_end:
            period_df = df[(df['ts'] >= current_start) & (df['ts'] <= current_end)].copy()
            dfs.append(period_df)

        return dfs

    async def get_delays_for_date(self, market: Markets, endpoint: Endpoints, date: datetime.date) -> pd.DataFrame:

        query = select(EndpointsDelay).where(
            and_(
                EndpointsDelay.market == market,
                EndpointsDelay.endpoint == endpoint,
                EndpointsDelay.date == date,
            )).order_by(EndpointsDelay.ts)

        result = await self.db_session.execute(query)
        entries = result.scalars().all()

        if not entries:
            return pd.DataFrame()

        data = [
            {
                'ts': entry.ts,
                'SYSTIME': entry.systime,
                'tradetime': entry.ts,
                'delay': entry.delay
            }
            for entry in entries
        ]

        for entry in entries:
            print(entry.delay)

        return pd.DataFrame(data)


async def plot_delay_chart(market: Markets, endpoint: Endpoints, date: datetime.date):
    async with async_session() as session:
        dal = EndpointsDelayDal(session)
        delays_df = await dal.get_delays_for_date(market, endpoint, date)

        if delays_df.empty:
            print("Нет данных для заданного рынка, эндпоинта и даты.")
            return

        delays_df.set_index('tradetime', inplace=True)

        num_entries = len(delays_df)
        width_per_bar = 0.2
        total_width = width_per_bar * num_entries

        plt.figure(figsize=(total_width, 7))
        ax = delays_df['delay'].plot.bar(width=0.8, ylim=[0, 300])
        plt.xlabel('Время')
        plt.ylabel('Задержка (в секундах)')
        plt.title(f'Задержка для {market.value} - {endpoint.value} на {date}')
        plt.grid(False)

        ax.set_xticks(range(num_entries))
        ax.set_xticklabels(delays_df.index.strftime('%H:%M:%S'), rotation=90, ha='right')

        res = ax.get_figure()
        res.savefig(f'{endpoint.value}.png')

        cap = f'{endpoint.value}\nmax: {delays_df["delay"].max()} sec.\nmed: {delays_df["delay"].median()} sec.'
        print(cap)


if __name__ == "__main__":
    async def main():
        market = Markets.SHARES
        endpoint = Endpoints.TRADESTATS
        date = datetime.date(2024, 5, 6)

        await plot_delay_chart(market, endpoint, date)


    import asyncio

    asyncio.run(main())