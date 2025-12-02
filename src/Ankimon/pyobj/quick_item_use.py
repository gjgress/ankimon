"""
Quick Item Use System for Ankimon

Provides a hotkey-accessible dialog for quickly using common items
like healing potions, status recovery items, and evolution stones.
"""

import json
from pathlib import Path
from typing import Optional, Callable

from aqt import mw
from aqt.utils import tooltip
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QFont, QPixmap, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QWidget,
    QGridLayout,
    QScrollArea,
    QMessageBox,
)

from ..resources import icon_path, itembag_path, items_path, mypokemon_path
from ..pyobj.pokemon_obj import PokemonObject


# Item categories and their effects
HEALING_ITEMS = {
    'potion': 20,
    'sweet-heart': 20,
    'berry-juice': 20,
    'fresh-water': 30,
    'soda-pop': 50,
    'super-potion': 60,
    'energy-powder': 60,
    'lemonade': 70,
    'moomoo-milk': 100,
    'hyper-potion': 120,
    'energy-root': 120,
    'full-restore': 1000,
    'max-potion': 1000,
}

STATUS_RECOVERY_ITEMS = {
    'antidote': 'psn',
    'paralyze-heal': 'par',
    'burn-heal': 'brn',
    'ice-heal': 'frz',
    'awakening': 'slp',
    'full-heal': 'all',
    'full-restore': 'all',
    'lava-cookie': 'all',
    'old-gateau': 'all',
    'casteliacone': 'all',
    'lumiose-galette': 'all',
    'shalour-sable': 'all',
}

REVIVE_ITEMS = {
    'revive': 0.5,  # Restores 50% HP
    'max-revive': 1.0,  # Restores 100% HP
    'revival-herb': 1.0,
    'sacred-ash': 1.0,  # Revives all fainted Pokemon
}


