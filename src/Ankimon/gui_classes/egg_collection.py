"""Egg Collection Dialog.

This module provides a GUI dialog to display the player's current egg
collection styled like a Pokemon PC box. Features:
  - Animated egg icons using sprite sheets (alternating left/right frames)
  - Clickable eggs that show full-size sprite in detail panel
  - Progress bars and card tracking
  - Search, favorites, and sorting functionality
  - Filter by type, rarity, and generation
  - Shiny egg indicators with special glow
  - Pokemon silhouette preview
  - Hatch prediction estimates
  - Release/gift egg options
  - Notification settings for ready eggs

The egg data is read from `eggs.json` and includes progress tracking.
"""

import json
import os
import random
from pathlib import Path

from aqt import mw
from aqt.utils import showInfo, tooltip, askUser
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QPixmap, QFont, QPainter, QColor, QBrush, QPen
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QGridLayout,
    QFrame,
    QProgressBar,
    QSizePolicy,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QMessageBox,
)

from ..resources import (
    eggs_path,
    eggs_sprites_path,
    eggs_main_sprite_path,
    eggs_icon_path,
    mypokemon_path,
)
from ..functions.sprite_functions import get_sprite_path
from ..functions.pokedex_functions import (
    search_pokedex,
    search_pokedex_by_id,
    search_pokeapi_db_by_id,
    get_all_pokemon_moves,
    get_pokemon_egg_moves,
)
from ..functions.pokemon_functions import pick_random_gender


# Pokemon PC Box inspired color palette
PC_COLORS = {
    "bg_dark": "#385868",       # Dark teal background
    "bg_medium": "#487888",     # Medium teal
    "bg_light": "#68a8b8",      # Light teal
    "box_bg": "#c8b870",        # Tan/sandy box background
    "box_border": "#a89850",    # Darker tan border
    "header_bg": "#e8e8d0",     # Cream header
    "header_border": "#88a8a8", # Teal border for header
    "text_dark": "#383838",     # Dark text
    "text_light": "#f8f8f8",    # Light text
    "selected": "#58d898",      # Green selection
    "selected_border": "#40b878", # Darker green for selection border
    "button_bg": "#7888a8",     # Button purple-gray
    "button_text": "#f8f8f8",   # Button text
    "detail_bg": "#68a8c0",     # Detail panel background
}

# Type colors - more muted/retro versions
EGG_TYPE_COLORS = {
    "fire": "#c04000",
    "water": "#3080b0",
    "grass": "#50a050",
    "electric": "#c0a000",
    "normal": "#808060",
    "psychic": "#c05080",
    "rock": "#907020",
    "ground": "#b08030",
    "ice": "#50a0a0",
    "dragon": "#6030a0",
    "dark": "#403020",
    "fairy": "#b06090",
    "poison": "#702080",
    "bug": "#708010",
    "fighting": "#801010",
    "ghost": "#504060",
    "steel": "#707090",
    "flying": "#6070c0",
}

# Egg rarity tiers
EGG_RARITIES = {
    "common": {"color": "#80a080", "label": "Common"},
    "uncommon": {"color": "#6090c0", "label": "Uncommon"},
    "rare": {"color": "#a060c0", "label": "Rare"},
    "legendary": {"color": "#d4af37", "label": "Legendary"},
}

# Pokemon generations by ID range
GENERATIONS = {
    "all": (1, 999),
    "gen1": (1, 151),
    "gen2": (152, 251),
    "gen3": (252, 386),
    "gen4": (387, 493),
    "gen5": (494, 649),
    "gen6": (650, 721),
    "gen7": (722, 809),
    "gen8": (810, 905),
}

# Notification settings key in eggs.json metadata
NOTIFY_ON_HATCH = "notify_on_hatch"


