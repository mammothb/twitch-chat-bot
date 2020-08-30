from twitchchatbot.plugins.base import BasePlugin
from twitchchatbot.plugins.base import PluginSetting
from twitchchatbot.plugins.base import PluginType

from twitchchatbot.plugins.echo import EchoPlugin
from twitchchatbot.plugins.eightball import EightBallPlugin

available_plugins = [
    EchoPlugin,
    EightBallPlugin
]
