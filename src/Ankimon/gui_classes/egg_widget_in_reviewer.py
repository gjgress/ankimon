"""Egg Widget for Reviewer.

This module provides a floating egg widget that appears in the reviewer
when studying a deck that has an egg assigned to it. The egg shakes
when the user answers a card correctly.
"""

import json
import os
import time
from pathlib import Path

from aqt import mw, gui_hooks
from aqt.utils import tooltip
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
    QProgressBar,
)

from ..resources import eggs_path, eggs_icon_path


def load_eggs() -> list:
    """Load eggs from the eggs.json file."""
    try:
        if os.path.exists(eggs_path):
            with open(eggs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        return []
    except Exception:
        return []


def save_eggs(eggs: list) -> bool:
    """Save eggs to the eggs.json file."""
    try:
        with open(eggs_path, "w", encoding="utf-8") as f:
            json.dump(eggs, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def update_sync_timestamp() -> bool:
    """Update the last sync timestamp to current time.
    
    This prevents the egg collection from double-counting reviews
    that were already counted in real-time by this widget.
    """
    try:
        meta_path = eggs_path.parent / "eggs_meta.json"
        data = {}
        if os.path.exists(meta_path):
            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["last_deck_sync_timestamp"] = int(time.time() * 1000)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception:
        return False


def get_egg_icon_path(pokemon_name: str) -> str:
    """Get the path to the egg icon sprite sheet."""
    icon_file = eggs_icon_path / f"{pokemon_name.lower()}_icon.png"
    if icon_file.exists():
        return str(icon_file)
    
    # Try uppercase
    icon_file = eggs_icon_path / f"{pokemon_name.upper()}_icon.png"
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


class ReviewerEggWidget(QFrame):
    """A floating egg widget that appears in the reviewer corner.
    
    Shows the egg assigned to the current deck and animates on correct answers.
    """
    
    # Class-level instance tracker
    _instance = None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.egg_data = None
        self.sprite_path = ""
        self.current_frame = 0
        self.left_pixmap = None
        self.right_pixmap = None
        self.is_shaking = False
        self.shake_step = 0
        self.original_pos = None
        
        # Animation timer for idle wobble
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self._animate)
        
        self._setup_ui()
        self.hide()  # Hidden by default
        
        # Track this instance
        ReviewerEggWidget._instance = self
    
    def _setup_ui(self):
        """Set up the widget UI."""
        self.setFixedSize(70, 85)
        self.setStyleSheet("""
            QFrame {
                background-color: rgba(40, 60, 80, 200);
                border: 2px solid #58d898;
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(2)
        
        # Egg sprite label
        self.egg_label = QLabel()
        self.egg_label.setFixedSize(50, 50)
        self.egg_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.egg_label.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.egg_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #a89850;
                background-color: #1a1a1a;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #58d898;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
    
    def set_egg(self, egg_data: dict):
        """Set the egg to display."""
        self.egg_data = egg_data
        
        if not egg_data:
            self.hide()
            self.animation_timer.stop()
            return
        
        # Load sprite
        pokemon_name = egg_data.get("pokemon_name", "")
        self.sprite_path = get_egg_icon_path(pokemon_name)
        self._load_sprite_sheet()
        self._update_display()
        self._update_progress()
        
        # Start animation
        self.animation_timer.start(600)
        self.show()
        self.raise_()
    
    def _load_sprite_sheet(self):
        """Load and split the sprite sheet into two frames."""
        if not self.sprite_path or not os.path.exists(self.sprite_path):
            self.left_pixmap = None
            self.right_pixmap = None
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
            scaled = pixmap.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.FastTransformation)
            self.egg_label.setPixmap(scaled)
        else:
            self.egg_label.setText("🥚")
            self.egg_label.setStyleSheet("background: transparent; border: none; font-size: 28px;")
    
    def _update_progress(self):
        """Update the progress bar."""
        if not self.egg_data:
            return
        
        cards_done = self.egg_data.get("cards_done", 0)
        cards_required = self.egg_data.get("cards_required", 100)
        progress_pct = min(100, int((cards_done / max(1, cards_required)) * 100))
        self.progress_bar.setValue(progress_pct)
    
    def _animate(self):
        """Toggle animation frame."""
        self.current_frame = 1 - self.current_frame
        self._update_display()
    
    def do_shake(self):
        """Perform a shake animation (called on correct answer)."""
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
    
    def add_progress(self, count: int = 1):
        """Add progress to the egg and update display."""
        if not self.egg_data:
            return
        
        # Update egg data
        old_cards = self.egg_data.get("cards_done", 0)
        self.egg_data["cards_done"] = old_cards + count
        
        # Update in eggs.json
        eggs = load_eggs()
        for egg in eggs:
            if egg.get("id") == self.egg_data.get("id"):
                egg["cards_done"] = self.egg_data["cards_done"]
                break
        save_eggs(eggs)
        
        # Update the sync timestamp so egg collection doesn't double-count
        update_sync_timestamp()
        
        # Update progress bar
        self._update_progress()
        
        # Check if hatched
        if self.egg_data["cards_done"] >= self.egg_data.get("cards_required", 100):
            # Egg is ready to hatch!
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 1px solid #d4af37;
                    background-color: #1a1a1a;
                    border-radius: 4px;
                }
                QProgressBar::chunk {
                    background-color: #d4af37;
                    border-radius: 3px;
                }
            """)
    
    def position_in_corner(self, corner: str = "top_right"):
        """Position the widget in a corner of the main window."""
        if not mw:
            return
        
        margin = 10
        mw_rect = mw.rect()
        
        if corner == "top_right":
            x = mw_rect.width() - self.width() - margin
            y = margin + 50  # Below toolbar
        elif corner == "top_left":
            x = margin
            y = margin + 50
        elif corner == "bottom_right":
            x = mw_rect.width() - self.width() - margin
            y = mw_rect.height() - self.height() - margin - 50
        else:  # bottom_left
            x = margin
            y = mw_rect.height() - self.height() - margin - 50
        
        self.move(x, y)
    
    @classmethod
    def get_instance(cls):
        """Get the current widget instance."""
        return cls._instance
    
    def cleanup(self):
        """Clean up the widget."""
        self.animation_timer.stop()
        self.hide()
        self.egg_data = None


# Global widget reference
_reviewer_egg_widget = None


def get_egg_for_deck(deck_id: int) -> dict:
    """Find an egg assigned to the given deck ID."""
    eggs = load_eggs()
    for egg in eggs:
        if egg.get("assigned_deck_id") == deck_id:
            return egg
    return None


def on_reviewer_did_show_question(card):
    """Called when a question is shown - update egg widget."""
    global _reviewer_egg_widget
    
    try:
        if not mw or not mw.reviewer or not card:
            return
        
        # Get current deck ID
        deck_id = card.current_deck_id()
        
        # Find egg for this deck
        egg = get_egg_for_deck(deck_id)
        
        # Create widget if needed
        if _reviewer_egg_widget is None:
            _reviewer_egg_widget = ReviewerEggWidget(mw)
        
        if egg:
            _reviewer_egg_widget.set_egg(egg)
            _reviewer_egg_widget.position_in_corner("top_right")
        else:
            _reviewer_egg_widget.hide()
            
    except Exception:
        pass


def on_reviewer_did_answer_card(reviewer, card, ease):
    """Called when a card is answered - animate egg on correct answer."""
    global _reviewer_egg_widget
    
    try:
        if not _reviewer_egg_widget or not _reviewer_egg_widget.egg_data:
            return
        
        # Check if answer was correct (not "Again")
        # ease: 1=Again, 2=Hard, 3=Good, 4=Easy
        if ease >= 2:  # Hard, Good, or Easy counts as correct
            _reviewer_egg_widget.do_shake()
            _reviewer_egg_widget.add_progress(1)
            
    except Exception:
        pass


def on_state_did_change(new_state, old_state):
    """Hide egg widget when leaving reviewer."""
    global _reviewer_egg_widget
    
    try:
        if new_state != "review" and _reviewer_egg_widget:
            _reviewer_egg_widget.hide()
    except Exception:
        pass


def setup_reviewer_egg_hooks():
    """Set up the hooks for the reviewer egg widget."""
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
    gui_hooks.reviewer_did_answer_card.append(on_reviewer_did_answer_card)
    gui_hooks.state_did_change.append(on_state_did_change)
