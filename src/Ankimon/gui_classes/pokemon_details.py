from math import exp, pi, cos, sin
import json
from typing import Any

from aqt import mw, qconnect
from aqt.utils import showWarning
from PyQt6.QtGui import QPixmap, QPainter, QIcon, QPen, QBrush, QPolygonF, QFont
from PyQt6.QtCore import Qt, QPointF, QPropertyAnimation, QRect, QEasingCurve, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QWidget,
    QMessageBox,
)

from ..pyobj.attack_dialog import AttackDialog
from ..pyobj.pokemon_trade import PokemonTrade
from ..pyobj.error_handler import show_warning_with_traceback
from ..pyobj.pokemon_obj import PokemonObject
from ..pyobj.InfoLogger import ShowInfoLogger
from .stat_comparison_dialog import show_stat_comparison
from ..functions.pokedex_functions import (
    get_pokemon_diff_lang_name,
    get_pokemon_descriptions,
    get_all_pokemon_moves,
    find_details_move,
    search_pokedex_by_id,
)
from ..functions.pokemon_functions import find_experience_for_level
from ..functions.gui_functions import type_icon_path, move_category_path
from ..functions.sprite_functions import get_sprite_path
from ..gui_entities import MovieSplashLabel
from ..business import split_string_by_length
from ..utils import format_move_name, load_custom_font
from ..resources import (
    icon_path,
    addon_dir,
    mainpokemon_path,
    mypokemon_path,
    pokemon_tm_learnset_path,
    itembag_path,
)
from ..texts import (
    attack_details_window_template,
    attack_details_window_template_end,
    remember_attack_details_window_template,
    remember_attack_details_window_template_end,
)


