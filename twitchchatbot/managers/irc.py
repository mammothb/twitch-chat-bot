import logging
import re
import socket
import ssl

from irc.client import (InvalidCharacters, MessageTooLong, ServerConnection,
                        ServerNotConnectedError)
from irc.connection import Factory
from ratelimiter import RateLimiter

from twitchchatbot.managers.schedule import ScheduleManager

LOG = logging.getLogger("Irc")


class Connection(ServerConnection):
    """We override the default irc.clientServerConnection because want
    to be able to send strings that are 2048(?) bytes long. This is not
    in accordance with the IRC standards, but it's the limit the Twitch
    IRC servers use.
    """
    def send_raw(self, string):
        """Send raw string to the server.
        The string will be padded with appropriate CR LF.
        """
        # The string should not contain any carriage return other than
        # the one added here.
        if "\n" in string or "\r" in string:
            raise InvalidCharacters("CR/LF not allowed in IRC commands")
        string_bytes = string.encode("utf-8") + b"\r\n"
        # According to the RFC http://tools.ietf.org/html/rfc2812#page-6,
        # clients should not transmit more than 512 bytes.
        # However, Twitch have raised that limit to 2048 in their servers.
        if len(string_bytes) > 2048:
            raise MessageTooLong("Messages limited to 2048 bytes including "
                                 "CR/LF")
        if self.socket is None:
            raise ServerNotConnectedError("Not connected.")
        sender = getattr(self.socket, "write", self.socket.send)
        try:
            sender(string_bytes)
        except socket.error:
            # Ouch!
            self.disconnect("Connection reset by peer.")

class Irc:
    RATE = 120  # message rate limit
    CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

    def __init__(self, bot):
        self.bot = bot
        self.sockets = {}

        self.conn = None
        self.ping_task = None

        self.num_privmsg_sent = 0

        self.channels = [self.bot.channel]

        bot.reactor.add_global_handler("all_events", self._dispatcher, -10)
        bot.reactor.add_global_handler("disconnect", self._on_disconnect)
        bot.reactor.add_global_handler("welcome", self._on_welcome)

    @RateLimiter(max_calls=1, period=2)
    def start(self):
        if self.conn is not None or self.ping_task is not None:
            raise AssertionError("start() should not be called while a "
                                 "connection is active")

        try:
            self._make_new_connection()
        except Exception:
            LOG.exception("Failed to open connection, retrying in 2 seconds")

            # reset our state back to if we weren't connected at all,
            # so we can start fresh once start() is called again, e.g.,
            # if _make_new_connection() fails at the part where it gets
            # the login password, and if this wasn't here, then it
            # would leave a self.conn behind that isn't None. (and the
            # AssertionError above would be raised in 2 seconds, once
            # self.start() gets called again via execute_delayed)
            self.conn = None

            self.bot.execute_delayed(2, self.start)

    def privmsg(self, channel, message):
        if self.conn is None or not self._can_send:
            LOG.error("Not connected or rate limit was reached. Delaying "
                      "message a few seconds.")
            self.bot.execute_delayed(2, self.privmsg, channel, message)
            return

        self.conn.privmsg(channel, message)

        self.num_privmsg_sent += 1
        self.bot.execute_delayed(31, self._reduce_num_privmsg_sent)

    @RateLimiter(max_calls=1, period=2)
    def join(self, channel):
        self.conn.join(channel)
        self.channels.append(channel)
        LOG.info("Joined channel %s", channel)

    @property
    def _can_send(self):
        return self.num_privmsg_sent < self.bot.privmsg_per_30

    def _dispatcher(self, conn, event):
        method = getattr(self.bot, "on_" + event.type, None)
        if method is not None:
            try:
                method(conn, event)
            except Exception:
                LOG.exception("Logging an uncaught exception (IRC event "
                              "handler)")

    def _make_new_connection(self):
        self.conn = Connection(self.bot.reactor)
        with self.bot.reactor.mutex:
            self.bot.reactor.connections.append(self.conn)
        self.conn.connect("irc.chat.twitch.tv",
                          6697,
                          self.bot.nickname,
                          self.bot.password,
                          self.bot.nickname,
                          connect_factory=Factory(wrapper=ssl.wrap_socket))

        self.ping_task = ScheduleManager.execute_every(
            30, lambda: self.bot.execute_now(self._send_ping))

    def _on_disconnect(self, _conn, event):
        LOG.error("Disconnected from IRC (%s)", event.arguments[0])
        self.conn = None
        # Stops the scheduled task from further executing
        self.ping_task.remove()
        self.ping_task = None
        self.start()

    def _on_welcome(self, conn, _event):
        LOG.info("Successfully connected and authenticated with IRC")
        conn.join(",".join(self.channels))

    def _reduce_num_privmsg_sent(self):
        self.num_privmsg_sent -= 1

    def _send_ping(self):
        if self.conn is not None:
            self.conn.ping("tmi.twitch.tv")
