"""
Stat Comparison Tool for Ankimon

Provides a side-by-side comparison of two Pokemon's stats,
including base stats, IVs, EVs, and calculated stats with radar charts.
"""

import json
import math
from typing import Optional, Dict, Any, List

from aqt import mw
from aqt.utils import tooltip
from PyQt6.QtCore import Qt, QPointF, QRectF
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QPolygonF, QPainterPath
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QWidget,
    QGridLayout,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
)

from ..resources import mypokemon_path, icon_path
from ..pyobj.pokemon_obj import PokemonObject


# Stat name mappings
STAT_NAMES = {
    "hp": "HP",
    "atk": "Attack",
    "def": "Defense",
    "spa": "Sp. Atk",
    "spd": "Sp. Def",
    "spe": "Speed",
}

# Short stat names for radar chart
STAT_SHORT = {
    "hp": "HP",
    "atk": "ATK",
    "def": "DEF",
    "spa": "SPA",
    "spd": "SPD",
    "spe": "SPE",
}

# Colors for stats - Optimized for dark mode visibility
STAT_COLORS = {
    "hp": "#FF6B6B",      # Bright coral red
    "atk": "#FFB347",     # Bright orange
    "def": "#FFD93D",     # Bright yellow
    "spa": "#6BCB77",     # Bright green (distinct from others)
    "spd": "#4D96FF",     # Bright blue
    "spe": "#C77DFF",     # Bright purple/magenta
}

# Pokemon colors for comparison - High contrast for dark mode
POKEMON_COLORS = {
    "current": "#00D9FF",  # Cyan - high visibility
    "compare": "#FF6B9D",  # Pink/magenta - high visibility
}


