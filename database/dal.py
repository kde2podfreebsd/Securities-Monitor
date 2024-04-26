import datetime
from typing import Union

from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError

from database.models import EndpointsDelay
from database.session import DBTransactionStatus, async_session
from monitor.utils import Markets, Endpoints


class EndpointsDelayDal:
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def check_existence(
            self,
            ts: datetime.datetime,
            market: str,
            endpoint: str,
            delay: float
    ) -> Union[DBTransactionStatus.SUCCESS, DBTransactionStatus.ALREADY_EXIST]:
        existing_entry = await self.db_session.execute(
            select(EndpointsDelay).where(
                and_(
                    EndpointsDelay.ts == ts,
                    EndpointsDelay.market == market,
                    EndpointsDelay.endpoint == endpoint,
                    EndpointsDelay.delay == delay
                )
            )
        )
        existing_entry = existing_entry.scalars().first()

        if existing_entry:
            return DBTransactionStatus.ALREADY_EXIST
        else:
            return DBTransactionStatus.SUCCESS

    async def create(
            self,
            ts: datetime.datetime,
            market: Markets,
            endpoint: Endpoints,
            delay: float
    ) -> Union[
        DBTransactionStatus.SUCCESS, DBTransactionStatus.ROLLBACK, DBTransactionStatus.ALREADY_EXIST
    ]:
        if await self.check_existence(ts, market, endpoint, delay) == DBTransactionStatus.ALREADY_EXIST:
            return DBTransactionStatus.ALREADY_EXIST

        new_entry = EndpointsDelay(
            ts=ts,
            market=market,
            endpoint=endpoint,
            delay=delay
        )

        self.db_session.add(new_entry)

        try:
            await self.db_session.commit()
            return DBTransactionStatus.SUCCESS

        except IntegrityError as e:
            await self.db_session.rollback()
            return DBTransactionStatus.ROLLBACK

    async def delete(
            self,
            ts: datetime.datetime,
            market: str,
            endpoint: str
    ) -> Union[DBTransactionStatus.SUCCESS, DBTransactionStatus.ROLLBACK]:
        existing_entry = await self.db_session.execute(
            select(EndpointsDelay).where(
                and_(
                    EndpointsDelay.ts == ts,
                    EndpointsDelay.market == market,
                    EndpointsDelay.endpoint == endpoint
                )
            )
        )
        existing_entry = existing_entry.scalars().first()

        if existing_entry:
            await self.db_session.delete(existing_entry)

            try:
                await self.db_session.commit()
                return DBTransactionStatus.SUCCESS
            except IntegrityError as e:
                await self.db_session.rollback()
                return DBTransactionStatus.ROLLBACK
        else:
            return DBTransactionStatus.ROLLBACK

    async def get_all(
            self,
    ) -> Union[list, None]:
        all_entries = await self.db_session.execute(select(EndpointsDelay).order_by(EndpointsDelay.ts))
        all_entries = all_entries.scalars().all()
        return all_entries

    async def get_by_market(
            self,
            market: str
    ) -> Union[list, None]:
        entries_by_market = await self.db_session.execute(
            select(EndpointsDelay).where(EndpointsDelay.market == market).order_by(EndpointsDelay.ts)
        )
        entries_by_market = entries_by_market.scalars().all()
        return entries_by_market

    async def get_by_endpoint(
            self,
            endpoint: str
    ) -> Union[list, None]:
        entries_by_endpoint = await self.db_session.execute(
            select(EndpointsDelay).where(EndpointsDelay.endpoint == endpoint).order_by(EndpointsDelay.ts)
        )
        entries_by_endpoint = entries_by_endpoint.scalars().all()
        return entries_by_endpoint


if __name__ == "__main__":
    import asyncio

    async def test():
        async with async_session() as session:
            ed_dal = EndpointsDelayDal(session)

            # status = await ed_dal.create(ts=datetime.datetime(2024, 4, 1, 12, 0, 0), market=Markets.SHARES, endpoint=Endpoints.TRADESTATS, delay=0.0)
            # print(status)
            # print(await ed_dal.get_all())

    asyncio.run(test())

