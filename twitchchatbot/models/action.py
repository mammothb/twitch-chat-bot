import logging

LOG = logging.getLogger(__name__)


class BaseAction:
    type = None
    subtype = None

    def reset(self):
        pass

class RawFuncAction(BaseAction):
    type = "rawfunc"

    def __init__(self, cb):
        self.cb = cb

    def run(self, bot, message, event, args=None):
        if args is None:
            args = {}
        return self.cb(bot=bot, message=message, event=event, args=args)
