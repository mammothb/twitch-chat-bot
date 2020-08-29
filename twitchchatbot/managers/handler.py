import logging
import operator

from twitchchatbot.utils import find

LOG = logging.getLogger("HandlerManager")

class HandlerManager:
    handlers = {}

    @staticmethod
    def init_handlers():
        HandlerManager.handlers = {}

        # on_pubmsg(source, message)
        HandlerManager.create_handler("on_pubmsg")

        # on_message(source, message, emote_instances, emote_counts,
        # whisper, urls, msg_id, event)
        HandlerManager.create_handler("on_message")

        # on_quit()
        HandlerManager.create_handler("on_quit")

    @staticmethod
    def create_handler(event):
        """ Create an empty list for the given event """
        HandlerManager.handlers[event] = []

    @staticmethod
    def add_handler(event, method, priority=0):
        try:
            HandlerManager.handlers[event].append((method, priority))
            HandlerManager.handlers[event].sort(key=operator.itemgetter(1),
                                                reverse=True)
        except KeyError:
            # No handlers for this event found
            LOG.error("add_handler No handler for %s found.", event)

    @staticmethod
    def method_matches(h, method):
        return h[0] == method

    @staticmethod
    def remove_handler(event, method):
        handler = None
        try:
            handler = find(lambda h: HandlerManager.method_matches(h, method),
                           HandlerManager.handlers[event])
            if handler is not None:
                HandlerManager.handlers[event].remove(handler)
        except KeyError:
            # No handlers for this event found
            LOG.error("remove_handler No handler for %s found.", event)

    @staticmethod
    def trigger(event_name, stop_on_false=True, *args, **kwargs):
        if event_name not in HandlerManager.handlers:
            LOG.error("No handler set for event %s", event_name)
            return False

        for handler, _ in HandlerManager.handlers[event_name]:
            res = None
            try:
                res = handler(*args, **kwargs)
            except Exception:
                LOG.exception("Unhandled exception from %s in %s", handler,
                              event_name)

            if res is False and stop_on_false is True:
                # Abort if handler returns false and stop_on_false is
                # enabled
                return False

        return True