def PokemonCollectionDetails(
    name: str,
    level: int,
    id: int,
    shiny: bool,
    ability: str,
    type: list[str],
    detail_stats: dict[Any, Any],
    attacks: list[str],
    base_experience: int,
    growth_rate: str,
    ev: dict[str, int],
    iv: dict[str, int],
    gender: str,
    nickname: str,
    individual_id: str,
    pokemon_defeated: int,
    everstone: bool,
    captured_date: str,
    language: int,
    gif_in_collection: bool,
    remove_levelcap: bool,
    logger: ShowInfoLogger,
    refresh_callback: callable,
    close_callback: callable = None,
    battles_won: int = 0,
    battles_lost: int = 0,
) -> QVBoxLayout:
    """
    Create a detailed information panel layout for a Pokemon in the PC collection.
    
    This function generates a comprehensive QVBoxLayout containing all relevant
    information about a Pokemon, including its sprite, stats radar chart, type icons,
    moves, and action buttons. The layout is designed to be displayed in the
    right-hand panel of the Pokemon PC dialog.
    
    The panel includes:
        - Pokemon sprite (animated GIF if enabled) with level
        - Hexagonal radar chart showing stat distribution with values
        - Pokemon name, nickname, gender symbol, and shiny indicator
        - Pokedex description text
        - Type icons (up to 2)
        - Ability name
        - Experience bar showing progress to next level
        - Current moves list
        - Action buttons: Attack Details, Learn Moves, Forget Moves, TM Moves
        - Caught date and defeated count
        - Rename input and button
        - Trade and Release buttons
    
    Args:
        name (str): The Pokemon's species name (e.g., "Pikachu").
        level (int): Current level (1-100, or higher if level cap removed).
        id (int): National Pokedex number (1-1010+).
        shiny (bool): Whether this is a shiny variant.
        ability (str): The Pokemon's ability name.
        type (list[str]): List of type names (1-2 types, e.g., ["Electric"]).
        detail_stats (dict[Any, Any]): Base stats dictionary with keys:
            'hp', 'atk', 'def', 'spa', 'spd', 'spe', and optionally 'xp'.
        attacks (list[str]): List of up to 4 move names the Pokemon knows.
        base_experience (int): Base experience yield when defeated.
        growth_rate (str): Experience growth rate category.
        ev (dict[str, int]): Effort Values for each stat.
        iv (dict[str, int]): Individual Values for each stat.
        gender (str): Gender identifier ("M", "F", or "" for genderless).
        nickname (str): Custom nickname, or empty string if none.
        individual_id (str): Unique UUID for this specific Pokemon instance.
        pokemon_defeated (int): Count of Pokemon this one has defeated.
        everstone (bool): Whether holding an Everstone (prevents evolution).
        captured_date (str): Date string when the Pokemon was caught.
        language (int): Language code for localized names and fonts.
        gif_in_collection (bool): Whether to use animated GIF sprites.
        remove_levelcap (bool): Whether the level 100 cap is removed.
        logger (ShowInfoLogger): Logger instance for error reporting.
        refresh_callback (callable): Function to call when UI needs refresh
            after actions like renaming or trading.
    
    Returns:
        QVBoxLayout: A vertical layout containing all Pokemon detail widgets.
            Can be set on a QWidget or added to another layout.
    
    Raises:
        Exception: Caught internally, logs error and returns empty layout.
    
    Example:
        >>> layout = PokemonCollectionDetails(
        ...     name="Charizard", level=50, id=6, shiny=False,
        ...     ability="Blaze", type=["Fire", "Flying"],
        ...     detail_stats={"hp": 78, "atk": 84, "def": 78, "spa": 109, "spd": 85, "spe": 100, "xp": 5000},
        ...     attacks=["Flamethrower", "Fly", "Dragon Claw", "Air Slash"],
        ...     base_experience=240, growth_rate="medium-slow",
        ...     ev={"hp": 0, "atk": 0, "def": 0, "spa": 3, "spd": 0, "spe": 0},
        ...     iv={"hp": 31, "atk": 25, "def": 28, "spa": 31, "spd": 30, "spe": 31},
        ...     gender="M", nickname="Blaze", individual_id="abc-123",
        ...     pokemon_defeated=42, everstone=False, captured_date="2024-01-15",
        ...     language=9, gif_in_collection=True, remove_levelcap=False,
        ...     logger=my_logger, refresh_callback=refresh_func
        ... )
        >>> container = QWidget()
        >>> container.setLayout(layout)
    """
    # Create a layout for the details panel
    try:
        lang_name = get_pokemon_diff_lang_name(int(id), language).capitalize()
        lang_desc = get_pokemon_descriptions(int(id), language)
        description = lang_desc
        
        # Main layout with proper spacing
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # === Calculate stats first (needed for radar) ===
        stats_list = []
        for key in ("hp", "atk", "def", "spa", "spd", "spe"):
            val = detail_stats.get(key, 0)
            stat = PokemonObject.calc_stat(key, val, level, iv[key], ev[key], "serious")
            stats_list.append(stat)
        stats_list.append(detail_stats.get("xp", 0))
        
        _stats_dict = {
            "hp": stats_list[0],
            "atk": stats_list[1],
            "def": stats_list[2],
            "spa": stats_list[3],
            "spd": stats_list[4],
            "spe": stats_list[5],
            "xp": stats_list[6],
        }
        
        radar_stats = {
            "HP": stats_list[0],
            "Atk": stats_list[1],
            "Def": stats_list[2],
            "Sp.A": stats_list[3],
            "Sp.D": stats_list[4],
            "Spd": stats_list[5],
        }
        
        # === HEADER SECTION: Sprite + Radar side by side ===
        header_section = QHBoxLayout()
        header_section.setSpacing(4)
        
        # Left: Pokemon sprite with level
        sprite_container = QVBoxLayout()
        sprite_container.setSpacing(2)
        
        pkmnimage_label = QLabel()
        pkmnpixmap = QPixmap()
        pkmnimage_path = get_sprite_path(
            "front", "gif" if gif_in_collection else "png", id, shiny, gender
        )

        if gif_in_collection:
            pkmnimage_label = MovieSplashLabel(pkmnimage_path)
        else:
            if not pkmnpixmap.load(str(pkmnimage_path)):
                logger.log_and_showinfo(
                    "warning", f"Failed to load Pokémon image: {pkmnimage_path}"
                )
            max_width = 96
            original_width = pkmnpixmap.width() if pkmnpixmap.width() > 0 else 1
            original_height = pkmnpixmap.height()
            new_height = (original_height * max_width) // original_width
            pkmnpixmap = pkmnpixmap.scaled(max_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pkmnimage_label.setPixmap(pkmnpixmap)
        
        pkmnimage_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pkmnimage_label.setMinimumSize(100, 100)
        sprite_container.addWidget(pkmnimage_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Level label under sprite
        level_font = load_custom_font(16, language)
        level_label = QLabel(f"Lv. {level}")
        level_label.setFont(level_font)
        level_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sprite_container.addWidget(level_label)
        
        header_section.addLayout(sprite_container)
        
        # Right: Radar chart with stat values
        radar_chart = createStatsRadarChart(radar_stats, size=180)
        radar_label = QLabel()
        radar_label.setPixmap(radar_chart)
        radar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        radar_label.setMinimumSize(180, 180)
        header_section.addWidget(radar_label)
        
        layout.addLayout(header_section)

        # Gender symbol
        if gender == "M":
            gender_symbol = "♂"
        elif gender == "F":
            gender_symbol = "♀"
        else:
            gender_symbol = ""

        # Name styling
        namefont = load_custom_font(22, language)
        namefont.setBold(True)
        
        if nickname:
            display_name = f"{nickname} ({lang_name})"
        else:
            display_name = lang_name
        
        shiny_indicator = " ✨" if shiny else ""
        name_label = QLabel(f"{display_name}{shiny_indicator} {gender_symbol}")
        name_label.setFont(namefont)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # === DESCRIPTION (below name) ===
        desc_font = load_custom_font(13, language)
        if language in (1, 2, 3, 4, 11, 12):
            result = list(split_string_by_length(description, 35))
        else:
            result = list(split_string_by_length(description, 50))
        description_formatted = "\n".join(result)
        
        desc_label = QLabel(description_formatted)
        desc_label.setFont(desc_font)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888888; font-style: italic;")
        layout.addWidget(desc_label)
        
        # === TYPE SECTION ===
        type_section = QHBoxLayout()
        type_section.setSpacing(8)
        type_section.addStretch()
        
        for t in type[:2]:  # Max 2 types
            type_file = f"{t.lower()}.png"
            type_path = addon_dir / "addon_sprites" / "Types" / type_file
            type_label = QLabel()
            type_pixmap = QPixmap()
            if type_pixmap.load(str(type_path)):
                type_pixmap = type_pixmap.scaled(36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                type_label.setPixmap(type_pixmap)
                type_section.addWidget(type_label)
        
        type_section.addStretch()
        layout.addLayout(type_section)
        
        # === INFO SECTION: Ability ===
        info_font = load_custom_font(14, language)
        
        ability_label = QLabel(f"Ability: {ability.capitalize()}")
        ability_label.setFont(info_font)
        ability_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ability_label)
        
        # === XP BAR ONLY ===
        xp_layout = PokemonDetailsXPBar(
            _stats_dict, growth_rate, level, remove_levelcap, language
        )
        
        xp_container = QWidget()
        xp_container.setLayout(xp_layout)
        layout.addWidget(xp_container)
        
        # === MOVES SECTION ===
        moves_font = load_custom_font(15, language)
        moves_header = QLabel("Moves")
        moves_header.setFont(load_custom_font(18, language))
        moves_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(moves_header)
        
        moves_text = " • ".join([a.capitalize().replace("-", " ") for a in attacks[:4]])
        moves_label = QLabel(moves_text)
        moves_label.setFont(moves_font)
        moves_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        moves_label.setWordWrap(True)
        layout.addWidget(moves_label)
        
        # === MOVE BUTTONS ===
        move_buttons_layout = QVBoxLayout()
        move_buttons_layout.setSpacing(4)
        
        attacks_details_button = QPushButton("Attack Details")
        qconnect(attacks_details_button.clicked, lambda: attack_details_window(attacks))
        
        all_attacks = get_all_pokemon_moves(name, level)
        remember_attacks_button = QPushButton("Learn Moves")
        qconnect(remember_attacks_button.clicked, lambda: remember_attack_details_window(individual_id, attacks, all_attacks, logger))
        
        forget_attacks_button = QPushButton("Forget Moves")
        qconnect(forget_attacks_button.clicked, lambda: forget_attack_details_window(individual_id, attacks, logger))
        
        tm_attacks_button = QPushButton("TM Moves")
        qconnect(tm_attacks_button.clicked, lambda: tm_attack_details_window(id, individual_id, attacks, logger))
        
        # Compare Stats button
        compare_button = QPushButton("📊 Compare Stats")
        compare_button.setStyleSheet("QPushButton { background-color: #1565c0; } QPushButton:hover { background-color: #1976d2; }")
        pokemon_data_for_compare = {
            'name': name,
            'level': level,
            'id': id,
            'base_stats': detail_stats,
            'iv': iv,
            'ev': ev,
            'individual_id': individual_id,
            'nickname': nickname,
        }
        qconnect(compare_button.clicked, lambda: show_stat_comparison(pokemon_data_for_compare))
        
        move_buttons_layout.addWidget(attacks_details_button)
        move_buttons_layout.addWidget(remember_attacks_button)
        move_buttons_layout.addWidget(forget_attacks_button)
        move_buttons_layout.addWidget(tm_attacks_button)
        move_buttons_layout.addWidget(compare_button)
        layout.addLayout(move_buttons_layout)
        
        # === EXTRA INFO ===
        extra_layout = QHBoxLayout()
        extra_font = load_custom_font(14, language)
        
        if captured_date:
            captured_label = QLabel(f"Caught: {captured_date.split()[0]}")
        else:
            captured_label = QLabel("Caught: N/A")
        captured_label.setFont(extra_font)
        
        defeated_label = QLabel(f"Defeated: {pokemon_defeated}")
        defeated_label.setFont(extra_font)
        
        extra_layout.addWidget(captured_label)
        extra_layout.addStretch()
        extra_layout.addWidget(defeated_label)
        layout.addLayout(extra_layout)
        
        # === BATTLE STATS ===
        battle_stats_layout = QHBoxLayout()
        
        total_battles = battles_won + battles_lost
        win_rate = (battles_won / total_battles * 100) if total_battles > 0 else 0
        
        wins_label = QLabel(f"⚔️ Wins: {battles_won}")
        wins_label.setFont(extra_font)
        wins_label.setStyleSheet("color: #2e7d32;")  # Green for wins
        
        losses_label = QLabel(f"💀 Losses: {battles_lost}")
        losses_label.setFont(extra_font)
        losses_label.setStyleSheet("color: #c62828;")  # Red for losses
        
        # Win rate with color coding
        if win_rate >= 75:
            rate_color = "#2e7d32"  # Green
        elif win_rate >= 50:
            rate_color = "#1565c0"  # Blue
        else:
            rate_color = "#c62828"  # Red
        
        rate_label = QLabel(f"📊 {win_rate:.0f}%")
        rate_label.setFont(extra_font)
        rate_label.setStyleSheet(f"color: {rate_color};")
        
        battle_stats_layout.addWidget(wins_label)
        battle_stats_layout.addStretch()
        battle_stats_layout.addWidget(losses_label)
        battle_stats_layout.addStretch()
        battle_stats_layout.addWidget(rate_label)
        layout.addLayout(battle_stats_layout)
        
        # === ACTION BUTTONS ===
        layout.addSpacing(8)
        
        rename_input = QLineEdit()
        rename_input.setPlaceholderText("New nickname...")
        layout.addWidget(rename_input)
        
        action_layout = QHBoxLayout()
        action_layout.setSpacing(6)
        
        rename_button = QPushButton("Rename")
        qconnect(rename_button.clicked, lambda: rename_pkmn(rename_input.text(), name, individual_id, logger, refresh_callback))
        
        trade_button = QPushButton("Trade")
        qconnect(trade_button.clicked, lambda: PokemonTrade(name, id, level, ability, iv, ev, gender, attacks, individual_id, shiny, logger, refresh_callback))
        
        release_button = QPushButton("Release")
        release_button.setStyleSheet("QPushButton { background-color: #b71c1c; } QPushButton:hover { background-color: #d32f2f; }")
        qconnect(release_button.clicked, lambda: PokemonFree(individual_id, name, logger, refresh_callback, pkmnimage_label, close_callback))
        
        action_layout.addWidget(rename_button)
        action_layout.addWidget(trade_button)
        action_layout.addWidget(release_button)
        layout.addLayout(action_layout)
        
        layout.addStretch()

        return layout

    except Exception as e:
        show_warning_with_traceback(
            exception=e, message="Error occured in Pokemon Details Button:"
        )
        return QVBoxLayout()


def PokemonDetailsXPBar(
    detail_stats: dict,
    growth_rate: str,
    level: int,
    remove_levelcap: bool,
    language: int
) -> QVBoxLayout:
    """
    Create a layout containing only the experience (XP) progress bar.
    
    This function generates a single-row layout displaying the Pokemon's current
    experience points as a visual progress bar. The bar fills proportionally
    based on the XP needed to reach the next level.
    
    Args:
        detail_stats (dict): Dictionary containing Pokemon stats.
            Must include 'xp' key with the current experience points.
            Example: {'hp': 100, 'atk': 50, 'xp': 1500}
        growth_rate (str): The Pokemon's growth rate category.
            Used to calculate XP needed for next level.
            Values: 'fast', 'medium-fast', 'medium-slow', 'slow', etc.
        level (int): The Pokemon's current level (1-100).
            Used to calculate XP threshold for next level.
        remove_levelcap (bool): Whether the level 100 cap is removed.
            If True, allows calculation beyond level 100.
        language (int): Language code for font loading.
            Determines which custom font variant to use.
    
    Returns:
        QVBoxLayout: A vertical layout containing the XP bar row with:
            - Label showing "Exp"
            - Numeric value of current XP
            - Visual progress bar (cyan colored)
    
    Example:
        >>> stats = {'xp': 500, 'hp': 45}
        >>> layout = PokemonDetailsXPBar(stats, 'medium-fast', 15, False, 9)
        >>> container.setLayout(layout)
    """
    layout = QVBoxLayout()
    layout.setSpacing(2)
    layout.setContentsMargins(8, 6, 8, 6)
    
    xp_color = QColor(100, 200, 255)  # Cyan
    stat_font = load_custom_font(13, language)
    
    xp_value = detail_stats.get("xp", 0)
    
    layout_row = QHBoxLayout()
    layout_row.setSpacing(4)
    layout_row.setContentsMargins(0, 0, 0, 0)
    
    # Stat name - left aligned
    stat_label = QLabel("Exp")
    stat_label.setFont(stat_font)
    stat_label.setFixedWidth(60)
    stat_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
    
    # Value - right aligned before bar
    value_label = QLabel(str(xp_value))
    value_label.setFont(stat_font)
    value_label.setFixedWidth(36)
    value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    
    # Calculate bar width
    bar_max = 180
    experience = int(find_experience_for_level(growth_rate, level, True))
    bar_value = int((int(xp_value) / max(1, int(experience))) * bar_max)
    
    # Create stat bar
    bar_label = QLabel()
    pixmap = createStatBar(xp_color, bar_value, bar_max)
    bar_label.setPixmap(pixmap)
    bar_label.setFixedHeight(12)
    
    layout_row.addWidget(stat_label)
    layout_row.addWidget(value_label)
    layout_row.addWidget(bar_label)
    
    layout.addLayout(layout_row)
    
    return layout


def PokemonDetailsStats(detail_stats, growth_rate, level, remove_levelcap, language):
    CompleteTable_layout = QVBoxLayout()
    CompleteTable_layout.setSpacing(2)
    CompleteTable_layout.setContentsMargins(8, 6, 8, 6)
    
    # Stat colors - Pokemon-style colors
    stat_colors = {
        "hp": QColor(255, 89, 89),     # Red
        "atk": QColor(255, 175, 85),   # Orange
        "def": QColor(250, 224, 80),   # Yellow
        "spa": QColor(100, 148, 237),  # Blue
        "spd": QColor(135, 206, 132),  # Green
        "spe": QColor(250, 130, 170),  # Pink
        "xp": QColor(100, 200, 255),   # Cyan
    }
    
    # Stat display names - full names for clarity
    stat_names = {
        "hp": "HP",
        "atk": "Attack",
        "def": "Defense",
        "spa": "Sp. Atk",
        "spd": "Sp. Def",
        "spe": "Speed",
        "xp": "Exp",
    }

    # Fonts
    stat_font = load_custom_font(13, language)

    # Populate the table and create the stat bars
    for stat, value in detail_stats.items():
        if stat not in stat_colors:
            continue

        layout_row = QHBoxLayout()
        layout_row.setSpacing(4)
        layout_row.setContentsMargins(0, 0, 0, 0)
        
        # Stat name - left aligned
        stat_label = QLabel(stat_names.get(stat, stat.upper()))
        stat_label.setFont(stat_font)
        stat_label.setFixedWidth(60)
        stat_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        # Value - right aligned before bar
        value_label = QLabel(str(value))
        value_label.setFont(stat_font)
        value_label.setFixedWidth(36)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        # Calculate bar width (max 255 stat = full bar)
        bar_max = 180
        if stat == "xp":
            experience = int(find_experience_for_level(growth_rate, level, True))
            bar_value = int((int(value) / max(1, int(experience))) * bar_max)
        else:
            # Scale based on typical max stat of ~255
            bar_value = min(int((value / 255) * bar_max), bar_max)
        
        # Create stat bar
        bar_label = QLabel()
        pixmap = createStatBar(stat_colors.get(stat), bar_value, bar_max)
        bar_label.setPixmap(pixmap)
        bar_label.setFixedHeight(12)
        
        layout_row.addWidget(stat_label)
        layout_row.addWidget(value_label)
        layout_row.addWidget(bar_label)
        
        CompleteTable_layout.addLayout(layout_row)

    return CompleteTable_layout


def createStatBar(
    color: QColor,
    value: int,
    max_width: int = 160
) -> QPixmap:
    """
    Create a rounded stat bar with a filled portion and dark background.
    
    Generates a horizontal progress bar as a QPixmap, with a dark rounded
    background and a colored fill representing the stat value. The bar
    uses anti-aliased rounded rectangles for a polished appearance.
    
    Args:
        color (QColor): The fill color for the stat portion of the bar.
            Different stats use different colors (e.g., red for HP, orange for Attack).
            If None, defaults to gray (#808080).
        value (int): The width in pixels to fill with color.
            Should be between 0 and max_width. Values exceeding max_width are clamped.
        max_width (int, optional): The total width of the bar in pixels.
            Defaults to 160. This is the width of the background bar.
    
    Returns:
        QPixmap: A 12-pixel tall pixmap containing the rendered stat bar.
            Has transparent areas outside the rounded corners.
    
    Visual Structure:
        - Background: Dark semi-transparent rounded rectangle (#282828 at 70% opacity)
        - Foreground: Colored rounded rectangle from 0 to `value` pixels
        - Corner radius: 4 pixels for smooth rounded ends
    
    Example:
        >>> hp_color = QColor(255, 89, 89)  # Red
        >>> bar_pixmap = createStatBar(hp_color, 120, 180)
        >>> label = QLabel()
        >>> label.setPixmap(bar_pixmap)
    """
    height = 12
    pixmap = QPixmap(max_width, height)
    pixmap.fill(QColor(0, 0, 0, 0))

    if color is None:
        color = QColor(128, 128, 128)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Draw background bar (rounded)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(40, 40, 40, 180))
    painter.drawRoundedRect(0, 0, max_width, height, 4, 4)

    # Draw colored bar (rounded)
    if value > 0:
        painter.setBrush(color)
        painter.drawRoundedRect(0, 0, min(value, max_width), height, 4, 4)

    painter.end()
    return pixmap


def createStatsRadarChart(stats_dict: dict, size: int = 160) -> QPixmap:
    """
    Create a hexagonal radar chart visualization for Pokemon stats.
    
    Generates a radar/spider chart with six axes representing the core Pokemon
    stats (HP, Attack, Defense, Special Attack, Special Defense, Speed). Each
    stat is normalized against a maximum value of 200 and displayed as a filled
    polygon with color-coded vertex points.
    
    The chart includes:
    - Hexagonal guide lines at 33%, 66%, and 100% levels
    - Axis lines from center to each vertex
    - Semi-transparent filled polygon showing stat distribution
    - Color-coded points at each stat vertex
    - Labels with stat names AND numeric values
    
    Args:
        stats_dict (dict): Dictionary mapping stat names to numeric values.
            Expected keys: 'HP', 'Atk', 'Def', 'Sp.A', 'Sp.D', 'Spd'
            Example: {'HP': 78, 'Atk': 84, 'Def': 78, 'Sp.A': 109, 'Sp.D': 85, 'Spd': 100}
        size (int, optional): The width and height of the output pixmap in pixels.
            Defaults to 160. Larger values provide more detail but use more memory.
    
    Returns:
        QPixmap: A square pixmap with transparent background containing the
            rendered radar chart. Can be displayed in a QLabel via setPixmap().
    
    Color Scheme:
        - HP: Red (#FF5959)
        - Attack: Orange (#FFAF55)
        - Defense: Yellow (#FAE050)
        - Sp.A: Blue (#6494ED)
        - Sp.D: Green (#87CE84)
        - Speed: Pink (#FA82AA)
        - Fill: Semi-transparent blue
    
    Example:
        >>> stats = {'HP': 80, 'Atk': 100, 'Def': 70, 'Sp.A': 120, 'Sp.D': 80, 'Spd': 90}
        >>> chart_pixmap = createStatsRadarChart(stats, size=180)
        >>> label = QLabel()
        >>> label.setPixmap(chart_pixmap)
    
    Note:
        Stats are normalized to a maximum of 200. Values above 200 are capped.
        Very low stats are given a minimum 5% radius to remain visible.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    
    center_x = size // 2
    center_y = size // 2
    max_radius = (size // 2) - 35  # Leave more room for labels with values
    
    # Stat order (clockwise from top): HP, Atk, Def, Spd, Sp.D, Sp.A
    stat_order = ["HP", "Atk", "Def", "Spd", "Sp.D", "Sp.A"]
    num_stats = len(stat_order)
    
    # Stat colors
    stat_colors = {
        "HP": QColor(255, 89, 89),
        "Atk": QColor(255, 175, 85),
        "Def": QColor(250, 224, 80),
        "Sp.A": QColor(100, 148, 237),
        "Sp.D": QColor(135, 206, 132),
        "Spd": QColor(250, 130, 170),
    }
    
    # Draw background hexagons (guide lines)
    for level in [0.33, 0.66, 1.0]:
        radius = max_radius * level
        points = []
        for i in range(num_stats):
            angle = (pi / 2) - (2 * pi * i / num_stats)  # Start from top
            x = center_x + radius * cos(angle)
            y = center_y - radius * sin(angle)
            points.append(QPointF(x, y))
        
        polygon = QPolygonF(points)
        painter.setPen(QPen(QColor(150, 150, 150, 100), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPolygon(polygon)
    
    # Draw axis lines from center to each vertex
    painter.setPen(QPen(QColor(150, 150, 150, 80), 1))
    for i in range(num_stats):
        angle = (pi / 2) - (2 * pi * i / num_stats)
        x = center_x + max_radius * cos(angle)
        y = center_y - max_radius * sin(angle)
        painter.drawLine(QPointF(center_x, center_y), QPointF(x, y))
    
    # Calculate stat points - scale based on max possible stat (~200 for most Pokemon)
    stat_points = []
    max_stat = 200  # More realistic max for leveled Pokemon
    for i, stat_name in enumerate(stat_order):
        value = stats_dict.get(stat_name, 0)
        normalized = min(value / max_stat, 1.0)  # Cap at 100%
        radius = max_radius * max(normalized, 0.05)  # Minimum 5% so stats are visible
        
        angle = (pi / 2) - (2 * pi * i / num_stats)
        x = center_x + radius * cos(angle)
        y = center_y - radius * sin(angle)
        stat_points.append(QPointF(x, y))
    
    # Draw filled stat polygon
    if stat_points:
        polygon = QPolygonF(stat_points)
        # Semi-transparent fill
        fill_color = QColor(100, 180, 255, 100)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(QPen(QColor(60, 140, 220, 200), 2))
        painter.drawPolygon(polygon)
    
    # Draw stat points
    for i, point in enumerate(stat_points):
        stat_name = stat_order[i]
        color = stat_colors.get(stat_name, QColor(255, 255, 255))
        painter.setBrush(QBrush(color))
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawEllipse(point, 4, 4)
    
    # Draw stat labels with values
    label_font = QFont("Arial", 9)
    label_font.setBold(True)
    painter.setFont(label_font)
    painter.setPen(QColor(220, 220, 220))
    
    label_offset = 16
    for i, stat_name in enumerate(stat_order):
        angle = (pi / 2) - (2 * pi * i / num_stats)
        x = center_x + (max_radius + label_offset) * cos(angle)
        y = center_y - (max_radius + label_offset) * sin(angle)
        
        # Include the stat value in the label
        stat_value = stats_dict.get(stat_name, 0)
        text = f"{stat_name}: {stat_value}"
        
        # Calculate text bounding rect for centering
        text_width = painter.fontMetrics().horizontalAdvance(text)
        text_height = painter.fontMetrics().height()
        
        text_x = x - text_width // 2
        text_y = y + text_height // 4
        
        painter.drawText(int(text_x), int(text_y), text)
    
    painter.end()
    return pixmap


def attack_details_window(attacks):
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    layout = QVBoxLayout()
    # HTML content
    html_content = attack_details_window_template
    # Loop through the list of attacks and add them to the HTML content
    for attack in attacks:
        move = find_details_move(format_move_name(attack))
        if move is None:
            attack = attack.replace(" ", "")
            try:
                move = find_details_move(format_move_name(attack))
            except:
                logger.log_and_showinfo(
                    "info", f"Can't find the attack {attack} in the database."
                )
                move = find_details_move("tackle")
        if move is None:
            continue
        html_content += f"""
        <tr>
          <td class="move-name">{move["name"]}</td>
          <td><img src="{type_icon_path(move["type"])}" alt="{move["type"]}"/></td>
          <td><img src="{move_category_path(move["category"].lower())}" alt="{move["category"]}"/></td>
          <td class="basePower">{move["basePower"]}</td>
          <td class="no-accuracy">{move["accuracy"]}</td>
          <td>{move["pp"]}</td>
          <td>{move["shortDesc"]}</td>
        </tr>
        """
    html_content += attack_details_window_template_end

    # Create a QLabel to display the HTML content
    label = QLabel(html_content)
    label.setAlignment(
        Qt.AlignmentFlag.AlignLeft
    )  # Align the label's content to the top
    label.setScaledContents(True)  # Enable scaling of the pixmap

    layout.addWidget(label)
    window.setLayout(layout)
    window.exec()


def remember_attack_details_window(individual_id, attack_set, all_attacks, logger):
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    outer_layout = QVBoxLayout(window)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    content_widget = QWidget()
    layout = QHBoxLayout(content_widget)
    html_content = remember_attack_details_window_template
    for attack in all_attacks:
        move = find_details_move(attack)
        html_content += f"""
        <tr>
          <td class="move-name">{move["name"]}</td>
          <td><img src="{type_icon_path(move["type"])}" alt="{move["type"]}"/></td>
          <td><img src="{move_category_path(move["category"].lower())}" alt="{move["category"]}"/></td>
          <td class="basePower">{move["basePower"]}</td>
          <td class="no-accuracy">{move["accuracy"]}</td>
          <td>{move["pp"]}</td>
          <td>{move["shortDesc"]}</td>
        </tr>
        """
    html_content += remember_attack_details_window_template_end
    label = QLabel(html_content)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    label.setScaledContents(True)
    attack_layout = QVBoxLayout()
    for attack in all_attacks:
        remember_attack_button = QPushButton(f"Remember {attack}")
        qconnect(
            remember_attack_button.clicked,
            lambda checked, a=attack: remember_attack(
                individual_id, attack_set, a, logger
            ),
        )
        attack_layout.addWidget(remember_attack_button)
    attack_layout_widget = QWidget()
    attack_layout_widget.setLayout(attack_layout)
    layout.addWidget(label)
    layout.addWidget(attack_layout_widget)
    scroll_area.setWidget(content_widget)
    outer_layout.addWidget(scroll_area)
    window.resize(1000, 400)
    window.exec()


def forget_attack_details_window(
    individual_id: int, attack_set: list[str], logger: "InfoLogger.ShowInfoLogger"
) -> None:
    """
    Creates a window that will allow the user to erase moves from a Pokemon.

    Args:
        id (int): The Pokemon's identifier.
        attack_set (list[str]): The Pokemon's move set.
        logger: Logger object that can log info and display windows containing messages.

    Returns:
        None
    """
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    outer_layout = QVBoxLayout(window)
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    content_widget = QWidget()
    layout = QHBoxLayout(content_widget)
    html_content = remember_attack_details_window_template
    for attack in attack_set:
        move = find_details_move(format_move_name(attack))
        if move is None:
            continue
        html_content += f"""
        <tr>
          <td class="move-name">{move["name"]}</td>
          <td><img src="{type_icon_path(move["type"])}" alt="{move["type"]}"/></td>
          <td><img src="{move_category_path(move["category"].lower())}" alt="{move["category"]}"/></td>
          <td class="basePower">{move["basePower"]}</td>
          <td class="no-accuracy">{move["accuracy"]}</td>
          <td>{move["pp"]}</td>
          <td>{move["shortDesc"]}</td>
        </tr>
        """
    html_content += remember_attack_details_window_template_end
    label = QLabel(html_content)
    label.setAlignment(Qt.AlignmentFlag.AlignLeft)
    label.setScaledContents(True)
    attack_layout = QVBoxLayout()
    for attack in attack_set:
        forget_attack_button = QPushButton(f"Forget {attack}")
        qconnect(
            forget_attack_button.clicked,
            lambda checked, a=attack: forget_attack(
                individual_id, attack_set, a, logger
            ),
        )
        attack_layout.addWidget(forget_attack_button)
    attack_layout_widget = QWidget()
    attack_layout_widget.setLayout(attack_layout)
    layout.addWidget(label)
    layout.addWidget(attack_layout_widget)
    scroll_area.setWidget(content_widget)
    outer_layout.addWidget(scroll_area)
    window.resize(1000, 400)
    window.exec()


def remember_attack(
    individual_id: str, attacks: list[str], new_attack: str, logger: ShowInfoLogger
):
    if new_attack in attacks:
        logger.log_and_showinfo("warning", "Your pokemon already knows this move!")
        return
    if not mainpokemon_path.is_file():
        logger.log_and_showinfo("warning", "Missing Mainpokemon Data !")
        return

    with open(str(mypokemon_path), "r", encoding="utf-8") as output_file:
        mypokemondata = json.load(output_file)
    for pokemon_data in mypokemondata:
        # Use individual_id for matching
        if pokemon_data["individual_id"] != individual_id:
            continue

        attacks = pokemon_data["attacks"]
        if new_attack:
            msg = ""
            msg += f"Your {pokemon_data['name'].capitalize()} can learn a new attack !"
            if len(attacks) < 4:
                attacks.append(new_attack)
                msg += f"\n Your {pokemon_data['name'].capitalize()} has learned {new_attack} !"
                logger.log_and_showinfo("info", f"{msg}")
            else:
                dialog = AttackDialog(attacks, new_attack)
                if dialog.exec() == QDialog.DialogCode.Accepted:
                    selected_attack = dialog.selected_attack
                    index_to_replace = None
                    for index, attack in enumerate(attacks):
                        if attack == selected_attack:
                            index_to_replace = index
                    if index_to_replace is not None:
                        attacks[index_to_replace] = new_attack
                        logger.log_and_showinfo(
                            "info", f"Replaced '{selected_attack}' with '{new_attack}'"
                        )
                    else:
                        logger.log_and_showinfo(
                            "info", f"{new_attack} will be discarded."
                        )
        pokemon_data["attacks"] = attacks

        with open(str(mypokemon_path), "w") as output_file:
            json.dump(mypokemondata, output_file, indent=2)

        # Update mainpokemon file if necessary
        with open(mainpokemon_path, "r", encoding="utf-8") as json_file:
            main_pokemon_data = json.load(json_file)
        for mainpkmndata in main_pokemon_data:
            if mainpkmndata["individual_id"] == individual_id:
                mainpkmndata["attacks"] = attacks
                break
        with open(str(mainpokemon_path), "w") as json_file:
            json.dump(main_pokemon_data, json_file, indent=2)

        break


def forget_attack(
    individual_id: int,
    attacks: list[str],
    attack_to_forget: str,
    logger: ShowInfoLogger,
) -> None:
    """
    Forgets a Pokemon's move. This is done by erasing the chosen move from the list
    of attacks known by the Pokemon and then saving that new Pokemon data in the main
    Pokemon data file.

    Args:
        id (int): The Pokemon's identifier.
        attacks (list[str]): The Pokemon's move set.
        attack_to_forget (str): Name of the move to forget.
        logger: Logger object that can log info and display windows containing messages.

    Returns:
        None
    """

    if not mainpokemon_path.is_file():
        logger.log_and_showinfo("warning", "Missing Mainpokemon Data !")
        return

    with open(str(mypokemon_path), "r", encoding="utf-8") as output_file:
        mypokemondata = json.load(output_file)
    for pokemon_data in mypokemondata:
        # Use individual_id for matching
        if pokemon_data["individual_id"] != individual_id:
            continue

        attacks = pokemon_data["attacks"]
        if attack_to_forget in attacks:
            if len(attacks) > 1:
                attacks.remove(attack_to_forget)
                msg = f"Your {pokemon_data['name'].capitalize()} forgot {attack_to_forget}."
                logger.log_and_showinfo("info", f"{msg}")
            else:  # If we reach here, it means the Pokemon only has 1 move left. We can't allow this move to be forgotten
                msg = f"Your {pokemon_data['name'].capitalize()} only knows this move, you can't forget it ! "
                logger.log_and_showinfo("info", f"{msg}")
        else:
            msg = f"Your {pokemon_data['name'].capitalize()} does not know {attack_to_forget}."
            logger.log_and_showinfo("info", f"{msg}")
        pokemon_data["attacks"] = attacks

        with open(str(mypokemon_path), "w") as output_file:
            json.dump(mypokemondata, output_file, indent=2)

        # Update mainpokemon file if necessary
        with open(mainpokemon_path, "r", encoding="utf-8") as json_file:
            main_pokemon_data = json.load(json_file)
        for mainpkmndata in main_pokemon_data:
            if mainpkmndata["individual_id"] == individual_id:
                mainpkmndata["attacks"] = attacks
                break
        with open(str(mainpokemon_path), "w") as json_file:
            json.dump(main_pokemon_data, json_file, indent=2)

        break


def tm_attack_details_window(
    id: int,
    individual_id: str,
    current_pokemon_moveset: list[str],
    logger: ShowInfoLogger,
) -> None:
    """
    Creates a window that will allow the user to learn TM moves.

    Args:
        id (int): The Pokemon's identifier.
        individual_id (str): The Pokemon's unique identifier.
        current_pokemon_moveset (list[str]): The moves that the Pokemon currently knows.
        logger: Logger object that can log info and display windows containing messages.

    Returns:
        None
    """
    window = QDialog()
    window.setWindowIcon(QIcon(str(icon_path)))
    layout = QHBoxLayout()
    window.setWindowTitle("Learn TM Move")  # Optional: Set a window title
    # Outer layout contains everything
    outer_layout = QVBoxLayout(window)

    # Create a scroll area that will contain our main layout
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)

    # Main widget that contains the content
    content_widget = QWidget()
    layout = QHBoxLayout(content_widget)  # The main layout is now set on this widget

    # HTML content
    html_content = remember_attack_details_window_template
    from pathlib import Path

    with open(pokemon_tm_learnset_path, "r") as f:
        pokemon_tm_learnset = json.load(f)

    pokemon_name = search_pokedex_by_id(id)
    tm_learnset = pokemon_tm_learnset.get(
        pokemon_name, []
    )  # TMs that can be learnt by the Pokemon
    with open(itembag_path, "r", encoding="utf-8") as json_file:
        itembag_list = json.load(json_file)
    owned_tms = [item["item"] for item in itembag_list if item.get("type") == "TM"]
    attack_set = [tm for tm in tm_learnset if tm in owned_tms]

    # Loop through the list of attacks and add them to the HTML content
    for attack in attack_set:
        move = find_details_move(attack) or find_details_move(format_move_name(attack))

        if move is None:
            continue

        html_content += f"""
        <tr>
          <td class="move-name">{move["name"]}</td>
          <td><img src="{type_icon_path(move["type"])}" alt="{move["type"]}"/></td>
          <td><img src="{move_category_path(move["category"].lower())}" alt="{move["category"]}"/></td>
          <td class="basePower">{move["basePower"]}</td>
          <td class="no-accuracy">{move["accuracy"]}</td>
          <td>{move["pp"]}</td>
          <td>{move["shortDesc"]}</td>
        </tr>
        """

    html_content += remember_attack_details_window_template_end

    # Create a QLabel to display the HTML content
    label = QLabel(html_content)
    label.setAlignment(
        Qt.AlignmentFlag.AlignLeft
    )  # Align the label's content to the top
    label.setScaledContents(True)  # Enable scaling of the pixmap
    attack_layout = QVBoxLayout()
    for attack in attack_set:
        move = find_details_move(attack)
        learn_attack_button = QPushButton(f"Learn {attack}")  # add Details to Moves
        learn_attack_button.clicked.connect(
            lambda checked,
            a=attack: remember_attack(  # We can use "remember_attack()" because the process is the same
                individual_id, current_pokemon_moveset, a, logger
            )
        )
        attack_layout.addWidget(learn_attack_button)
    attack_layout_widget = QWidget()
    attack_layout_widget.setLayout(attack_layout)
    # Add the label and button layout widget to the main layout
    layout.addWidget(label)
    layout.addWidget(attack_layout_widget)

    # Set the main widget with content as the scroll area's widget
    scroll_area.setWidget(content_widget)

    # Add the scroll area to the outer layout
    outer_layout.addWidget(scroll_area)

    window.setLayout(outer_layout)
    window.resize(1000, 400)  # Optional: Set a default size for the window
    window.exec()


def rename_pkmn(
    nickname: str,
    pkmn_name: str,
    individual_id: str,
    logger: ShowInfoLogger,
    refresh_callback,
):
    try:
        # Load the captured Pokémon data
        with open(mypokemon_path, "r", encoding="utf-8") as json_file:
            captured_pokemon_data = json.load(json_file)
            pokemon = None

            # Find the Pokémon by individual_id
            for index, pokemon_data in enumerate(captured_pokemon_data):
                if pokemon_data["individual_id"] == individual_id:
                    pokemon = pokemon_data
                    break

            if pokemon is not None:
                # Update the nickname
                pokemon["nickname"] = nickname
                # Reflect the change in the output JSON file
                with open(str(mypokemon_path), "r", encoding="utf-8") as output_file:
                    mypokemondata = json.load(output_file)
                    # Update the specified Pokémon's data
                    for idx, data in enumerate(mypokemondata):
                        if data["individual_id"] == individual_id:
                            mypokemondata[idx] = pokemon
                            break
                # Save the modified data
                with open(str(mypokemon_path), "w") as output_file:
                    json.dump(mypokemondata, output_file, indent=2)
                # Logging and UI update
                logger.log_and_showinfo(
                    "info",
                    f"Your {pkmn_name.capitalize()} has been renamed to {nickname}!",
                )
                refresh_callback()
            else:
                showWarning("Pokémon not found.")
    except Exception as e:
        show_warning_with_traceback(
            parent=mw, exception=e, message=f"An error occurred: {e}"
        )


def PokemonFree(
    individual_id: str, name: str, logger: ShowInfoLogger, refresh_callback, sprite_label: QLabel = None, close_callback: callable = None
):
    """Release a Pokemon with a run-off animation.
    
    Args:
        individual_id: Unique ID of the Pokemon to release
        name: Name of the Pokemon
        logger: Logger instance for messages
        refresh_callback: Function to call after release
        sprite_label: The sprite widget to animate running off screen
        close_callback: Optional function to close the details panel after release
    """
    # Confirmation dialog
    reply = QMessageBox.question(
        None,
        "Confirm Release",
        f"Are you sure you want to release {name}?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )

    if reply == QMessageBox.StandardButton.No:
        logger.log_and_showinfo("info", "Release cancelled.")
        return

    # Check if the Pokémon is in the main Pokémon file
    with open(mainpokemon_path, "r", encoding="utf-8") as file:
        pokemon_data = json.load(file)

    for pokemon in pokemon_data:
        if pokemon["individual_id"] == individual_id:
            logger.log_and_showinfo("info", "You can't free your Main Pokémon!")
            return  # Exit the function if it's a Main Pokémon

    # Load Pokémon list from 'mypokemon_path' file
    try:
        with open(mypokemon_path, "r", encoding="utf-8") as file:
            pokemon_list = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        logger.log_and_showinfo("info", "Error: Could not load Pokémon data.")
        return

    # Find the position of the Pokémon with the given individual_id
    position = -1
    for idx, pokemon in enumerate(pokemon_list):
        if pokemon.get("individual_id") == individual_id:
            position = idx
            break

    if position == -1:
        logger.log_and_showinfo("info", "No Pokémon found with the specified ID.")
        return

    def complete_release():
        """Complete the release after animation finishes."""
        nonlocal pokemon_list, position
        pokemon_list.pop(position)
        with open(mypokemon_path, "w") as file:
            json.dump(pokemon_list, file, indent=2)
        logger.log_and_showinfo("info", f"{name.capitalize()} ran away into the wild!")
        # Close the details panel (which also refreshes the PC)
        if close_callback is not None:
            close_callback()
        else:
            refresh_callback()

    # Animate the sprite running off screen if we have a sprite label
    if sprite_label is not None:
        try:
            original_geometry = sprite_label.geometry()
            
            # Calculate off-screen position (run to the right)
            off_screen_x = original_geometry.x() + 500  # Move 500px to the right
            off_screen_geometry = QRect(
                off_screen_x,
                original_geometry.y(),
                original_geometry.width(),
                original_geometry.height()
            )
            
            # Store animation as attribute to prevent garbage collection
            sprite_label._run_animation = QPropertyAnimation(sprite_label, b"geometry")
            sprite_label._run_animation.setDuration(400)  # 400ms run animation
            sprite_label._run_animation.setStartValue(original_geometry)
            sprite_label._run_animation.setEndValue(off_screen_geometry)
            sprite_label._run_animation.setEasingCurve(QEasingCurve.Type.InQuad)  # Accelerate as it runs
            
            # Connect animation finished to complete the release
            sprite_label._run_animation.finished.connect(complete_release)
            
            # Start the animation
            sprite_label._run_animation.start()
            return
            
        except Exception:
            # If animation fails, just complete normally
            pass
    
    # No sprite or animation failed - complete immediately
    complete_release()
