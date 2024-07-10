import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import time, datetime, date
from src.monitor import ISSEndpointsFetcher
from src.trading_calendar import MOEXTradingCalendar
from src.monitor import Market, Endpoint
from src.bot.handlers.alerts import send_fo_obstats_tickers_count, draw_plot, send_plots

load_dotenv()

class TradingScheduler:

    def __init__(self):
        self.scheduler = AsyncIOScheduler(job_defaults={'max_instances': 2})
        self.iss_fetcher = ISSEndpointsFetcher()
        self.moex_trading_calendar = MOEXTradingCalendar()

        self.eq_session1_start_time = time(7, 5, 10)
        self.eq_session1_end_time = time(18, 40, 50)
        self.eq_session2_start_time = time(18, 50, 10)
        self.eq_session2_end_time = time(23, 50, 50)

        self.fx_session1_start_time = time(7, 5, 10)
        self.fx_session1_end_time = time(18, 00, 50)

        self.fo_session1_start_time = time(9, 5, 10)
        self.fo_session1_end_time = time(14, 00, 50)
        self.fo_session2_start_time = time(14, 10, 10)
        self.fo_session2_end_time = time(18, 50, 50)
        self.fo_session3_start_time = time(19, 10, 10)
        self.fo_session3_end_time = time(23, 50, 50)

        self.interval_minutes = int(os.getenv('INTERVAL_REQUEST'))

    async def eq_monitoring_delays(self):
        status = self.moex_trading_calendar.get_status(trading_date=date.today())
        if status:
            await self.iss_fetcher.process_market_endpoints(Market.SHARES, date.today())
        else:
            print(f"{date.today()} is not trading date")

    async def fx_monitoring_delays(self):
        status = self.moex_trading_calendar.get_status(trading_date=date.today())
        if status:
            await self.iss_fetcher.process_market_endpoints(Market.CURRENCY, date.today())
        else:
            print(f"{date.today()} is not trading date")

    async def fo_monitoring_delays(self):
        status = self.moex_trading_calendar.get_status(trading_date=date.today())
        if status:
            await self.iss_fetcher.process_market_endpoints(Market.FUTURES, date.today())
            fo_obstats_count_tickers, current_interval = await self.iss_fetcher.tickers_count_fo_obstats()
            await send_fo_obstats_tickers_count(count=fo_obstats_count_tickers, trading_time=current_interval)
        else:
            print(f"{date.today()} is not trading date")

    async def send_plots_to_chat(self):
        eq_tradestats_filename = await draw_plot(market=Market.SHARES, endpoint=Endpoint.TRADESTATS, trading_date=date.today())
        eq_orderstats_filename = await draw_plot(market=Market.SHARES, endpoint=Endpoint.ORDERSTATS, trading_date=date.today())
        eq_obstats_filename = await draw_plot(market=Market.SHARES, endpoint=Endpoint.ORDERBOOKSTATS, trading_date=date.today())
        fx_tradestats_filename = await draw_plot(market=Market.CURRENCY, endpoint=Endpoint.TRADESTATS, trading_date=date.today())
        fx_orderstats_filename = await draw_plot(market=Market.CURRENCY, endpoint=Endpoint.ORDERSTATS, trading_date=date.today())
        fx_obstats_filename = await draw_plot(market=Market.CURRENCY, endpoint=Endpoint.ORDERBOOKSTATS, trading_date=date.today())
        fo_tradestats_filename = await draw_plot(market=Market.FUTURES, endpoint=Endpoint.TRADESTATS, trading_date=date.today())
        fo_obstats_filename = await draw_plot(market=Market.FUTURES, endpoint=Endpoint.ORDERBOOKSTATS, trading_date=date.today())
        await send_plots(files=[eq_tradestats_filename, eq_orderstats_filename, eq_obstats_filename], market='eq')
        await send_plots(files=[fx_tradestats_filename, fx_orderstats_filename, fx_obstats_filename], market='fx')
        await send_plots(files=[fo_tradestats_filename, fo_obstats_filename], market='fo')

        os.remove(eq_tradestats_filename)
        os.remove(eq_orderstats_filename)
        os.remove(eq_obstats_filename)
        os.remove(fx_tradestats_filename)
        os.remove(fx_orderstats_filename)
        os.remove(fx_obstats_filename)
        os.remove(fo_tradestats_filename)
        os.remove(fo_obstats_filename)

    def list_jobs(self):
        jobs = self.scheduler.get_jobs()
        job_details = []
        for job in jobs:
            job_details.append(f"Job ID: {job.id}")
            job_details.append(f"Next Run Time: {job.next_run_time}")
            job_details.append(f"Trigger: {job.trigger}")
            job_details.append(f"Function: {job.func}")
            job_details.append("-" * 20)
        return "\n".join(job_details)

    def run_jobs(self):
        self.scheduler.remove_all_jobs()

        # EQ
        eq_session1_interval_trigger = IntervalTrigger(
            minutes=self.interval_minutes,
            start_date=datetime.combine(datetime.today(), self.eq_session1_start_time),
            end_date=datetime.combine(datetime.today(), self.eq_session1_end_time)
        )

        eq_session2_interval_trigger = IntervalTrigger(
            minutes=self.interval_minutes,
            start_date=datetime.combine(datetime.today(), self.eq_session2_start_time),
            end_date=datetime.combine(datetime.today(), self.eq_session2_end_time)
        )

        self.scheduler.add_job(self.eq_monitoring_delays, eq_session1_interval_trigger, id="EQ1", max_instances=1, misfire_grace_time=600)
        self.scheduler.add_job(self.eq_monitoring_delays, eq_session2_interval_trigger, id="EQ2", max_instances=1, misfire_grace_time=600)

        # FX
        fx_session1_interval_trigger = IntervalTrigger(
            minutes=self.interval_minutes,
            start_date=datetime.combine(datetime.today(), self.fx_session1_start_time),
            end_date=datetime.combine(datetime.today(), self.fx_session1_end_time)
        )

        self.scheduler.add_job(self.fx_monitoring_delays, fx_session1_interval_trigger, id="FX1", max_instances=1, misfire_grace_time=600)

        # FO
        fo_session1_interval_trigger = IntervalTrigger(
            minutes=self.interval_minutes,
            start_date=datetime.combine(datetime.today(), self.fo_session1_start_time),
            end_date=datetime.combine(datetime.today(), self.fo_session1_end_time)
        )

        fo_session2_interval_trigger = IntervalTrigger(
            minutes=self.interval_minutes,
            start_date=datetime.combine(datetime.today(), self.fo_session2_start_time),
            end_date=datetime.combine(datetime.today(), self.fo_session2_end_time)
        )

        fo_session3_interval_trigger = IntervalTrigger(
            minutes=self.interval_minutes,
            start_date=datetime.combine(datetime.today(), self.fo_session3_start_time),
            end_date=datetime.combine(datetime.today(), self.fo_session3_end_time)
        )

        self.scheduler.add_job(self.fo_monitoring_delays, fo_session1_interval_trigger, id="FO1", max_instances=1, misfire_grace_time=600)
        self.scheduler.add_job(self.fo_monitoring_delays, fo_session2_interval_trigger, id="FO2", max_instances=1, misfire_grace_time=600)
        self.scheduler.add_job(self.fo_monitoring_delays, fo_session3_interval_trigger, id="FO3", max_instances=1, misfire_grace_time=600)

    def run(self):
        self.run_jobs()
        cron_trigger_send_plots = CronTrigger(hour=18, minute=55, second=0)
        self.scheduler.add_job(self.send_plots_to_chat, cron_trigger_send_plots, id="Send_plots")
        cron_trigger_run_jobs = CronTrigger(hour=0, minute=0, second=0)
        self.scheduler.add_job(self.run_jobs, cron_trigger_run_jobs, id="Daily_run_jobs")
        self.scheduler.start()
        print(self.list_jobs())

trading_scheduler = TradingScheduler()
