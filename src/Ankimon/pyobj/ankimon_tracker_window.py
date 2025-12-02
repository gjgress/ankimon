from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QGridLayout, QSpacerItem, QSizePolicy, QGroupBox, QFrame,
    QScrollArea, QPushButton, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
from aqt import mw
from typing import Optional, Dict, Any

class AnkimonTrackerWindow:
    """
    A debug window that displays real-time tracking statistics for Ankimon gameplay.
    
    This window provides live updates of:
    - Session statistics (total reviews, streaks, multipliers, timers)
    - Main Pokémon stats during battle
    - Enemy Pokémon stats during battle
    - Card rating breakdowns
    
    The window updates every second via a QTimer and supports both light and dark themes.
    
    Attributes:
        tracker: AnkimonTracker object containing all gameplay statistics
        mw: Anki's main window reference
        window: The QWidget window container (created on first show)
        layout: Main QVBoxLayout for the window
        stats_labels: Dictionary mapping stat keys to their QLabel widgets
        title_label: QLabel for the window title
        previous_stats: Dictionary for tracking stat changes (for highlighting)
        timer: QTimer for real-time updates
        
    Example:
        >>> tracker_window = AnkimonTrackerWindow(tracker=ankimon_tracker_obj)
        >>> tracker_window.toggle_window()  # Show/hide the window
    """
    
    def __init__(self, tracker) -> None:
        """
        Initialize the AnkimonTrackerWindow.
        
        Args:
            tracker: AnkimonTracker object containing gameplay statistics to display.
                    Must have get_stats(), get_main_pokemon_stats(), and 
                    get_enemy_pokemon_stats() methods.
        """
        self.tracker = tracker
        self.mw = mw
        self.window: Optional[QWidget] = None
        self.layout: Optional[QVBoxLayout] = None
        self.stats_labels: Dict[str, QLabel] = {}
        self.title_label: Optional[QLabel] = None
        self.previous_stats: Dict[str, Any] = {}
        self.timer: Optional[QTimer] = None
        
        # Group box references for updating
        self.main_pokemon_box: Optional[QGroupBox] = None
        self.enemy_pokemon_box: Optional[QGroupBox] = None
        self.session_stats_box: Optional[QGroupBox] = None
        self.card_ratings_box: Optional[QGroupBox] = None

    def get_text_color(self) -> str:
        """
        Returns the appropriate text color based on Anki's current theme.
        
        Returns:
            str: "white" for dark mode, "black" for light mode
        """
        return "white" if self.mw.pm.night_mode() else "black"
    
    def get_secondary_color(self) -> str:
        """
        Returns a secondary/muted text color based on theme.
        
        Returns:
            str: Muted gray color appropriate for the current theme
        """
        return "#b0b0b0" if self.mw.pm.night_mode() else "#666666"
    
    def get_background_color(self) -> str:
        """
        Returns the appropriate background color based on theme.
        
        Returns:
            str: Background color hex string
        """
        return "#2b2b2b" if self.mw.pm.night_mode() else "#f5f5f5"
    
    def get_card_background(self) -> str:
        """
        Returns the card/panel background color based on theme.
        
        Returns:
            str: Card background color hex string
        """
        return "#363636" if self.mw.pm.night_mode() else "#ffffff"
    
    def get_accent_color(self) -> str:
        """
        Returns the accent color for highlights.
        
        Returns:
            str: Accent color hex string
        """
        return "#4a9eff"  # Pokemon blue
    
    def get_border_color(self) -> str:
        """
        Returns border color based on theme.
        
        Returns:
            str: Border color hex string
        """
        return "#4a4a4a" if self.mw.pm.night_mode() else "#ddd"
    
    def _get_egg_reward_status(self) -> Dict[str, Any]:
        """
        Get the current egg reward system status.
        
        Returns:
            Dict containing consecutive_days, progress_percent, total_eggs_awarded
        """
        try:
            from .egg_reward_system import get_egg_reward_status
            return get_egg_reward_status()
        except ImportError:
            return {
                "consecutive_days": 0,
                "days_until_egg": 3,
                "total_eggs_awarded": 0,
                "last_usage_date": None,
                "progress_percent": 0,
            }

    def get_group_box_style(self, title_color: str = None) -> str:
        """
        Returns stylesheet for QGroupBox with consistent styling.
        
        Args:
            title_color: Optional custom color for the title. Defaults to text color.
            
        Returns:
            str: Complete stylesheet for QGroupBox
        """
        tc = title_color or self.get_text_color()
        bg = self.get_card_background()
        border = "#4a4a4a" if self.mw.pm.night_mode() else "#ddd"
        
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

    def create_stat_label(self, key: str, value: Any, is_pokemon_stat: bool = False) -> QLabel:
        """
        Creates a styled stat label.
        
        Args:
            key: The stat name/key
            value: The stat value
            is_pokemon_stat: Whether this is a Pokemon stat (for formatting)
            
        Returns:
            QLabel: Styled label widget
        """
        if is_pokemon_stat:
            stat_name = key.split("_", 2)[-1].capitalize()
            display_text = f"{stat_name}: {value if value is not None else 'N/A'}"
        else:
            display_text = f"{self._format_key(key)}: {self._format_value(key, value)}"
        
        label = QLabel(display_text)
        label.setFont(QFont("Segoe UI", 11))
        label.setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 8px;")
        return label
    
    def _format_key(self, key: str) -> str:
        """
        Formats a stat key for display.
        
        Args:
            key: Raw stat key name
            
        Returns:
            str: Formatted display name
        """
        key_mappings = {
            "total_reviews": "Total Reviews",
            "card_streak": "Card Streak",
            "multiplier": "Multiplier",
            "card_time_elapsed": "Card Time",
            "session_time": "Session Time",
            "current_mode": "Current Mode",
            "streak_days": "Streak Days",
        }
        return key_mappings.get(key, key.replace("_", " ").title())
    
    def _format_value(self, key: str, value: Any) -> str:
        """
        Formats a stat value for display.
        
        Args:
            key: The stat key (for context)
            value: The raw value
            
        Returns:
            str: Formatted value string
        """
        if key in ["card_time_elapsed", "session_time"]:
            # Format as mm:ss
            if isinstance(value, (int, float)):
                minutes = int(value) // 60
                seconds = int(value) % 60
                return f"{minutes:02d}:{seconds:02d}"
        elif key == "multiplier":
            if isinstance(value, (int, float)):
                return f"{value:.2f}x"
        elif key == "streak_days":
            if isinstance(value, list) and len(value) > 0:
                if isinstance(value[0], list) and len(value[0]) > 1:
                    return f"{value[0][1]} days"
                return str(value)
        elif key == "card_ratings_count" or key == "multiplier_card_ratings_count":
            if isinstance(value, dict):
                return f"A:{value.get('again', 0)} H:{value.get('hard', 0)} G:{value.get('good', 0)} E:{value.get('easy', 0)}"
        return str(value)

    def create_gui(self) -> None:
        """
        Creates and sets up the improved GUI layout for the tracker stats.
        
        The layout consists of:
        - Header with title and session timer
        - Left column: Session stats and card ratings
        - Right column: Main Pokemon and Enemy Pokemon stats
        
        All styled with consistent colors and modern design.
        """
        if not self.window:
            self.window = QWidget(self.mw)
            self.window.setMinimumSize(650, 450)
            
            # Main container with background
            main_container = QVBoxLayout()
            main_container.setContentsMargins(16, 16, 16, 16)
            main_container.setSpacing(12)
            
            # Header section
            header_frame = QFrame()
            header_layout = QHBoxLayout(header_frame)
            header_layout.setContentsMargins(0, 0, 0, 8)
            
            # Title with icon
            self.title_label = QLabel("Ankimon Tracker")
            self.title_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
            self.title_label.setStyleSheet(f"color: {self.get_accent_color()}; padding: 4px;")
            header_layout.addWidget(self.title_label)
            
            header_layout.addStretch()
            
            # Session timer display
            self.session_timer_label = QLabel("00:00")
            self.session_timer_label.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
            self.session_timer_label.setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 12px; background-color: {self.get_card_background()}; border-radius: 6px;")
            header_layout.addWidget(self.session_timer_label)
            
            main_container.addWidget(header_frame)
            
            # Separator line
            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setStyleSheet(f"background-color: {self.get_secondary_color()};")
            separator.setFixedHeight(1)
            main_container.addWidget(separator)
            
            # Content area with scroll
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QFrame.Shape.NoFrame)
            scroll_area.setStyleSheet("QScrollArea { background: transparent; }")
            
            scroll_content = QWidget()
            scroll_layout = QHBoxLayout(scroll_content)
            scroll_layout.setSpacing(16)
            
            # Left column: Session stats
            left_column = QVBoxLayout()
            left_column.setSpacing(12)
            
            # Session Statistics GroupBox
            self.session_stats_box = QGroupBox("Session Statistics")
            self.session_stats_box.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.session_stats_box.setStyleSheet(self.get_group_box_style())
            session_layout = QVBoxLayout()
            session_layout.setSpacing(6)
            
            stats = self.tracker.get_stats()
            session_stats_keys = ["total_reviews", "card_streak", "multiplier", "current_mode"]
            
            for key in session_stats_keys:
                if key in stats:
                    label = self.create_stat_label(key, stats[key])
                    session_layout.addWidget(label)
                    self.stats_labels[key] = label
            
            self.session_stats_box.setLayout(session_layout)
            left_column.addWidget(self.session_stats_box)
            
            # Card Ratings GroupBox
            self.card_ratings_box = QGroupBox("Card Ratings")
            self.card_ratings_box.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.card_ratings_box.setStyleSheet(self.get_group_box_style())
            ratings_layout = QGridLayout()
            ratings_layout.setSpacing(8)
            
            ratings = stats.get("card_ratings_count", {})
            rating_colors = {
                "again": "#ff6b6b",
                "hard": "#ffa94d", 
                "good": "#69db7c",
                "easy": "#4dabf7"
            }
            
            for i, (rating, count) in enumerate(ratings.items()):
                rating_label = QLabel(f"{rating.upper()}")
                rating_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                rating_label.setStyleSheet(f"color: {rating_colors.get(rating, self.get_text_color())}; padding: 4px;")
                rating_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                count_label = QLabel(str(count))
                count_label.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
                count_label.setStyleSheet(f"color: {self.get_text_color()}; padding: 4px;")
                count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                ratings_layout.addWidget(rating_label, 0, i)
                ratings_layout.addWidget(count_label, 1, i)
                self.stats_labels[f"rating_{rating}"] = count_label
            
            self.card_ratings_box.setLayout(ratings_layout)
            left_column.addWidget(self.card_ratings_box)
            
            # Egg Reward Progress GroupBox
            self.egg_reward_box = QGroupBox("Egg Reward Progress")
            self.egg_reward_box.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.egg_reward_box.setStyleSheet(self.get_group_box_style("#ffd43b"))
            egg_layout = QVBoxLayout()
            egg_layout.setSpacing(8)
            
            # Get egg reward status
            egg_status = self._get_egg_reward_status()
            
            # Progress label
            egg_progress_text = f"Streak: {egg_status['consecutive_days']}/3 days"
            self.egg_progress_label = QLabel(egg_progress_text)
            self.egg_progress_label.setFont(QFont("Segoe UI", 11))
            self.egg_progress_label.setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 8px;")
            egg_layout.addWidget(self.egg_progress_label)
            
            # Progress bar
            self.egg_progress_bar = QProgressBar()
            self.egg_progress_bar.setRange(0, 100)
            self.egg_progress_bar.setValue(egg_status['progress_percent'])
            self.egg_progress_bar.setTextVisible(True)
            self.egg_progress_bar.setFormat(f"{egg_status['progress_percent']}%")
            self.egg_progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid {self.get_border_color()};
                    border-radius: 6px;
                    background-color: {self.get_card_background()};
                    text-align: center;
                    color: {self.get_text_color()};
                    height: 20px;
                }}
                QProgressBar::chunk {{
                    background-color: #ffd43b;
                    border-radius: 5px;
                }}
            """)
            egg_layout.addWidget(self.egg_progress_bar)
            
            # Total eggs earned
            total_eggs_text = f"Total Eggs Earned: {egg_status['total_eggs_awarded']}"
            self.total_eggs_label = QLabel(total_eggs_text)
            self.total_eggs_label.setFont(QFont("Segoe UI", 10))
            self.total_eggs_label.setStyleSheet(f"color: {self.get_secondary_color()}; padding: 4px 8px;")
            egg_layout.addWidget(self.total_eggs_label)
            
            self.egg_reward_box.setLayout(egg_layout)
            left_column.addWidget(self.egg_reward_box)
            
            left_column.addStretch()
            scroll_layout.addLayout(left_column)
            
            # Right column: Pokemon stats
            right_column = QVBoxLayout()
            right_column.setSpacing(12)
            
            # Main Pokemon GroupBox
            self.main_pokemon_box = QGroupBox("Main Pokemon")
            self.main_pokemon_box.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.main_pokemon_box.setStyleSheet(self.get_group_box_style("#69db7c"))
            main_pkmn_layout = QGridLayout()
            main_pkmn_layout.setSpacing(6)
            
            main_pokemon_stats = self.tracker.get_main_pokemon_stats()
            if main_pokemon_stats:
                if self.tracker.main_pokemon:
                    self.main_pokemon_box.setTitle(f"{self.tracker.main_pokemon.name}")
                row, col = 0, 0
                for key, value in main_pokemon_stats.items():
                    label = self.create_stat_label(f"main_pokemon_{key}", value, is_pokemon_stat=True)
                    main_pkmn_layout.addWidget(label, row, col)
                    self.stats_labels[f"main_pokemon_{key}"] = label
                    col += 1
                    if col == 2:
                        col = 0
                        row += 1
            else:
                no_data_label = QLabel("No Pokémon in battle")
                no_data_label.setStyleSheet(f"color: {self.get_secondary_color()}; font-style: italic; padding: 8px;")
                main_pkmn_layout.addWidget(no_data_label, 0, 0)
            
            self.main_pokemon_box.setLayout(main_pkmn_layout)
            right_column.addWidget(self.main_pokemon_box)
            
            # Enemy Pokemon GroupBox
            self.enemy_pokemon_box = QGroupBox("Enemy Pokemon")
            self.enemy_pokemon_box.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            self.enemy_pokemon_box.setStyleSheet(self.get_group_box_style("#ff6b6b"))
            enemy_pkmn_layout = QGridLayout()
            enemy_pkmn_layout.setSpacing(6)
            
            enemy_pokemon_stats = self.tracker.get_enemy_pokemon_stats()
            if enemy_pokemon_stats:
                if self.tracker.enemy_pokemon:
                    self.enemy_pokemon_box.setTitle(f"{self.tracker.enemy_pokemon.name}")
                row, col = 0, 0
                for key, value in enemy_pokemon_stats.items():
                    label = self.create_stat_label(f"enemy_pokemon_{key}", value, is_pokemon_stat=True)
                    enemy_pkmn_layout.addWidget(label, row, col)
                    self.stats_labels[f"enemy_pokemon_{key}"] = label
                    col += 1
                    if col == 2:
                        col = 0
                        row += 1
            else:
                no_data_label = QLabel("No enemy encountered")
                no_data_label.setStyleSheet(f"color: {self.get_secondary_color()}; font-style: italic; padding: 8px;")
                enemy_pkmn_layout.addWidget(no_data_label, 0, 0)
            
            self.enemy_pokemon_box.setLayout(enemy_pkmn_layout)
            right_column.addWidget(self.enemy_pokemon_box)
            
            right_column.addStretch()
            scroll_layout.addLayout(right_column)
            
            scroll_area.setWidget(scroll_content)
            main_container.addWidget(scroll_area, 1)
            
            # Footer with refresh info
            footer_label = QLabel("Auto-refreshes every second")
            footer_label.setFont(QFont("Segoe UI", 9))
            footer_label.setStyleSheet(f"color: {self.get_secondary_color()}; padding: 4px;")
            footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_container.addWidget(footer_label)
            
            self.window.setLayout(main_container)
            self.window.setWindowTitle("Ankimon Tracker")
            self.window.setStyleSheet(f"background-color: {self.get_background_color()};")
            self.window.show()

    def update_stats(self) -> None:
        """
        Updates all displayed stats in real-time.
        
        This method is called every second by the timer. It:
        - Updates the session timer display
        - Refreshes all stat labels with current values
        - Updates Pokemon names in group box titles
        - Applies theme-appropriate colors
        
        Note:
            Creates new labels for stats that don't have existing labels.
        """
        # Update the session timer in header
        if hasattr(self, 'session_timer_label'):
            session_time = self.tracker.session_time_elapsed
            minutes = session_time // 60
            seconds = session_time % 60
            self.session_timer_label.setText(f"{minutes:02d}:{seconds:02d}")
            self.session_timer_label.setStyleSheet(
                f"color: {self.get_text_color()}; padding: 4px 12px; "
                f"background-color: {self.get_card_background()}; border-radius: 6px;"
            )

        stats = self.tracker.get_stats()
        main_pokemon_stats = self.tracker.get_main_pokemon_stats()
        enemy_pokemon_stats = self.tracker.get_enemy_pokemon_stats()
        
        # Update session stats
        session_stats_keys = ["total_reviews", "card_streak", "multiplier", "current_mode"]
        for key in session_stats_keys:
            if key in self.stats_labels and key in stats:
                self.stats_labels[key].setText(f"{self._format_key(key)}: {self._format_value(key, stats[key])}")
                self.stats_labels[key].setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 8px;")
        
        # Update card ratings
        ratings = stats.get("card_ratings_count", {})
        for rating, count in ratings.items():
            label_key = f"rating_{rating}"
            if label_key in self.stats_labels:
                self.stats_labels[label_key].setText(str(count))
                self.stats_labels[label_key].setStyleSheet(f"color: {self.get_text_color()}; padding: 4px;")
        
        # Update Pokemon group box titles
        if self.main_pokemon_box and self.tracker.main_pokemon:
            self.main_pokemon_box.setTitle(f"{self.tracker.main_pokemon.name}")
            self.main_pokemon_box.setStyleSheet(self.get_group_box_style("#69db7c"))
        
        if self.enemy_pokemon_box and self.tracker.enemy_pokemon:
            self.enemy_pokemon_box.setTitle(f"{self.tracker.enemy_pokemon.name}")
            self.enemy_pokemon_box.setStyleSheet(self.get_group_box_style("#ff6b6b"))
        
        # Update main Pokemon stats
        if main_pokemon_stats:
            for key, value in main_pokemon_stats.items():
                label_key = f"main_pokemon_{key}"
                if label_key in self.stats_labels:
                    stat_name = key.capitalize()
                    self.stats_labels[label_key].setText(f"{stat_name}: {value if value is not None else 'N/A'}")
                    self.stats_labels[label_key].setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 8px;")
        
        # Update enemy Pokemon stats
        if enemy_pokemon_stats:
            for key, value in enemy_pokemon_stats.items():
                label_key = f"enemy_pokemon_{key}"
                if label_key in self.stats_labels:
                    stat_name = key.capitalize()
                    self.stats_labels[label_key].setText(f"{stat_name}: {value if value is not None else 'N/A'}")
                    self.stats_labels[label_key].setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 8px;")
        
        # Update theme colors for group boxes
        if self.session_stats_box:
            self.session_stats_box.setStyleSheet(self.get_group_box_style())
        if self.card_ratings_box:
            self.card_ratings_box.setStyleSheet(self.get_group_box_style())
        
        # Update egg reward progress
        if hasattr(self, 'egg_reward_box') and self.egg_reward_box:
            egg_status = self._get_egg_reward_status()
            if hasattr(self, 'egg_progress_label'):
                self.egg_progress_label.setText(f"Streak: {egg_status['consecutive_days']}/3 days")
                self.egg_progress_label.setStyleSheet(f"color: {self.get_text_color()}; padding: 4px 8px;")
            if hasattr(self, 'egg_progress_bar'):
                self.egg_progress_bar.setValue(egg_status['progress_percent'])
                self.egg_progress_bar.setFormat(f"{egg_status['progress_percent']}%")
            if hasattr(self, 'total_eggs_label'):
                self.total_eggs_label.setText(f"Total Eggs Earned: {egg_status['total_eggs_awarded']}")
                self.total_eggs_label.setStyleSheet(f"color: {self.get_secondary_color()}; padding: 4px 8px;")
            self.egg_reward_box.setStyleSheet(self.get_group_box_style("#ffd43b"))
        
        # Update window background
        if self.window:
            self.window.setStyleSheet(f"background-color: {self.get_background_color()};")
            
        # Update title color
        if self.title_label:
            self.title_label.setStyleSheet(f"color: {self.get_accent_color()}; padding: 4px;")

    def start_real_time_updates(self) -> None:
        """
        Starts real-time stat updates using a QTimer.
        
        Creates a timer that calls update_stats() every 1000ms (1 second).
        The timer continues until the window is closed or stop is called.
        """
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_stats)
        self.timer.start(1000)

    def toggle_window(self) -> None:
        """
        Toggles the visibility of the tracker window.
        
        If the window is visible, it will be closed.
        If the window is not visible or doesn't exist, it will be created/shown.
        The window is set as a Tool window so it stays above Anki but not other apps.
        """
        if self.window and self.window.isVisible():
            self.window.close()
        else:
            if not self.window:
                self.create_gui()
                self.start_real_time_updates()
                self.window.setWindowFlag(Qt.WindowType.Tool)
            self.window.show()
