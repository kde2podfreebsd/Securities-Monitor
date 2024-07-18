import os
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import time, datetime, date
from src.monitor import ISSEndpointsFetcher
from src.trading_calendar import MOEXTradingCalendar
from src.monitor import Market, Endpoint
from src.bot.handlers.alerts import send_fo_obstats_tickers_count, send_plots
import asyncio
import cmd

load_dotenv()

class TradingScheduler(cmd.Cmd):

    def __init__(self):
        super().__init__()
        self.scheduler = AsyncIOScheduler(job_defaults={'max_instances': 100})
        self.iss_fetcher = ISSEndpointsFetcher()
        self.moex_trading_calendar = MOEXTradingCalendar()

        # EQ
        self.eq_session1_start_time = time(10, 10, 30)
        self.eq_session1_end_time = time(18, 40, 50)

        self.eq_session2_start_time = time(19, 15, 30)
        self.eq_session2_end_time = time(23, 50, 50)

        # FX
        self.fx_session1_start_time = time(10, 10, 30)
        self.fx_session1_end_time = time(19, 0, 50)

        # FO
        self.fo_session1_start_time = time(10, 10, 30)
        self.fo_session1_end_time = time(14, 0, 50)

        self.fo_session2_start_time = time(14, 15, 30)
        self.fo_session2_end_time = time(18, 50, 50)

        self.fo_session3_start_time = time(19, 15, 30)
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

            ######################################
            # fo_obstats_count_tickers, fo_tradestats_count_tickers, current_interval = await self.iss_fetcher.tickers_count_fo_obstats()

            # if fo_obstats_count_tickers < fo_tradestats_count_tickers:
            #     await send_fo_obstats_tickers_count(
            #         fo_obstats_count_tickers=fo_obstats_count_tickers,
            #         fo_tradestats_count_tickers=fo_tradestats_count_tickers,
            #         trading_time=current_interval
            #         )
            ######################################

            await self.iss_fetcher.futoi_delay_notifications(date.today())
        else:
            print(f"{date.today()} is not trading date")

    async def hi2_checker(self):
        await self.iss_fetcher.check_hi2_status()

    async def send_plots_to_chat(self):
        eq_tradestats_filename = await self.iss_fetcher.draw_plot(market=Market.SHARES, endpoint=Endpoint.TRADESTATS, trading_date=date.today())
        eq_orderstats_filename = await self.iss_fetcher.draw_plot(market=Market.SHARES, endpoint=Endpoint.ORDERSTATS, trading_date=date.today())
        eq_obstats_filename = await self.iss_fetcher.draw_plot(market=Market.SHARES, endpoint=Endpoint.ORDERBOOKSTATS, trading_date=date.today())
        fx_tradestats_filename = await self.iss_fetcher.draw_plot(market=Market.CURRENCY, endpoint=Endpoint.TRADESTATS, trading_date=date.today())
        fx_orderstats_filename = await self.iss_fetcher.draw_plot(market=Market.CURRENCY, endpoint=Endpoint.ORDERSTATS, trading_date=date.today())
        fx_obstats_filename = await self.iss_fetcher.draw_plot(market=Market.CURRENCY, endpoint=Endpoint.ORDERBOOKSTATS, trading_date=date.today())
        fo_tradestats_filename = await self.iss_fetcher.draw_plot(market=Market.FUTURES, endpoint=Endpoint.TRADESTATS, trading_date=date.today())
        fo_obstats_filename = await self.iss_fetcher.draw_plot(market=Market.FUTURES, endpoint=Endpoint.ORDERBOOKSTATS, trading_date=date.today())
        fo_futoi_filename = await self.iss_fetcher.draw_plot(market=Market.FUTURES, endpoint='futoi', trading_date=date.today())
        await send_plots(files=[eq_tradestats_filename, eq_orderstats_filename, eq_obstats_filename], market='eq')
        await send_plots(files=[fx_tradestats_filename, fx_orderstats_filename, fx_obstats_filename], market='fx')
        await send_plots(files=[fo_tradestats_filename, fo_obstats_filename, fo_futoi_filename], market='fo')

        os.remove(eq_tradestats_filename)
        os.remove(eq_orderstats_filename)
        os.remove(eq_obstats_filename)
        os.remove(fx_tradestats_filename)
        os.remove(fx_orderstats_filename)
        os.remove(fx_obstats_filename)
        os.remove(fo_tradestats_filename)
        os.remove(fo_obstats_filename)
        os.remove(fo_futoi_filename)

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
        cron_trigger_send_plots = CronTrigger(hour=18, minute=27, second=5)
        self.scheduler.add_job(self.send_plots_to_chat, cron_trigger_send_plots, id="Send_plots")

        hi2_cron_trigger = CronTrigger(hour=19, minute=3, second=30)
        self.scheduler.add_job(self.hi2_checker, hi2_cron_trigger, id="hi2_check")

        cron_trigger_run_jobs = CronTrigger(hour=0, minute=0, second=0)
        self.scheduler.add_job(self.run_jobs, cron_trigger_run_jobs, id="Daily_run_jobs")
        self.scheduler.start()
        print(self.list_jobs())

        loop = asyncio.get_event_loop()
        loop.create_task(self.command_interface(loop))
        loop.run_forever()

    async def command_interface(self, loop):
        class CommandProcessor(cmd.Cmd):
            prompt = '> print current jobs list - jobs:   '

            def do_jobs(self, arg):
                print(trading_scheduler.list_jobs())

            def do_exit(self, arg):
                print("Exiting...")
                loop.stop()
                return True

        processor = CommandProcessor()
        await loop.run_in_executor(None, processor.cmdloop)

if __name__ == "__main__":
    trading_scheduler = TradingScheduler()
    trading_scheduler.run()

