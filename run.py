import logging

from twitchchatbot.bot import Bot

FORMAT = '%(asctime)-15s %(levelname)7s %(name)7s: %(message)s'
logging.basicConfig(format=FORMAT, level=logging.INFO)
# logging.basicConfig(format=FORMAT, level=logging.DEBUG)

BOT = Bot()
BOT.prepare()
BOT.run()
