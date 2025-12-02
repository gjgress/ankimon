from aqt import gui_hooks
from .utils import addon_config_editor_will_display_json


# Custom Ankimon hooks for internal communication
class AnkimonHooks:
    """Custom hook system for Ankimon addon internal events."""
    
    _pc_refresh_callbacks: list = []
    
    @classmethod
    def register_pc_refresh(cls, callback: callable) -> None:
        """Register a callback to be called when PC needs refresh.
        
        Args:
            callback: Function to call when refresh_pokemon_pc is triggered.
        """
        if callback not in cls._pc_refresh_callbacks:
            cls._pc_refresh_callbacks.append(callback)
    
    @classmethod
    def unregister_pc_refresh(cls, callback: callable) -> None:
        """Unregister a PC refresh callback.
        
        Args:
            callback: Function to remove from callbacks.
        """
        if callback in cls._pc_refresh_callbacks:
            cls._pc_refresh_callbacks.remove(callback)
    
    @classmethod
    def refresh_pokemon_pc(cls) -> None:
        """Trigger all registered PC refresh callbacks.
        
        Call this from anywhere in the addon to refresh the Pokemon PC.
        """
        for callback in cls._pc_refresh_callbacks:
            try:
                callback()
            except Exception:
                pass  # Silently ignore errors from callbacks


# Convenience function for easy access
def refresh_pokemon_pc() -> None:
    """Refresh the Pokemon PC if it's open.
    
    This can be called from anywhere in the addon to trigger a PC refresh.
    """
    AnkimonHooks.refresh_pokemon_pc()


def setupHooks(check_data, ankimon_tracker_obj):
    """Set up Ankimon hooks - updated to handle None check_data"""

    # Only set up sync hooks if check_data exists and has the required methods
    if check_data is not None:
        if hasattr(check_data, 'modify_json_configuration_on_save'):
            gui_hooks.addon_config_editor_will_save_json.append(check_data.modify_json_configuration_on_save)

        if hasattr(check_data, 'sync_on_anki_close'):
            gui_hooks.sync_did_finish.append(check_data.sync_on_anki_close)

    # Always set up these hooks regardless of check_data
    gui_hooks.addon_config_editor_will_display_json.append(addon_config_editor_will_display_json)
