import json
import uuid
from typing import Any, Callable

from aqt import mw, gui_hooks
from aqt.qt import (
    Qt,
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QPixmap,
)

from aqt.theme import theme_manager # Check if light / dark mode in Anki

from PyQt6.QtWidgets import QLineEdit, QComboBox, QCheckBox, QMenu, QWidget, QScrollArea, QFrame, QRadioButton, QButtonGroup
from PyQt6.QtCore import QSize, QTimer, QPropertyAnimation, QRect, QEasingCurve
from PyQt6.QtGui import QIcon, QFont, QAction, QMovie, QCloseEvent

from ..pyobj.pokemon_obj import PokemonObject
from ..pyobj.reviewer_obj import Reviewer_Manager
from ..pyobj.test_window import TestWindow
from ..pyobj.translator import Translator
from ..pyobj.collection_dialog import MainPokemon
from ..gui_classes.pokemon_details import PokemonCollectionDetails
from ..pyobj.InfoLogger import ShowInfoLogger

from ..pyobj.settings import Settings
from ..functions.sprite_functions import get_sprite_path
from ..utils import load_custom_font, get_tier_by_id
from ..resources import mypokemon_path, itembag_path
from ..hooks import AnkimonHooks


# Box background colors - Pokemon PC style wallpapers with vibrant themes
BOX_COLORS_DARK = [
    ("#1b5e20", "Forest"),      # Rich forest green
    ("#0d47a1", "Ocean"),       # Deep ocean blue
    ("#4a148c", "Dusk"),        # Rich purple dusk
    ("#3e2723", "Cave"),        # Dark cave brown
    ("#006064", "Ice"),         # Deep cyan ice
    ("#b71c1c", "Volcano"),     # Vibrant volcanic red
    ("#f57f17", "Desert"),      # Warm desert orange
    ("#01579b", "Sky"),         # Bright sky blue
    ("#6a1b9a", "Psychic"),     # Vivid mystic purple
    ("#004d40", "Marsh"),       # Deep teal marsh
    ("#827717", "Electric"),    # Electric olive
    ("#311b92", "Ghost"),       # Deep ghostly indigo
    ("#5d4037", "Ground"),      # Earthy brown
    ("#37474f", "Steel"),       # Steel gray-blue
    ("#33691e", "Bug"),         # Vibrant bug green
    ("#880e4f", "Fairy"),       # Rich fairy magenta
]

BOX_COLORS_LIGHT = [
    ("#a5d6a7", "Forest"),      # Fresh forest green
    ("#90caf9", "Ocean"),       # Bright ocean blue
    ("#ce93d8", "Dusk"),        # Soft purple dusk
    ("#bcaaa4", "Cave"),        # Warm cave brown
    ("#80deea", "Ice"),         # Bright icy cyan
    ("#ef9a9a", "Volcano"),     # Soft volcanic red
    ("#ffe082", "Desert"),      # Warm desert gold
    ("#81d4fa", "Sky"),         # Light sky blue
    ("#b39ddb", "Psychic"),     # Soft mystic purple
    ("#80cbc4", "Marsh"),       # Fresh teal marsh
    ("#dce775", "Electric"),    # Bright electric lime
    ("#9fa8da", "Ghost"),       # Soft ghostly lavender
    ("#ffcc80", "Ground"),      # Warm earthy orange
    ("#b0bec5", "Steel"),       # Clean steel gray
    ("#aed581", "Bug"),         # Fresh bug green
    ("#f48fb1", "Fairy"),       # Bright fairy pink
]


def format_item_name(item_name: str) -> str:
    return item_name.replace("-", " ").title()

