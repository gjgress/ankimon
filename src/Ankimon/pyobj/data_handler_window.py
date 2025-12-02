from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QTextEdit, QScrollArea, QFrame, QGroupBox, QPushButton,
    QTabWidget, QSplitter, QTreeWidget, QTreeWidgetItem, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor
from aqt import mw
from typing import Optional, Dict, Any, List
import json

class DataHandlerWindow(QMainWindow):
    """
    A debug window for viewing and inspecting Ankimon's internal data structures.
    
    This window provides a comprehensive view of all data managed by the DataHandler:
    - Pokemon collection (mypokemon)
    - Main/active Pokemon (mainpokemon)
    - Inventory items
    - Team configuration
    - Achievement badges
    - Raw data entries
    
    The window uses tabs for organization and provides JSON formatting for complex data.
    Supports both light and dark themes.
    
    Attributes:
        data_handler: The DataHandler object containing all game data
        tab_widget: QTabWidget for organizing different data views
        
    Example:
        >>> data_window = DataHandlerWindow(data_handler=data_handler_obj)
        >>> data_window.show_window()
    """
    
    def __init__(self, data_handler) -> None:
        """
        Initialize the DataHandlerWindow.
        
        Args:
            data_handler: DataHandler object containing all Ankimon game data.
                         Must have attributes: mypokemon, mainpokemon, items, team, 
                         data, badges, and methods assign_unique_ids, assign_new_variables,
                         save_file.
        """
        super().__init__()
        self.data_handler = data_handler
        self.tab_widget: Optional[QTabWidget] = None
        self.init_ui()

    def get_text_color(self) -> str:
        """
        Returns the appropriate text color based on Anki's current theme.
        
        Returns:
            str: "white" for dark mode, "black" for light mode
        """
        return "white" if mw.pm.night_mode() else "black"
    
    def get_secondary_color(self) -> str:
        """
        Returns a secondary/muted text color based on theme.
        
        Returns:
            str: Muted gray color appropriate for the current theme
        """
        return "#b0b0b0" if mw.pm.night_mode() else "#666666"
    
    def get_background_color(self) -> str:
        """
        Returns the appropriate background color based on theme.
        
        Returns:
            str: Background color hex string
        """
        return "#2b2b2b" if mw.pm.night_mode() else "#f5f5f5"
    
    def get_card_background(self) -> str:
        """
        Returns the card/panel background color based on theme.
        
        Returns:
            str: Card background color hex string
        """
        return "#363636" if mw.pm.night_mode() else "#ffffff"
    
    def get_accent_color(self) -> str:
        """
        Returns the accent color for highlights.
        
        Returns:
            str: Accent color hex string (Pokemon blue)
        """
        return "#4a9eff"
    
    def get_border_color(self) -> str:
        """
        Returns border color based on theme.
        
        Returns:
            str: Border color hex string
        """
        return "#4a4a4a" if mw.pm.night_mode() else "#ddd"

    def get_text_edit_style(self) -> str:
        """
        Returns stylesheet for QTextEdit widgets.
        
        Returns:
            str: Complete stylesheet for read-only text editors
        """
        return f"""
            QTextEdit {{
                background-color: {self.get_card_background()};
                color: {self.get_text_color()};
                border: 1px solid {self.get_border_color()};
                border-radius: 6px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }}
        """
    
    def get_tab_style(self) -> str:
        """
        Returns stylesheet for QTabWidget.
        
        Returns:
            str: Complete stylesheet for tabs
        """
        bg = self.get_background_color()
        card_bg = self.get_card_background()
        text = self.get_text_color()
        accent = self.get_accent_color()
        border = self.get_border_color()
        
        return f"""
            QTabWidget::pane {{
                border: 1px solid {border};
                border-radius: 6px;
                background: {card_bg};
            }}
            QTabBar::tab {{
                background: {bg};
                color: {text};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }}
            QTabBar::tab:selected {{
                background: {card_bg};
                color: {accent};
                font-weight: bold;
            }}
            QTabBar::tab:hover {{
                background: {card_bg};
            }}
        """
    
    def get_group_box_style(self, title_color: str = None) -> str:
        """
        Returns stylesheet for QGroupBox with consistent styling.
        
        Args:
            title_color: Optional custom color for the title
            
        Returns:
            str: Complete stylesheet for QGroupBox
        """
        tc = title_color or self.get_text_color()
        bg = self.get_card_background()
        border = self.get_border_color()
        
        return f"""
            QGroupBox {{
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 8px;
                margin-top: 16px;
                padding: 12px;
                padding-top: 24px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                left: 12px;
                padding: 0 8px;
                color: {tc};
                font-weight: bold;
                font-size: 13px;
            }}
        """

    def init_ui(self) -> None:
        """
        Initializes the main UI layout with tabs for different data categories.
        
        Creates a tabbed interface with:
        - Overview tab: Summary counts of all data
        - Pokemon tab: mypokemon and mainpokemon data
        - Items tab: Inventory items
        - Team tab: Current team configuration
        - Badges tab: Achievement badges
        - Raw Data tab: Full raw data dump
        """
        self.setWindowTitle('Ankimon Data Viewer')
        self.setMinimumSize(800, 600)
        
        # Central widget with main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Ankimon Data Viewer")
        title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {self.get_accent_color()};")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setFont(QFont("Segoe UI", 10))
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.get_accent_color()};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #3a8eef;
            }}
        """)
        refresh_btn.clicked.connect(self.refresh_data)
        header_layout.addWidget(refresh_btn)
        
        main_layout.addLayout(header_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {self.get_border_color()};")
        separator.setFixedHeight(1)
        main_layout.addWidget(separator)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self.get_tab_style())
        self.tab_widget.setFont(QFont("Segoe UI", 10))
        
        # Create tabs
        self.create_overview_tab()
        self.create_pokemon_tab()
        self.create_items_tab()
        self.create_team_tab()
        self.create_badges_tab()
        self.create_raw_data_tab()
        
        main_layout.addWidget(self.tab_widget, 1)
        
        # Apply background
        central_widget.setStyleSheet(f"background-color: {self.get_background_color()};")
        self.setCentralWidget(central_widget)
        
        # Process data (assign IDs, etc.)
        self._process_data()
    
    def _process_data(self) -> None:
        """
        Processes the data handler's data (assign IDs, save files, etc.).
        
        This is called during initialization and refresh to ensure data integrity.
        """
        for attr_name in ['mypokemon', 'mainpokemon']:
            if hasattr(self.data_handler, attr_name):
                content = getattr(self.data_handler, attr_name)
                self.data_handler.assign_unique_ids(content)
                self.data_handler.assign_new_variables(content)
                self.data_handler.save_file(attr_name)
    
    def create_overview_tab(self) -> None:
        """
        Creates the Overview tab with summary statistics.
        
        Shows counts and quick stats for all data categories.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Stats grid
        stats_group = QGroupBox("Data Summary")
        stats_group.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        stats_group.setStyleSheet(self.get_group_box_style())
        
        stats_layout = QVBoxLayout()
        
        # Calculate counts
        stats_data = [
            ("My Pokemon", self._get_count("mypokemon")),
            ("Main Pokemon", self._get_count("mainpokemon")),
            ("Items", self._get_count("items")),
            ("Team Size", self._get_count("team")),
            ("Badges", self._get_count("badges")),
            ("Data Entries", self._get_count("data")),
        ]
        
        for label_text, count in stats_data:
            row = QHBoxLayout()
            
            label = QLabel(label_text)
            label.setFont(QFont("Segoe UI", 12))
            label.setStyleSheet(f"color: {self.get_text_color()};")
            row.addWidget(label)
            
            row.addStretch()
            
            count_label = QLabel(str(count))
            count_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            count_label.setStyleSheet(f"color: {self.get_accent_color()};")
            row.addWidget(count_label)
            
            stats_layout.addLayout(row)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Overview")
    
    def _get_count(self, attr_name: str) -> int:
        """
        Gets the count of items in a data attribute.
        
        Args:
            attr_name: Name of the attribute to count
            
        Returns:
            int: Number of items (0 if not a list/dict or doesn't exist)
        """
        if hasattr(self.data_handler, attr_name):
            content = getattr(self.data_handler, attr_name)
            if isinstance(content, (list, dict)):
                return len(content)
            elif content is not None:
                return 1
        return 0
    
    def create_pokemon_tab(self) -> None:
        """
        Creates the Pokemon tab with mypokemon and mainpokemon data.
        
        Uses a tree view for Pokemon data with expandable entries.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Splitter for my pokemon and main pokemon
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # My Pokemon section
        my_pokemon_group = QGroupBox("My Pokemon Collection")
        my_pokemon_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        my_pokemon_group.setStyleSheet(self.get_group_box_style("#69db7c"))
        my_layout = QVBoxLayout()
        
        my_pokemon_tree = self._create_data_tree(
            getattr(self.data_handler, 'mypokemon', [])
        )
        my_layout.addWidget(my_pokemon_tree)
        my_pokemon_group.setLayout(my_layout)
        splitter.addWidget(my_pokemon_group)
        
        # Main Pokemon section
        main_pokemon_group = QGroupBox("Main Pokemon")
        main_pokemon_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        main_pokemon_group.setStyleSheet(self.get_group_box_style("#ffd43b"))
        main_layout = QVBoxLayout()
        
        main_pokemon_tree = self._create_data_tree(
            getattr(self.data_handler, 'mainpokemon', [])
        )
        main_layout.addWidget(main_pokemon_tree)
        main_pokemon_group.setLayout(main_layout)
        splitter.addWidget(main_pokemon_group)
        
        layout.addWidget(splitter)
        
        self.tab_widget.addTab(tab, "Pokemon")
    
    def _create_data_tree(self, data: Any) -> QTreeWidget:
        """
        Creates a tree widget for displaying hierarchical data.
        
        Args:
            data: List or dict of data to display
            
        Returns:
            QTreeWidget: Configured tree widget with data
        """
        tree = QTreeWidget()
        tree.setHeaderLabels(["Property", "Value"])
        tree.setAlternatingRowColors(True)
        tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: {self.get_card_background()};
                color: {self.get_text_color()};
                border: 1px solid {self.get_border_color()};
                border-radius: 6px;
                padding: 4px;
            }}
            QTreeWidget::item {{
                padding: 4px;
            }}
            QTreeWidget::item:alternate {{
                background-color: {self.get_background_color()};
            }}
            QHeaderView::section {{
                background-color: {self.get_background_color()};
                color: {self.get_text_color()};
                padding: 6px;
                border: none;
                font-weight: bold;
            }}
        """)
        
        if isinstance(data, list):
            for i, item in enumerate(data):
                parent = QTreeWidgetItem(tree, [f"Item {i + 1}", ""])
                self._add_tree_items(parent, item)
        elif isinstance(data, dict):
            for key, value in data.items():
                parent = QTreeWidgetItem(tree, [str(key), ""])
                self._add_tree_items(parent, value)
        else:
            QTreeWidgetItem(tree, ["Value", str(data)])
        
        tree.expandToDepth(0)
        tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        
        return tree
    
    def _add_tree_items(self, parent: QTreeWidgetItem, data: Any) -> None:
        """
        Recursively adds items to a tree widget parent.
        
        Args:
            parent: Parent tree widget item
            data: Data to add as children
        """
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    child = QTreeWidgetItem(parent, [str(key), ""])
                    self._add_tree_items(child, value)
                else:
                    QTreeWidgetItem(parent, [str(key), str(value)])
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    child = QTreeWidgetItem(parent, [f"[{i}]", ""])
                    self._add_tree_items(child, item)
                else:
                    QTreeWidgetItem(parent, [f"[{i}]", str(item)])
        else:
            QTreeWidgetItem(parent, ["Value", str(data)])
    
    def create_items_tab(self) -> None:
        """
        Creates the Items tab with inventory data.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        
        items_group = QGroupBox("Inventory Items")
        items_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        items_group.setStyleSheet(self.get_group_box_style("#74c0fc"))
        items_layout = QVBoxLayout()
        
        items_tree = self._create_data_tree(
            getattr(self.data_handler, 'items', [])
        )
        items_layout.addWidget(items_tree)
        items_group.setLayout(items_layout)
        
        layout.addWidget(items_group)
        
        self.tab_widget.addTab(tab, "Items")
    
    def create_team_tab(self) -> None:
        """
        Creates the Team tab with team configuration data.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        
        team_group = QGroupBox("Team Configuration")
        team_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        team_group.setStyleSheet(self.get_group_box_style("#da77f2"))
        team_layout = QVBoxLayout()
        
        team_tree = self._create_data_tree(
            getattr(self.data_handler, 'team', [])
        )
        team_layout.addWidget(team_tree)
        team_group.setLayout(team_layout)
        
        layout.addWidget(team_group)
        
        self.tab_widget.addTab(tab, "Team")
    
    def create_badges_tab(self) -> None:
        """
        Creates the Badges tab with achievement badge data.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        
        badges_group = QGroupBox("Achievement Badges")
        badges_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        badges_group.setStyleSheet(self.get_group_box_style("#ffd43b"))
        badges_layout = QVBoxLayout()
        
        badges_tree = self._create_data_tree(
            getattr(self.data_handler, 'badges', [])
        )
        badges_layout.addWidget(badges_tree)
        badges_group.setLayout(badges_layout)
        
        layout.addWidget(badges_group)
        
        self.tab_widget.addTab(tab, "Badges")
    
    def create_raw_data_tab(self) -> None:
        """
        Creates the Raw Data tab with full JSON dump of all data.
        
        Provides scrollable, formatted JSON view of the complete data structure.
        """
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        
        # Info label
        info_label = QLabel("Complete raw data dump (read-only, JSON formatted)")
        info_label.setFont(QFont("Segoe UI", 10))
        info_label.setStyleSheet(f"color: {self.get_secondary_color()}; padding: 4px;")
        layout.addWidget(info_label)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # List of attributes to display
        attributes = ['mypokemon', 'mainpokemon', 'items', 'team', 'badges', 'data']
        
        for attr_name in attributes:
            if hasattr(self.data_handler, attr_name):
                group = QGroupBox(f"{attr_name}")
                group.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                group.setStyleSheet(self.get_group_box_style())
                group_layout = QVBoxLayout()
                
                text_edit = QTextEdit()
                text_edit.setReadOnly(True)
                text_edit.setStyleSheet(self.get_text_edit_style())
                text_edit.setMinimumHeight(150)
                text_edit.setMaximumHeight(300)
                
                content = getattr(self.data_handler, attr_name)
                try:
                    formatted = json.dumps(content, indent=2, default=str)
                except:
                    formatted = str(content)
                text_edit.setPlainText(formatted)
                
                group_layout.addWidget(text_edit)
                group.setLayout(group_layout)
                scroll_layout.addWidget(group)
        
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)
        
        self.tab_widget.addTab(tab, "Raw Data")
    
    def refresh_data(self) -> None:
        """
        Refreshes all data displays by reinitializing the UI.
        
        Called when the refresh button is clicked.
        """
        # Remember current tab
        current_tab = self.tab_widget.currentIndex() if self.tab_widget else 0
        
        # Clear and recreate tabs
        if self.tab_widget:
            self.tab_widget.clear()
            self.create_overview_tab()
            self.create_pokemon_tab()
            self.create_items_tab()
            self.create_team_tab()
            self.create_badges_tab()
            self.create_raw_data_tab()
            
            # Restore tab selection
            self.tab_widget.setCurrentIndex(current_tab)

    def show_window(self) -> None:
        """
        Shows the data viewer window.
        
        Refreshes data before showing to ensure up-to-date information.
        """
        self.refresh_data()
        self.show()

