import collections
import logging
import re
import socket
import time
import types

LOG = logging.getLogger("Chat")

Connection = collections.namedtuple("Connection", ["host", "port", "nick",
                                                   "passwd"])

class Chat:
    RATE = 120  # message rate limit
    CHAT_MSG = re.compile(r"^:\w+!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :")

    def __init__(self, bot):
        self.bot = bot
        self.sockets = {}

        self.channel = None
        self.conn = None
        self.is_loaded = False

    def connect(self, channel=None):
        if channel is None:
            self.sockets[self.channel] = types.SimpleNamespace(
                sock=socket.socket()
            )
            self._connect(self.sockets[self.channel].sock, self.channel)
        else:
            self.sockets[channel] = types.SimpleNamespace(sock=socket.socket())
            self._connect(self.sockets[channel].sock, channel)
            LOG.debug(channel)

    def disconnect(self, channel):
        if channel in self.sockets:
            self._disconnect(self.sockets[channel].sock, channel)
            del self.sockets[channel]
            LOG.debug(channel)
            print(self.sockets)

    def scanloop(self):
        """Loops through all the sockets we have and scan for response
        while respecting the rate limit
        """
        for chan in list(self.sockets):
            self._scan(chan)

    def send_msg(self, channel, message):
        if channel is None:
            channel = self.channel
        self.sockets[channel].sock.send(
            ":{0}!{0}@{0}.tmi.twitch.tv PRIVMSG {1} :{2}\r\n".format(
                self.conn.nick, channel, message
            ).encode("utf-8")
        )

    def set_config(self, config):
        try:
            self.conn = Connection(
                config["host"],
                int(config["port"]),
                config["nick"],
                config["pass"],
            )
            self.channel = config["chan"]
            self.is_loaded = True
        except (KeyError, ValueError):
            LOG.error("Config not loaded! Check config file and reboot bot.")
            self.is_loaded = False

    def is_bot(self, username):
        return username.lower() == self.conn.nick.lower()

    @property
    def is_ready(self):
        return self.is_loaded

    def _connect(self, sock, chan):
        sock.connect((self.conn.host, self.conn.port))
        sock.send(f"PASS {self.conn.passwd}\r\n".encode("utf-8"))
        sock.send(f"NICK {self.conn.nick}\r\n".encode("utf-8"))
        sock.send(f"JOIN {chan}\r\n".encode("utf-8"))
        time.sleep(1)
        sock.setblocking(0)

    def _disconnect(self, sock, chan):
        sock.send(f"PART {chan}\r\n".encode("utf-8"))
        time.sleep(1)

    def _scan(self, channel):
        try:
            response = self.sockets[channel].sock.recv(1024).decode("utf-8")
            if response == "PING :tmi.twitch.tv\r\n":
                self.sockets[channel].sock.send(
                    "PONG :tmi.twitch.tv\r\n".encode("utf-8")
                )
                LOG.info("Pong sent")
                return
            username = re.search(r"\w+", response).group(0)
            if self.is_bot(username):
                return
            message = self.CHAT_MSG.sub("", response)
            LOG.debug("USER: %s%s : %s", username, channel, message)
            self.bot.process_message(username, channel, message)
        except (AttributeError, BlockingIOError, KeyError, UnicodeDecodeError):
            pass
        finally:
            time.sleep(1 / self.RATE)

class WriteOnlyConn(Chat):
    def _connect(self, sock, chan):
        sock.connect((self.conn.host, self.conn.port))
        sock.send(f"PASS {self.conn.passwd}\r\n".encode("utf-8"))
        sock.send(f"NICK {self.conn.nick}\r\n".encode("utf-8"))
        sock.send(f"JOIN {chan}\r\n".encode("utf-8"))
        time.sleep(1)
        sock.setblocking(0)

    def _scan(self, channel):
        try:
            response = self.sockets[channel].sock.recv(1024).decode("utf-8")
            if response == "PING :tmi.twitch.tv\r\n":
                self.sockets[channel].sock.send(
                    "PONG :tmi.twitch.tv\r\n".encode("utf-8")
                )
                LOG.info("Pong sent")
                return
        except (BlockingIOError, AttributeError, UnicodeDecodeError):
            pass
        finally:
            time.sleep(1 / self.RATE)