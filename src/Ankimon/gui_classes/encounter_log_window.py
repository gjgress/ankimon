"""
Encounter Log Window for Ankimon

Displays the history of Pokemon encounters with timestamps and battle outcomes.
Also shows individual Pokemon battle statistics.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from aqt import mw
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QPixmap, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QWidget,
    QHeaderView,
    QAbstractItemView,
    QSpinBox,
    QMessageBox,
)

from ..pyobj.encounter_log import (
    get_recent_encounters,
    get_encounter_stats,
    get_top_battlers,
    clear_encounter_log,
)
from ..resources import icon_path, frontdefault
from ..functions.sprite_functions import get_sprite_path


class EncounterLogWindow(QDialog):
    """Window to display the encounter log and battle statistics."""
    
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Encounter Log & Battle Stats")
        self.setWindowIcon(QIcon(str(icon_path)))
        self.setMinimumSize(700, 500)
        self.resize(800, 600)
        
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Encounter Log
        self.encounter_tab = QWidget()
        self.init_encounter_tab()
        self.tabs.addTab(self.encounter_tab, "📋 Encounter Log")
        
        # Tab 2: Battle Statistics
        self.stats_tab = QWidget()
        self.init_stats_tab()
        self.tabs.addTab(self.stats_tab, "⚔️ Battle Stats")
        
        # Tab 3: Top Battlers
        self.battlers_tab = QWidget()
        self.init_battlers_tab()
        self.tabs.addTab(self.battlers_tab, "🏆 Top Battlers")
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("🔄 Refresh")
        self.refresh_btn.clicked.connect(self.load_data)
        button_layout.addWidget(self.refresh_btn)
        
        button_layout.addStretch()
        
        self.clear_btn = QPushButton("🗑️ Clear Log")
        self.clear_btn.clicked.connect(self.confirm_clear_log)
        button_layout.addWidget(self.clear_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def init_encounter_tab(self):
        """Initialize the encounter log tab."""
        layout = QVBoxLayout(self.encounter_tab)
        
        # Header with count selector
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("Show last:"))
        
        self.count_spinner = QSpinBox()
        self.count_spinner.setRange(10, 100)
        self.count_spinner.setValue(50)
        self.count_spinner.valueChanged.connect(self.load_encounter_log)
        header_layout.addWidget(self.count_spinner)
        
        header_layout.addWidget(QLabel("encounters"))
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Encounter table
        self.encounter_table = QTableWidget()
        self.encounter_table.setColumnCount(7)
        self.encounter_table.setHorizontalHeaderLabels([
            "Time", "Pokemon", "Level", "Tier", "Shiny", "Outcome", "Main Pokemon"
        ])
        self.encounter_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.encounter_table.horizontalHeader().setStretchLastSection(True)
        self.encounter_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.encounter_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.encounter_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.encounter_table)
    
    def init_stats_tab(self):
        """Initialize the battle statistics tab."""
        layout = QVBoxLayout(self.stats_tab)
        
        # Title
        title = QLabel("📊 Encounter Statistics")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # Stats grid
        self.stats_labels = {}
        stats_layout = QVBoxLayout()
        
        stat_names = [
            ("total_encounters", "Total Encounters"),
            ("caught", "Pokemon Caught"),
            ("defeated", "Pokemon Defeated"),
            ("fled", "Pokemon Fled"),
            ("lost", "Battles Lost"),
            ("shinies_encountered", "Shinies Encountered"),
            ("catch_rate", "Catch Rate"),
        ]
        
        for key, display_name in stat_names:
            row = QHBoxLayout()
            
            name_label = QLabel(f"{display_name}:")
            name_label.setFont(QFont("Arial", 11))
            name_label.setMinimumWidth(200)
            row.addWidget(name_label)
            
            value_label = QLabel("0")
            value_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            self.stats_labels[key] = value_label
            row.addWidget(value_label)
            
            row.addStretch()
            stats_layout.addLayout(row)
        
        layout.addLayout(stats_layout)
        layout.addStretch()
    
    def init_battlers_tab(self):
        """Initialize the top battlers tab."""
        layout = QVBoxLayout(self.battlers_tab)
        
        # Title
        title = QLabel("🏆 Top Battling Pokemon")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Battlers table
        self.battlers_table = QTableWidget()
        self.battlers_table.setColumnCount(6)
        self.battlers_table.setHorizontalHeaderLabels([
            "Pokemon", "Level", "Wins", "Losses", "Total", "Win Rate"
        ])
        self.battlers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.battlers_table.horizontalHeader().setStretchLastSection(True)
        self.battlers_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.battlers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.battlers_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.battlers_table)
    
    def load_data(self):
        """Load all data for all tabs."""
        self.load_encounter_log()
        self.load_stats()
        self.load_top_battlers()
    
    def load_encounter_log(self):
        """Load and display the encounter log."""
        count = self.count_spinner.value()
        encounters = get_recent_encounters(count)
        
        self.encounter_table.setRowCount(len(encounters))
        
        for row, encounter in enumerate(encounters):
            # Format timestamp
            try:
                dt = datetime.fromisoformat(encounter.get("timestamp", ""))
                time_str = dt.strftime("%m/%d %H:%M")
            except:
                time_str = "Unknown"
            
            # Create table items
            self.encounter_table.setItem(row, 0, QTableWidgetItem(time_str))
            self.encounter_table.setItem(row, 1, QTableWidgetItem(encounter.get("pokemon_name", "Unknown")))
            self.encounter_table.setItem(row, 2, QTableWidgetItem(str(encounter.get("level", "?"))))
            self.encounter_table.setItem(row, 3, QTableWidgetItem(encounter.get("tier", "Normal")))
            
            # Shiny indicator
            shiny_text = "✨ Yes" if encounter.get("shiny", False) else "No"
            self.encounter_table.setItem(row, 4, QTableWidgetItem(shiny_text))
            
            # Outcome with color coding
            outcome = encounter.get("outcome", "unknown")
            outcome_item = QTableWidgetItem(outcome.capitalize())
            
            if outcome == "caught":
                outcome_item.setForeground(Qt.GlobalColor.darkGreen)
            elif outcome == "defeated":
                outcome_item.setForeground(Qt.GlobalColor.blue)
            elif outcome == "fled":
                outcome_item.setForeground(Qt.GlobalColor.darkYellow)
            elif outcome == "lost":
                outcome_item.setForeground(Qt.GlobalColor.red)
            
            self.encounter_table.setItem(row, 5, outcome_item)
            
            # Main Pokemon used
            main_name = encounter.get("main_pokemon_name", "-")
            self.encounter_table.setItem(row, 6, QTableWidgetItem(main_name or "-"))
    
    def load_stats(self):
        """Load and display encounter statistics."""
        stats = get_encounter_stats()
        
        for key, label in self.stats_labels.items():
            value = stats.get(key, 0)
            if key == "catch_rate":
                label.setText(f"{value:.1f}%")
            else:
                label.setText(str(value))
    
    def load_top_battlers(self):
        """Load and display top battling Pokemon."""
        battlers = get_top_battlers(20)
        
        self.battlers_table.setRowCount(len(battlers))
        
        for row, battler in enumerate(battlers):
            # Pokemon name (with nickname if exists)
            name = battler.get("name", "Unknown")
            nickname = battler.get("nickname", "")
            display_name = f"{nickname} ({name})" if nickname and nickname != name else name
            
            self.battlers_table.setItem(row, 0, QTableWidgetItem(display_name))
            self.battlers_table.setItem(row, 1, QTableWidgetItem(str(battler.get("level", "?"))))
            self.battlers_table.setItem(row, 2, QTableWidgetItem(str(battler.get("battles_won", 0))))
            self.battlers_table.setItem(row, 3, QTableWidgetItem(str(battler.get("battles_lost", 0))))
            self.battlers_table.setItem(row, 4, QTableWidgetItem(str(battler.get("total_battles", 0))))
            
            # Win rate with color
            win_rate = battler.get("win_rate", 0)
            rate_item = QTableWidgetItem(f"{win_rate}%")
            
            if win_rate >= 75:
                rate_item.setForeground(Qt.GlobalColor.darkGreen)
            elif win_rate >= 50:
                rate_item.setForeground(Qt.GlobalColor.blue)
            else:
                rate_item.setForeground(Qt.GlobalColor.red)
            
            self.battlers_table.setItem(row, 5, rate_item)
    
    def confirm_clear_log(self):
        """Confirm before clearing the encounter log."""
        reply = QMessageBox.question(
            self,
            "Clear Encounter Log",
            "Are you sure you want to clear the entire encounter log?\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            clear_encounter_log()
            self.load_data()


def show_encounter_log_window():
    """Show the encounter log window."""
    window = EncounterLogWindow()
    window.exec()
