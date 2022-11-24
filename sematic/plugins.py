# Standard Library
import abc
import enum
import logging
from collections import defaultdict
from typing import Callable, Dict, Type

# Sematic
from sematic.config.user_settings import UserSettingsVar, get_user_settings

logger = logging.getLogger(__name__)


class PluginScope(enum.Enum):
    STORAGE = "STORAGE"


class AbstractPlugin(abc.ABC):
    __author__: str


_scoped_plugin_registry_factory: Callable[
    [], Dict[str, Type[AbstractPlugin]]
] = lambda: dict()


_PLUGIN_REGISTRY: Dict[PluginScope, Dict[str, Type[AbstractPlugin]]] = defaultdict(
    _scoped_plugin_registry_factory
)


def register_plugin(
    scope: PluginScope, author: str
) -> Callable[[Type[AbstractPlugin]], Type[AbstractPlugin]]:
    if not isinstance(scope, PluginScope):
        raise ValueError(
            f"scope must be of type {PluginScope.__name__},"
            f" got {scope} of type {type(scope)}"
        )

    def _wrapper(plugin: Type[AbstractPlugin]) -> Type[AbstractPlugin]:
        if not issubclass(plugin, AbstractPlugin):
            raise ValueError(
                f"plugin {plugin.__name__} must be of type {AbstractPlugin.__name__}"
            )

        name = plugin.__name__

        if name in _PLUGIN_REGISTRY[scope]:
            logger.warning("Overriding plugin %s for scope %s", name, scope.value)

        plugin.__author__ = author

        _PLUGIN_REGISTRY[scope][name] = plugin

        return plugin

    return _wrapper


def get_selected_plugin(
    scope: PluginScope, default: Type[AbstractPlugin]
) -> Type[AbstractPlugin]:
    setting_var_name = f"SEMATIC_{scope.value}"

    try:
        setting_var = UserSettingsVar[setting_var_name]
    except KeyError:
        # RuntimeError because this is a bug, it means the settingsvar is not defined
        raise RuntimeError(f"Setting var not found: {setting_var_name}")

    setting_value = get_user_settings(setting_var, default.__name__)

    return get_registered_plugin(scope, setting_value)


def get_registered_plugin(scope: PluginScope, name: str) -> Type[AbstractPlugin]:
    try:
        return _PLUGIN_REGISTRY[scope][name]
    except KeyError:
        raise ValueError(
            f"No plugin named {name} for scope {scope.value} was registered."
        )
