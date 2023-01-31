"""
The module that contains the definition of the AbstractPublisher plugin, which is used
to publish notifications externally.
"""
# Standard Library
import abc
from typing import Any, List, Type, cast

# Sematic
from sematic.abstract_plugin import AbstractPlugin, PluginScope
from sematic.config.settings import get_active_plugins


class AbstractPublisher(abc.ABC):
    """
    Abstract base class to represent an event external publisher.
    """

    @abc.abstractmethod
    def publish(self, event: Any) -> None:
        pass


def get_publishing_plugins(
    default: List[Type[AbstractPlugin]],
) -> List[Type[AbstractPublisher]]:
    """
    Return all configured "PUBLISH" scope plugins.
    """
    publisher_plugins = get_active_plugins(scope=PluginScope.PUBLISH, default=default)

    publisher_classes = [
        cast(Type[AbstractPublisher], plugin) for plugin in publisher_plugins
    ]

    return publisher_classes