def load_all_pokemon() -> List[Dict]:
    """Load all Pokemon from mypokemon.json."""
    try:
        with open(mypokemon_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Ankimon: Error loading Pokemon for comparison: {e}")
        return []


class RadarChartWidget(QWidget):
    """Widget to display a hexagonal radar chart for Pokemon stats."""
    
    def __init__(self, stats1: Dict[str, int], stats2: Optional[Dict[str, int]] = None,
                 name1: str = "Pokemon 1", name2: str = "Pokemon 2",
                 max_stat: int = 255, parent=None):
        super().__init__(parent)
        self.stats1 = stats1
        self.stats2 = stats2
        self.name1 = name1
        self.name2 = name2
        self.max_stat = max_stat
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions
        width = self.width()
        height = self.height()
        center_x = width / 2
        center_y = height / 2
        radius = min(width, height) / 2 - 50
        
        # Draw dark background
        painter.fillRect(self.rect(), QColor("#1E1E1E"))
        
        # Stat keys in order (clockwise from top)
        stat_keys = ["hp", "atk", "def", "spe", "spd", "spa"]
        num_stats = len(stat_keys)
        angle_step = 360 / num_stats
        
        # Draw grid lines (hexagons at 25%, 50%, 75%, 100%) - Dark mode
        for pct in [0.25, 0.5, 0.75, 1.0]:
            grid_radius = radius * pct
            grid_points = []
            for i in range(num_stats):
                angle = math.radians(-90 + i * angle_step)
                x = center_x + grid_radius * math.cos(angle)
                y = center_y + grid_radius * math.sin(angle)
                grid_points.append(QPointF(x, y))
            
            polygon = QPolygonF(grid_points)
            pen = QPen(QColor("#444444"), 1)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPolygon(polygon)
        
        # Draw axis lines from center to each vertex - Dark mode
        for i in range(num_stats):
            angle = math.radians(-90 + i * angle_step)
            end_x = center_x + radius * math.cos(angle)
            end_y = center_y + radius * math.sin(angle)
            painter.setPen(QPen(QColor("#555555"), 1))
            painter.drawLine(QPointF(center_x, center_y), QPointF(end_x, end_y))
        
        # Draw stat labels with values
        font = QFont("Arial", 9, QFont.Weight.Bold)
        painter.setFont(font)
        
        for i, key in enumerate(stat_keys):
            angle = math.radians(-90 + i * angle_step)
            label_radius = radius + 35
            x = center_x + label_radius * math.cos(angle)
            y = center_y + label_radius * math.sin(angle)
            
            stat_name = STAT_SHORT[key]
            val1 = self.stats1.get(key, 0)
            val2 = self.stats2.get(key, 0) if self.stats2 else None
            
            # Draw stat name
            painter.setPen(QColor(STAT_COLORS[key]))
            text_rect = QRectF(x - 40, y - 20, 80, 18)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, stat_name)
            
            # Draw values below stat name
            if val2 is not None:
                # Show both values
                painter.setPen(QColor(POKEMON_COLORS["current"]))
                val_rect1 = QRectF(x - 40, y - 4, 40, 16)
                painter.drawText(val_rect1, Qt.AlignmentFlag.AlignRight, str(val1))
                
                painter.setPen(QColor("#666666"))
                slash_rect = QRectF(x - 5, y - 4, 10, 16)
                painter.drawText(slash_rect, Qt.AlignmentFlag.AlignCenter, "/")
                
                painter.setPen(QColor(POKEMON_COLORS["compare"]))
                val_rect2 = QRectF(x, y - 4, 40, 16)
                painter.drawText(val_rect2, Qt.AlignmentFlag.AlignLeft, str(val2))
            else:
                # Show single value
                painter.setPen(QColor(POKEMON_COLORS["current"]))
                val_rect = QRectF(x - 40, y - 4, 80, 16)
                painter.drawText(val_rect, Qt.AlignmentFlag.AlignCenter, str(val1))
        
        # Draw Pokemon 2 stats polygon (if exists) - draw first so it's behind
        if self.stats2:
            points2 = []
            for i, key in enumerate(stat_keys):
                angle = math.radians(-90 + i * angle_step)
                stat_val = self.stats2.get(key, 0)
                stat_radius = (stat_val / self.max_stat) * radius
                x = center_x + stat_radius * math.cos(angle)
                y = center_y + stat_radius * math.sin(angle)
                points2.append(QPointF(x, y))
            
            polygon2 = QPolygonF(points2)
            color2 = QColor(POKEMON_COLORS["compare"])
            color2.setAlpha(80)
            painter.setBrush(QBrush(color2))
            painter.setPen(QPen(QColor(POKEMON_COLORS["compare"]), 2))
            painter.drawPolygon(polygon2)
        
        # Draw Pokemon 1 stats polygon
        points1 = []
        for i, key in enumerate(stat_keys):
            angle = math.radians(-90 + i * angle_step)
            stat_val = self.stats1.get(key, 0)
            stat_radius = (stat_val / self.max_stat) * radius
            x = center_x + stat_radius * math.cos(angle)
            y = center_y + stat_radius * math.sin(angle)
            points1.append(QPointF(x, y))
        
        polygon1 = QPolygonF(points1)
        color1 = QColor(POKEMON_COLORS["current"])
        color1.setAlpha(80)
        painter.setBrush(QBrush(color1))
        painter.setPen(QPen(QColor(POKEMON_COLORS["current"]), 2))
        painter.drawPolygon(polygon1)
        
        # Draw legend at bottom - Dark mode
        if self.stats2:
            legend_y = height - 25
            
            # Pokemon 1 legend
            painter.setPen(QPen(QColor(POKEMON_COLORS["current"]), 2))
            painter.setBrush(QBrush(QColor(POKEMON_COLORS["current"])))
            painter.drawEllipse(QPointF(center_x - 80, legend_y), 5, 5)
            painter.setPen(QColor("#E8E8E8"))
            painter.drawText(QRectF(center_x - 70, legend_y - 8, 60, 16), 
                           Qt.AlignmentFlag.AlignLeft, self.name1[:8])
            
            # Pokemon 2 legend
            painter.setPen(QPen(QColor(POKEMON_COLORS["compare"]), 2))
            painter.setBrush(QBrush(QColor(POKEMON_COLORS["compare"])))
            painter.drawEllipse(QPointF(center_x + 20, legend_y), 5, 5)
            painter.setPen(QColor("#E8E8E8"))
            painter.drawText(QRectF(center_x + 30, legend_y - 8, 60, 16), 
                           Qt.AlignmentFlag.AlignLeft, self.name2[:8])