def load_eggs() -> list:
    """Load eggs data from the eggs.json file.

    Returns:
        list: A list of egg dictionaries. Returns empty list if file
              is missing or cannot be parsed.
    """
    try:
        if os.path.exists(eggs_path):
            with open(eggs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        return []
    except Exception:
        return []


def load_pending_reviews() -> int:
    """Load pending reviews count from eggs.json metadata file.
    
    Returns:
        int: Number of pending reviews from other devices.
    """
    try:
        meta_path = eggs_path.parent / "eggs_meta.json"
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("pending_reviews_elsewhere", 0)
        return 0
    except Exception:
        return 0


def save_pending_reviews(count: int) -> bool:
    """Save pending reviews count to eggs.json metadata file.
    
    Args:
        count: Number of pending reviews to save.
        
    Returns:
        bool: True if save succeeded.
    """
    try:
        meta_path = eggs_path.parent / "eggs_meta.json"
        data = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["pending_reviews_elsewhere"] = count
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def get_last_sync_timestamp() -> int:
    """Get the timestamp of the last deck-based sync.
    
    Returns:
        int: Timestamp in milliseconds, or 0 if never synced.
    """
    try:
        meta_path = eggs_path.parent / "eggs_meta.json"
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_deck_sync_timestamp", 0)
        return 0
    except Exception:
        return 0


def save_last_sync_timestamp(timestamp: int) -> bool:
    """Save the timestamp of the last deck-based sync.
    
    Args:
        timestamp: Timestamp in milliseconds.
        
    Returns:
        bool: True if save succeeded.
    """
    try:
        meta_path = eggs_path.parent / "eggs_meta.json"
        data = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["last_deck_sync_timestamp"] = timestamp
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def get_todays_reviews_by_deck() -> dict:
    """Get count of reviews done today for each deck.
    
    Returns:
        dict: Mapping of deck_id to review count for today.
    """
    try:
        if not mw.col:
            return {}
        
        # Get the start of today in Anki's day cutoff terms
        # Anki uses rollover at 4am by default
        from datetime import datetime, timedelta
        
        # Get today's cutoff timestamp
        day_cutoff = mw.col.sched.day_cutoff
        # day_cutoff is the END of today, so start is 24 hours before
        today_start_secs = day_cutoff - (24 * 60 * 60)
        today_start_ms = today_start_secs * 1000
        
        # Get last sync timestamp
        last_sync = get_last_sync_timestamp()
        
        # Use the later of today's start or last sync
        start_from = max(today_start_ms, last_sync)
        
        # Query reviews since start_from, grouped by deck
        # revlog.id is milliseconds timestamp, cid is card id
        # cards.did is deck id
        query = """
            SELECT c.did, COUNT(r.id) 
            FROM revlog r
            JOIN cards c ON r.cid = c.id
            WHERE r.id > ?
            GROUP BY c.did
        """
        
        results = mw.col.db.all(query, start_from)
        
        deck_reviews = {}
        for deck_id, count in results:
            deck_reviews[deck_id] = count
        
        return deck_reviews
        
    except Exception:
        return {}


def save_eggs(eggs: list) -> bool:
    """Save eggs data to the eggs.json file.

    Args:
        eggs: List of egg dictionaries to save.

    Returns:
        bool: True if save succeeded, False otherwise.
    """
    try:
        with open(eggs_path, "w", encoding="utf-8") as f:
            json.dump(eggs, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def get_egg_sprite_path(pokemon_name: str) -> str:
    """Get the path to the full egg sprite based on Pokémon name.

    Tries to find a matching sprite in the MainSprite folder.
    Falls back to a generic egg if not found.

    Args:
        pokemon_name: Name of the Pokémon in the egg.

    Returns:
        str: Path to the egg sprite image.
    """
    # Try lowercase (most common)
    sprite_file = eggs_main_sprite_path / f"{pokemon_name.lower()}.png"
    if sprite_file.exists():
        return str(sprite_file)

    # Try exact match (uppercase)
    sprite_file = eggs_main_sprite_path / f"{pokemon_name.upper()}.png"
    if sprite_file.exists():
        return str(sprite_file)

    # Try capitalized
    sprite_file = eggs_main_sprite_path / f"{pokemon_name.capitalize()}.png"
    if sprite_file.exists():
        return str(sprite_file)

    # Fallback: return first available egg sprite or empty
    try:
        for f in eggs_main_sprite_path.iterdir():
            if f.suffix.lower() == ".png":
                return str(f)
    except Exception:
        pass

    return ""


def get_egg_icon_path(pokemon_name: str) -> str:
    """Get the path to the egg icon sprite sheet.

    Args:
        pokemon_name: Name of the Pokémon in the egg.

    Returns:
        str: Path to the egg icon sprite sheet.
    """
    # Try lowercase with _icon suffix
    icon_file = eggs_icon_path / f"{pokemon_name.lower()}_icon.png"
    if icon_file.exists():
        return str(icon_file)

    # Fallback to any icon
    try:
        for f in eggs_icon_path.iterdir():
            if f.suffix.lower() == ".png":
                return str(f)
    except Exception:
        pass

    return ""


class AnimatedEggLabel(QLabel):
    """A label that displays an animated egg icon from a sprite sheet.
    
    The sprite sheet has two frames side by side. This label alternates
    between them to create a wobble animation. Shiny eggs have a special
    golden glow effect.
    """

    def __init__(self, sprite_path: str, egg_data: dict, parent=None):
        super().__init__(parent)
        self.egg_data = egg_data
        self.sprite_path = sprite_path
        self.current_frame = 0
        self.left_pixmap = None
        self.right_pixmap = None
        self.is_selected = False
        self.is_shaking = False
        self.shake_step = 0
        self.original_pos = None
        self.hover_widget = None
        self.glow_phase = 0  # For animated shiny glow
        
        self.setFixedSize(48, 48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMouseTracking(True)
        
        self._load_sprite_sheet()
        self._update_display()
        self._update_style()

    def _load_sprite_sheet(self):
        """Load and split the sprite sheet into two frames."""
        if not self.sprite_path or not os.path.exists(self.sprite_path):
            return
            
        full_pixmap = QPixmap(self.sprite_path)
        if full_pixmap.isNull():
            return
            
        # Split into left and right halves
        width = full_pixmap.width()
        height = full_pixmap.height()
        half_width = width // 2
        
        self.left_pixmap = full_pixmap.copy(0, 0, half_width, height)
        self.right_pixmap = full_pixmap.copy(half_width, 0, half_width, height)

    def _update_display(self):
        """Update the displayed frame."""
        pixmap = self.left_pixmap if self.current_frame == 0 else self.right_pixmap
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, 
                                   Qt.TransformationMode.FastTransformation)
            self.setPixmap(scaled)
        else:
            self.setText("?")

    def animate(self):
        """Toggle to the next animation frame."""
        self.current_frame = 1 - self.current_frame
        self._update_display()
        
        # Animate shiny glow
        if self.egg_data.get("shiny", False):
            self.glow_phase = (self.glow_phase + 1) % 4
            self._update_style()

    def enterEvent(self, event):
        """Show progress tooltip on hover."""
        self._show_hover_progress()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide progress tooltip when leaving."""
        self._hide_hover_progress()
        super().leaveEvent(event)

    def _show_hover_progress(self):
        """Create and show the hover progress widget (only progress bar)."""
        if self.hover_widget:
            return
            
        cards_done = self.egg_data.get("cards_done", 0)
        cards_required = self.egg_data.get("cards_required", 100)
        progress_pct = min(100, int((cards_done / max(1, cards_required)) * 100))
        
        # Create hover widget - only progress bar
        self.hover_widget = QFrame(self.window())
        self.hover_widget.setStyleSheet(f"""
            QFrame {{
                background-color: #2a2a2a;
                border: 2px solid {PC_COLORS['selected']};
                border-radius: 4px;
            }}
        """)
        
        layout = QVBoxLayout(self.hover_widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(0)
        
        # Progress bar only
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 100)
        progress_bar.setValue(progress_pct)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat(f"{progress_pct}%")
        progress_bar.setFixedHeight(14)
        progress_bar.setFixedWidth(60)
        progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {PC_COLORS['box_border']};
                background-color: #1a1a1a;
                border-radius: 4px;
                color: {PC_COLORS['text_light']};
                font-size: 9px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {PC_COLORS['selected']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(progress_bar)
        
        self.hover_widget.adjustSize()
        
        # Position above the egg icon
        global_pos = self.mapToGlobal(self.rect().center())
        window_pos = self.window().mapFromGlobal(global_pos)
        x = window_pos.x() - self.hover_widget.width() // 2
        y = window_pos.y() - self.hover_widget.height() - 30
        
        # Keep within window bounds
        x = max(5, min(x, self.window().width() - self.hover_widget.width() - 5))
        y = max(5, y)
        
        self.hover_widget.move(x, y)
        self.hover_widget.show()
        self.hover_widget.raise_()

    def _hide_hover_progress(self):
        """Hide and destroy the hover progress widget."""
        if self.hover_widget:
            self.hover_widget.hide()
            self.hover_widget.deleteLater()
            self.hover_widget = None

    def do_shake(self):
        """Perform a shake animation on click."""
        if self.is_shaking:
            return
        self.is_shaking = True
        self.shake_step = 0
        self.original_pos = self.pos()
        self._shake_step()

    def _shake_step(self):
        """Execute one step of the shake animation."""
        if self.shake_step >= 8:
            # Reset to original position
            if self.original_pos:
                self.move(self.original_pos)
            self.is_shaking = False
            return
        
        # Alternating left-right-up-down movement
        offsets = [(-3, 0), (3, 0), (-2, -1), (2, 1), (-2, 0), (2, 0), (-1, 0), (1, 0)]
        offset = offsets[self.shake_step % len(offsets)]
        
        if self.original_pos:
            self.move(self.original_pos.x() + offset[0], self.original_pos.y() + offset[1])
        
        self.shake_step += 1
        QTimer.singleShot(40, self._shake_step)

    def set_selected(self, selected: bool):
        """Set the selection state."""
        self.is_selected = selected
        self._update_style()

    def _update_style(self):
        """Update the visual style based on state."""
        is_favorite = self.egg_data.get("favorite", False)
        is_shiny = self.egg_data.get("shiny", False)
        is_ready = self.egg_data.get("cards_done", 0) >= self.egg_data.get("cards_required", 100)
        
        if self.is_selected:
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: {PC_COLORS['selected']};
                    border: 2px solid {PC_COLORS['selected_border']};
                    border-radius: 4px;
                }}
            """)
        elif is_shiny:
            # Animated golden glow for shiny eggs
            glow_colors = ["#ffd700", "#ffec8b", "#ffd700", "#daa520"]
            glow_color = glow_colors[self.glow_phase % len(glow_colors)]
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(255, 215, 0, 0.3);
                    border: 3px solid {glow_color};
                    border-radius: 6px;
                }}
            """)
        elif is_ready:
            # Pulsing green glow for ready-to-hatch eggs
            self.setStyleSheet(f"""
                QLabel {{
                    background-color: rgba(88, 216, 152, 0.3);
                    border: 2px solid {PC_COLORS['selected']};
                    border-radius: 4px;
                }}
            """)
        else:
            self.setStyleSheet("background: transparent; border: none;")


class HoverRevealLabel(QLabel):
    """A label that shows egg sprite normally, but reveals Pokemon silhouette on hover.
    
    When hovering over the egg sprite in the detail panel, this widget shows
    a darkened silhouette of the actual Pokemon that will hatch.
    """
    
    # Signal emitted when hatching animation completes
    hatching_complete = None  # Will be set as callback

    def __init__(self, parent=None):
        super().__init__(parent)
        self.egg_pixmap = None
        self.silhouette_pixmap = None
        self.pokemon_id = None
        self.setMouseTracking(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("background: transparent;")
        
        # Hatching animation state
        self.is_hatching = False
        self.hatch_step = 0
        self.original_pos = None
        self.hatch_callback = None

    def set_egg_sprite(self, pixmap: QPixmap, pokemon_id: int = None):
        """Set the egg sprite and pokemon ID for silhouette generation."""
        self.egg_pixmap = pixmap
        self.pokemon_id = pokemon_id
        self.silhouette_pixmap = None  # Reset silhouette
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)

    def _load_pokemon_silhouette(self):
        """Load and create silhouette from the actual Pokemon sprite."""
        if self.silhouette_pixmap is not None or self.pokemon_id is None:
            return
        
        # Get the actual Pokemon sprite using sprite_functions
        pokemon_sprite_path = get_sprite_path("front", "png", self.pokemon_id, False, "M")
        if pokemon_sprite_path and os.path.exists(pokemon_sprite_path):
            pokemon_pixmap = QPixmap(pokemon_sprite_path)
            if not pokemon_pixmap.isNull():
                # Create silhouette (dark shadow version)
                self.silhouette_pixmap = self._create_silhouette(pokemon_pixmap)

    def _create_silhouette(self, pixmap: QPixmap) -> QPixmap:
        """Create a darkened silhouette of the sprite."""
        if pixmap.isNull():
            return pixmap
        
        # Create a copy and darken it to make a shadow/silhouette
        result = QPixmap(pixmap.size())
        result.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(result)
        painter.drawPixmap(0, 0, pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(result.rect(), QColor(40, 40, 60, 220))
        painter.end()
        
        # Scale to fit the label
        return result.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)

    def enterEvent(self, event):
        """Show Pokemon silhouette on hover."""
        self._load_pokemon_silhouette()
        if self.silhouette_pixmap and not self.silhouette_pixmap.isNull():
            self.setPixmap(self.silhouette_pixmap)
            self.setToolTip("Pokemon silhouette preview")
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Restore egg sprite when not hovering."""
        if self.egg_pixmap and not self.egg_pixmap.isNull():
            scaled = self.egg_pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            self.setPixmap(scaled)
        super().leaveEvent(event)

    def clear(self):
        """Clear all sprites."""
        self.egg_pixmap = None
        self.silhouette_pixmap = None
        self.pokemon_id = None
        super().clear()
    
    def start_hatch_animation(self, callback=None):
        """Start the hatching wiggle animation.
        
        Args:
            callback: Function to call when animation completes.
        """
        if self.is_hatching:
            return
        
        self.is_hatching = True
        self.hatch_step = 0
        self.original_pos = self.pos()
        self.hatch_callback = callback
        self._hatch_wiggle_step()
    
    def _hatch_wiggle_step(self):
        """Execute one step of the hatching wiggle animation."""
        # Animation lasts about 4 seconds (80 steps at 50ms each)
        total_steps = 80
        
        if self.hatch_step >= total_steps:
            # Animation complete - reset position and show Pokemon
            if self.original_pos:
                self.move(self.original_pos)
            self.is_hatching = False
            
            # Show the Pokemon sprite briefly before callback
            self._load_pokemon_silhouette()
            if self.silhouette_pixmap:
                # Show actual Pokemon (not silhouette) - load full color sprite
                pokemon_sprite_path = get_sprite_path("front", "png", self.pokemon_id, False, "M")
                if pokemon_sprite_path and os.path.exists(pokemon_sprite_path):
                    pokemon_pixmap = QPixmap(pokemon_sprite_path)
                    if not pokemon_pixmap.isNull():
                        scaled = pokemon_pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio,
                                                       Qt.TransformationMode.SmoothTransformation)
                        self.setPixmap(scaled)
            
            # Call completion callback after a brief pause to show Pokemon
            if self.hatch_callback:
                QTimer.singleShot(500, self.hatch_callback)
            return
        
        # Wiggle pattern - gets more intense as it progresses
        progress = self.hatch_step / total_steps
        intensity = 2 + int(progress * 6)  # Starts at 2, goes up to 8
        
        # Alternating pattern with varying intensity
        if self.hatch_step % 4 == 0:
            offset = (-intensity, 0)
        elif self.hatch_step % 4 == 1:
            offset = (intensity, -1)
        elif self.hatch_step % 4 == 2:
            offset = (-intensity, 0)
        else:
            offset = (intensity, 1)
        
        if self.original_pos:
            self.move(self.original_pos.x() + offset[0], self.original_pos.y() + offset[1])
        
        self.hatch_step += 1
        
        # Speed up towards the end
        delay = 50 if progress < 0.7 else 30
        QTimer.singleShot(delay, self._hatch_wiggle_step)


