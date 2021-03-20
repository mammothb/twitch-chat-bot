import asyncio
import configparser
import errno
import logging
import os.path
import time
import types

from twitchchatbot.chat import Chat, WriteOnlyConn
from twitchchatbot.plugins import color, search

CONFIG_PATH = "config.ini"
LOG = logging.getLogger("Bot")

class Bot:
    COMMANDS = ["color", "echo", "join", "leave", "search", "stop"]
    NAME = "Bot"
    VERSION = "0.1.0"

    def __init__(self):
        LOG.info("Bot starting...")
        self.is_loaded = False
        self.is_running = False
        self.chat = Chat(self)
        self.writer = WriteOnlyConn(self)
        self.var = types.SimpleNamespace()
        self.var.color_mode = "pleb"

    def prepare(self):
        """Load config and perform ready checks
        """
        self._load_config()
        self.is_running = (
            self.chat.is_ready and self.writer.is_ready and self.is_ready
        )

    def process_message(self, username, chan, message):
        clean_message = message.strip()
        if self.is_admin(username):
            self._change_color(color.randomize(self.var.color_mode == "prime"))
        if message[0] == self.var.prefix:
            split_message = clean_message.split(" ")
            if split_message[0][1 :] in self.COMMANDS:
                LOG.info("Command recognized.")
                self._execute_command(username, chan, split_message)
                time.sleep(1)

    def run(self):
        if self.is_running:
            try:
                self.chat.connect()
                self.writer.connect()
                LOG.info("%s v%s loaded.", self.NAME, self.VERSION)
            except (OSError,):
                LOG.error(
                    "Connection failed. Check config file and reboot bot."
                )
                self.is_running = False
        else:
            LOG.error("Bot NOT running! Check the errors and reboot bot.")

        while self.is_running:
            self.chat.scanloop()
            self.writer.scanloop()

    def is_admin(self, username):
        return username == self.var.admin

    @property
    def is_ready(self):
        return self.is_loaded

    def _execute_command(self, username, channel, split_message):
        command = split_message[0][1 :]
        # ADMIN ONLY COMMANDS
        if self.is_admin(username):
            if command == "color":
                self._set_color_mode(split_message[1])
            elif command == "echo":
                self._send_msg(" ".join(split_message[1 :]), channel)
            elif command == "join":
                self.chat.connect(f"#{split_message[1]}")
                self.writer.connect(f"#{split_message[1]}")
            elif command == "leave":
                self.chat.disconnect(f"#{split_message[1]}")
                self.writer.disconnect(f"#{split_message[1]}")
            elif command == "search":
                self._send_msg(search.googleimg(" ".join(split_message[1 :])),
                               channel)
            elif command == "stop":
                self._stop()

    def _load_config(self):
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                    CONFIG_PATH)
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        self.chat.set_config(config["Chat"])
        self.writer.set_config(config["Writer"])

        self._set_variables(config)
        LOG.info("Config loaded.")

    def _send_msg(self, message, channel=None):
        self.chat.send_msg(channel, message)

    def _change_color(self, message, channel=None):
        self.writer.send_msg(channel, f"/color {message}")

    def _set_color_mode(self, mode):
        if mode.lower() in ("prime", "pleb"):
            self.var.color_mode = mode.lower()

    def _set_variables(self, config):
        try:
            self._set_bot_variables(config["Bot"])
            self._set_admin_variables(config["Admin"])
            self.is_loaded = True
        except (KeyError, ValueError):
            LOG.error("Config not loaded! Check config file and reboot bot.")
            self.is_loaded = False

    def _set_admin_variables(self, config):
        self.var.admin = config["admin"]

    def _set_bot_variables(self, config):
        self.var.prefix = config["prefix"]

    def _stop(self):
        self.is_running = False
