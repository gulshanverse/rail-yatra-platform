"""
Plugin Architecture for Milestone 6.6 AI Response Composer Platform.
Provides extension points for future multi-modal integrations (IRCTC, Metro, Bus, Flight, Hotel,
Maps, Voice, Payments) without modifying core platform code.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class IComposerPlugin(ABC):
    """Abstract interface for all Response Composer plugins."""

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """Returns unique plugin identifier."""
        pass

    @property
    @abstractmethod
    def supported_intents(self) -> List[str]:
        """Returns list of intent codes handled by this plugin."""
        pass

    @abstractmethod
    def process_data(self, intent: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Processes intent payload and returns enriched composition elements."""
        pass


class MetroConnectionPlugin(IComposerPlugin):
    """Plugin enriching responses with last-mile Metro station transfer guidance."""

    @property
    def plugin_name(self) -> str:
        return "METRO_CONNECTION_PLUGIN"

    @property
    def supported_intents(self) -> List[str]:
        return ["METRO_TRANSFER", "STATION_LAST_MILE"]

    def process_data(self, intent: str, input_payload: Dict[str, Any]) -> Dict[str, Any]:
        station = input_payload.get("station", "NDLS")
        return {
            "section_type": "DETAILS",
            "content": f"🚇 **Metro Transfer Info**: Yellow Line Metro connects directly to Gate 2 of {station}.",
            "priority": "SECONDARY",
        }


class PluginRegistry:
    """Centralized registry for managing platform extension plugins."""

    def __init__(self):
        self._plugins: Dict[str, IComposerPlugin] = {}

    def register_plugin(self, plugin: IComposerPlugin) -> None:
        """Registers a plugin instance."""
        if not isinstance(plugin, IComposerPlugin):
            raise TypeError("Must implement IComposerPlugin protocol.")
        self._plugins[plugin.plugin_name] = plugin

    def get_plugin(self, plugin_name: str) -> Optional[IComposerPlugin]:
        """Retrieves registered plugin by name."""
        return self._plugins.get(plugin_name)

    def execute_plugin(self, plugin_name: str, intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executes a target plugin."""
        plugin = self.get_plugin(plugin_name)
        if not plugin:
            return {}
        return plugin.process_data(intent, payload)


# Singleton plugin registry
plugin_registry = PluginRegistry()
# Register default metro plugin
plugin_registry.register_plugin(MetroConnectionPlugin())