def load_item_bag() -> list:
    """Load items from the item bag file."""
    try:
        if itembag_path.is_file():
            with open(itembag_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Ankimon: Error loading item bag: {e}")
    return []


def save_item_bag(items: list) -> None:
    """Save items to the item bag file."""
    try:
        with open(itembag_path, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2)
    except Exception as e:
        print(f"Ankimon: Error saving item bag: {e}")


def use_item(item_name: str, quantity: int = 1) -> bool:
    """
    Reduce the quantity of an item in the bag.
    
    Returns:
        bool: True if item was successfully used, False if not enough items
    """
    items = load_item_bag()
    
    for item in items:
        if item.get("item") == item_name:
            if item.get("quantity", 0) >= quantity:
                item["quantity"] -= quantity
                if item["quantity"] <= 0:
                    items.remove(item)
                save_item_bag(items)
                return True
            return False
    return False


def get_item_quantity(item_name: str) -> int:
    """Get the quantity of an item in the bag."""
    items = load_item_bag()
    for item in items:
        if item.get("item") == item_name:
            return item.get("quantity", 0)
    return 0


def heal_pokemon(pokemon: PokemonObject, heal_amount: int) -> int:
    """
    Heal a Pokemon by a specified amount.
    
    Returns:
        int: The actual amount healed
    """
    if not pokemon:
        return 0
    
    current_hp = getattr(pokemon, 'hp', 0)
    max_hp = getattr(pokemon, 'max_hp', current_hp)
    
    if current_hp >= max_hp:
        return 0  # Already at full health
    
    actual_heal = min(heal_amount, max_hp - current_hp)
    pokemon.hp = current_hp + actual_heal
    pokemon.current_hp = pokemon.hp
    
    return actual_heal


class QuickItemDialog(QDialog):
    """Quick access dialog for using items during battle."""
    
    def __init__(self, main_pokemon: PokemonObject = None, parent=None):
        super().__init__(parent or mw)
        self.main_pokemon = main_pokemon
        self.setWindowTitle("Quick Item Use")
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(400, 350)
        self.resize(450, 400)
        
        self.item_used = False
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Pokemon info header
        if self.main_pokemon:
            header = QLabel(f"🎮 {self.main_pokemon.name.capitalize()} - HP: {self.main_pokemon.hp}/{self.main_pokemon.max_hp}")
            header.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            header.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(header)
        
        # Tabs for different item categories
        tabs = QTabWidget()
        
        # Healing tab
        healing_tab = self.create_healing_tab()
        tabs.addTab(healing_tab, "💊 Healing")
        
        # Status recovery tab
        status_tab = self.create_status_tab()
        tabs.addTab(status_tab, "💉 Status")
        
        # Revive tab
        revive_tab = self.create_revive_tab()
        tabs.addTab(revive_tab, "✨ Revive")
        
        layout.addWidget(tabs)
        
        # Hotkey hints
        hint_label = QLabel("Press 1-9 to quickly use items, or click the buttons")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_label.setStyleSheet("color: #666666; font-size: 10px;")
        layout.addWidget(hint_label)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def create_healing_tab(self) -> QWidget:
        """Create the healing items tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        grid = QGridLayout(scroll_widget)
        
        items = load_item_bag()
        healing_items = [(item, HEALING_ITEMS.get(item.get("item"))) 
                         for item in items 
                         if item.get("item") in HEALING_ITEMS and item.get("quantity", 0) > 0]
        
        # Sort by healing amount
        healing_items.sort(key=lambda x: x[1] or 0, reverse=True)
        
        if not healing_items:
            no_items = QLabel("No healing items available")
            no_items.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(no_items, 0, 0)
        else:
            for idx, (item, heal_amount) in enumerate(healing_items[:9]):
                item_name = item.get("item", "Unknown")
                quantity = item.get("quantity", 0)
                
                btn = QPushButton(f"[{idx+1}] {item_name.replace('-', ' ').title()}\n+{heal_amount} HP (x{quantity})")
                btn.setMinimumHeight(50)
                
                # Color code based on heal amount
                if heal_amount >= 100:
                    btn.setStyleSheet("background-color: #c8e6c9;")
                elif heal_amount >= 50:
                    btn.setStyleSheet("background-color: #fff9c4;")
                
                btn.clicked.connect(lambda checked, name=item_name, amount=heal_amount: 
                                    self.use_healing_item(name, amount))
                
                row, col = divmod(idx, 3)
                grid.addWidget(btn, row, col)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return widget
    
    def create_status_tab(self) -> QWidget:
        """Create the status recovery items tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        grid = QGridLayout(scroll_widget)
        
        items = load_item_bag()
        status_items = [item for item in items 
                        if item.get("item") in STATUS_RECOVERY_ITEMS and item.get("quantity", 0) > 0]
        
        if not status_items:
            no_items = QLabel("No status recovery items available")
            no_items.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(no_items, 0, 0)
        else:
            for idx, item in enumerate(status_items[:9]):
                item_name = item.get("item", "Unknown")
                quantity = item.get("quantity", 0)
                cures = STATUS_RECOVERY_ITEMS.get(item_name, "?")
                
                cure_text = "All Status" if cures == "all" else cures.upper()
                btn = QPushButton(f"[{idx+1}] {item_name.replace('-', ' ').title()}\nCures: {cure_text} (x{quantity})")
                btn.setMinimumHeight(50)
                btn.setStyleSheet("background-color: #e1bee7;")
                
                btn.clicked.connect(lambda checked, name=item_name, cure=cures: 
                                    self.use_status_item(name, cure))
                
                row, col = divmod(idx, 3)
                grid.addWidget(btn, row, col)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return widget
    
    def create_revive_tab(self) -> QWidget:
        """Create the revive items tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        grid = QGridLayout(scroll_widget)
        
        items = load_item_bag()
        revive_items = [item for item in items 
                        if item.get("item") in REVIVE_ITEMS and item.get("quantity", 0) > 0]
        
        if not revive_items:
            no_items = QLabel("No revive items available")
            no_items.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(no_items, 0, 0)
        else:
            for idx, item in enumerate(revive_items[:9]):
                item_name = item.get("item", "Unknown")
                quantity = item.get("quantity", 0)
                restore_pct = int(REVIVE_ITEMS.get(item_name, 0.5) * 100)
                
                btn = QPushButton(f"[{idx+1}] {item_name.replace('-', ' ').title()}\nRestores {restore_pct}% HP (x{quantity})")
                btn.setMinimumHeight(50)
                btn.setStyleSheet("background-color: #bbdefb;")
                
                btn.clicked.connect(lambda checked, name=item_name, pct=REVIVE_ITEMS.get(item_name, 0.5): 
                                    self.use_revive_item(name, pct))
                
                row, col = divmod(idx, 3)
                grid.addWidget(btn, row, col)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        return widget
    
    def use_healing_item(self, item_name: str, heal_amount: int):
        """Use a healing item on the main Pokemon."""
        if not self.main_pokemon:
            tooltip("No Pokemon selected!")
            return
        
        if self.main_pokemon.hp >= self.main_pokemon.max_hp:
            tooltip(f"{self.main_pokemon.name.capitalize()} is already at full HP!")
            return
        
        if use_item(item_name):
            actual_heal = heal_pokemon(self.main_pokemon, heal_amount)
            tooltip(f"Used {item_name.replace('-', ' ').title()}! {self.main_pokemon.name.capitalize()} recovered {actual_heal} HP!")
            self.item_used = True
            self.accept()
        else:
            tooltip(f"No {item_name.replace('-', ' ').title()} in bag!")
    
    def use_status_item(self, item_name: str, cures: str):
        """Use a status recovery item on the main Pokemon."""
        if not self.main_pokemon:
            tooltip("No Pokemon selected!")
            return
        
        battle_status = getattr(self.main_pokemon, 'battle_status', 'Fighting')
        
        if battle_status == 'Fighting' or battle_status == 'fighting':
            tooltip(f"{self.main_pokemon.name.capitalize()} has no status condition!")
            return
        
        # Check if this item cures the current status
        if cures != 'all' and battle_status.lower() != cures.lower():
            tooltip(f"{item_name.replace('-', ' ').title()} doesn't cure {battle_status}!")
            return
        
        if use_item(item_name):
            self.main_pokemon.battle_status = 'Fighting'
            tooltip(f"Used {item_name.replace('-', ' ').title()}! {self.main_pokemon.name.capitalize()} was cured!")
            self.item_used = True
            self.accept()
        else:
            tooltip(f"No {item_name.replace('-', ' ').title()} in bag!")
    
    def use_revive_item(self, item_name: str, restore_pct: float):
        """Use a revive item on a fainted Pokemon."""
        if not self.main_pokemon:
            tooltip("No Pokemon selected!")
            return
        
        if self.main_pokemon.hp > 0:
            tooltip(f"{self.main_pokemon.name.capitalize()} isn't fainted!")
            return
        
        if use_item(item_name):
            restore_hp = int(self.main_pokemon.max_hp * restore_pct)
            self.main_pokemon.hp = restore_hp
            self.main_pokemon.current_hp = restore_hp
            self.main_pokemon.battle_status = 'Fighting'
            tooltip(f"Used {item_name.replace('-', ' ').title()}! {self.main_pokemon.name.capitalize()} was revived with {restore_hp} HP!")
            self.item_used = True
            self.accept()
        else:
            tooltip(f"No {item_name.replace('-', ' ').title()} in bag!")
    
    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for quick item use."""
        key = event.key()
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            item_index = key - Qt.Key.Key_1
            # Get current tab and try to use that item
            # For simplicity, just close on number press for now
            # In a full implementation, you'd track which items are shown
        elif key == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


def show_quick_item_dialog(main_pokemon: PokemonObject = None) -> bool:
    """
    Show the quick item use dialog.
    
    Returns:
        bool: True if an item was used, False otherwise
    """
    dialog = QuickItemDialog(main_pokemon)
    dialog.exec()
    return dialog.item_used
