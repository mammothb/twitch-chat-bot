import logging

from twitchchatbot.utils import find

LOG = logging.getLogger(__name__)


class PluginSetting:
    """
    A single setting for a Plugin.

    Available types:
      * text - A text input
        Available constraints:
          * min_str_len
          * max_str_len
      * number - A number input (Integer)
          * min_value
          * max_value
      * boolean - A checkbox input
      * options - A select/options list
    """

    def __init__(self, key, label, type, required=False, placeholder="",
                 default=None, constraints={}, options=[]):
        self.key = key
        self.label = label
        self.type = type
        self.required = required
        self.placeholder = placeholder
        self.default = default
        self.constraints = constraints
        self.options = options

    def validate(self, value):
        """ Validate the input for this plugin.
        This will call the relevant submethod, located as
        validate_{type}. You always get a tuple back, with the first
        value being True or False depending on if the input value was
        validated properly. The second value is the properly parsed
        value. So for example, calling validate('50') on a number
        setting would return (True, 50)
        """

        validator = getattr(self, f"validate_{self.type}", None)
        if validator is None:
            LOG.info("No validator available for type %s", type)
            return True, value

        if not callable(validator):
            LOG.error("Validator is not callable %s", type)
            return True, value

        return validator(value)

    def validate_text(self, value):
        """ Validate a text value """
        value = value.strip()
        if ("min_str_len" in self.constraints
                and len(value) < self.constraints["min_str_len"]):
            return (False, "needs to be at least "
                    f"{self.constraints['min_str_len']} characters long")
        if ("max_str_len" in self.constraints
                and len(value) > self.constraints["max_str_len"]):
            return (False, "needs to be at most "
                    f"{self.constraints['max_str_len']} characters long")
        return True, value

    def validate_number(self, value):
        """ Validate a number value """
        try:
            value = int(value)
        except ValueError:
            return False, "Not a valid integer"

        if ("min_value" in self.constraints
                and value < self.constraints["min_value"]):
            return (False, "needs to have a value that is at least "
                    f"{self.constraints['min_value']}")
        if ("max_value" in self.constraints
                and value > self.constraints["max_value"]):
            return (False, "needs to have a value that is at most "
                    f"{self.constraints['max_value']}")
        return True, value

    @staticmethod
    def validate_boolean(value):
        """ Validate a boolean value """
        return True, value == "on"

    def validate_options(self, value):
        """ Validate a options value """
        return value in self.options, value


class PluginType:
    TYPE_NORMAL = 1
    TYPE_ALWAYS_ENABLED = 2


class BasePlugin:
    """
    This class will include all the basics that a plugin needs
    to be operable.
    """

    ID = __name__.split(".")[-1]
    NAME = "Base Plugin"
    DESCRIPTION = ("This is the description for the base plugin. "
                   "It's what will be shown on the website where you can "
                   "enable and disable plugins.")
    SETTINGS = []
    ENABLED_DEFAULT = False
    PARENT_MODULE = None
    CATEGORY = "Uncategorized"
    HIDDEN = False
    MODULE_TYPE = PluginType.TYPE_NORMAL
    CONFIGURE_LEVEL = 500

    def __init__(self, bot):
        """Initialize any dictionaries the plugin might or might not
        use.
        """
        self.bot = bot

        self.commands = {}
        self.default_settings = {}
        self.settings = {}
        self.subplugins = []
        self.parent_plugin = None

        # We store a dictionary with the default settings for
        # convenience
        for setting in self.SETTINGS:
            self.default_settings[setting.key] = setting.default

    def load(self, **options):
        """ This method will load everything from the plugin into
        their proper dictionaries, which we can then use later. """

        self.settings = self.plugin_settings()

        self.commands = {}
        self.load_commands(**options)

        return self

    @classmethod
    def plugin_settings(cls):
        settings = {}

        # Load any unset settings
        for setting in cls.SETTINGS:
            if setting.key not in settings:
                settings[setting.key] = setting.default

        return settings

    @classmethod
    def is_enabled(cls):
        return cls.ENABLED_DEFAULT

    def load_commands(self, **options):
        pass

    def parse_settings(self, **in_settings):
        ret = {}
        for key, value in in_settings.items():
            setting = find(lambda setting, setting_key=key:
                           setting.key == setting_key, self.SETTINGS)
            if setting is None:
                # We were passed a setting that's not available for
                # this plugin
                return False
            LOG.debug("%s: %s", key, value)
            res, new_value = setting.validate(value)
            if res is False:
                # Something went wrong when validating one of the
                # settings
                LOG.warning(new_value)
                return False

            ret[key] = new_value

        for setting in self.SETTINGS:
            if setting.type == "boolean":
                if setting.key not in ret:
                    ret[setting.key] = False
                    LOG.debug("%s: %s - special", setting.key, False)

        return ret

    def enable(self, bot):
        pass

    def disable(self, bot):
        pass

    def on_loaded(self):
        pass

    def get_phrase(self, key, **arguments):
        if key not in self.settings:
            LOG.error("%s is not in this plugins settings.", key)
            return "KeyError in get_phrase"

        try:
            return self.settings[key].format(**arguments)
        except (IndexError, ValueError, KeyError):
            LOG.warning("An error occured when formatting phrase '%s. "
                        "Arguments: (%s) Will fall back to default phrase.",
                        self.settings[key], arguments)

        try:
            return self.default_settings[key].format(**arguments)
        except Exception:
            LOG.exception("ABORT - The default phrase %s is BAD. Arguments: "
                          "(%s)", self.default_settings[key], arguments)

        return "FatalError in get_phrase"
