from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


class ScheduledTasks:
    _instance = None

    def __init__(self, scheduler: AsyncIOScheduler):
        self.scheduler = scheduler
        self.existing_jobs = {}

    async def process(self):
        await self.send_donation_alerts()

    async def send_donation_alerts(self):
        moscow_tz = timezone(timedelta(hours=3))
        today = datetime.now(moscow_tz).date()

    def run(self):
        moscow_tz = timezone(timedelta(hours=3))

        trigger = CronTrigger(hour=12, minute=0, second=0, timezone=moscow_tz)

        job_id = "daily_task"
        self.scheduler.add_job(
            self.process, trigger, id=job_id, misfire_grace_time=30, coalesce=True
        )
        self.scheduler.start()


scheduled_tasks = ScheduledTasks(scheduler=AsyncIOScheduler())