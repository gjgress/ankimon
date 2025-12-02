from ..functions.sprite_functions import get_sprite_path
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea, QGroupBox, QFrame, QGridLayout, QComboBox, QDialogButtonBox
from PyQt6.QtGui import QPixmap
import json
import os
from typing import Optional, List, Dict, Any
from aqt import mw
from aqt.utils import showInfo, showWarning
from ..resources import mypokemon_path, frontdefault, team_pokemon_path


# Pokemon type colors (same as overview_team.py)
TYPE_COLORS = {
    "fire": "#F08030",
    "water": "#6890F0",
    "grass": "#78C850",
    "electric": "#F8D030",
    "normal": "#A8A878",
    "psychic": "#F85888",
    "rock": "#B8A038",
    "ground": "#E0C068",
    "ice": "#98D8D8",
    "dragon": "#7038F8",
    "dark": "#705848",
    "fairy": "#EE99AC",
    "poison": "#A040A0",
    "bug": "#A8B820",
    "fighting": "#C03028",
    "ghost": "#705898",
    "steel": "#B8B8D0",
    "flying": "#A890F0"
}


def get_type_color(types: List[str]) -> str:
    """Return a single hex color based on Pokemon's primary type."""
    if not types:
        return TYPE_COLORS.get("normal", "#A8A878")
    
    primary_type = types[0].lower() if types else "normal"
    return TYPE_COLORS.get(primary_type, TYPE_COLORS.get("normal", "#A8A878"))


