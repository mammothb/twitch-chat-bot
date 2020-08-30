import logging
from collections import UserDict

from twitchchatbot.models.command import Command

log = logging.getLogger(__name__)


class CommandManager(UserDict):
    """ This class is responsible for compiling commands from multiple
    sources into one easily accessible source.
    The following sources are used:
     - internal_commands = Commands that are added in source
     - plugin_commands = Commands that are loaded from enabled plugins
    """
    def __init__(self, plugin_manager=None, bot=None):
        UserDict.__init__(self)

        self.internal_commands = {}
        self.plugin_commands = {}
        self.data = {}

        self.bot = bot
        self.plugin_manager = plugin_manager

    def load_internal_commands(self):
        if self.internal_commands:
            return self.internal_commands

        self.internal_commands = {}

        self.internal_commands["join"] = Command.bot_command(
            self.bot,
            "join",
            command="join",
            description="Join the specified channel"
        )

        self.internal_commands["quit"] = Command.bot_command(
            self.bot,
            "quit",
            command="quit",
            description="Shut down the bot",
        )
        self.internal_commands["stop"] = self.internal_commands["quit"]

        return self.internal_commands

    def rebuild(self):
        """Rebuild the internal commands list from all sources.
        """
        def merge_commands(in_dict, out):
            for alias, command in in_dict.items():
                if command.action:
                    # Resets any previous modifications to the action.
                    # Right now, the only thing this resets is the MultiAction
                    # command list.
                    command.action.reset()

                if alias in out:
                    if (command.action
                            and command.action.type == "multi"
                            and out[alias].action
                            and out[alias].action.type == "multi"):
                        out[alias].action += command.action
                    else:
                        out[alias] = command
                else:
                    out[alias] = command

        self.data = {}

        merge_commands(self.internal_commands, self.data)

        if self.plugin_manager is not None:
            for enabled_plugin in self.plugin_manager.plugins:
                merge_commands(enabled_plugin.commands, self.data)

    def load(self):
        self.load_internal_commands()

        self.rebuild()

        return self
