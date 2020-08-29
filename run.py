import configparser
import logging
import os.path

from twitchchatbot.bot import Bot

FORMAT = '%(asctime)-15s %(levelname)7s %(name)7s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
# logging.basicConfig(format=FORMAT, level=logging.DEBUG)

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.ini")

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if not config.sections():
        raise ValueError(f"Failed to load {CONFIG_PATH}")

    bot = Bot(config)
    bot.connect()

    try:
        bot.start()
    except KeyboardInterrupt:
        bot.quit_bot()
