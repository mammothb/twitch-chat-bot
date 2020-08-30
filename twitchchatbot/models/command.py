import logging

from twitchchatbot.managers.schedule import ScheduleManager
from twitchchatbot.models.action import RawFuncAction
from twitchchatbot.utils import now

LOG = logging.getLogger(__name__)


class Command:
    DEFAULT_CD_ALL = 5

    notify_on_error = False

    def __init__(self, **options):
        self.id = options.get("id", None)

        self.action = None
        self.extra_args = {"command": self}
        self.delay_all = Command.DEFAULT_CD_ALL
        self.description = None
        self.enabled = True
        self.command = None

        self.last_run = 0

        self.run_in_thread = False
        self.notify_on_error = False

        self.set(**options)

    def set(self, **options):
        if "extra_args" in options:
            self.extra_args = {"command": self}
            self.extra_args.update(options["extra_args"])
        self.command = options.get("command", self.command)
        self.description = options.get("description", self.description)
        self.delay_all = options.get("delay_all", self.delay_all)
        if self.delay_all < 0:
            self.delay_all = 0
        self.enabled = options.get("enabled", self.enabled)
        self.run_in_thread = options.get("run_in_thread", self.run_in_thread)
        self.notify_on_error = options.get("notify_on_error",
                                           self.notify_on_error)

    def __str__(self):
        return f"Command(!{self.command})"

    @classmethod
    def raw_command(cls, cb, **options):
        cmd = cls(**options)
        try:
            cmd.action = RawFuncAction(cb)
        except Exception:
            LOG.exception("Uncaught exception in Command.raw_command. catch "
                          "the following exception manually!")
            cmd.enabled = False
        return cmd

    @classmethod
    def bot_command(cls, bot, method_name, **options):
        cmd = cls(**options)
        cmd.description = options.get("description", None)
        cmd.action = RawFuncAction(getattr(bot, method_name))
        try:
            cmd.action = RawFuncAction(getattr(bot, method_name))
        except Exception:
            pass
        return cmd

    def is_enabled(self):
        return self.enabled and self.action is not None

    def run(self, bot, message, event, args):
        if self.action is None:
            LOG.warning("This command is not available.")
            return False

        if not bot.is_admin(event.source.user):
            return False

        cd_modifier = 1.0

        cur_time = now().timestamp()
        time_since_last_run = (cur_time - self.last_run) / cd_modifier

        if time_since_last_run < self.delay_all:
            LOG.debug("Command was run %.2f seconds ago, waiting...",
                      time_since_last_run)
            return False

        args.update(self.extra_args)
        if self.run_in_thread:
            LOG.debug("Running %s in a thread", self)
            ScheduleManager.execute_now(self.run_action,
                                        args=[bot, message, event, args])
        else:
            self.run_action(bot, message, event, args)

        return True

    def run_action(self, bot, message, event, args):
        cur_time = now().timestamp()
        self.action.run(bot, message, event, args)

        self.last_run = cur_time