class EggCollectionDialog(QDialog):
    """Dialog displaying the player's egg collection like a Pokemon PC.

    Features:
      - Animated egg icons using sprite sheets
      - Clickable eggs that show full-size sprite in detail panel
      - Progress bars and card tracking
      - Search, favorites, and sorting
      - Filter by type, rarity, generation
      - Shiny egg indicators
      - Pokemon silhouette preview
      - Hatch predictions
      - Release/gift egg options

    Attributes:
        eggs (list): List of egg data dictionaries loaded from eggs.json.
        filtered_eggs (list): Currently displayed eggs after filtering/sorting.
        egg_icons (list): List of AnimatedEggLabel widgets for animation.
        selected_egg (AnimatedEggLabel): Currently selected egg icon.
        detail_panel (QFrame): Right-side panel showing selected egg details.
        animation_timer (QTimer): Timer for sprite sheet animation.
        search_input (QLineEdit): Search box for filtering eggs.
        sort_combo (QComboBox): Dropdown for sorting options.
        show_favorites_only (bool): Whether to show only favorite eggs.
        type_filter (str): Current type filter ("all" or type name).
        rarity_filter (str): Current rarity filter ("all" or rarity name).
        gen_filter (str): Current generation filter ("all" or gen name).
        notify_on_hatch (bool): Whether to show notification when eggs are ready.
    """

    def __init__(self, parent=None):
        """Initialize the Egg Collection dialog."""
        super().__init__(parent or mw)

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("EGG BOX")
        self.setMinimumSize(900, 650)
        self.resize(1000, 700)

        # Track egg icon widgets for animation
        self.egg_icons = []
        self.selected_egg = None
        self.detail_sprite_label = None
        self.detail_name_label = None
        self.detail_progress_bar = None
        self.detail_progress_label = None
        self.detail_type_label = None
        self.detail_fav_btn = None
        self.detail_prediction_label = None
        self.detail_rarity_label = None
        self.detail_deck_combo = None
        self.detail_hatch_btn = None
        
        # Search and filter state
        self.search_text = ""
        self.sort_order = "name_asc"  # name_asc, name_desc, progress_asc, progress_desc
        self.show_favorites_only = False
        self.type_filter = "all"
        self.rarity_filter = "all"
        self.gen_filter = "all"
        self.notify_on_hatch = True  # Default to notifications on
        
        # Grid container reference for rebuilding
        self.grid_container = None
        self.grid_layout = None
        
        # Pending reviews from other devices to apply
        self.pending_reviews_elsewhere = 0
        self.reviews_banner = None

        # Apply Pokemon PC box styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {PC_COLORS['bg_dark']};
            }}
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background-color: {PC_COLORS['bg_medium']};
                width: 12px;
                border: 2px solid {PC_COLORS['bg_light']};
            }}
            QScrollBar::handle:vertical {{
                background-color: {PC_COLORS['header_bg']};
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QLineEdit {{
                background-color: {PC_COLORS['header_bg']};
                border: 2px solid {PC_COLORS['box_border']};
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
                font-size: 11px;
            }}
            QComboBox {{
                background-color: {PC_COLORS['header_bg']};
                border: 2px solid {PC_COLORS['box_border']};
                border-radius: 4px;
                padding: 4px 8px;
                color: {PC_COLORS['text_dark']};
                font-size: 10px;
                min-width: 100px;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {PC_COLORS['header_bg']};
                color: {PC_COLORS['text_dark']};
                selection-background-color: {PC_COLORS['selected']};
            }}
        """)

        # Load egg data
        self.eggs = load_eggs()
        self.filtered_eggs = self.eggs.copy()

        self._setup_ui()
        
        # Setup animation timer for sprite sheets
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate_eggs)
        self.animation_timer.start(500)  # Animate every 500ms
        
        # Sync deck-based reviews to assigned eggs (also shows banner for unassigned)
        self._sync_deck_reviews()
        
        # Check for any previously saved pending reviews
        self._check_saved_pending_reviews()

    def _get_filtered_eggs(self) -> list:
        """Get eggs filtered by search, favorites, type, rarity, generation, then sorted."""
        result = self.eggs.copy()
        
        # Filter by search text
        if self.search_text:
            search_lower = self.search_text.lower()
            result = [e for e in result if search_lower in e.get("pokemon_name", "").lower()]
        
        # Filter by favorites
        if self.show_favorites_only:
            result = [e for e in result if e.get("favorite", False)]
        
        # Filter by type
        if self.type_filter != "all":
            result = [e for e in result if e.get("egg_type", "normal").lower() == self.type_filter.lower()]
        
        # Filter by rarity
        if self.rarity_filter != "all":
            result = [e for e in result if e.get("rarity", "common").lower() == self.rarity_filter.lower()]
        
        # Filter by generation
        if self.gen_filter != "all" and self.gen_filter in GENERATIONS:
            gen_range = GENERATIONS[self.gen_filter]
            result = [e for e in result if gen_range[0] <= e.get("pokemon_id", 0) <= gen_range[1]]
        
        # Sort
        if self.sort_order == "name_asc":
            result.sort(key=lambda e: e.get("pokemon_name", "").lower())
        elif self.sort_order == "name_desc":
            result.sort(key=lambda e: e.get("pokemon_name", "").lower(), reverse=True)
        elif self.sort_order == "progress_asc":
            result.sort(key=lambda e: e.get("cards_done", 0) / max(1, e.get("cards_required", 100)))
        elif self.sort_order == "progress_desc":
            result.sort(key=lambda e: e.get("cards_done", 0) / max(1, e.get("cards_required", 100)), reverse=True)
        
        return result

    def _on_search_changed(self, text: str):
        """Handle search text change."""
        self.search_text = text
        self._rebuild_egg_grid()

    def _on_sort_changed(self, index: int):
        """Handle sort selection change."""
        sort_options = ["name_asc", "name_desc", "progress_asc", "progress_desc"]
        self.sort_order = sort_options[index] if index < len(sort_options) else "name_asc"
        self._rebuild_egg_grid()

    def _on_favorites_toggle(self):
        """Toggle favorites only filter."""
        self.show_favorites_only = not self.show_favorites_only
        self.fav_filter_btn.setText("★ FAV" if self.show_favorites_only else "☆ FAV")
        self.fav_filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {"#f0c040" if self.show_favorites_only else PC_COLORS['button_bg']};
                color: {PC_COLORS['text_dark'] if self.show_favorites_only else PC_COLORS['button_text']};
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {"#e0b030" if self.show_favorites_only else PC_COLORS['bg_light']};
            }}
        """)
        self._rebuild_egg_grid()

    def _on_type_filter_changed(self, index: int):
        """Handle type filter change."""
        types = ["all", "fire", "water", "grass", "electric", "normal", "psychic", 
                 "rock", "ground", "ice", "dragon", "dark", "fairy", "poison", 
                 "bug", "fighting", "ghost", "steel", "flying"]
        self.type_filter = types[index] if index < len(types) else "all"
        self._rebuild_egg_grid()

    def _on_rarity_filter_changed(self, index: int):
        """Handle rarity filter change."""
        rarities = ["all", "common", "uncommon", "rare", "legendary"]
        self.rarity_filter = rarities[index] if index < len(rarities) else "all"
        self._rebuild_egg_grid()

    def _on_gen_filter_changed(self, index: int):
        """Handle generation filter change."""
        gens = ["all", "gen1", "gen2", "gen3", "gen4", "gen5", "gen6", "gen7", "gen8"]
        self.gen_filter = gens[index] if index < len(gens) else "all"
        self._rebuild_egg_grid()

    def _on_notify_toggle(self, state: int):
        """Toggle hatch notification setting."""
        self.notify_on_hatch = state == Qt.CheckState.Checked.value
        tooltip("Hatch notifications " + ("enabled" if self.notify_on_hatch else "disabled"))

    def _release_egg(self):
        """Release/abandon the currently selected egg."""
        if not self.selected_egg:
            tooltip("Select an egg first!")
            return
        
        egg_data = self.selected_egg.egg_data
        pokemon_name = egg_data.get("pokemon_name", "this egg")
        
        if not askUser(f"Are you sure you want to release {pokemon_name}'s egg?\n\nThis cannot be undone!"):
            return
        
        # Remove from eggs list
        egg_id = egg_data.get("id")
        self.eggs = [e for e in self.eggs if e.get("id") != egg_id]
        
        # Save
        save_eggs(self.eggs)
        
        # Rebuild UI
        self.selected_egg = None
        self._rebuild_egg_grid()
        self._clear_detail_panel()
        
        tooltip(f"Released {pokemon_name}'s egg")

    def _gift_egg(self):
        """Gift the currently selected egg (placeholder for future feature)."""
        if not self.selected_egg:
            tooltip("Select an egg first!")
            return
        
        pokemon_name = self.selected_egg.egg_data.get("pokemon_name", "this egg")
        showInfo(f"Egg gifting coming soon!\n\nYou would be gifting {pokemon_name}'s egg to a friend.")

    def _hatch_egg(self):
        """Hatch the currently selected egg and add the Pokemon to the collection."""
        if not self.selected_egg:
            tooltip("Select an egg first!")
            return
        
        egg_data = self.selected_egg.egg_data
        cards_done = egg_data.get("cards_done", 0)
        cards_required = egg_data.get("cards_required", 100)
        
        if cards_done < cards_required:
            tooltip("This egg isn't ready to hatch yet!")
            return
        
        pokemon_name = egg_data.get("pokemon_name", "Unknown")
        pokemon_id = egg_data.get("pokemon_id", 1)
        is_shiny = egg_data.get("shiny", False)
        egg_type = egg_data.get("egg_type", "normal")
        
        # Confirm hatching
        shiny_text = " SHINY" if is_shiny else ""
        if not askUser(f"Hatch this egg?\n\nA{shiny_text} {pokemon_name} will join your team!"):
            return
        
        # Disable the hatch button during animation
        if self.detail_hatch_btn:
            self.detail_hatch_btn.setEnabled(False)
            self.detail_hatch_btn.setText("Hatching...")
        
        # Start the hatching animation
        self.detail_sprite_label.start_hatch_animation(
            callback=lambda: self._complete_hatch(egg_data, pokemon_name, pokemon_id, is_shiny, egg_type)
        )
    
    def _complete_hatch(self, egg_data, pokemon_name, pokemon_id, is_shiny, egg_type):
        """Complete the hatching process after animation.
        
        Looks up actual Pokemon data from the pokedex instead of relying on
        stored egg data, similar to how generate_random_pokemon works.
        """
        try:
            import uuid
            from datetime import datetime
            
            # Look up the Pokemon name from ID to ensure accuracy
            name = search_pokedex_by_id(pokemon_id)
            if not name:
                name = pokemon_name
            
            # Look up actual Pokemon data from pokedex
            pokemon_type = search_pokedex(name, "types")
            if not pokemon_type:
                pokemon_type = egg_data.get("types", [egg_type])
            
            base_stats = search_pokedex(name, "baseStats")
            if not base_stats:
                base_stats = egg_data.get("stats", {"hp": 45, "atk": 49, "def": 49, "spa": 65, "spd": 65, "spe": 45})
            
            base_experience = search_pokeapi_db_by_id(pokemon_id, "base_experience")
            if not base_experience:
                base_experience = egg_data.get("base_experience", 64)
            
            growth_rate = search_pokeapi_db_by_id(pokemon_id, "growth_rate")
            if not growth_rate:
                growth_rate = egg_data.get("growth_rate", "medium")
            
            # Get gender using the proper function
            gender = pick_random_gender(name)
            if not gender:
                gender = egg_data.get("gender", "Pokemon")
            
            # Get ability from pokedex
            ability = "Unknown"
            possible_abilities = search_pokedex(name, "abilities")
            if possible_abilities:
                numeric_abilities = {k: v for k, v in possible_abilities.items() if k.isdigit()}
                if numeric_abilities:
                    import random
                    ability = random.choice(list(numeric_abilities.values()))
            
            # Get moves the Pokemon can learn at level 1
            hatched_level = 1
            all_possible_moves = get_all_pokemon_moves(name, hatched_level)
            
            # Get egg moves for this Pokemon - hatched Pokemon can have egg moves!
            egg_moves_available = get_pokemon_egg_moves(name)
            
            # Determine final moveset: Start with level-up moves, then potentially add an egg move
            import random
            attacks = []
            
            # Add level-up moves first (up to 3 if we want to leave room for an egg move)
            if all_possible_moves:
                if egg_moves_available and len(all_possible_moves) > 0:
                    # Reserve 1 slot for a random egg move
                    num_level_moves = min(3, len(all_possible_moves))
                    if len(all_possible_moves) <= num_level_moves:
                        attacks = list(all_possible_moves)
                    else:
                        attacks = random.sample(all_possible_moves, num_level_moves)
                else:
                    # No egg moves available, use all level-up moves
                    if len(all_possible_moves) <= 4:
                        attacks = list(all_possible_moves)
                    else:
                        attacks = random.sample(all_possible_moves, 4)
            
            # Add a random egg move if available (50% chance, or guaranteed if no other moves)
            inherited_egg_move = None
            if egg_moves_available:
                if not attacks or random.random() < 0.5:  # 50% chance to get an egg move
                    inherited_egg_move = random.choice(egg_moves_available)
                    # Make sure we don't duplicate moves
                    if inherited_egg_move not in attacks:
                        if len(attacks) >= 4:
                            # Replace the last move with the egg move
                            attacks[-1] = inherited_egg_move
                        else:
                            attacks.append(inherited_egg_move)
            
            if not attacks:
                attacks = egg_data.get("attacks", ["Tackle"])
            
            # Generate random IVs for the hatched Pokemon
            stat_names = ["hp", "atk", "def", "spa", "spd", "spe"]
            iv = {stat: random.randint(0, 31) for stat in stat_names}
            
            # Create the hatched Pokemon data with proper looked-up values
            hatched_pokemon = {
                "name": name.capitalize() if name else pokemon_name.capitalize(),
                "nickname": "",
                "level": hatched_level,
                "gender": gender,
                "id": pokemon_id,
                "ability": ability,
                "type": pokemon_type,
                "stats": base_stats,
                "ev": {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
                "iv": iv,
                "attacks": attacks,
                "base_experience": base_experience,
                "current_hp": 50,  # Will be recalculated when used
                "growth_rate": growth_rate,
                "friendship": 120,  # Hatched Pokemon have higher friendship
                "pokemon_defeated": 0,
                "xp": 0,
                "everstone": False,
                "shiny": is_shiny,
                "captured_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "individual_id": str(uuid.uuid4()),
                "mega": False,
                "special_form": None,
                "tier": egg_data.get("tier", "Normal"),
                "is_favorite": False,
                "held_item": None,
                "hatched_from_egg": True
            }
            
            # Load existing Pokemon
            pokemon_list = []
            if mypokemon_path.is_file():
                with open(mypokemon_path, "r", encoding="utf-8") as f:
                    pokemon_list = json.load(f)
            
            # Add hatched Pokemon
            pokemon_list.append(hatched_pokemon)
            
            # Save
            with open(mypokemon_path, "w", encoding="utf-8") as f:
                json.dump(pokemon_list, f, indent=2, ensure_ascii=False)
            
            # Remove egg from eggs list
            egg_id = egg_data.get("id")
            self.eggs = [e for e in self.eggs if e.get("id") != egg_id]
            save_eggs(self.eggs)
            
            # Show success message
            shiny_msg = "\n\nIt's SHINY!" if is_shiny else ""
            egg_move_msg = f"\n\nIt inherited the egg move: {inherited_egg_move.replace('_', ' ').title()}!" if inherited_egg_move else ""
            display_name = name.capitalize() if name else pokemon_name
            showInfo(f"Congratulations!\n\nYour egg hatched into {display_name}!{shiny_msg}{egg_move_msg}\n\nIt has been added to your Pokemon collection.", title="Egg Hatched!")
            
            # Clear selection and rebuild UI
            self.selected_egg = None
            self._rebuild_egg_grid()
            self._clear_detail_panel()
            
        except Exception as e:
            showInfo(f"Error hatching egg: {str(e)}")

    def _clear_detail_panel(self):
        """Clear the detail panel to default state."""
        self.detail_sprite_label.clear()
        self.detail_sprite_label.setText("Select\nan egg")
        self.detail_name_label.setText("---")
        self.detail_type_label.setText("Type: ---")
        self.detail_rarity_label.setText("Rarity: ---")
        self.detail_progress_bar.setValue(0)
        self.detail_progress_label.setText("0 / 0")
        self.detail_prediction_label.setText("~??? cards to hatch")

    def _sync_deck_reviews(self):
        """Sync today's reviews from assigned decks to their eggs.
        
        Also tracks unassigned reviews to show in the banner.
        """
        try:
            # Get today's reviews grouped by deck
            deck_reviews = get_todays_reviews_by_deck()
            if not deck_reviews:
                return
            
            # Get all deck IDs that are assigned to eggs
            assigned_deck_ids = set()
            for egg in self.eggs:
                deck_id = egg.get("assigned_deck_id")
                if deck_id is not None:
                    assigned_deck_ids.add(deck_id)
            
            eggs_updated = 0
            total_reviews_applied = 0
            eggs_hatched = 0
            egg_details = []  # Track which eggs got reviews
            
            # Find eggs with assigned decks and apply reviews
            for egg in self.eggs:
                deck_id = egg.get("assigned_deck_id")
                if deck_id is None:
                    continue
                
                # Check if this deck has reviews
                reviews_for_deck = deck_reviews.get(deck_id, 0)
                if reviews_for_deck <= 0:
                    continue
                
                # Apply reviews to this egg
                old_cards = egg.get("cards_done", 0)
                cards_required = egg.get("cards_required", 100)
                egg["cards_done"] = old_cards + reviews_for_deck
                eggs_updated += 1
                total_reviews_applied += reviews_for_deck
                
                # Track details
                pokemon_name = egg.get("pokemon_name", "Unknown")
                is_hatched = egg["cards_done"] >= cards_required
                if is_hatched:
                    eggs_hatched += 1
                egg_details.append((pokemon_name, reviews_for_deck, is_hatched))
            
            # Calculate unassigned reviews (decks without eggs)
            unassigned_reviews = 0
            for deck_id, count in deck_reviews.items():
                if deck_id not in assigned_deck_ids:
                    unassigned_reviews += count
            
            # Save if any eggs were updated
            if eggs_updated > 0:
                save_eggs(self.eggs)
                
                # Update the timestamp so we don't double-count
                import time
                save_last_sync_timestamp(int(time.time() * 1000))
                
                # Show dialog notification for assigned reviews
                self._show_reviews_applied_dialog(total_reviews_applied, egg_details, eggs_hatched)
                
                # Rebuild grid to show updated progress
                self._rebuild_egg_grid()
            elif unassigned_reviews > 0:
                # Only update timestamp if we're tracking unassigned reviews
                import time
                save_last_sync_timestamp(int(time.time() * 1000))
            
            # Store unassigned reviews for the banner
            if unassigned_reviews > 0 and len(self.eggs) > 0:
                self.pending_reviews_elsewhere = unassigned_reviews
                self._show_reviews_banner()
                
        except Exception as e:
            pass  # Silently fail to not disrupt the user experience
    
    def _show_reviews_applied_dialog(self, total_reviews: int, egg_details: list, eggs_hatched: int):
        """Show a dialog notifying the user that reviews were applied to eggs."""
        try:
            # Build message
            if len(egg_details) == 1:
                name, count, hatched = egg_details[0]
                if hatched:
                    message = f"{count} reviews applied to an egg!\n\nThe egg is ready to hatch!"
                else:
                    message = f"{count} reviews applied to an egg!"
            else:
                if eggs_hatched > 0:
                    message = f"{total_reviews} reviews applied to {len(egg_details)} eggs!\n\n{eggs_hatched} egg(s) ready to hatch!"
                else:
                    message = f"{total_reviews} reviews applied to {len(egg_details)} eggs!"
            
            showInfo(message, title="Egg Progress Updated")
            
        except Exception:
            pass

    def _check_saved_pending_reviews(self):
        """Check for previously saved pending reviews and show banner if any."""
        try:
            # Check for previously saved pending reviews
            saved_pending = load_pending_reviews()
            if saved_pending > 0 and len(self.eggs) > 0:
                # Add to any existing pending reviews
                self.pending_reviews_elsewhere += saved_pending
                # Clear saved pending since we're showing them now
                save_pending_reviews(0)
                
                # Show or update banner if not already visible
                if not self.reviews_banner:
                    self._show_reviews_banner()
            
        except Exception as e:
            # Silently fail if there are issues
            pass
    
    def _show_reviews_banner(self):
        """Show a banner indicating there are reviews to apply."""
        if self.reviews_banner:
            self.reviews_banner.deleteLater()
        
        self.reviews_banner = QFrame()
        self.reviews_banner.setStyleSheet("""
            QFrame {
                background-color: #2d5a27;
                border: 3px solid #4a8f3f;
                border-radius: 8px;
            }
        """)
        
        banner_layout = QHBoxLayout(self.reviews_banner)
        banner_layout.setContentsMargins(16, 10, 16, 10)
        banner_layout.setSpacing(12)
        
        # Icon/emoji
        icon_label = QLabel("📚")
        icon_label.setStyleSheet("font-size: 20px; background: transparent;")
        banner_layout.addWidget(icon_label)
        
        # Text content
        title_label = QLabel(f"<b>{self.pending_reviews_elsewhere} Unassigned Reviews!</b> Click any egg to apply them.")
        title_label.setStyleSheet("color: #90EE90; font-size: 12px; background: transparent;")
        banner_layout.addWidget(title_label)
        
        banner_layout.addStretch()
        
        # Buttons - horizontal now
        dismiss_btn = QPushButton("Save for Later")
        dismiss_btn.setFixedHeight(26)
        dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: #3d7a37;
                color: white;
                border: 2px solid #5a9f4f;
                border-radius: 4px;
                padding: 4px 10px;
                font-weight: bold;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4a8f3f;
            }
        """)
        dismiss_btn.clicked.connect(self._save_reviews_for_later)
        banner_layout.addWidget(dismiss_btn)
        
        discard_btn = QPushButton("✕")
        discard_btn.setFixedSize(26, 26)
        discard_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #a0c0a0;
                border: 1px solid #5a7f5a;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(255,255,255,0.1);
                color: white;
            }
        """)
        discard_btn.clicked.connect(self._dismiss_reviews_banner)
        banner_layout.addWidget(discard_btn)
        
        self.reviews_banner.setFixedHeight(50)
        
        # Insert into layout at position 0 (top)
        self.layout().insertWidget(0, self.reviews_banner)
    
    def _save_reviews_for_later(self):
        """Save the pending reviews for later and hide banner."""
        if self.pending_reviews_elsewhere > 0:
            save_pending_reviews(self.pending_reviews_elsewhere)
            tooltip(f"Saved {self.pending_reviews_elsewhere} reviews for later!")
        self.pending_reviews_elsewhere = 0
        if self.reviews_banner:
            # Remove from layout first
            self.layout().removeWidget(self.reviews_banner)
            self.reviews_banner.hide()
            self.reviews_banner.deleteLater()
            self.reviews_banner = None
    
    def _dismiss_reviews_banner(self):
        """Dismiss the reviews banner without saving."""
        self.pending_reviews_elsewhere = 0
        if self.reviews_banner:
            # Remove from layout first
            self.layout().removeWidget(self.reviews_banner)
            self.reviews_banner.hide()
            self.reviews_banner.deleteLater()
            self.reviews_banner = None

    def _toggle_favorite(self):
        """Toggle favorite status of selected egg."""
        if not self.selected_egg:
            return
        
        egg_data = self.selected_egg.egg_data
        egg_data["favorite"] = not egg_data.get("favorite", False)
        
        # Update in main eggs list
        for egg in self.eggs:
            if egg.get("id") == egg_data.get("id"):
                egg["favorite"] = egg_data["favorite"]
                break
        
        # Save to file
        save_eggs(self.eggs)
        
        # Update UI
        self._update_fav_button()
        self.selected_egg._update_style()
        tooltip("Added to favorites!" if egg_data["favorite"] else "Removed from favorites")

    def _update_fav_button(self):
        """Update the favorite button state."""
        if self.selected_egg and self.detail_fav_btn:
            is_fav = self.selected_egg.egg_data.get("favorite", False)
            self.detail_fav_btn.setText("★ FAVORITE" if is_fav else "☆ FAVORITE")
            self.detail_fav_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {"#f0c040" if is_fav else PC_COLORS['header_bg']};
                    color: {PC_COLORS['text_dark']};
                    border: none;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 9px;
                }}
                QPushButton:hover {{
                    background-color: {"#e0b030" if is_fav else "#d8d8c0"};
                }}
            """)

    def _animate_eggs(self):
        """Animate all egg icons by toggling their sprite frame."""
        for egg_icon in self.egg_icons:
            egg_icon.animate()

    def _on_egg_clicked(self, egg_icon: AnimatedEggLabel):
        """Handle egg icon click - show in detail panel and shake."""
        # Check if we have pending reviews to apply
        if self.pending_reviews_elsewhere > 0:
            self._apply_pending_reviews_to_egg(egg_icon)
            return
        
        # Deselect previous
        if self.selected_egg:
            self.selected_egg.set_selected(False)
        
        # Select new
        self.selected_egg = egg_icon
        egg_icon.set_selected(True)
        
        # Shake animation
        egg_icon.do_shake()
        
        # Update detail panel
        self._update_detail_panel(egg_icon.egg_data)
    
    def _apply_pending_reviews_to_egg(self, egg_icon: AnimatedEggLabel):
        """Apply pending reviews from another device to the clicked egg."""
        egg_data = egg_icon.egg_data
        cards_to_apply = self.pending_reviews_elsewhere
        
        # Update egg progress
        old_cards = egg_data.get("cards_done", 0)
        egg_data["cards_done"] = old_cards + cards_to_apply
        
        # Update in main eggs list
        for egg in self.eggs:
            if egg.get("id") == egg_data.get("id"):
                egg["cards_done"] = egg_data["cards_done"]
                break
        
        # Save
        save_eggs(self.eggs)
        
        # Check if hatched
        if egg_data["cards_done"] >= egg_data.get("cards_required", 100):
            tooltip(f"Added {cards_to_apply} reviews! Egg is ready to hatch!")
        else:
            remaining = egg_data.get("cards_required", 100) - egg_data["cards_done"]
            tooltip(f"Added {cards_to_apply} reviews! ~{remaining} cards remaining")
        
        # Clear pending reviews and hide banner
        self._dismiss_reviews_banner()
        
        # Shake the egg
        egg_icon.do_shake()
        
        # Select this egg and update UI
        if self.selected_egg:
            self.selected_egg.set_selected(False)
        self.selected_egg = egg_icon
        egg_icon.set_selected(True)
        
        # Rebuild grid to update progress display
        self._rebuild_egg_grid()
        self._update_detail_panel(egg_data)

    def _update_detail_panel(self, egg: dict):
        """Update the detail panel with egg information."""
        if not egg:
            return
            
        # Update sprite with hover reveal functionality
        pokemon_name = egg.get("pokemon_name", "???")
        pokemon_id = egg.get("pokemon_id", None)
        sprite_path = get_egg_sprite_path(pokemon_name)
        
        if sprite_path and os.path.exists(sprite_path):
            pixmap = QPixmap(sprite_path)
            # Use set_egg_sprite which enables hover silhouette reveal
            self.detail_sprite_label.set_egg_sprite(pixmap, pokemon_id)
        else:
            self.detail_sprite_label.clear()
            self.detail_sprite_label.setText("?")
        
        # Update name (show "???" until 90% progress)
        cards_done = egg.get("cards_done", 0)
        cards_required = egg.get("cards_required", 100)
        progress_pct = min(100, int((cards_done / max(1, cards_required)) * 100))
        
        if progress_pct < 90:
            # Hide name completely with question marks
            self.detail_name_label.setText("???")
        else:
            self.detail_name_label.setText(pokemon_name.upper())
        
        # Update progress
        self.detail_progress_bar.setValue(progress_pct)
        self.detail_progress_label.setText(f"{cards_done} / {cards_required}")
        
        # Hatch prediction
        cards_remaining = max(0, cards_required - cards_done)
        self.detail_prediction_label.setText(f"~{cards_remaining} cards to hatch")
        
        # Update type
        egg_type = egg.get("egg_type", "normal")
        type_color = EGG_TYPE_COLORS.get(egg_type.lower(), "#808080")
        self.detail_type_label.setText(f"Type: {egg_type.capitalize()}")
        self.detail_type_label.setStyleSheet(f"color: {type_color}; font-weight: bold; background-color: white; border-radius: 4px; padding: 2px 6px;")
        
        # Update rarity
        rarity = egg.get("rarity", "common")
        rarity_info = EGG_RARITIES.get(rarity.lower(), EGG_RARITIES["common"])
        self.detail_rarity_label.setText(f"Rarity: {rarity_info['label']}")
        self.detail_rarity_label.setStyleSheet(f"color: {rarity_info['color']}; font-weight: bold; background-color: white; border-radius: 4px; padding: 2px 6px;")
        
        # Shiny indicator
        if egg.get("shiny", False):
            self.detail_name_label.setText("[SHINY] " + self.detail_name_label.text())
        
        # Show/hide hatch button based on progress
        is_ready_to_hatch = cards_done >= cards_required
        if self.detail_hatch_btn:
            if is_ready_to_hatch:
                self.detail_hatch_btn.show()
                self.detail_prediction_label.setText("Ready to hatch!")
                self.detail_prediction_label.setStyleSheet("color: #d4af37; background: transparent; font-weight: bold;")
            else:
                self.detail_hatch_btn.hide()
                self.detail_prediction_label.setStyleSheet(f"color: #606060; background: transparent; font-style: italic;")
        
        # Update favorite button
        self._update_fav_button()
        
        # Update deck combo selection
        self._update_deck_combo(egg)

    def _populate_deck_combo(self):
        """Populate the deck combo box with all available Anki decks."""
        self.detail_deck_combo.blockSignals(True)
        self.detail_deck_combo.clear()
        self.detail_deck_combo.addItem("No Deck", None)
        
        if mw and mw.col:
            try:
                # Get all deck names sorted alphabetically
                decks = mw.col.decks.all_names_and_ids()
                for deck in sorted(decks, key=lambda d: d.name.lower()):
                    self.detail_deck_combo.addItem(deck.name, deck.id)
            except Exception:
                pass
        
        self.detail_deck_combo.blockSignals(False)

    def _update_deck_combo(self, egg: dict):
        """Update the deck combo box to show the egg's assigned deck."""
        if not self.detail_deck_combo:
            return
            
        self.detail_deck_combo.blockSignals(True)
        
        assigned_deck_id = egg.get("assigned_deck_id", None)
        if assigned_deck_id is None:
            self.detail_deck_combo.setCurrentIndex(0)  # "No Deck"
        else:
            # Find the deck in the combo box
            for i in range(self.detail_deck_combo.count()):
                if self.detail_deck_combo.itemData(i) == assigned_deck_id:
                    self.detail_deck_combo.setCurrentIndex(i)
                    break
            else:
                # Deck not found (maybe deleted), reset to No Deck
                self.detail_deck_combo.setCurrentIndex(0)
        
        self.detail_deck_combo.blockSignals(False)

    def _on_deck_changed(self, index: int):
        """Handle deck selection change for the current egg."""
        if not self.selected_egg:
            return
        
        deck_id = self.detail_deck_combo.itemData(index)
        deck_name = self.detail_deck_combo.currentText() if deck_id else None
        
        # Update egg data
        egg_data = self.selected_egg.egg_data
        egg_data["assigned_deck_id"] = deck_id
        egg_data["assigned_deck_name"] = deck_name
        
        # Save to eggs.json
        if save_eggs(self.eggs):
            if deck_name and deck_name != "No Deck":
                tooltip(f"Egg assigned to deck: {deck_name}")
            else:
                tooltip("Egg deck assignment removed")
        else:
            tooltip("Failed to save deck assignment")

    def _setup_ui(self):
        """Build the dialog UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # Pokemon PC style header
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['header_bg']};
                border: none;
                border-radius: 4px;
            }}
        """)
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 6, 16, 6)

        left_btn = QLabel("◀")
        left_btn.setStyleSheet(f"color: {PC_COLORS['bg_dark']}; font-size: 16px; background: transparent;")
        header_layout.addWidget(left_btn)
        header_layout.addStretch()

        header = QLabel("EGG BOX")
        header_font = QFont("Arial", 13)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background: transparent;")
        header_layout.addWidget(header)

        header_layout.addStretch()
        right_btn = QLabel("▶")
        right_btn.setStyleSheet(f"color: {PC_COLORS['bg_dark']}; font-size: 16px; background: transparent;")
        header_layout.addWidget(right_btn)

        main_layout.addWidget(header_frame)

        # Search and filter bar
        filter_frame = QFrame()
        filter_frame.setStyleSheet(f"background-color: {PC_COLORS['bg_medium']}; border: none; border-radius: 4px;")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(8, 6, 8, 6)
        filter_layout.setSpacing(6)

        # Search input
        search_label = QLabel("Search:")
        search_label.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent; font-size: 10px;")
        filter_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search eggs...")
        self.search_input.setFixedWidth(120)
        self.search_input.textChanged.connect(self._on_search_changed)
        filter_layout.addWidget(self.search_input)

        filter_layout.addSpacing(6)

        # Sort dropdown
        sort_label = QLabel("Sort:")
        sort_label.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent; font-size: 10px;")
        filter_layout.addWidget(sort_label)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name A-Z", "Name Z-A", "Progress ↑", "Progress ↓"])
        self.sort_combo.setFixedWidth(90)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        filter_layout.addWidget(self.sort_combo)

        filter_layout.addSpacing(6)

        # Type filter dropdown
        type_label = QLabel("Type:")
        type_label.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent; font-size: 10px;")
        filter_layout.addWidget(type_label)

        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Fire", "Water", "Grass", "Electric", "Normal", 
                                   "Psychic", "Rock", "Ground", "Ice", "Dragon", "Dark",
                                   "Fairy", "Poison", "Bug", "Fighting", "Ghost", "Steel", "Flying"])
        self.type_combo.setFixedWidth(80)
        self.type_combo.currentIndexChanged.connect(self._on_type_filter_changed)
        filter_layout.addWidget(self.type_combo)

        # Rarity filter dropdown
        rarity_label = QLabel("Rarity:")
        rarity_label.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent; font-size: 10px;")
        filter_layout.addWidget(rarity_label)

        self.rarity_combo = QComboBox()
        self.rarity_combo.addItems(["All", "Common", "Uncommon", "Rare", "Legendary"])
        self.rarity_combo.setFixedWidth(85)
        self.rarity_combo.currentIndexChanged.connect(self._on_rarity_filter_changed)
        filter_layout.addWidget(self.rarity_combo)

        # Generation filter dropdown
        gen_label = QLabel("Gen:")
        gen_label.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent; font-size: 10px;")
        filter_layout.addWidget(gen_label)

        self.gen_combo = QComboBox()
        self.gen_combo.addItems(["All", "Gen 1", "Gen 2", "Gen 3", "Gen 4", "Gen 5", "Gen 6", "Gen 7", "Gen 8"])
        self.gen_combo.setFixedWidth(65)
        self.gen_combo.currentIndexChanged.connect(self._on_gen_filter_changed)
        filter_layout.addWidget(self.gen_combo)

        filter_layout.addSpacing(6)

        # Favorites filter button
        self.fav_filter_btn = QPushButton("☆ FAV")
        self.fav_filter_btn.setFixedSize(55, 24)
        self.fav_filter_btn.clicked.connect(self._on_favorites_toggle)
        self.fav_filter_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PC_COLORS['button_bg']};
                color: {PC_COLORS['button_text']};
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {PC_COLORS['bg_light']};
            }}
        """)
        filter_layout.addWidget(self.fav_filter_btn)

        # Notification toggle
        self.notify_checkbox = QCheckBox("Notify")
        self.notify_checkbox.setChecked(self.notify_on_hatch)
        self.notify_checkbox.setToolTip("Notify when eggs are ready to hatch")
        self.notify_checkbox.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent;")
        self.notify_checkbox.stateChanged.connect(self._on_notify_toggle)
        filter_layout.addWidget(self.notify_checkbox)

        filter_layout.addStretch()

        main_layout.addWidget(filter_frame)

        # Content area: egg grid on left, detail panel on right
        content_layout = QHBoxLayout()
        content_layout.setSpacing(8)

        # Left side: Egg grid box
        grid_frame = QFrame()
        grid_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['box_bg']};
                border: none;
                border-radius: 6px;
            }}
        """)
        grid_frame_layout = QVBoxLayout(grid_frame)
        grid_frame_layout.setContentsMargins(6, 6, 6, 6)

        # Scroll area for eggs
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("background: transparent;")

        # Container for egg icon grid - 6 columns like Pokemon PC
        self.grid_container = QWidget()
        self.grid_container.setStyleSheet("background: transparent;")
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self.grid_layout.setSpacing(4)

        self._populate_egg_grid()

        self.scroll_area.setWidget(self.grid_container)
        grid_frame_layout.addWidget(self.scroll_area)

        content_layout.addWidget(grid_frame, 2)

        # Right side: Detail panel
        self.detail_panel = QFrame()
        self.detail_panel.setFixedWidth(240)
        self.detail_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['detail_bg']};
                border: none;
                border-radius: 6px;
            }}
        """)
        detail_layout = QVBoxLayout(self.detail_panel)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(6)

        # Detail sprite container with silhouette preview
        sprite_frame = QFrame()
        sprite_frame.setFixedSize(150, 150)
        sprite_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['header_bg']};
                border: 3px solid {PC_COLORS['box_border']};
                border-radius: 8px;
            }}
        """)
        sprite_layout = QVBoxLayout(sprite_frame)
        sprite_layout.setContentsMargins(10, 10, 10, 10)

        # Use HoverRevealLabel for egg sprite - shows silhouette on hover
        self.detail_sprite_label = HoverRevealLabel()
        self.detail_sprite_label.setFixedSize(130, 130)
        self.detail_sprite_label.setText("Select\nan egg")
        self.detail_sprite_label.setFont(QFont("Arial", 10))
        sprite_layout.addWidget(self.detail_sprite_label)

        # Center sprite frame
        sprite_h = QHBoxLayout()
        sprite_h.addStretch()
        sprite_h.addWidget(sprite_frame)
        sprite_h.addStretch()
        detail_layout.addLayout(sprite_h)

        # Pokemon name
        self.detail_name_label = QLabel("---")
        name_font = QFont("Arial", 13)
        name_font.setBold(True)
        self.detail_name_label.setFont(name_font)
        self.detail_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_name_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background: transparent;")
        detail_layout.addWidget(self.detail_name_label)

        # Type and Rarity in a row
        type_rarity_layout = QHBoxLayout()
        
        self.detail_type_label = QLabel("Type: ---")
        self.detail_type_label.setFont(QFont("Arial", 9))
        self.detail_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_type_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background-color: white; border-radius: 4px; padding: 2px 6px;")
        type_rarity_layout.addWidget(self.detail_type_label)
        
        self.detail_rarity_label = QLabel("Rarity: ---")
        self.detail_rarity_label.setFont(QFont("Arial", 9))
        self.detail_rarity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_rarity_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background-color: white; border-radius: 4px; padding: 2px 6px;")
        type_rarity_layout.addWidget(self.detail_rarity_label)
        
        detail_layout.addLayout(type_rarity_layout)

        # Favorite button
        self.detail_fav_btn = QPushButton("☆ FAVORITE")
        self.detail_fav_btn.setFixedHeight(24)
        self.detail_fav_btn.clicked.connect(self._toggle_favorite)
        self.detail_fav_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PC_COLORS['header_bg']};
                color: {PC_COLORS['text_dark']};
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: #d8d8c0;
            }}
        """)
        detail_layout.addWidget(self.detail_fav_btn)

        # Deck assignment section
        deck_frame = QFrame()
        deck_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['header_bg']};
                border: 2px solid {PC_COLORS['box_border']};
                border-radius: 4px;
            }}
        """)
        deck_layout = QVBoxLayout(deck_frame)
        deck_layout.setContentsMargins(8, 6, 8, 6)
        deck_layout.setSpacing(4)

        deck_label = QLabel("ASSIGN TO DECK")
        deck_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        deck_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        deck_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background: transparent;")
        deck_layout.addWidget(deck_label)

        self.detail_deck_combo = QComboBox()
        self.detail_deck_combo.setFixedHeight(24)
        self.detail_deck_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: white;
                color: {PC_COLORS['text_dark']};
                border: 1px solid {PC_COLORS['box_border']};
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 9px;
            }}
            QComboBox::drop-down {{
                border: none;
            }}
            QComboBox::down-arrow {{
                width: 8px;
                height: 8px;
            }}
        """)
        self._populate_deck_combo()
        self.detail_deck_combo.currentIndexChanged.connect(self._on_deck_changed)
        deck_layout.addWidget(self.detail_deck_combo)

        detail_layout.addWidget(deck_frame)

        # Progress section
        progress_frame = QFrame()
        progress_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['header_bg']};
                border: 2px solid {PC_COLORS['box_border']};
                border-radius: 4px;
            }}
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(8, 6, 8, 6)
        progress_layout.setSpacing(4)

        hatch_label = QLabel("HATCH PROGRESS")
        hatch_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        hatch_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hatch_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background: transparent;")
        progress_layout.addWidget(hatch_label)

        self.detail_progress_bar = QProgressBar()
        self.detail_progress_bar.setRange(0, 100)
        self.detail_progress_bar.setValue(0)
        self.detail_progress_bar.setTextVisible(False)
        self.detail_progress_bar.setFixedHeight(16)
        self.detail_progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 2px solid {PC_COLORS['box_border']};
                background-color: #f0f0e0;
                border-radius: 4px;
            }}
            QProgressBar::chunk {{
                background-color: {PC_COLORS['selected']};
                border-radius: 2px;
            }}
        """)
        progress_layout.addWidget(self.detail_progress_bar)

        self.detail_progress_label = QLabel("0 / 0")
        self.detail_progress_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.detail_progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_progress_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; background: transparent;")
        progress_layout.addWidget(self.detail_progress_label)

        # Hatch prediction
        self.detail_prediction_label = QLabel("~??? cards to hatch")
        self.detail_prediction_label.setFont(QFont("Arial", 9))
        self.detail_prediction_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_prediction_label.setStyleSheet(f"color: #606060; background: transparent; font-style: italic;")
        progress_layout.addWidget(self.detail_prediction_label)

        # Hatch button (hidden by default, shown when egg is ready)
        self.detail_hatch_btn = QPushButton("🥚 HATCH EGG! 🥚")
        self.detail_hatch_btn.setFixedHeight(36)
        self.detail_hatch_btn.clicked.connect(self._hatch_egg)
        self.detail_hatch_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #d4af37;
                color: #1a1a1a;
                border: 2px solid #b8960c;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #e8c84a;
            }}
        """)
        self.detail_hatch_btn.hide()  # Hidden by default
        progress_layout.addWidget(self.detail_hatch_btn)

        detail_layout.addWidget(progress_frame)

        # Action buttons (Release and Gift)
        action_layout = QHBoxLayout()
        action_layout.setSpacing(6)

        release_btn = QPushButton("Release")
        release_btn.setFixedHeight(26)
        release_btn.clicked.connect(self._release_egg)
        release_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #c05050;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: #d06060;
            }}
        """)
        action_layout.addWidget(release_btn)

        gift_btn = QPushButton("Gift")
        gift_btn.setFixedHeight(26)
        gift_btn.clicked.connect(self._gift_egg)
        gift_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #5080c0;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 9px;
            }}
            QPushButton:hover {{
                background-color: #6090d0;
            }}
        """)
        action_layout.addWidget(gift_btn)

        detail_layout.addLayout(action_layout)
        detail_layout.addStretch()

        content_layout.addWidget(self.detail_panel)

        main_layout.addLayout(content_layout, 1)

        # Bottom button bar
        btn_frame = QFrame()
        btn_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {PC_COLORS['bg_medium']};
                border: none;
                border-radius: 4px;
            }}
        """)
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(12, 5, 12, 5)

        egg_count = len(self.eggs)
        self.count_label = QLabel(f"EGGS: {egg_count}")
        count_font = QFont("Arial", 10)
        count_font.setBold(True)
        self.count_label.setFont(count_font)
        self.count_label.setStyleSheet(f"color: {PC_COLORS['text_light']}; background: transparent;")
        btn_layout.addWidget(self.count_label)

        btn_layout.addStretch()

        close_btn = QPushButton("CLOSE")
        close_font = QFont("Arial", 10)
        close_font.setBold(True)
        close_btn.setFont(close_font)
        close_btn.clicked.connect(self.close)
        close_btn.setFixedWidth(90)
        close_btn.setFixedHeight(26)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {PC_COLORS['button_bg']};
                color: {PC_COLORS['button_text']};
                border: 2px solid {PC_COLORS['bg_light']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {PC_COLORS['bg_light']};
            }}
            QPushButton:pressed {{
                background-color: {PC_COLORS['selected']};
                color: {PC_COLORS['text_dark']};
            }}
        """)
        btn_layout.addWidget(close_btn)

        main_layout.addWidget(btn_frame)

        # Auto-select first egg if available
        if self.egg_icons:
            self._on_egg_clicked(self.egg_icons[0])

    def _populate_egg_grid(self):
        """Populate the egg grid with filtered/sorted eggs."""
        filtered = self._get_filtered_eggs()
        
        if not filtered:
            no_eggs_label = QLabel("No eggs found!" if self.eggs else "No eggs yet!\nCatch Pokemon\nto find eggs...")
            no_eggs_font = QFont("Arial", 10)
            no_eggs_label.setFont(no_eggs_font)
            no_eggs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_eggs_label.setStyleSheet(f"color: {PC_COLORS['text_dark']}; padding: 20px; background: transparent;")
            self.grid_layout.addWidget(no_eggs_label, 0, 0, 1, 6)
        else:
            # Create animated egg icons - 6 columns
            for idx, egg in enumerate(filtered):
                egg_icon = self._create_egg_icon(egg)
                row = idx // 6
                col = idx % 6
                self.grid_layout.addWidget(egg_icon, row, col)

            # Fill remaining slots in the row
            remainder = len(filtered) % 6
            if remainder > 0:
                for col in range(remainder, 6):
                    empty = QLabel()
                    empty.setFixedSize(48, 48)
                    empty.setStyleSheet(f"background-color: {PC_COLORS['box_border']}; border-radius: 4px;")
                    self.grid_layout.addWidget(empty, len(filtered) // 6, col)

            self.grid_layout.setRowStretch(len(filtered) // 6 + 1, 1)

    def _rebuild_egg_grid(self):
        """Rebuild the egg grid after filter/sort change."""
        # Clear current icons
        self.egg_icons.clear()
        self.selected_egg = None
        
        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Repopulate
        self._populate_egg_grid()
        
        # Update count label
        filtered = self._get_filtered_eggs()
        if hasattr(self, 'count_label'):
            self.count_label.setText(f"EGGS: {len(filtered)}/{len(self.eggs)}")
        
        # Auto-select first egg if available
        if self.egg_icons:
            self._on_egg_clicked(self.egg_icons[0])

    def _create_egg_icon(self, egg: dict) -> AnimatedEggLabel:
        """Create an animated egg icon widget.

        Args:
            egg: Dictionary containing egg data.

        Returns:
            AnimatedEggLabel: Clickable animated egg icon.
        """
        pokemon_name = egg.get("pokemon_name", "")
        icon_path = get_egg_icon_path(pokemon_name)
        
        egg_icon = AnimatedEggLabel(icon_path, egg, self)
        egg_icon.mousePressEvent = lambda event, e=egg_icon: self._on_egg_clicked(e)
        
        self.egg_icons.append(egg_icon)
        return egg_icon

    def closeEvent(self, event):
        """Stop timer when dialog closes."""
        self.animation_timer.stop()
        super().closeEvent(event)

    def refresh(self):
        """Reload egg data and refresh the display."""
        self.animation_timer.stop()
        self.egg_icons.clear()
        self.selected_egg = None
        self.eggs = load_eggs()
        # Clear and rebuild UI
        for i in reversed(range(self.layout().count())):
            item = self.layout().itemAt(i)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear nested layouts
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        self._setup_ui()
        self.animation_timer.start(500)


def show_egg_collection():
    """Convenience function to show the egg collection dialog."""
    dialog = EggCollectionDialog()
    dialog.exec()
    return dialog
