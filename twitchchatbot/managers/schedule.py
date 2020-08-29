import datetime
import logging

from apscheduler.schedulers.background import BackgroundScheduler

from twitchchatbot.utils import now

log = logging.getLogger(__name__)


class ScheduledJob:
    def __init__(self, job):
        self.job = job

    def pause(self, *args, **kwargs):
        if self.job:
            self.job.pause(*args, **kwargs)

    def resume(self, *args, **kwargs):
        if self.job:
            self.job.resume(*args, **kwargs)

    def remove(self, *args, **kwargs):
        if self.job:
            self.job.remove(*args, **kwargs)


class ScheduleManager:
    base_scheduler = None

    @staticmethod
    def init():
        if not ScheduleManager.base_scheduler:
            ScheduleManager.base_scheduler = BackgroundScheduler(daemon=True)
            ScheduleManager.base_scheduler.start()

    @staticmethod
    def execute_now(method, args=None, kwargs=None, scheduler=None):
        if scheduler is None:
            scheduler = ScheduleManager.base_scheduler

        if scheduler is None:
            raise ValueError("No scheduler available")

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        job = scheduler.add_job(method, "date", run_date=now(),
                                args=args, kwargs=kwargs)
        return ScheduledJob(job)

    @staticmethod
    def execute_delayed(delay, method, args=None, kwargs=None, scheduler=None):
        if scheduler is None:
            scheduler = ScheduleManager.base_scheduler

        if scheduler is None:
            raise ValueError("No scheduler available")

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        job = scheduler.add_job(
            method, "date",
            run_date=now() + datetime.timedelta(seconds=delay),
            args=args, kwargs=kwargs
        )
        return ScheduledJob(job)

    @staticmethod
    def execute_every(interval, method, args=None, kwargs=None, scheduler=None,
                      jitter=None):
        if scheduler is None:
            scheduler = ScheduleManager.base_scheduler

        if scheduler is None:
            raise ValueError("No scheduler available")

        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}
        job = scheduler.add_job(method, "interval", seconds=interval,
                                args=args, kwargs=kwargs, jitter=jitter)
        return ScheduledJob(job)
