import logging

from twitchchatbot.utils import find

LOG = logging.getLogger("Plugin")


class Plugin:
    def __init__(self, plugin_id, **options):
        self.id = plugin_id
        self.enabled = options.get("enabled", False)
        self.settings = None


class PluginManager:
    def __init__(self, bot=None):
        # List of all enabled plugins
        self.plugins = []

        # List of all available plugins, both enabled and disabled
        self.all_plugins = []

        self.bot = bot

    def get_plugin(self, plugin_id):
        return find(lambda m: m.ID == plugin_id, self.all_plugins)

    def on_plugin_update(self, data):
        new_state = data.get("new_state", None)
        if new_state is True:
            self.enable_plugin(data["id"])
        elif new_state is False:
            self.disable_plugin(data["id"])
        else:
            plugin = self.get_plugin(data["id"])

            if plugin:
                plugin.load()

    def enable_plugin(self, plugin_id):
        plugin = self.get_plugin(plugin_id)
        if plugin is None:
            LOG.error("No plugin with the ID %s found.", plugin_id)
            return False

        plugin.load()

        plugin.enable(self.bot)

        if plugin in self.plugins:
            LOG.error("Plugin %s is already in the list of enabled plugins",
                      plugin_id)
            return False

        self.plugins.append(plugin)

        return True

    def disable_plugin(self, plugin_id):
        plugin = self.get_plugin(plugin_id)
        if not plugin:
            LOG.error("No plugin with the ID %s found.", plugin_id)
            return False

        plugin.disable(self.bot)

        if plugin not in self.plugins:
            LOG.error("Plugin %s is not in the list of enabled plugins",
                      plugin_id)
            return False

        self.plugins.remove(plugin)

        return True

    def load(self, do_reload=True):
        """Load plugin classes"""

        from twitchchatbot.plugins import available_plugins

        self.all_plugins = [plugin(self.bot) for plugin in available_plugins]

        if do_reload is True:
            self.reload()

        return self

    def reload(self):
        for plugin in self.plugins:
            plugin.disable(self.bot)

        self.plugins = []
        for enabled_plugin in self.all_plugins:
            plugin = self.get_plugin(enabled_plugin.ID)
            if plugin is not None:
                options = {}
                if enabled_plugin.settings is not None:
                    try:
                        options["settings"] = enabled_plugin.settings
                    except ValueError:
                        LOG.warning("Invalid JSON")

                self.plugins.append(plugin.load(**options))
                plugin.enable(self.bot)

        to_be_removed = []
        self.plugins.sort(key=lambda m: 1 if m.PARENT_MODULE is not None
                          else 0)
        for plugin in self.plugins:
            if plugin.PARENT_MODULE is None:
                plugin.subplugins = []
            else:
                parent = find(lambda m: m.__class__ == plugin.PARENT_MODULE,
                              self.plugins)
                if parent is not None:
                    parent.subplugins.append(plugin)
                    plugin.parent_plugin = parent
                else:
                    plugin.parent_plugin = None
                    to_be_removed.append(plugin)

        for plugin in to_be_removed:
            plugin.disable(self.bot)
            self.plugins.remove(plugin)

        # Perform a last on_loaded call on each plugin.
        # This is used for things that require subplugins to be loaded
        # properly, i.e., the quest system
        for plugin in self.plugins:
            plugin.on_loaded()

    def __getitem__(self, plugin):
        for enabled_plugin in self.plugins:
            if enabled_plugin.ID == plugin:
                return enabled_plugin
        return None

    def __contains__(self, plugin):
        """We override the contains operator for the PluginManager.
        This allows us to use the following syntax to check if a plugin
        is enabled: if 'duel' in plugin_manager:
        """
        for enabled_plugin in self.plugins:
            if enabled_plugin.ID == plugin:
                return True
        return False
