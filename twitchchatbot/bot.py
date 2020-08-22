import asyncio
import configparser
import errno
import logging
import os.path
import time
import types

from twitchchatbot.chat import Chat
from twitchchatbot.plugins import search

CONFIG_PATH = "config.ini"
LOG = logging.getLogger("Bot")

class Bot:
    COMMANDS = ["echo", "join", "search", "setemote", "stop"]
    NAME = "Bot"
    VERSION = "0.1.0"

    def __init__(self):
        LOG.info("Bot starting...")
        self.is_loaded = False
        self.is_running = False
        self.chat = Chat(self)
        self.var = types.SimpleNamespace()

    def prepare(self):
        """Load config and perform ready checks
        """
        self._load_config()
        self.is_running = self.chat.is_ready and self.is_ready

    def process_message(self, username, chan, message):
        clean_message = message.strip()
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
                self._send_msg("")
                LOG.info("%s v%s loaded.", self.NAME, self.VERSION)
            except (OSError,):
                LOG.error("Connection failed. Check config file and reboot "
                          "bot.")
                self.is_running = False
        else:
            LOG.error("Bot NOT running! Check the errors and reboot bot.")

        while self.is_running:
            self.chat.scanloop()

    def is_admin(self, username):
        return username in self.var.admins

    @property
    def is_ready(self):
        return self.is_loaded

    def _execute_command(self, username, channel, split_message):
        command = split_message[0][1 :]
        # ADMIN ONLY COMMANDS
        if self.is_admin(username):
            if command == "echo":
                self._send_msg(" ".join(split_message[1 :]), channel)
            elif command == "join":
                try:
                    self.chat.connect(f"#{split_message[1]}", split_message[2])
                except IndexError:
                    self.chat.connect(f"#{split_message[1]}")
            elif command == "search":
                self._send_msg(search.googleimg(" ".join(split_message[1 :])),
                               channel)
            elif command == "setemote":
                self.chat.set_emote(channel, split_message[1])
                self._send_msg("Emote updated!", channel)
            elif command == "stop":
                self._stop()

    def _load_config(self):
        if not os.path.exists(CONFIG_PATH):
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT),
                                    CONFIG_PATH)
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        self.chat.set_config(config["Chat"])
        self._set_variables(config)
        LOG.info("Config loaded.")

    def _send_msg(self, message, channel=None):
        self.chat.send_msg(channel, message)

    def _set_variables(self, config):
        try:
            self._set_bot_variables(config["Bot"])
            self._set_admin_variables(config["Admin"])
            self.is_loaded = True
        except (KeyError, ValueError):
            LOG.error("Config not loaded! Check config file and reboot bot.")
            self.is_loaded = False

    def _set_admin_variables(self, config):
        self.var.admins = config["admins"].split(",")

    def _set_bot_variables(self, config):
        self.var.prefix = config["prefix"]

    def _stop(self):
        self.is_running = False
