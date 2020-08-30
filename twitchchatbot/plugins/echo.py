import logging

from twitchchatbot.models.command import Command
from twitchchatbot.plugins import BasePlugin
from twitchchatbot.plugins import PluginSetting

log = logging.getLogger(__name__)


class EchoPlugin(BasePlugin):
    ID = __name__.split(".")[-1]
    NAME = "Echo"
    DESCRIPTION = "Gives users access to the !echo command!"
    CATEGORY = "Game"
    SETTINGS = [
        PluginSetting(
            key="online_global_cd",
            label="Global cooldown (seconds)",
            type="number",
            required=True,
            placeholder="",
            default=4,
            constraints={"min_value": 0, "max_value": 120},
        )
    ]

    def echo_command(self, bot, message, _event, **_kwargs):
        if not message:
            return

        bot.say(message)

    def load_commands(self, **options):
        self.commands["echo"] = Command.raw_command(
            self.echo_command,
            delay_all=self.settings["online_global_cd"],
            description="Echo an phrase"
        )