def clear_layout(layout):
    """
    Recursively removes all widgets and nested layouts from a given layout.

    This function iterates through all items in the provided layout, removes
    each widget or sub-layout, and ensures proper deletion and memory cleanup.

    Args:
        layout (QLayout): The layout to be cleared. Can contain widgets and/or nested layouts.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout():
            clear_layout(item.layout())

class ScaledMovieLabel(QLabel):
    """
    A QLabel subclass that displays scaled GIF animations with automatic aspect ratio preservation.
    
    This widget is designed for displaying Pokemon sprite GIFs in a fixed-size container
    while maintaining proper aspect ratios and centering. Each frame of the GIF is
    scaled on-the-fly to fit within the specified dimensions.
    
    Attributes:
        target_width (int): The maximum width for scaling the animation frames.
        target_height (int): The maximum height for scaling the animation frames.
        movie (QMovie): The QMovie instance handling the animation playback.
    
    Example:
        >>> sprite = ScaledMovieLabel("/path/to/pokemon.gif", width=64, height=64)
        >>> grid.addWidget(sprite, row, col, Qt.AlignmentFlag.AlignCenter)
    
    Note:
        The scaling is performed on each frame change, which may have performance
        implications for very high frame-rate GIFs or very large images.
    """
    
    def __init__(self, gif_path: str, width: int, height: int) -> None:
        """
        Initialize the ScaledMovieLabel with a GIF animation and target dimensions.
        
        Args:
            gif_path (str): The file path to the GIF image to display.
                Must be a valid path to an animated GIF file.
            width (int): The target width in pixels for the scaled animation.
                The actual width may be smaller to preserve aspect ratio.
            height (int): The target height in pixels for the scaled animation.
                The actual height may be smaller to preserve aspect ratio.
        
        Side Effects:
            - Creates and starts a QMovie instance
            - Sets a fixed size on the widget
            - Centers content alignment within the label
        """
        super().__init__()
        self.target_width: int = width
        self.target_height: int = height
        self.movie: QMovie = QMovie(gif_path)
        self.movie.frameChanged.connect(self.on_frame_changed)
        self.movie.start()
        self.setFixedSize(width, height)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

    def on_frame_changed(self, frame_number: int) -> None:
        """
        Handle frame change events and scale the current frame.
        
        Called automatically when the QMovie advances to a new frame.
        Retrieves the current frame, scales it to fit within the target
        dimensions while preserving aspect ratio, and updates the display.
        
        Args:
            frame_number (int): The index of the current frame (0-based).
                Provided by the QMovie.frameChanged signal but not used directly.
        
        Side Effects:
            - Updates the label's pixmap with the scaled frame
        """
        pixmap = self.movie.currentPixmap()
        scaled_pixmap = pixmap.scaled(
            self.target_width, 
            self.target_height, 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )
        self.setPixmap(scaled_pixmap)

class PokemonPC(QDialog):
    def __init__(
            self,
            logger: ShowInfoLogger,
            translator: Translator,
            reviewer_obj: Reviewer_Manager,
            test_window: TestWindow,
            settings: Settings,
            main_pokemon: PokemonObject,
            parent=mw,
    ):
        super().__init__(parent)

        self.logger = logger
        self.translator = translator
        self.reviewer_obj = reviewer_obj
        self.test_window = test_window
        self.settings = settings
        self.main_pokemon_function_callback = lambda _pokemon_data: MainPokemon(_pokemon_data, main_pokemon, logger, translator, reviewer_obj, test_window)

        self.n_cols = 6
        self.n_rows = 5
        self.current_box_idx = 0  # Index of current displayed box
        self.gif_in_collection = settings.get("gui.gif_in_collection")

        self.slot_size = 72  # Side length in pixels of a PC slot (larger for sprites)
        self.main_layout = QHBoxLayout()  # Main horizontal layout for split panels
        self.details_layout = QVBoxLayout()  # Layout for details panel
        self.details_widget = QWidget()  # Widget to hold details
        self.pokemon_details_layout = None
        self.selected_pokemon = None  # Store the selected pokemon data for details panel

        # Widgets for filtering and sorting
        self.search_edit = None
        self.type_combo = None
        self.generation_combo = None
        self.tier_combo = None
        self.filter_favorites = None
        self.filter_is_holding_item = None
        self.filter_shiny = None
        self.sort_by_id = None
        self.sort_by_name = None
        self.sort_by_level = None
        self.sort_by_date = None
        self.sort_group = None
        self.selected_sort_key = "Date"
        self.desc_sort = None  # Sort by descending order

        # Subscribe to theme change hook to update UI dynamically
        gui_hooks.theme_did_change.append(self.on_theme_change)
        
        # Register with AnkimonHooks for external refresh requests
        AnkimonHooks.register_pc_refresh(self._on_external_refresh)

        self.ensure_data_integrity()  # Necessary for legacy reasons
        self.create_gui()

    def on_theme_change(self):
        """
        Callback function triggered when Anki's theme changes (light to dark or vice versa).
        Refreshes the GUI to apply the new theme settings.
        """
        self.refresh_gui()

    def _on_external_refresh(self):
        """Handle external refresh requests via AnkimonHooks.
        
        Only refreshes if the dialog is currently visible to avoid
        unnecessary processing when the PC is closed.
        """
        if self.isVisible():
            self.refresh_gui()

    def closeEvent(self, event: QCloseEvent):
        """Handle dialog close - unregister from hooks.
        
        Note: We don't unregister here because the dialog is reused.
        The singleton pattern means this dialog persists for the session.
        """
        super().closeEvent(event)


    def create_gui(self):
        """
        Builds and sets up the main graphical user interface for displaying and managing Pokémon.

        This method initializes the GUI layout, including:
        - Navigation controls to switch between Pokémon storage boxes
        - A grid display for showing Pokémon in the current box
        - Filters and sorting options to refine the displayed Pokémon
        - Optional animated sprites or static images based on user settings
        - A right-hand details panel with flexible width

        The GUI components include:
        - Navigation buttons and current box label
        - A dynamically populated grid of Pokémon buttons with sprite icons
        - Filtering options (search by name, type, generation, tier, favorites)
        - Sorting options (by ID, name, level, ascending/descending)
        - A flexible-width details panel on the right

        All components are added to the main layout and displayed within a resizable window.

        Side Effects:
            - Modifies the instance's layout and widget properties.
            - Connects UI elements to their corresponding interaction handlers.
        """
        self.setWindowTitle("Pokémon PC")

        # Determine theme based on Anki's night mode
        is_dark_mode = theme_manager.night_mode # Correctly checks Anki's theme

        # Define authentic Pokémon-themed color palettes
        if is_dark_mode:
            # Dark Mode: Inspired by modern, sleek game UIs
            background_color = "#003A70"
            text_color = "#E0E0E0"
            button_bg = "#3B4CCA"
            button_border = "#6A73D9"
            hover_color = "#6A73D9"
            favorite_color = "#B3A125"
            favorite_hover_color = "#AF8308"
            input_bg = "#002B5A" # Slightly lighter than background for input fields
            slot_bg_color = "#002B5A"
        else:
            # Light Mode: Inspired by classic PC Box / Pokédex
            background_color = "#E6F3FF"
            text_color = "#003A70"
            button_bg = "#3D7DCA"
            button_border = "#003A70"
            hover_color = "#A8D8FF"
            favorite_color = "#FFDE00"
            favorite_hover_color = "#FFA600"
            input_bg = "#FFFFFF" # White background for input fields
            slot_bg_color = "#CCE5FF"

        # Set stylesheet for the entire dialog, now correctly using all theme variables
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {background_color};
            }}
            QWidget {{
                color: {text_color};
            }}
            QPushButton {{
                background-color: {button_bg};
                border: 1px solid {button_border};
                border-radius: 5px;
                padding: 5px;
                color: {text_color};
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QLineEdit, QComboBox {{
                background-color: {input_bg};
                border: 1px solid {button_border};
                border-radius: 3px;
                padding: 3px;
                color: {text_color};
            }}
            QLabel {{
                color: {text_color};
            }}
        """)

        self.gif_in_collection = self.settings.get("gui.gif_in_collection")

        pokemon_list = self.load_pokemon_data()
        pokemon_list = self.filter_pokemon_list(pokemon_list)
        pokemon_list = self.sort_pokemon_list(pokemon_list)
        max_box_idx = (len(pokemon_list) - 1) // (self.n_rows * self.n_cols)

        # Get box-specific background color
        box_colors = BOX_COLORS_DARK if is_dark_mode else BOX_COLORS_LIGHT
        box_color_idx = self.current_box_idx % len(box_colors)
        box_bg_color, box_theme_name = box_colors[box_color_idx]

        # Collection panel
        collection_layout = QVBoxLayout()
        collection_layout.setSpacing(4)
        collection_layout.setContentsMargins(5, 5, 5, 5)
        
        box_selector_layout = QHBoxLayout()
        box_selector_layout.setSpacing(8)
        prev_box_button = QPushButton("◀")
        next_box_button = QPushButton("▶")
        prev_box_button.setFixedSize(40, 32)
        next_box_button.setFixedSize(40, 32)
        prev_box_button.setFont(QFont('System', 16))
        next_box_button.setFont(QFont('System', 16))
        prev_box_button.clicked.connect(lambda: self.looparound_go_to_box(self.current_box_idx - 1, max_box_idx))
        next_box_button.clicked.connect(lambda: self.looparound_go_to_box(self.current_box_idx + 1, max_box_idx))
        # Show box name with theme
        curr_box_label = QLabel(f"Box {self.current_box_idx + 1} - {box_theme_name}")
        curr_box_label.setFixedSize(160, 32)
        curr_box_label.setFont(load_custom_font(14, int(self.settings.get("misc.language"))))
        curr_box_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        curr_box_label.setStyleSheet(f"border: 2px solid {button_border}; background-color: {box_bg_color}; border-radius: 6px; font-weight: bold;")
        box_selector_layout.addStretch()
        box_selector_layout.addWidget(prev_box_button)
        box_selector_layout.addWidget(curr_box_label)
        box_selector_layout.addWidget(next_box_button)
        box_selector_layout.addStretch()
        collection_layout.addLayout(box_selector_layout)

        # Pokémon grid with box-specific background
        pokemon_grid_container = QFrame()
        pokemon_grid_container.setStyleSheet(f"""
            QFrame {{
                background-color: {box_bg_color};
                border: 2px solid {button_border};
                border-radius: 8px;
            }}
        """)
        start_index = self.current_box_idx * self.n_cols * self.n_rows
        end_index = (self.current_box_idx + 1) * self.n_cols * self.n_rows
        pokemon_list_slice = pokemon_list[start_index:end_index]
        pokemon_grid = QGridLayout()
        pokemon_grid.setSpacing(8)
        pokemon_grid.setContentsMargins(12, 12, 12, 12)
        
        for row in range(self.n_rows):
            for col in range(self.n_cols):
                pokemon_idx = row * self.n_cols + col
                if pokemon_idx >= len(pokemon_list_slice):
                    empty_slot = QFrame()
                    empty_slot.setFixedSize(self.slot_size, self.slot_size)
                    empty_slot.setStyleSheet(f"""
                        QFrame {{
                            background-color: transparent;
                            border: none;
                        }}
                    """)
                    pokemon_grid.addWidget(empty_slot, row, col)
                    continue

                pokemon = pokemon_list_slice[pokemon_idx]
                pkmn_image_path = get_sprite_path("front", "gif" if self.gif_in_collection else "png", pokemon['id'], pokemon.get("shiny", False), pokemon["gender"])
                pokemon_button = QPushButton("")
                pokemon_button.setFixedSize(self.slot_size, self.slot_size)

                # Minimal style - no border, only subtle hover effect
                if pokemon.get("is_favorite", False):
                    # Favorites get a subtle golden glow
                    style_sheet_str = f"""
                        QPushButton {{
                            background-color: rgba(255, 215, 0, 0.2);
                            border: none;
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: rgba(255, 255, 255, 0.3);
                        }}
                    """
                else:
                    style_sheet_str = f"""
                        QPushButton {{
                            background-color: transparent;
                            border: none;
                            border-radius: 8px;
                        }}
                        QPushButton:hover {{
                            background-color: rgba(255, 255, 255, 0.2);
                        }}
                    """
                pokemon_button.setStyleSheet(style_sheet_str)

                sprite_size = self.slot_size - 8
                if self.gif_in_collection:
                    sprite_label = ScaledMovieLabel(pkmn_image_path, sprite_size, sprite_size)
                    sprite_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                    pokemon_grid.addWidget(pokemon_button, row, col, Qt.AlignmentFlag.AlignCenter)
                    pokemon_grid.addWidget(sprite_label, row, col, Qt.AlignmentFlag.AlignCenter)
                else:
                    # Create a label inside the button for the sprite
                    sprite_label = QLabel(pokemon_button)
                    sprite_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
                    pixmap = QPixmap(pkmn_image_path)
                    scaled_pixmap = pixmap.scaled(sprite_size, sprite_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    sprite_label.setPixmap(scaled_pixmap)
                    sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    # Center the label inside the button - calculate based on actual pixmap size
                    actual_width = scaled_pixmap.width()
                    actual_height = scaled_pixmap.height()
                    label_x = (self.slot_size - actual_width) // 2
                    label_y = (self.slot_size - actual_height) // 2
                    sprite_label.setFixedSize(actual_width, actual_height)
                    sprite_label.move(label_x, label_y)
                    pokemon_grid.addWidget(pokemon_button, row, col, Qt.AlignmentFlag.AlignCenter)
                
                # Store sprite reference and connect click handler
                pokemon_button.sprite_label = sprite_label
                pokemon_button.clicked.connect(lambda checked, pb=pokemon_button, pkmn=pokemon: self._on_pokemon_clicked(pb, pkmn))
        
        # Set the grid layout on the container and add to collection
        pokemon_grid_container.setLayout(pokemon_grid)
        collection_layout.addWidget(pokemon_grid_container)

        # Bottom part to filter the Pokémon displayed
        filters_layout = QGridLayout()
        # Name filtering
        prev_text = self.search_edit.text() if self.search_edit is not None else ""
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search Pokémon (by nickname, name)")
        self.search_edit.setText(prev_text)
        self.search_edit.returnPressed.connect(lambda: self.go_to_box(0))
        search_button = QPushButton("Search")
        search_button.clicked.connect(lambda: self.go_to_box(0))
        # Type filtering
        prev_idx = self.type_combo.currentIndex() if self.type_combo is not None else 0
        self.type_combo = QComboBox()
        self.type_combo.addItem("All types")
        self.type_combo.addItems(["Normal", "Fire", "Water", "Electric", "Grass", "Ice", "Fighting", "Poison", "Ground", "Flying", "Psychic", "Bug", "Rock", "Ghost", "Dragon", "Dark", "Steel", "Fairy"])
        self.type_combo.setCurrentIndex(prev_idx)
        self.type_combo.currentIndexChanged.connect(lambda: self.go_to_box(0))
        # Generation filtering
        prev_idx = self.generation_combo.currentIndex() if self.generation_combo is not None else 0
        self.generation_combo = QComboBox()
        self.generation_combo.addItem("All gens")
        self.generation_combo.addItems([f"Gen {i}" for i in range(1, 9, 1)])
        self.generation_combo.setCurrentIndex(prev_idx)
        self.generation_combo.currentIndexChanged.connect(lambda: self.go_to_box(0))
        # Tier filtering
        prev_idx = self.tier_combo.currentIndex() if self.tier_combo is not None else 0
        self.tier_combo = QComboBox()
        self.tier_combo.addItem("All tiers")
        self.tier_combo.addItems(["Normal", "Legendary", "Mythical", "Baby", "Ultra", "Fossil", "Starter"])
        self.tier_combo.setCurrentIndex(prev_idx)
        self.tier_combo.currentIndexChanged.connect(lambda: self.go_to_box(0))
        # Sorting by favorites
        is_checked = self.filter_favorites.isChecked() if self.filter_favorites is not None else False
        self.filter_favorites = QCheckBox("Favorites")
        self.filter_favorites.setChecked(is_checked)
        self.filter_favorites.stateChanged.connect(lambda: self.go_to_box(0))
        # Filtering Pokemon who hold items
        is_checked = self.filter_is_holding_item.isChecked() if self.filter_is_holding_item is not None else False
        self.filter_is_holding_item = QCheckBox("Holds item")
        self.filter_is_holding_item.setChecked(is_checked)
        self.filter_is_holding_item.stateChanged.connect(lambda: self.go_to_box(0))
        # Shiny filter
        is_checked = self.filter_shiny.isChecked() if self.filter_shiny is not None else False
        self.filter_shiny = QCheckBox("Shiny")
        self.filter_shiny.setChecked(is_checked)
        self.filter_shiny.stateChanged.connect(lambda: self.go_to_box(0))
        # Sorting options
        sort_label = QLabel("Sort by:")

        # Radio buttons for mutually exclusive sorting
        self.sort_group = QButtonGroup(self)
        self.sort_by_id = QRadioButton("ID")
        self.sort_by_name = QRadioButton("Name")
        self.sort_by_level = QRadioButton("Level")
        self.sort_by_date = QRadioButton("Date")

        # Style radio buttons with white text
        radio_style = "QRadioButton { color: white; }"
        self.sort_by_id.setStyleSheet(radio_style)
        self.sort_by_name.setStyleSheet(radio_style)
        self.sort_by_level.setStyleSheet(radio_style)
        self.sort_by_date.setStyleSheet(radio_style)
        sort_label.setStyleSheet("color: white;")

        self.sort_group.addButton(self.sort_by_id)
        self.sort_group.addButton(self.sort_by_name)
        self.sort_group.addButton(self.sort_by_level)
        self.sort_group.addButton(self.sort_by_date)

        if self.selected_sort_key == "ID":
            self.sort_by_id.setChecked(True)
        elif self.selected_sort_key == "Name":
            self.sort_by_name.setChecked(True)
        elif self.selected_sort_key == "Level":
            self.sort_by_level.setChecked(True)
        else:  # Date is the default
            self.sort_by_date.setChecked(True)

        # Connect signals
        self.sort_group.buttonClicked.connect(self.on_sort_button_clicked)

        sort_radio_layout = QHBoxLayout()
        sort_radio_layout.addWidget(sort_label)
        sort_radio_layout.addWidget(self.sort_by_id)
        sort_radio_layout.addWidget(self.sort_by_name)
        sort_radio_layout.addWidget(self.sort_by_level)
        sort_radio_layout.addWidget(self.sort_by_date)
        sort_radio_widget = QWidget()
        sort_radio_widget.setLayout(sort_radio_layout)

        # Checkboxes for other options
        is_checked = self.desc_sort.isChecked() if self.desc_sort is not None else False
        self.desc_sort = QCheckBox("Descending")
        self.desc_sort.setChecked(is_checked)
        self.desc_sort.stateChanged.connect(lambda: self.go_to_box(0))

        # Adding the widgets to the layout
        filters_layout.addWidget(self.search_edit, 0, 0, 1, 4)
        filters_layout.addWidget(search_button, 0, 4, 1, 1)
        filters_layout.addWidget(self.type_combo, 1, 0, 1, 2)
        filters_layout.addWidget(self.generation_combo, 1, 2, 1, 2)
        filters_layout.addWidget(self.tier_combo, 1, 4, 1, 1)

        checkboxes_layout = QHBoxLayout()
        checkboxes_layout.addWidget(self.filter_favorites)
        checkboxes_layout.addWidget(self.filter_is_holding_item)
        checkboxes_layout.addWidget(self.filter_shiny)
        checkboxes_layout.addWidget(self.desc_sort)  # Moved here
        checkboxes_widget = QWidget()
        checkboxes_widget.setLayout(checkboxes_layout)

        filters_layout.addWidget(checkboxes_widget, 2, 0, 1, 5)
        filters_layout.addWidget(sort_radio_widget, 3, 0, 1, 5)
        collection_layout.addLayout(filters_layout)

        # Finalizing layout - calculate size based on grid
        collection_widget = QWidget()
        collection_widget.setLayout(collection_layout)
        grid_width = self.n_cols * (self.slot_size + 4) + 24  # slot + spacing + margins
        grid_height = self.n_rows * (self.slot_size + 4) + 180  # + header + filters
        collection_widget.setFixedWidth(grid_width)
        collection_widget.setMinimumHeight(grid_height)

        self.main_layout.addWidget(collection_widget, 1)

        # Check for existing details panel and apply styles
        # Recreate details layout from stored pokemon data if available
        if self.selected_pokemon is not None:
            pokemon = self.selected_pokemon
            if pokemon.get('base_stats'):
                detail_stats = {**pokemon['base_stats'], "xp": pokemon.get("xp", 0)}
            elif pokemon.get('stats'):
                detail_stats = {**pokemon['stats'], "xp": pokemon.get("xp", 0)}
            else:
                detail_stats = {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0, "xp": 0}
            
            self.pokemon_details_layout = PokemonCollectionDetails(
                name=pokemon['name'],
                level=pokemon['level'],
                id=pokemon['id'],
                shiny=pokemon.get("shiny", False),
                ability=pokemon['ability'],
                type=pokemon['type'],
                detail_stats=detail_stats,
                attacks=pokemon['attacks'],
                base_experience=pokemon['base_experience'],
                growth_rate=pokemon['growth_rate'],
                ev=pokemon['ev'],
                iv=pokemon['iv'],
                gender=pokemon['gender'],
                nickname=pokemon.get('nickname'),
                individual_id=pokemon.get('individual_id'),
                pokemon_defeated=pokemon.get('pokemon_defeated', 0),
                everstone=pokemon.get('everstone', False),
                captured_date=pokemon.get('captured_date', 'Missing'),
                language=int(self.settings.get("misc.language")),
                gif_in_collection=self.gif_in_collection,
                remove_levelcap=self.settings.get("misc.remove_level_cap"),
                logger=self.logger,
                refresh_callback=self.refresh_gui,
                close_callback=self.close_details_panel,
                battles_won=pokemon.get('battles_won', 0),
                battles_lost=pokemon.get('battles_lost', 0),
            )
        
        if self.pokemon_details_layout is not None:
            # Create container for close button + scroll area
            details_container = QWidget()
            details_container_layout = QVBoxLayout(details_container)
            details_container_layout.setContentsMargins(0, 0, 0, 0)
            details_container_layout.setSpacing(0)
            
            # Close button at top
            close_button = QPushButton("✕ Close")
            close_button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {button_bg};
                    color: {text_color};
                    border: none;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-weight: bold;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: #b71c1c;
                }}
            """)
            close_button.clicked.connect(self.close_details_panel)
            details_container_layout.addWidget(close_button)
            
            # Create scroll area for details
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_area.setStyleSheet(f"""
                QScrollArea {{
                    background-color: {background_color};
                    border: none;
                }}
                QScrollBar:vertical {{
                    background-color: {input_bg};
                    width: 10px;
                    border-radius: 5px;
                }}
                QScrollBar::handle:vertical {{
                    background-color: {button_bg};
                    border-radius: 5px;
                    min-height: 20px;
                }}
                QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                    height: 0px;
                }}
            """)
            
            self.details_widget = QWidget()
            self.details_widget.setLayout(self.pokemon_details_layout)
            self.details_widget.setStyleSheet(f"""
                QWidget {{
                    background-color: {background_color};
                }}
                QLabel {{
                    color: {text_color};
                }}
                QPushButton {{
                    background-color: {button_bg};
                    color: {text_color};
                    border: 1px solid {button_border};
                    border-radius: 6px;
                    padding: 6px 12px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {hover_color};
                }}
                QLineEdit {{
                    background-color: {input_bg};
                    color: {text_color};
                    border: 2px solid {button_border};
                    border-radius: 4px;
                    padding: 4px 8px;
                }}
            """)
            
            scroll_area.setWidget(self.details_widget)
            details_container_layout.addWidget(scroll_area)
            
            details_container.setMinimumWidth(420)
            details_container.setMaximumWidth(480)
            self.main_layout.addWidget(details_container, 2)
        else:
            # Ensure the panel is collapsed if no pokemon is selected
            self.details_widget = QWidget()
            self.details_widget.setLayout(QVBoxLayout())
            self.details_widget.setMinimumWidth(0)
            self.details_widget.setMaximumWidth(0)
            self.main_layout.addWidget(self.details_widget, 2)

        self.setLayout(self.main_layout)

    def close_details_panel(self) -> None:
        """
        Close the Pokemon details side panel and resize the window.
        
        This method handles the cleanup and UI refresh needed when the user
        closes the details panel (e.g., by clicking the close button). It
        clears the details layout, resets the selected Pokemon, refreshes
        the GUI, and resizes the window to fit the remaining content.
        
        Side Effects:
            - Clears and deletes all widgets in the details layout
            - Sets pokemon_details_layout to None
            - Sets selected_pokemon to None
            - Triggers a full GUI refresh via refresh_gui()
            - Calls adjustSize() to resize the window appropriately
        
        Note:
            The window resize is important because the details panel takes
            up significant horizontal space. Without adjustSize(), the window
            would retain its larger size with empty space.
        """
        if self.pokemon_details_layout is not None:
            clear_layout(self.pokemon_details_layout)
            self.pokemon_details_layout = None
        self.selected_pokemon = None
        self.refresh_gui()
        # Resize window to fit content without the details panel
        self.adjustSize()

    def refresh_gui(self):
        """
        Refreshes the entire graphical user interface by rebuilding its layout.

        This method clears the current main layout, reconstructs it by calling `create_gui()`,
        and then invalidates and reactivates the layout to ensure proper rendering.

        Side Effects:
            - Removes all widgets from the main layout.
            - Recreates and re-adds all GUI elements.
            - Forces layout recalculation and update.
        """
        clear_layout(self.main_layout)
        self.create_gui()
        self.layout().invalidate()
        self.layout().activate()

    def go_to_box(self, idx: int):
        """
        Navigates to the specified Pokémon storage box and updates the GUI accordingly.

        Args:
            idx (int): The index of the box to navigate to.

        Side Effects:
            - Updates the current box index.
            - Triggers a full GUI refresh to display the selected box's contents.
        """
        self.current_box_idx = idx
        self.refresh_gui()

    def looparound_go_to_box(self, idx: int, max_idx: int):
        """
        Navigates to a box index with wrap-around behavior.

        If the provided index is less than 0, wraps around to the maximum index.
        If the index exceeds the maximum, wraps around to 0.
        Then updates the GUI to show the selected box.

        Args:
            idx (int): The target box index to navigate to.
            max_idx (int): The maximum valid box index.

        Side Effects:
            - Updates the current box index with wrapping.
            - Triggers a GUI refresh to display the selected box.
        """
        if idx < 0:
            idx = max_idx
        elif idx > max_idx:
            idx = 0
        self.go_to_box(idx)

    def adjust_pixmap_size(self, pixmap, max_width, max_height):
        """
        Scales a QPixmap to fit within the specified maximum width and height while maintaining aspect ratio.

        If the pixmap's width exceeds `max_width`, it is scaled down proportionally.
        Note: This implementation currently only scales based on width and does not consider `max_height`.

        Args:
            pixmap (QPixmap): The original pixmap to be resized.
            max_width (int): The maximum allowed width.
            max_height (int): The maximum allowed height (currently unused).

        Returns:
            QPixmap: The scaled pixmap, or the original if no scaling was needed.
        """
        original_width = pixmap.width()
        original_height = pixmap.height()

        if original_width > max_width:
            new_width = max_width
            new_height = (original_height * max_width) // original_width
            pixmap = pixmap.scaled(new_width, new_height)

        return pixmap

    def load_pokemon_data(self) -> list:
        """Reads the mypokemon.json file and loads Pokémon data into self.pokemon_list."""
        try:
            with open(mypokemon_path, "r", encoding="utf-8") as file:
                pokemon_list = json.load(file)
                for i, pokemon in enumerate(pokemon_list):
                    pokemon['original_index'] = i
                return pokemon_list
        except FileNotFoundError:
            self.logger.log("error","mypokemon.json file not found.")
        except json.JSONDecodeError:
            self.logger.log("error","mypokemon.json file not found.")

        return []

    def filter_pokemon_list(self, pokemon_list: list) -> list:
        """
        Filters a list of Pokémon dictionaries based on multiple UI-selected criteria.

        The filtering considers:
        - Search text matching Pokémon name (case-insensitive).
        - Selected Pokémon type from a dropdown.
        - Selected tier category from a dropdown.
        - Whether only favorites should be shown.
        - Selected generation range based on Pokémon ID.

        Args:
            pokemon_list (list): List of Pokémon dictionaries to filter. Each dictionary should
                contain keys like "name", "type", "tier", "is_favorite", and "id".

        Returns:
            list: A new list containing only Pokémon that match all the active filter criteria.
        """
        def filtering_func(pokemon: dict) -> bool:
            if self.search_edit is not None:
                if self.search_edit.text().lower() not in pokemon.get("name").lower():
                    return False

            if self.type_combo is not None:
                if self.type_combo.currentIndex() != 0 and self.type_combo.currentText() not in pokemon.get("type", ""):
                    return False

            if self.tier_combo is not None:
                if (
                    self.tier_combo.currentIndex() != 0
                    and pokemon.get("tier") is not None
                    and self.tier_combo.currentText() != pokemon.get("tier")
                ):
                    return False

            if self.filter_favorites is not None:
                if self.filter_favorites.isChecked() and not pokemon.get("is_favorite", False):
                    return False

            if self.filter_is_holding_item is not None:
                if self.filter_is_holding_item.isChecked() and not pokemon.get("held_item", False):
                    return False

            if self.filter_shiny is not None:
                if self.filter_shiny.isChecked() and not pokemon.get("shiny", False):
                    return False

            if self.generation_combo is not None:
                gen_idx = self.generation_combo.currentIndex()
                if gen_idx != 0 and (
                    (1 <= pokemon["id"] <= 151 and gen_idx != 1) or
                    (152 <= pokemon["id"] <= 251 and gen_idx != 2) or
                    (252 <= pokemon["id"] <= 386 and gen_idx != 3) or
                    (387 <= pokemon["id"] <= 493 and gen_idx != 4) or
                    (494 <= pokemon["id"] <= 649 and gen_idx != 5) or
                    (650 <= pokemon["id"] <= 721 and gen_idx != 6) or
                    (722 <= pokemon["id"] <= 809 and gen_idx != 7) or
                    (810 <= pokemon["id"] <= 898 and gen_idx != 8)
                ):
                    return False

            return True

        return list(filter(filtering_func, pokemon_list.copy()))

    def sort_pokemon_list(self, pokemon_list: list) -> list:
        reverse = self.desc_sort is not None and self.desc_sort.isChecked()

        sort_key_str = self.selected_sort_key.lower()
        if sort_key_str == "date":
            sort_key_str = "original_index"

        def sort_key(p):
            if sort_key_str == "name":
                return (p.get("name", ""), p.get("nickname", ""))
            else:
                return p.get(sort_key_str, 0)

        return sorted(
            pokemon_list,
            reverse=reverse,
            key=sort_key
        )

    def on_sort_button_clicked(self, button):
        self.selected_sort_key = button.text()
        self.go_to_box(0)

    def _on_pokemon_clicked(self, button: QPushButton, pokemon: dict[str, Any]):
        """Handle pokemon click - trigger jump animation on sprite then show menu."""
        sprite_label = getattr(button, 'sprite_label', None)
        if sprite_label:
            self._do_sprite_jump_animation(sprite_label, lambda: self.show_actions_submenu(button, pokemon))
        else:
            # Fallback if no sprite label
            self.show_actions_submenu(button, pokemon)

    def _do_sprite_jump_animation(self, sprite_label: QWidget, callback: Callable = None):
        """Make a sprite label jump up twice within its parent."""
        from PyQt6.QtCore import QSequentialAnimationGroup
        
        jump_height = 10
        
        original_geometry = sprite_label.geometry()
        jumped_geometry = QRect(
            original_geometry.x(),
            original_geometry.y() - jump_height,
            original_geometry.width(),
            original_geometry.height()
        )
        
        # Create sequential animation group for two jumps
        self._jump_group = QSequentialAnimationGroup()
        
        # First jump up
        jump_up_1 = QPropertyAnimation(sprite_label, b"geometry")
        jump_up_1.setDuration(80)
        jump_up_1.setStartValue(original_geometry)
        jump_up_1.setEndValue(jumped_geometry)
        jump_up_1.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # First jump down
        jump_down_1 = QPropertyAnimation(sprite_label, b"geometry")
        jump_down_1.setDuration(80)
        jump_down_1.setStartValue(jumped_geometry)
        jump_down_1.setEndValue(original_geometry)
        jump_down_1.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Second jump up
        jump_up_2 = QPropertyAnimation(sprite_label, b"geometry")
        jump_up_2.setDuration(80)
        jump_up_2.setStartValue(original_geometry)
        jump_up_2.setEndValue(jumped_geometry)
        jump_up_2.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Second jump down
        jump_down_2 = QPropertyAnimation(sprite_label, b"geometry")
        jump_down_2.setDuration(80)
        jump_down_2.setStartValue(jumped_geometry)
        jump_down_2.setEndValue(original_geometry)
        jump_down_2.setEasingCurve(QEasingCurve.Type.InQuad)
        
        # Add all animations in sequence
        self._jump_group.addAnimation(jump_up_1)
        self._jump_group.addAnimation(jump_down_1)
        self._jump_group.addAnimation(jump_up_2)
        self._jump_group.addAnimation(jump_down_2)
        
        if callback:
            self._jump_group.finished.connect(callback)
        
        self._jump_group.start()

    def show_actions_submenu(self, button: QPushButton, pokemon: dict[str, Any]):
        """
        Displays a context menu with actions related to a specific Pokémon.

        The menu includes:
        - A non-interactive title showing the Pokémon's nickname, name, gender symbol, and level.
        - An option to view detailed information about the Pokémon.
        - An option to select the Pokémon as the main Pokémon.
        - An option to toggle the Pokémon's favorite status.

        Args:
            button (QPushButton): The button widget where the menu will be displayed.
            pokemon (dict[str, Any]): A dictionary containing Pokémon data, expected to include keys
                like "name", "nickname", "gender", "level", and "is_favorite".

        Side Effects:
            - Displays a popup menu aligned below the specified button.
            - Connects menu actions to respective handlers in the parent class.
        """
        menu = QMenu(self)

        # QMenu doesn't have a "window name" property or the like. So let's emulate one.
        if pokemon.get("gender") == "M":
            gender_symbol = "♂"
        elif pokemon.get("gender") == "F":
            gender_symbol = "♀"
        else:
            gender_symbol = ""
        if pokemon.get("nickname"):
            title = f'{pokemon["nickname"]} ({pokemon["name"]}) {gender_symbol} - lvl {pokemon["level"]}'
        else:
            title = f'{pokemon["name"]} {gender_symbol} - lvl {pokemon["level"]}'
        title_action = QAction(title, menu)
        title_action.setEnabled(False)  # Disabled, so it can't be clicked
        menu.addAction(title_action)
        menu.addSeparator()

        pokemon_details_action = QAction("Pokémon details", self)
        main_pokemon_action = QAction("Pick as main Pokémon", self)
        make_favorite_action = QAction(
            "Unmake favorite" if pokemon.get("is_favorite", False) else "Make favorite"
            )
        give_held_item = QAction("Give a held item", self)

        # Connect actions to methods or lambda functions
        pokemon_details_action.triggered.connect(lambda: self.show_pokemon_details(pokemon))
        main_pokemon_action.triggered.connect(lambda: self._set_main_pokemon_with_check(pokemon))
        make_favorite_action.triggered.connect(lambda: self.toggle_favorite(pokemon))
        give_held_item.triggered.connect(lambda: self.give_held_item(pokemon))

        menu.addAction(pokemon_details_action)
        menu.addAction(main_pokemon_action)
        menu.addAction(make_favorite_action)
        menu.addAction(give_held_item)
        if pokemon.get("held_item"):
            remove_held_item = QAction(f"Remove held item : {format_item_name(pokemon['held_item'])}", self)
            remove_held_item.triggered.connect(lambda: self.remove_held_item(pokemon))
            menu.addAction(remove_held_item)

        # Show the menu at the button's position, aligned below the button
        menu.exec(button.mapToGlobal(button.rect().topRight()))

    def show_pokemon_details(self, pokemon):
        """
        Displays detailed information about a specific Pokémon in the right-hand details panel.

        The method prepares detailed stats by merging base stats or stats with experience points,
        then updates the `self.details_layout` with a `PokemonCollectionDetails` layout.

        Args:
            pokemon (dict): A dictionary containing Pokémon data with expected keys such as:
                - 'name', 'level', 'id', 'ability', 'type', 'attacks', 'base_experience',
                'growth_rate', 'ev', 'iv', 'gender'
                - Optional keys include 'shiny', 'nickname', 'individual_id', 'pokemon_defeated',
                'everstone', 'captured_date', and 'xp'.

        Raises:
            ValueError: If neither 'base_stats' nor 'stats' are available in the Pokémon dictionary.
        """
        # Store the pokemon data so we can recreate the panel on refresh
        self.selected_pokemon = pokemon
        self.refresh_gui()

    def _set_main_pokemon_with_check(self, pokemon: dict) -> None:
        """
        Set a Pokemon as the main Pokemon with review-state protection.
        
        This method wraps the main Pokemon selection callback with a safety
        check that prevents team changes during an active review session.
        Changing the main Pokemon during review could cause inconsistencies
        in battle state, XP distribution, and displayed Pokemon.
        
        Args:
            pokemon (dict): The Pokemon data dictionary to set as main.
                Should contain at minimum:
                - 'name' (str): The Pokemon's species name
                - 'individual_id' (str): Unique identifier for this Pokemon
                - 'level' (int): Current level
                - Other stats and attributes as needed by MainPokemon
        
        Side Effects:
            - If in review: Shows a warning dialog and returns without action
            - If not in review: Calls self.main_pokemon_function_callback(pokemon)
              which updates the main Pokemon and refreshes relevant UI elements
        
        Example:
            >>> # User clicks "Pick as main Pokemon" in context menu
            >>> self._set_main_pokemon_with_check(selected_pokemon)
            # If reviewing: Warning shown, no change
            # If not reviewing: Pokemon becomes the new main Pokemon
        """
        from aqt.utils import showWarning
        if mw.state == "review":
            showWarning("Cannot change main Pokémon while reviewing. Please finish or exit the review session first.")
            return
        self.main_pokemon_function_callback(pokemon)

    def toggle_favorite(self, pokemon: dict[list, Any]):
        """
        Toggles the favorite status of a specific Pokémon in the saved Pokémon data.

        This method loads the current Pokémon list, finds the Pokémon by its unique individual ID,
        switches its "is_favorite" status, saves the updated list back to file, and refreshes the GUI.

        Args:
            pokemon (dict[list, Any]): A dictionary representing the Pokémon, expected to contain
                a unique "individual_id" key and a "name" key.

        Side Effects:
            - Updates the "is_favorite" status of the Pokémon in persistent storage.
            - Refreshes the GUI to reflect the change.
            - Logs an info message if the Pokémon is not found in the list.
        """
        pokemon_list = self.load_pokemon_data()
        for i in range(len(pokemon_list)):
            if pokemon_list[i].get("individual_id") == pokemon["individual_id"]:
                is_currently_favorite = pokemon_list[i].get("is_favorite", False)
                pokemon_list[i]["is_favorite"] = not is_currently_favorite

                with open(str(mypokemon_path), "w", encoding="utf-8") as json_file:
                    json.dump(pokemon_list, json_file, indent=2)

                self.refresh_gui()
                return

        if self.logger is not None:
            self.logger.log("info", f"Could not make/unmake {pokemon['name']} favorite")

    def give_held_item(self, pokemon: dict[list, Any]):
        """
        Opens a window to select and give a held item to the specified Pokémon.

        This function reads the available items from the item bag, filters out
        non-holdable items (items with a non-None "type"), and presents the user with a
        selection window. Once an item is selected, it is assigned to the Pokémon, a
        confirmation message is shown, and the GUI is refreshed to reflect the change.

        Args:
            pokemon (dict[list, Any]): A dictionary representing the Pokémon's data.

        Returns:
            None

        Side Effects:
            - Opens a modal `GiveItemWindow` for item selection.
            - Updates the Pokémon's held item via `PokemonObject.give_held_item`.
            - Logs and displays an info message using `ShowInfoLogger`.
            - Refreshes the GUI via `self.refresh_gui()`.
        """
        with open(itembag_path, "r", encoding="utf-8") as f:
            items_list = json.load(f)
        items_names = [item_data["item"] for item_data in items_list if item_data.get("type") is None]
        pokemon_obj = PokemonObject.from_dict(pokemon)

        def func(item_name: str):
            # small intermediary function. This allows me to display a confirmation message after giving the item and refresh the PC after giving the item.
            # Refreshing the PC after giving the item is important in order to update the pokemon information with the new held item
            pokemon_obj.give_held_item(item_name)
            self.logger.log_and_showinfo("info", f"{item_name} was given to {pokemon.get('name')}.")
            self.refresh_gui()

        give_item_window = GiveItemWindow(
            item_list=items_names,
            give_item_func=lambda item_name: func(item_name),
            logger=self.logger
        )
        give_item_window.exec()

    def remove_held_item(self, pokemon: dict[list, Any]):
        """
        Removes the held item from the specified Pokémon.

        Converts the Pokémon dictionary into a `PokemonObject`, removes the held item,
        logs the change, and refreshes the GUI. If the Pokémon does not have a held item,
        raises a `ValueError`.

        Args:
            pokemon (dict[list, Any]): A dictionary representing the Pokémon's data.

        Returns:
            None

        Raises:
            ValueError: If the Pokémon does not currently hold an item.

        Side Effects:
            - Updates the Pokémon's data to remove the held item.
            - Logs and displays an info message using `ShowInfoLogger`.
            - Refreshes the GUI via `self.refresh_gui()`.
        """
        pokemon_obj = PokemonObject.from_dict(pokemon)
        if pokemon.get('held_item') is None:
            raise ValueError("The pokemon does not hold an item.")
        pokemon_obj.remove_held_item()
        self.logger.log_and_showinfo("info", f"{format_item_name(pokemon['held_item'])} was removed from {pokemon.get('name')}.")

        # Refreshing the PC after giving the item is important in order to update the pokemon information without the held item
        self.refresh_gui()

    def ensure_data_integrity(self):
        """
        Iterates through all Pokémon to ensure they have required non-stat fields,
        adding default values if fields are missing. This handles data
        from older addon versions. Stat-related fields are ignored.
        """
        pokemon_list = self.load_pokemon_data()
        if not pokemon_list:
            return

        # --- QUICK CHECK ---
        # First, quickly determine if any migration is needed at all.
        default_keys = {
            "nickname", "gender", "ability", "type", "attacks", "base_experience", 
            "growth_rate", "everstone", "shiny", "captured_date", "individual_id", 
            "mega", "special_form", "xp", "friendship", "pokemon_defeated", 
            "tier", "is_favorite", "held_item"
        }
        
        is_migration_needed = any(
            key not in pokemon
            for pokemon in pokemon_list
            if isinstance(pokemon, dict)
            for key in default_keys
        )

        if not is_migration_needed:
            return  # All Pokémon are up-to-date, exit early.

        # --- FULL MIGRATION (only if needed) ---
        needs_update = False
        default_values = {
            "nickname": "", "gender": "N", "ability": "Illuminate", "type": ["Normal"],
            "attacks": ["Struggle"], "base_experience": 0, "growth_rate": "medium",
            "everstone": False, "shiny": False, "captured_date": None,
            "individual_id": lambda p: str(uuid.uuid4()), "mega": False,
            "special_form": None, "xp": 0, "friendship": 0,
            "pokemon_defeated": 0, "tier": lambda p: get_tier_by_id(p.get("id", 0)) or "Normal",
            "is_favorite": False, "held_item": None
        }

        for i, pokemon in enumerate(pokemon_list):
            if not isinstance(pokemon, dict):
                continue

            for key, default_generator in default_values.items():
                if key not in pokemon:
                    needs_update = True
                    if callable(default_generator):
                        value = default_generator(pokemon)
                    else:
                        value = default_generator
                    pokemon_list[i][key] = value

        if needs_update:
            with open(str(mypokemon_path), "w", encoding="utf-8") as json_file:
                json.dump(pokemon_list, json_file, indent=2)

    def on_window_close(self):
        if self.pokemon_details_layout is not None:
            clear_layout(self.pokemon_details_layout)
            self.details_widget.setFixedSize(0, 0)
            self.pokemon_details_layout = None

    def closeEvent(self, event: QCloseEvent):
        self.on_window_close()
        event.accept()  # Accept the close event

    def reject(self):  # Called when pressing Escape
        self.on_window_close()
        super().reject()


class GiveItemWindow(QDialog):
    """
    Small window that opens up when the user gives an item to the Pokemon from a PC box
    """
    def __init__(self, item_list: list[str], give_item_func: Callable, logger):
        super().__init__()
        self.setWindowTitle("Give an Item")
        self.resize(400, 400)

        # Outer layout for the dialog
        main_layout = QVBoxLayout(self)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # Container widget inside scroll area
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        self.give_item_func = give_item_func
        self.logger = logger

        NOT_YET_IMPLEMENTED_ITEMS = [
            "focus-sash",
            "focus-band",
            "white-herb",
            "mental-herb",
            "power-herb",
            "throat-spray",
            "weakness-policy",
        ]

        # Add item rows
        for item in item_list:
            row_layout = QHBoxLayout()

            item_label = QLabel(format_item_name(item))
            give_button = QPushButton(f"Give {format_item_name(item)}")
            give_button.clicked.connect(lambda clicked, i=item: self.expanded_give_item_func(i))
            if item in NOT_YET_IMPLEMENTED_ITEMS or item.endswith("-berry") or item.endswith("-gem"):
                # NOTE (Axil): As time of writing, single use items are not yet implemented.
                # It seems to me that, actually, they are not even implemented in the Poke-engine. Although
                # I haven't dug too much.
                # Therefore, for now, and hopefully as a not too permanent temporary fix, I will prevent the
                # user from giving out single-use items.
                give_button.setToolTip("Single use held items are not yet implemented.")
                give_button.setEnabled(False)
                give_button.clicked.connect(
                    lambda clicked: self.logger.log_and_showinfo("info", "Single use held items are not yet implemented.")
                    )

            row_layout.addWidget(item_label)
            row_layout.addStretch()
            row_layout.addWidget(give_button)

            # Optional: separate rows with a line
            row_frame = QFrame()
            row_frame.setLayout(row_layout)
            scroll_layout.addWidget(row_frame)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        # Add scroll area to main layout
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

    def expanded_give_item_func(self, item_name: str):
        # small intermediary function. This allows me to display a confirmation message after giving the item.
        self.give_item_func(item_name)
        self.close()
