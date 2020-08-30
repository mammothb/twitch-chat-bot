import logging

import random

from twitchchatbot.models.command import Command
from twitchchatbot.plugins import BasePlugin
from twitchchatbot.plugins import PluginSetting

log = logging.getLogger(__name__)


class EightBallPlugin(BasePlugin):
    ID = __name__.split(".")[-1]
    NAME = "8-ball"
    DESCRIPTION = "Gives users access to the !8ball command!"
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

    def __init__(self, bot):
        super().__init__(bot)
        self.phrases = [
            "sure",
            "are you kidding?!",
            "yeah",
            "no",
            "i think so",
            "don't bet on it",
            "ja",
            "doubtful",
            "for sure",
            "forget about it",
            "nein",
            "maybe",
            "Kappa Keepo PogChamp",
            "sure",
            "i dont think so",
            "it is so",
            "leaning towards no",
            "look deep in your heart and you will see the answer",
            "most definitely",
            "most likely",
            "my sources say yes",
            "never",
            "nah m8",
            "might actually be yes",
            "no.",
            "outlook good",
            "outlook not so good",
            "perhaps",
            "mayhaps",
            "that's a tough one",
            "idk kev",
            "don't ask that",
            "the answer to that isn't pretty",
            "the heavens point to yes",
            "who knows?",
            "without a doubt",
            "yesterday it would've been a yes, but today it's a yep",
            "you will have to wait",
        ]

        self.emotes = [
            "Kappa",
            "Keepo",
            "xD",
            "KKona",
            "4Head",
            "EleGiggle",
            "DansGame",
            "KappaCool",
            "BrokeBack",
            "OpieOP",
            "KappaRoss",
            "KappaPride",
            "FeelsBadMan",
            "FeelsGoodMan",
            "PogChamp",
            "VisLaud",
            "OhMyDog",
            "FrankerZ",
            "DatSheffy",
            "BabyRage",
            "VoHiYo",
            "haHAA",
            "FeelsBirthdayMan",
            "LUL",
        ]

    def eightball_command(self, bot, message, event, **_kwargs):
        if not message:
            return

        phrase = random.choice(self.phrases)
        emote = random.choice(self.emotes)
        bot.me(f"{event.source.user}, the 8-ball says... {phrase} {emote}")

    def load_commands(self, **options):
        self.commands["8ball"] = Command.raw_command(
            self.eightball_command,
            delay_all=self.settings["online_global_cd"],
            description="Need help with a decision? Use the !8ball command!"
        )
