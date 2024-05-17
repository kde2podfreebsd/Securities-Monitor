import datetime
from datetime import timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from src.monitor.trading_calendar import MOEXTradingCalendar
from src.monitor.fetch import ISSEndpointsFetcher


class ScheduledTasks:
    _instance = None

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.schedule_task()
        self.moex_trading_calendar = MOEXTradingCalendar()
        self.iss_fetcher = ISSEndpointsFetcher()

    def schedule_task(self):
        # TODO сделать именно с 7:00 до 23:50, тк minute='0-50/1' - отсекает последние 10 минут каждого часа
        trigger = CronTrigger(hour='0-23', minute='0-59/1', timezone=timezone(timedelta(hours=3)))
        self.scheduler.add_job(self.task_to_run, trigger)

    async def task_to_run(self):
        status = self.moex_trading_calendar.get_status(trading_date=datetime.date.today())
        print(status)
        if status:
            await self.iss_fetcher.upload_history_delay(
                start_date=datetime.date.today(),
                end_date=datetime.date.today()
            )


async def main():
    scheduler = AsyncIOScheduler()
    ScheduledTasks(scheduler)
    scheduler.start()

    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())