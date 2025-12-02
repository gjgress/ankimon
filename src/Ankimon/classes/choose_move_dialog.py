import sys
import json
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from ..functions.pokedex_functions import find_details_move
from ..resources import effectiveness_chart_file_path
import random


def get_move_effectiveness(move_type: str, defender_types: list) -> float:
    """
    Calculate the type effectiveness multiplier for a move against defender types.
    
    Args:
        move_type: The type of the attacking move
        defender_types: List of the defender's types
        
    Returns:
        float: The effectiveness multiplier (0, 0.25, 0.5, 1, 2, or 4)
    """
    if not move_type or not defender_types:
        return 1.0
    
    try:
        with open(effectiveness_chart_file_path, 'r', encoding='utf-8') as f:
            chart = json.load(f)
        
        move_type = move_type.capitalize()
        if move_type not in chart:
            return 1.0
        
        multiplier = 1.0
        for def_type in defender_types:
            def_type = def_type.capitalize()
            if def_type in chart.get(move_type, {}):
                multiplier *= chart[move_type][def_type]
        
        return multiplier
    except Exception:
        return 1.0


def get_effectiveness_text(multiplier: float) -> tuple:
    """
    Get the display text and color for an effectiveness multiplier.
    
    Returns:
        tuple: (text, color) for the effectiveness
    """
    if multiplier == 0:
        return ("No Effect", "#666666")
    elif multiplier < 1:
        return ("Not Very Effective", "#cc6600")
    elif multiplier == 1:
        return ("Normal", "#888888")
    elif multiplier >= 2:
        return ("Super Effective!", "#22cc22")
    else:
        return ("Effective", "#888888")


class MoveSelectionDialog(QDialog):
    def __init__(self, mainpokemon_attacks, enemy_types=None):
        super().__init__()

        # Dialog settings
        self.setWindowTitle("Select a Move")
        self.resize(400, 250)
        self.selected_move = random.choice(mainpokemon_attacks)
        self.mainpokemon_attacks = mainpokemon_attacks
        self.enemy_types = enemy_types or []

        # Create and set layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Add a title label
        title_label = QLabel("Press a number (1-4) or click to select a move:")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        layout.addWidget(title_label)
        
        # Show enemy type info if available
        if self.enemy_types:
            enemy_type_text = " / ".join([t.capitalize() for t in self.enemy_types])
            enemy_label = QLabel(f"Enemy Type: {enemy_type_text}")
            enemy_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            enemy_label.setFont(QFont("Arial", 10))
            enemy_label.setStyleSheet("color: #666666;")
            layout.addWidget(enemy_label)

        # Add labels for each move with effectiveness
        self.move_labels = []
        for index, move in enumerate(mainpokemon_attacks):
            move_detail = find_details_move(move)
            move_type = move_detail.get('type', '')
            
            # Create horizontal layout for move + effectiveness
            move_row = QHBoxLayout()
            
            # Move info label
            move_text = f"{index + 1}. {move_detail.get('name', move.capitalize())} ({move_detail.get('basePower', '-')})"
            move_label = QLabel(move_text)
            move_label.setToolTip(f"{move_detail.get('desc', 'No description available')}")
            move_label.setFont(QFont("Arial", 11))
            move_label.setMinimumWidth(180)
            
            # Effectiveness indicator
            if self.enemy_types and move_type:
                multiplier = get_move_effectiveness(move_type, self.enemy_types)
                eff_text, eff_color = get_effectiveness_text(multiplier)
                
                eff_label = QLabel(f"[{eff_text}]")
                eff_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                eff_label.setStyleSheet(f"color: {eff_color};")
            else:
                eff_label = QLabel("")
            
            # Container widget for click handling
            container = QLabel()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(5, 2, 5, 2)
            container_layout.addWidget(move_label)
            container_layout.addStretch()
            container_layout.addWidget(eff_label)
            
            container.setStyleSheet("""
                QLabel { 
                    border: 1px solid #ccc; 
                    border-radius: 3px; 
                    background-color: #f8f8f8;
                }
                QLabel:hover { 
                    background-color: #e8e8ff; 
                    border-color: #aaa;
                }
            """)
            container.setFixedHeight(28)
            container.mousePressEvent = self.create_mouse_press_handler(index)
            
            layout.addWidget(container)
            self.move_labels.append(container)


    def create_mouse_press_handler(self, index):
        def handle_mouse_press(event):
            self.select_move(index)
        return handle_mouse_press

    def select_move(self, index):
        """Handle move selection and close the dialog."""
        self.selected_move = self.mainpokemon_attacks[index]
        self.accept()

    def keyPressEvent(self, event):
        """Handle keyboard shortcuts for move selection."""
        key = event.key()
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            move_index = key - Qt.Key.Key_1  # Convert key to list index
            if 0 <= move_index < len(self.mainpokemon_attacks):
                self.select_move(move_index)