class StatComparisonDialog(QDialog):
    """Dialog for comparing stats of two Pokemon side-by-side."""
    
    def __init__(self, current_pokemon: Dict, parent=None):
        super().__init__(parent or mw)
        self.current_pokemon = current_pokemon
        self.compare_pokemon = None
        self.all_pokemon = load_all_pokemon()
        
        self.setWindowTitle("⚔️ Stat Comparison Tool")
        self.setMinimumSize(750, 650)
        self.resize(850, 700)
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Header with Pokemon selection
        header = QHBoxLayout()
        header.setSpacing(20)
        
        # Current Pokemon label with styled box - Dark mode
        current_box = QFrame()
        current_box.setStyleSheet("""
            QFrame {
                background-color: #1E3A5F;
                border: 2px solid #00D9FF;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        current_box_layout = QVBoxLayout(current_box)
        current_box_layout.setContentsMargins(10, 5, 10, 5)
        
        current_title = QLabel("YOUR POKÉMON")
        current_title.setFont(QFont("Arial", 9))
        current_title.setStyleSheet("color: #00D9FF; font-weight: bold;")
        current_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_name = QLabel(f"🔵 {self.current_pokemon.get('name', 'Unknown').capitalize()}")
        current_name.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        current_name.setStyleSheet("color: #E8E8E8;")
        current_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_level = QLabel(f"Lv. {self.current_pokemon.get('level', 1)}")
        current_level.setFont(QFont("Arial", 11))
        current_level.setStyleSheet("color: #A0A0A0;")
        current_level.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        current_box_layout.addWidget(current_title)
        current_box_layout.addWidget(current_name)
        current_box_layout.addWidget(current_level)
        
        # VS label
        vs_label = QLabel("VS")
        vs_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        vs_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        vs_label.setStyleSheet("color: #FFD93D;")
        vs_label.setFixedWidth(60)
        
        # Compare Pokemon selector with styled box - Dark mode
        compare_box = QFrame()
        compare_box.setStyleSheet("""
            QFrame {
                background-color: #3D1F3D;
                border: 2px solid #FF6B9D;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        compare_box_layout = QVBoxLayout(compare_box)
        compare_box_layout.setContentsMargins(10, 5, 10, 5)
        
        compare_title = QLabel("COMPARE WITH")
        compare_title.setFont(QFont("Arial", 9))
        compare_title.setStyleSheet("color: #FF6B9D; font-weight: bold;")
        compare_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.pokemon_selector = QComboBox()
        self.pokemon_selector.setMinimumWidth(180)
        self.pokemon_selector.setStyleSheet("""
            QComboBox {
                padding: 5px 10px;
                border: 1px solid #555555;
                border-radius: 4px;
                background: #2D2D2D;
                color: #E8E8E8;
                font-size: 12px;
            }
            QComboBox:hover {
                border-color: #FF6B9D;
            }
            QComboBox QAbstractItemView {
                background: #2D2D2D;
                color: #E8E8E8;
                selection-background-color: #3D1F3D;
            }
        """)
        self.pokemon_selector.addItem("🔴 Select Pokémon...", None)
        
        for pokemon in self.all_pokemon:
            if pokemon.get('individual_id') != self.current_pokemon.get('individual_id'):
                display_name = pokemon.get('nickname') or pokemon.get('name', 'Unknown').capitalize()
                level = pokemon.get('level', 1)
                self.pokemon_selector.addItem(f"{display_name} (Lv.{level})", pokemon)
        
        self.pokemon_selector.currentIndexChanged.connect(self.on_pokemon_selected)
        
        self.compare_name_label = QLabel("—")
        self.compare_name_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.compare_name_label.setStyleSheet("color: #808080;")
        self.compare_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        compare_box_layout.addWidget(compare_title)
        compare_box_layout.addWidget(self.pokemon_selector)
        compare_box_layout.addWidget(self.compare_name_label)
        
        header.addWidget(current_box, 1)
        header.addWidget(vs_label)
        header.addWidget(compare_box, 1)
        
        layout.addLayout(header)
        
        # Tab widget for different stat views - Dark mode
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #444444;
                border-radius: 4px;
                background: #1E1E1E;
            }
            QTabBar::tab {
                padding: 8px 20px;
                margin-right: 2px;
                background: #2D2D2D;
                color: #A0A0A0;
                border: 1px solid #444444;
                border-bottom: none;
                border-radius: 4px 4px 0 0;
            }
            QTabBar::tab:selected {
                background: #1E1E1E;
                color: #E8E8E8;
                font-weight: bold;
            }
            QTabBar::tab:hover {
                background: #383838;
            }
        """)
        
        # Create tabs
        self.base_stats_tab = self.create_stats_tab("base_stats", "Base Stats", 255)
        self.calculated_tab = self.create_stats_tab("calculated", "Battle Stats", 500)
        self.iv_tab = self.create_stats_tab("iv", "Individual Values (IVs)", 31)
        self.ev_tab = self.create_stats_tab("ev", "Effort Values (EVs)", 252)
        
        self.tabs.addTab(self.base_stats_tab, "📊 Base Stats")
        self.tabs.addTab(self.calculated_tab, "⚔️ Battle Stats")
        self.tabs.addTab(self.iv_tab, "🧬 IVs")
        self.tabs.addTab(self.ev_tab, "💪 EVs")
        
        layout.addWidget(self.tabs, 1)
        
        # Close button - Dark mode
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 30px;
                background-color: #00D9FF;
                color: #1E1E1E;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00BFDF;
            }
        """)
        close_btn.clicked.connect(self.close)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Initial update
        self.update_all_tabs()
    
    def create_stats_tab(self, stat_key: str, title: str, max_stat: int) -> QWidget:
        """Create a tab with radar chart and stats table."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Store references for updating
        tab.stat_key = stat_key
        tab.max_stat = max_stat
        
        # Title - Dark mode
        title_label = QLabel(f"📈 {title}")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #E8E8E8;")
        layout.addWidget(title_label)
        
        # Description - Dark mode
        descriptions = {
            "base_stats": "Base stats determine a Pokémon's natural strengths. Higher base stats = stronger in that area.",
            "calculated": "Actual stats used in battle, calculated from Base Stats, Level, IVs, and EVs.",
            "iv": "Individual Values (0-31) are randomly determined when you catch a Pokémon. Higher = better potential.",
            "ev": "Effort Values (0-252, max 510 total) are gained from defeating Pokémon. Train to boost specific stats.",
        }
        desc_label = QLabel(descriptions.get(stat_key, ""))
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #A0A0A0; padding: 5px; background: #2D2D2D; border-radius: 4px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Content area with radar chart and table
        content = QHBoxLayout()
        content.setSpacing(20)
        
        # Radar chart
        tab.radar_chart = RadarChartWidget({}, None, "", "", max_stat)
        tab.radar_chart.setMinimumSize(300, 300)
        content.addWidget(tab.radar_chart, 1)
        
        # Stats comparison table
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_layout.setSpacing(5)
        
        table_title = QLabel("📋 Stat Breakdown")
        table_title.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        table_title.setStyleSheet("color: #E8E8E8;")
        table_layout.addWidget(table_title)
        
        tab.stats_grid = QGridLayout()
        tab.stats_grid.setSpacing(8)
        table_layout.addLayout(tab.stats_grid)
        table_layout.addStretch()
        
        content.addWidget(table_widget, 1)
        layout.addLayout(content, 1)
        
        return tab
    
    def on_pokemon_selected(self, index: int):
        """Handle Pokemon selection change."""
        self.compare_pokemon = self.pokemon_selector.itemData(index)
        
        if self.compare_pokemon:
            display_name = self.compare_pokemon.get('nickname') or self.compare_pokemon.get('name', 'Unknown').capitalize()
            self.compare_name_label.setText(f"🔴 {display_name}")
            self.compare_name_label.setStyleSheet("color: #FF6B9D; font-weight: bold;")
        else:
            self.compare_name_label.setText("—")
            self.compare_name_label.setStyleSheet("color: #808080;")
        
        self.update_all_tabs()
    
    def update_all_tabs(self):
        """Update all stat tabs with current data."""
        current_stats = self.calculate_stats(self.current_pokemon)
        compare_stats = self.calculate_stats(self.compare_pokemon) if self.compare_pokemon else None
        
        current_name = self.current_pokemon.get('name', 'Pokemon').capitalize()
        compare_name = self.compare_pokemon.get('name', 'Pokemon').capitalize() if self.compare_pokemon else None
        
        for i in range(self.tabs.count()):
            tab = self.tabs.widget(i)
            stat_key = tab.stat_key
            max_stat = tab.max_stat
            
            # Update radar chart
            stats1 = current_stats.get(stat_key, {})
            stats2 = compare_stats.get(stat_key, {}) if compare_stats else None
            
            tab.radar_chart.stats1 = stats1
            tab.radar_chart.stats2 = stats2
            tab.radar_chart.name1 = current_name
            tab.radar_chart.name2 = compare_name or ""
            tab.radar_chart.max_stat = max_stat
            tab.radar_chart.update()
            
            # Update stats table
            self.update_stats_grid(tab.stats_grid, stats1, stats2, current_name, compare_name)
    
    def update_stats_grid(self, grid: QGridLayout, stats1: Dict, stats2: Optional[Dict],
                          name1: str, name2: Optional[str]):
        """Update the stats comparison grid."""
        # Clear existing widgets
        while grid.count():
            child = grid.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Header row - Dark mode
        headers = ["Stat", f"🔵 {name1}"]
        if stats2:
            headers.append(f"🔴 {name2}")
            headers.append("Diff")
        
        for col, header in enumerate(headers):
            label = QLabel(header)
            label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("background: #383838; color: #E8E8E8; padding: 5px; border-radius: 3px;")
            grid.addWidget(label, 0, col)
        
        # Stat rows - Dark mode
        stat_keys = ["hp", "atk", "def", "spa", "spd", "spe"]
        for row, key in enumerate(stat_keys, 1):
            # Stat name with color
            name_label = QLabel(STAT_NAMES[key])
            name_label.setStyleSheet(f"color: {STAT_COLORS[key]}; font-weight: bold; padding: 5px; background: #2D2D2D; border-radius: 3px;")
            grid.addWidget(name_label, row, 0)
            
            # Current Pokemon value
            val1 = stats1.get(key, 0)
            val1_label = QLabel(str(val1))
            val1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val1_label.setStyleSheet("color: #00D9FF; font-weight: bold; padding: 5px; background: #1E3A5F; border-radius: 3px;")
            grid.addWidget(val1_label, row, 1)
            
            if stats2:
                # Compare Pokemon value
                val2 = stats2.get(key, 0)
                val2_label = QLabel(str(val2))
                val2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                val2_label.setStyleSheet("color: #FF6B9D; font-weight: bold; padding: 5px; background: #3D1F3D; border-radius: 3px;")
                grid.addWidget(val2_label, row, 2)
                
                # Difference
                diff = val1 - val2
                diff_text = f"+{diff}" if diff > 0 else str(diff)
                diff_label = QLabel(diff_text)
                diff_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if diff > 0:
                    diff_label.setStyleSheet("color: #6BCB77; font-weight: bold; background: #1F3D1F; padding: 5px; border-radius: 3px;")
                elif diff < 0:
                    diff_label.setStyleSheet("color: #FF6B6B; font-weight: bold; background: #3D1F1F; padding: 5px; border-radius: 3px;")
                else:
                    diff_label.setStyleSheet("color: #808080; background: #2D2D2D; padding: 5px; border-radius: 3px;")
                grid.addWidget(diff_label, row, 3)
        
        # Total row - Dark mode
        total_row = len(stat_keys) + 1
        total_label = QLabel("TOTAL")
        total_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        total_label.setStyleSheet("background: #FFD93D; color: #1E1E1E; padding: 5px; border-radius: 3px;")
        grid.addWidget(total_label, total_row, 0)
        
        total1 = sum(stats1.get(k, 0) for k in stat_keys)
        total1_label = QLabel(str(total1))
        total1_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        total1_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        total1_label.setStyleSheet("color: #00D9FF; background: #1E3A5F; padding: 5px; border-radius: 3px;")
        grid.addWidget(total1_label, total_row, 1)
        
        if stats2:
            total2 = sum(stats2.get(k, 0) for k in stat_keys)
            total2_label = QLabel(str(total2))
            total2_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            total2_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            total2_label.setStyleSheet("color: #FF6B9D; background: #3D1F3D; padding: 5px; border-radius: 3px;")
            grid.addWidget(total2_label, total_row, 2)
            
            total_diff = total1 - total2
            diff_text = f"+{total_diff}" if total_diff > 0 else str(total_diff)
            total_diff_label = QLabel(diff_text)
            total_diff_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            total_diff_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            if total_diff > 0:
                total_diff_label.setStyleSheet("color: #1E1E1E; background: #6BCB77; padding: 5px; border-radius: 3px;")
            elif total_diff < 0:
                total_diff_label.setStyleSheet("color: #FFFFFF; background: #FF6B6B; padding: 5px; border-radius: 3px;")
            else:
                total_diff_label.setStyleSheet("color: #A0A0A0; background: #383838; padding: 5px; border-radius: 3px;")
            grid.addWidget(total_diff_label, total_row, 3)
    
    def calculate_stats(self, pokemon: Optional[Dict]) -> Dict:
        """Calculate all stats for a Pokemon."""
        if not pokemon:
            return {}
        
        level = pokemon.get('level', 1)
        base_stats = pokemon.get('base_stats') or pokemon.get('stats') or {}
        iv = pokemon.get('iv') or {}
        ev = pokemon.get('ev') or {}
        
        # Calculate actual stats
        calculated = {}
        for stat_key in ["hp", "atk", "def", "spa", "spd", "spe"]:
            base = base_stats.get(stat_key, 0)
            iv_val = iv.get(stat_key, 0)
            ev_val = ev.get(stat_key, 0)
            calculated[stat_key] = PokemonObject.calc_stat(stat_key, base, level, iv_val, ev_val, "serious")
        
        return {
            "base_stats": base_stats,
            "iv": iv,
            "ev": ev,
            "calculated": calculated,
        }


def show_stat_comparison(pokemon_data: Dict, parent=None):
    """Show the stat comparison dialog."""
    dialog = StatComparisonDialog(pokemon_data, parent)
    dialog.exec()
