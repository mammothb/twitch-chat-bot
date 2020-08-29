import logging
import sys

import irc.client

from twitchchatbot.constants import NAME, VERSION
from twitchchatbot.eventloop import SafeDefaultScheduler
from twitchchatbot.managers.handler import HandlerManager
from twitchchatbot.managers.irc import Irc
from twitchchatbot.managers.schedule import ScheduleManager
from twitchchatbot.plugins import search

LOG = logging.getLogger("Bot")

class Bot:
    COMMANDS = ["echo", "join", "search", "stop"]

    def __init__(self, config):
        LOG.info("Bot starting...")
        self.config = config

        ScheduleManager.init()

        self.privmsg_per_30 = 90
        self.phrases = {
            "welcome": ["{nickname} {version} running! peepoChag"],
            "quit": ["{nickname} {version} shutting down... peepoKEKWait"],
        }
        self.welcome_messages_sent = False

        self.admins = self.config["Bot"]["admins"].split(",")
        self.channel = f"#{self.config['Bot']['channel']}"
        self.nickname = self.config["Bot"]["nickname"]
        self.password = self.config["Bot"]["password"]
        self.prefix = self.config["Bot"]["prefix"]

        LOG.debug("Config loaded.")

        self.reactor = irc.client.Reactor()
        # SafeDefaultScheduler makes the bot not exit on exception in
        # the main thread, e.g., on actions via bot.execute_now, etc.
        self.reactor.scheduler_class = SafeDefaultScheduler
        self.reactor.scheduler = SafeDefaultScheduler()

        HandlerManager.init_handlers()

        self.irc = Irc(self)
        self.is_running = True

    def connect(self):
        self.irc.start()

    def start(self):
        """Start the IRC client."""
        self.reactor.process_forever()

    def quit_bot(self):
        HandlerManager.trigger("on_quit")
        phrase_data = {"nickname": NAME, "version": VERSION}

        try:
            ScheduleManager.base_scheduler.print_jobs()
            ScheduleManager.base_scheduler.shutdown(wait=False)
        except Exception:
            LOG.exception("Error while shutting down the apscheduler")

        try:
            for p in self.phrases["quit"]:
                self.privmsg(p.format(**phrase_data))
        except Exception:
            LOG.exception("Exception caught while trying to say quit phrase")

        sys.exit(0)

    def privmsg(self, message, channel=None):
        if channel is None:
            channel = self.channel

        self.irc.privmsg(channel, message)

    def on_pubmsg(self, _chatconn, event):
        if self.is_bot(event.source.user):
            return False

        res = HandlerManager.trigger("on_pubmsg", message=event.arguments[0])
        if res is False:
            return False

        self.parse_message(event.arguments[0], event)

    def on_welcome(self, _conn, _event):
        """Gets triggered on IRC welcome, i.e. when the login is
        successful.
        """
        if self.welcome_messages_sent:
            return

        for p in self.phrases["welcome"]:
            self.privmsg(p.format(nickname=NAME, version=VERSION))

        self.welcome_messages_sent = True

    def parse_message(self, message, event):
        res = HandlerManager.trigger("on_message", message=message,
                                     event=event)
        if res is False:
            return False

        msg_lower = message.lower()
        if msg_lower[0] == self.prefix:
            trigger = msg_lower.split(" ")[0][1 :]
            msg_raw_parts = message.split(" ")
            remaining_message = (" ".join(msg_raw_parts[1 :])
                                 if len(msg_raw_parts) > 1 else "")
            if trigger in self.COMMANDS:
                self._execute_command(trigger, remaining_message, event)

    def is_admin(self, username):
        return username in self.admins

    def is_bot(self, username):
        return username.lower() == self.nickname.lower()

    def execute_delayed(self, delay, function, *args, **kwargs):
        self.reactor.scheduler.execute_after(
            delay, lambda: function(*args, **kwargs))

    def execute_every(self, period, function, *args, **kwargs):
        self.reactor.scheduler.execute_every(
            period, lambda: function(*args, **kwargs))

    def execute_now(self, function, *args, **kwargs):
        self.execute_delayed(0, function, *args, **kwargs)

    def _execute_command(self, command, remaining_message, event):
        # ADMIN ONLY COMMANDS
        if self.is_admin(event.source.user):
            if command == "echo":
                self.privmsg(remaining_message, event.target)
            elif command == "join":
                self.irc.join(f"#{remaining_message.split(' ')[0]}")
            elif command == "search":
                self.privmsg(search.googleimg(remaining_message),
                             event.target)
            elif command == "stop":
                self.quit_bot()