class PokemonTeamDialog(QDialog):
    """
    Dialog for managing the player's Pokemon team composition.
    
    This dialog allows users to select up to 6 Pokemon from their collection
    to form their active team. It also supports XP Share assignment to
    distribute experience points to a designated team member.
    
    The dialog is protected from being opened during an active review session
    to prevent team changes that could cause inconsistencies in battle state.
    
    Attributes:
        settings: Settings object for storing team configuration.
        logger: Logger instance for debug/info messages.
        my_pokemon (List[Dict]): All Pokemon owned by the player.
        team_pokemon (List[Optional[Dict]]): Current team (6 slots, None if empty).
        pokemon_frames (List[Dict]): UI frame data for each team slot.
        xp_share_combo (QComboBox): Dropdown for XP Share assignment.
    
    Example:
        >>> dialog = PokemonTeamDialog(settings_obj, logger)
        # Dialog opens, user selects team, clicks OK
        # Team is saved to team_pokemon_path
    """
    
    def __init__(
        self,
        settings_obj: Any,
        logger: Any,
        parent: Optional[QDialog] = None
    ) -> None:
        """
        Initialize the Pokemon Team Dialog.
        
        Checks if the user is currently in a review session and blocks
        team changes if so. Otherwise, sets up the full team selection UI.
        
        Args:
            settings_obj: Settings object for reading/writing configuration.
                Must support get() and set() methods for keys like
                'trainer.team' and 'trainer.xp_share'.
            logger: Logger instance for displaying messages.
                Must support log_and_showinfo(level, message) method.
            parent (QDialog, optional): Parent widget. Defaults to Anki main window.
        
        Side Effects:
            - If in review: Shows warning and rejects dialog immediately
            - If not in review: Creates full UI, loads team data, displays dialog
        
        Note:
            The review check prevents team changes during active study sessions
            which could cause battle state inconsistencies or XP distribution issues.
        """
        super().__init__(parent or mw)
        
        # Check if in reviewer - don't allow team changes during review
        if mw.state == "review":
            showWarning("Cannot change team while reviewing. Please finish or exit the review session first.")
            self.reject()
            return

        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowTitle("Choose Pokémon Team")
        self.settings = settings_obj
        self.logger = logger

        # Set the minimum size of the dialog
        self.setMinimumSize(700, 450)

        # Load the Pokémon team data
        self.my_pokemon: List[Dict[str, Any]] = self.load_my_pokemon()
        self.team_pokemon: List[Optional[Dict[str, Any]]] = [None] * 6
        self.team_pokemon = self.load_pokemon_team()

        # Layout
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # Title label
        title_label = QLabel("Select up to 6 Pokémon for your team:")
        layout.addWidget(title_label)

        # Team selection area (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        team_widget = QGroupBox()
        team_layout = QGridLayout()

        # Create a frame for each Pokémon in the team
        self.pokemon_frames = []
        for i in range(6):
            row = i // 3
            col = i % 3

            frame = QFrame()
            frame.setFrameShape(QFrame.Shape.StyledPanel)

            pokemon_layout = QVBoxLayout()
            pokemon_layout.setSpacing(5)

            # Add Pokémon sprite preview with dark background
            sprite_frame = QFrame()
            sprite_frame.setFixedSize(72, 72)
            sprite_frame.setStyleSheet("QFrame { background-color: #2A2A2A; border-radius: 6px; }")
            sprite_frame_layout = QVBoxLayout(sprite_frame)
            sprite_frame_layout.setContentsMargins(4, 4, 4, 4)
            
            sprite_label = QLabel()
            sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sprite_label.setMinimumSize(64, 64)
            sprite_frame_layout.addWidget(sprite_label)
            
            pokemon_layout.addWidget(sprite_frame, alignment=Qt.AlignmentFlag.AlignCenter)

            # Label for Pokémon name and level
            pokemon_label = QLabel(f"Slot {i+1}: Empty")
            pokemon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pokemon_layout.addWidget(pokemon_label)

            # Buttons
            button_layout = QHBoxLayout()
            
            switch_button = QPushButton("Switch")
            switch_button.clicked.connect(lambda _, i=i: self.switch_out_pokemon(i))
            button_layout.addWidget(switch_button)

            remove_button = QPushButton("Remove")
            remove_button.clicked.connect(lambda _, i=i: self.remove_pokemon(i))
            button_layout.addWidget(remove_button)

            pokemon_layout.addLayout(button_layout)

            frame.setLayout(pokemon_layout)
            team_layout.addWidget(frame, row, col)
            self.pokemon_frames.append({'frame': frame, 'label': pokemon_label, 'sprite': sprite_label, 'sprite_frame': sprite_frame, 'switch_button': switch_button, 'remove_button': remove_button})

        team_widget.setLayout(team_layout)
        scroll_area.setWidget(team_widget)
        layout.addWidget(scroll_area)

        # XP Share section
        xp_share_layout = QHBoxLayout()
        xp_share_label = QLabel("XP Share:")
        xp_share_layout.addWidget(xp_share_label)
        
        self.xp_share_combo = QComboBox()
        self.xp_share_combo.setMinimumWidth(200)
        xp_share_layout.addWidget(self.xp_share_combo)
        xp_share_layout.addStretch()
        
        layout.addLayout(xp_share_layout)

        # OK Button
        ok_button = QPushButton("Save Team")
        ok_button.clicked.connect(self.on_ok)
        layout.addWidget(ok_button)

        # Set layout
        self.setLayout(layout)

        # Initialize team with current Pokémon data
        self.update_team_display()

        self.exec()

    def load_my_pokemon(self):
        """Load the player's Pokémon data from a JSON string (in this case, hardcoded)"""
        # Replace the following with the actual loading method if from a file:
        with open(mypokemon_path, "r", encoding="utf-8") as file:
            pokemon_data = json.load(file)
        return pokemon_data

    def load_pokemon_team(self):
        """Load the player's Pokémon Team from a JSON string (in this case, hardcoded)"""
        with open(team_pokemon_path, "r", encoding="utf-8") as file:
            team_data = json.load(file)

        # Load the player's Pokémon data (mypokemon_path)
        my_pokemon_data = self.load_my_pokemon()

        matching_pokemon = []

        # Loop through each Pokémon in the team and find corresponding Pokémon in 'mypokemon_path'
        for pokemon_in_team in team_data:
            individual_id = pokemon_in_team.get('individual_id')
            # Find Pokémon in 'mypokemon_path' with matching individual_id
            for pokemon_in_my_pokemon in my_pokemon_data:
                if pokemon_in_my_pokemon.get('individual_id', '') == individual_id:
                    matching_pokemon.append(pokemon_in_my_pokemon)

        return matching_pokemon

    def update_team_display(self):
        """Update the display with the player's current team"""
        # Ensure team_pokemon has 6 slots (pad with None if less than 6)
        max_pokemon_slots = 6
        self.team_pokemon = self.team_pokemon[:max_pokemon_slots]  # Trim to a max of 6 Pokémon
        self.team_pokemon.extend([None] * (max_pokemon_slots - len(self.team_pokemon)))  # Pad with None if less than 6

        for i, frame_data in enumerate(self.pokemon_frames):
            # Check if a Pokémon is selected for this slot (i.e., it's not None)
            if self.team_pokemon[i] is not None:
                pokemon = self.team_pokemon[i]
                pokemon_name = pokemon['name'].capitalize()
                pokemon_level = pokemon['level']
                sprite_path = os.path.join(frontdefault, f"{pokemon['id']}.png")

                # Update label with name and level
                frame_data['label'].setText(f"{pokemon_name}\nLv. {pokemon_level}")
                frame_data['label'].setStyleSheet("color: #E8E8E8; font-size: 11px; font-weight: bold;")

                # Apply type-based background color to sprite frame
                types = pokemon.get('type', [])
                type_color = get_type_color(types)
                frame_data['sprite_frame'].setStyleSheet(f"QFrame {{ background-color: {type_color}; border-radius: 6px; }}")
                frame_data['frame'].setStyleSheet("QFrame { background-color: transparent; }")

                # Display the sprite image
                if os.path.exists(sprite_path):
                    pixmap = QPixmap(sprite_path)
                    frame_data['sprite'].setPixmap(pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
                else:
                    frame_data['sprite'].clear()
            else:
                frame_data['label'].setText(f"Slot {i+1}: Empty")
                frame_data['label'].setStyleSheet("color: #888888; font-size: 11px;")
                frame_data['sprite_frame'].setStyleSheet("QFrame { background-color: #2A2A2A; border-radius: 6px; }")
                frame_data['frame'].setStyleSheet("QFrame { background-color: transparent; }")
                frame_data['sprite'].clear()
        
        # Update the XP Share dropdown to only show team members
        self.update_xp_share_combo()

    def update_xp_share_combo(self):
        """Update the XP Share dropdown to only show Pokémon currently in the team."""
        current_xp_share_id = self.xp_share_combo.currentData()
        
        self.xp_share_combo.clear()
        self.xp_share_combo.addItem("No XP Share", None)
        
        for pokemon in self.team_pokemon:
            if pokemon is not None:
                pokemon_name = pokemon['name'].capitalize()
                self.xp_share_combo.addItem(f"{pokemon_name} (Lv. {pokemon['level']})", pokemon['individual_id'])
                
                sprite_path = get_sprite_path("front", "png", pokemon['id'], pokemon.get("shiny", False), pokemon.get("gender", "male"))
                pixmap = QPixmap(sprite_path)
                self.xp_share_combo.setItemData(self.xp_share_combo.count() - 1, pixmap, Qt.ItemDataRole.DecorationRole)
        
        # Restore previous selection if still valid
        if current_xp_share_id:
            for i in range(self.xp_share_combo.count()):
                if self.xp_share_combo.itemData(i) == current_xp_share_id:
                    self.xp_share_combo.setCurrentIndex(i)
                    return
        
        # Try to restore from settings
        xp_share_pokemon_individual_id = self.settings.get("trainer.xp_share")
        if xp_share_pokemon_individual_id:
            for i in range(self.xp_share_combo.count()):
                if self.xp_share_combo.itemData(i) == xp_share_pokemon_individual_id:
                    self.xp_share_combo.setCurrentIndex(i)
                    return

    def switch_out_pokemon(self, slot):
        """Allow the player to switch out a Pokémon for the selected slot"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Select Pokémon for Slot {slot + 1}")
        dialog.setMinimumSize(280, 280)
        dialog.setStyleSheet("QDialog { background-color: #2D2D30; } QLabel { color: #E8E8E8; }")

        layout = QVBoxLayout()

        label = QLabel("Choose a Pokémon:")
        layout.addWidget(label)

        combo_box = QComboBox()
        combo_box.setStyleSheet("QComboBox { background-color: #3C3C3C; color: #E8E8E8; padding: 4px; }")

        # Add only Pokémon not already in the team
        used_pokemon_ids = []
        for i, pokemon in enumerate(self.team_pokemon):
            if pokemon is not None and i != slot:
                used_pokemon_ids.append(pokemon['individual_id'])
        
        available_pokemon = [p for p in self.my_pokemon if p and p['individual_id'] not in used_pokemon_ids]

        if available_pokemon:
            for pokemon in available_pokemon:
                combo_box.addItem(f"{pokemon['name'].capitalize()} (Lv. {pokemon['level']})", pokemon)
                sprite_path = get_sprite_path("front", "png", pokemon['id'], pokemon.get("shiny", False), pokemon.get("gender", "male"))
                pixmap = QPixmap(sprite_path)
                combo_box.setItemData(combo_box.count() - 1, pixmap, Qt.ItemDataRole.DecorationRole)
        else:
            combo_box.addItem("No available Pokémon", None)

        layout.addWidget(combo_box)

        # Preview with type-based background
        preview_label = QLabel("Preview:")
        layout.addWidget(preview_label)
        
        preview_frame = QFrame()
        preview_frame.setMinimumSize(100, 100)
        preview_frame.setStyleSheet("QFrame { background-color: #3C3C3C; border-radius: 8px; }")
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setMinimumSize(96, 96)
        preview_layout.addWidget(image_label)
        
        layout.addWidget(preview_frame)

        def update_preview(index):
            pokemon = combo_box.itemData(index)
            if pokemon:
                sprite_path = get_sprite_path("front", "png", pokemon['id'], pokemon.get("shiny", False), pokemon.get("gender", "male"))
                pixmap = QPixmap(sprite_path)
                image_label.setPixmap(pixmap.scaled(96, 96, Qt.AspectRatioMode.KeepAspectRatio))
                
                # Apply type-based background color
                types = pokemon.get('type', [])
                type_color = get_type_color(types)
                preview_frame.setStyleSheet(f"QFrame {{ background-color: {type_color}; border-radius: 8px; }}")

        combo_box.currentIndexChanged.connect(lambda: update_preview(combo_box.currentIndex()))
        
        if combo_box.count() > 0:
            update_preview(0)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.setStyleSheet("QPushButton { background-color: #3C3C3C; color: #E8E8E8; padding: 6px 12px; border-radius: 4px; } QPushButton:hover { background-color: #505050; }")
        button_box.accepted.connect(lambda: self.confirm_switch(combo_box.currentIndex(), slot, dialog))
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        dialog.setLayout(layout)
        dialog.exec()

    def confirm_switch(self, selected_index, slot, dialog):
        """Confirm the Pokémon switch and update the team"""
        selected_pokemon = dialog.findChild(QComboBox).itemData(selected_index)

        if selected_pokemon:
            self.team_pokemon[slot] = selected_pokemon
            self.update_team_display()

        dialog.accept()

    def remove_pokemon(self, slot):
        """Remove the Pokémon from the team and handle XP Share if necessary"""
        # Check if there's a Pokémon in the selected slot
        if self.team_pokemon[slot] is not None:
            # Check if the Pokémon in this slot is the one with XP Share
            pokemon_individual_id = self.team_pokemon[slot]['individual_id']
            xp_share_pokemon_individual_id = self.settings.get("trainer.xp_share")

            if xp_share_pokemon_individual_id == pokemon_individual_id:
                # Remove XP Share from the Pokémon if it exists
                self.settings.set("trainer.xp_share", None)

            # Remove the Pokémon from the team slot
            self.team_pokemon[slot] = None

            # Update the display after removal
            self.update_team_display()

    def on_ok(self):
        """Store the selected Pokémon team and XP Share setting, then close the dialog"""
        #team = [frame_data['label'].text() for frame_data in self.pokemon_frames if frame_data['label'].text() != "Pokémon Not Selected"]
        team_data = []  # Initialize the list to store selected Pokémon

        # Process each Pokémon frame to construct the team
        for frame_data in self.team_pokemon:
            if frame_data:  # Ensure the Pokémon has a name
                # Restructure Pokémon data to the desired format
                pokemon_data = {
                    "individual_id": frame_data['individual_id']
                }
                team_data.append(pokemon_data)

        pokemon_names = []

        for frame_data in self.team_pokemon:
            if frame_data:
                # Restructure Pokémon data to the desired format
                pokemon_name = {
                    "name": frame_data['name']
                }
                pokemon_names.append(pokemon_name)

        # Get the selected Pokémon for XP Share
        xp_share_pokemon = self.xp_share_combo.currentText()
        if xp_share_pokemon != "No XP Share":
            # Retrieve the individual_id of the selected Pokémon
            current_index = self.xp_share_combo.currentIndex()
            xp_share_individual_id = self.xp_share_combo.itemData(current_index)
        else:
            xp_share_individual_id = None

        # Update settings with the selected team and XP Share setting
        self.settings.set("trainer.team", team_data)
        self.settings.set("trainer.xp_share", xp_share_individual_id)  # Save XP Share Pokémon

        try:
            with open(team_pokemon_path, "w") as json_file:
                json.dump(team_data, json_file, indent=4)

            self.logger.log_and_showinfo("info", f"Trainer settings saved to {team_pokemon_path}.")
            self.logger.log_and_showinfo("info", f"You chose the following team: [{', '.join([pokemon['name'] for pokemon in pokemon_names])}]\nXP Share: {xp_share_pokemon}")
        except Exception as e:
            self.logger.log_and_showinfo("error", f"Failed to save trainer settings: {e}")

        self.accept()  # Close the dialog
