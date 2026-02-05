import os
from dataclasses import dataclass
from typing import Any

import orjson
from aqt import (
    QCheckBox,
    QComboBox,
    QDoubleValidator,
    QIntValidator,
    mw,
)
from aqt.qt import (
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPainter,
    QPainterPath,
    QPixmap,
    QPushButton,
    QRectF,
    QScrollArea,
    Qt,
    QVBoxLayout,
    QWidget,
)
from aqt.theme import theme_manager
from aqt.utils import showWarning


# create_rounded_pixmap function remains the same
def create_rounded_pixmap(source_pixmap, radius):
    if source_pixmap.isNull():
        return QPixmap()
    rounded = QPixmap(source_pixmap.size())
    rounded.fill(Qt.GlobalColor.transparent)
    painter = QPainter(rounded)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    path = QPainterPath()
    rect = QRectF(source_pixmap.rect())
    path.addRoundedRect(rect, radius, radius)
    painter.setClipPath(path)
    painter.drawPixmap(0, 0, source_pixmap)
    painter.end()
    return rounded


@dataclass
class Toggle:
    setting: str


@dataclass
class DropDown:
    setting: str
    options: dict[str, Any]


@dataclass
class Text:
    setting: str


@dataclass
class Integer:
    setting: str
    min: int | None
    max: int | None


@dataclass
class Float:
    setting: str
    min: float | None
    max: float | None


setting_ui_structure = {
    "General": {
        "settings": [
            Text("trainer.name"),
            DropDown(
                "misc.language",
                {
                    "Japanese (Hir & Kata)": 1,
                    "Japanese (Roomaji)": 2,
                    "Korean": 3,
                    "Chinese (Traditional)": 4,
                    "French": 5,
                    "German": 6,
                    "Spanish": 7,
                    "Italian": 8,
                    "English": 9,
                    "Czech": 10,
                    "Japanese": 11,
                    "Chinese (Simplified)": 12,
                    "Portuguese (Brazil)": 13,
                    "Spanish (Latin America)": 14,
                },
            ),
            Toggle("misc.show_tip_on_startup"),
        ],
        "subgroups": {
            "Technical Settings": {
                "settings": [
                    Toggle("misc.ssh"),
                    Toggle("misc.YouShallNotPass_Ankimon_News"),
                    Toggle("misc.ankiweb_sync"),
                    Toggle("misc.leaderboard"),
                    Toggle("misc.developer_mode"),
                ]
            },
            "Discord Integration": {
                "settings": [
                    Toggle("misc.discord_rich_presence"),
                    DropDown(
                        "misc.discord_rich_presence_text",
                        {
                            "Ankimon Quotes": 1,
                            "Pokémon in the battle": 2,
                        },
                    ),
                ]
            },
        },
    },
    "Battle": {
        "settings": [
            DropDown(
                "battle.automatic_battle",
                {
                    "Disabled": 0,
                    "Auto-catch": 1,
                    "Auto-defeat (to gain XP)": 2,
                    "Catch if NEW Pokémon (not in collection), otherwise defeat": 3,
                },
            ),
            Integer("battle.cards_per_round", min=1, max=None),
            DropDown(
                "gui.show_mainpkmn_in_reviewer",
                {"Hide": 0, "Same level view": 1, "Battle view": 2},
            ),
            Toggle("controls.pokemon_buttons"),
            Toggle("gui.pop_up_dialog_message_on_defeat"),
            Toggle("gui.reviewer_text_message_box"),
            Integer("gui.reviewer_text_message_box_time", min=1, max=5),
            Toggle("battle.review_based_damage"),
        ],
        "subgroups": {
            "Fight Hotkeys": {
                "settings": [
                    Text("controls.defeat_key"),
                    Text("controls.catch_key"),
                    Text("controls.key_for_opening_closing_ankimon"),
                    Toggle("controls.allow_to_choose_moves"),
                ]
            },
            "HP, XP and Level Settings": {
                "settings": [
                    Toggle("gui.hp_bar_config"),
                    Toggle("gui.xp_bar_config"),
                    DropDown("gui.xp_bar_location", {"Top": 1, "Bottom": 2}),
                    Toggle("misc.remove_level_cap"),
                ]
            },
        },
    },
    "Styling": {
        "settings": [
            Toggle("gui.styling_in_reviewer"),
            Toggle("gui.animate_time"),
            Integer("gui.review_hp_bar_thickness", None, None),
            Toggle("gui.reviewer_image_gif"),
            Toggle("gui.view_main_front"),
            Toggle("gui.gif_in_collection"),
        ]
    },
    "Sound": {
        "settings": [
            Toggle("audio.sound_effects"),
            Toggle("audio.sounds"),
            Toggle("audio.battle_sounds"),
            Float("audio.volume", min=0.0, max=1.0),
        ]
    },
    "Study": {
        "settings": [
            Integer("battle.daily_average", min=0, max=None),
            Integer("battle.card_max_time", min=0, max=None),
        ]
    },
    "Generations": {
        "settings": [
            Toggle("misc.gen1"),
            Toggle("misc.gen2"),
            Toggle("misc.gen3"),
            Toggle("misc.gen4"),
            Toggle("misc.gen5"),
            Toggle("misc.gen6"),
            Toggle("misc.gen7"),
            Toggle("misc.gen8"),
            Toggle("misc.gen9"),
        ]
    },
}


class SettingsWindow(QMainWindow):
    def __init__(
        self, config, set_config_callback, save_config_callback, load_config_callback
    ):
        super().__init__()
        self.config = config
        self.original_config = config.copy()
        self.save_config_callback = save_config_callback
        self.load_config = load_config_callback
        self.setWindowTitle("Settings")
        self.setMaximumWidth(600)
        self.setMaximumHeight(900)
        self.parent = mw

        self.descriptions = self.load_descriptions()
        self.friendly_names = self.load_friendly_names()

        self.group_widgets = {}
        self.group_states = {}
        self.searchable_settings = []
        self.title_buttons = {}  # To store references to title buttons
        self.input_values = {}

        self.setup_ui()

    @property
    def is_dark_mode(self):
        """Checks if Anki is in dark mode."""
        return theme_manager.night_mode

    def _apply_stylesheet(self):
        """Applies the appropriate stylesheet based on the current theme."""
        if self.is_dark_mode:
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #2e2e2e;
                    color: #f0f0f0;
                }
                QLabel[class="setting-label"] {
                    font-weight: bold;
                    margin-top: 5px;
                    color: #f0f0f0;
                }
                QLabel[class="description-label"] {
                    color: #aaaaaa;
                    padding-left: 5px;
                }
                QRadioButton {
                    color: #f0f0f0;
                }
                QLineEdit {
                    background-color: #3c3c3c;
                    color: #f0f0f0;
                    border: 1px solid #555555;
                    padding: 4px;
                }
                QComboBox {
                    background-color: #3c3c3c;
                    color: #f0f0f0;
                    border: 1px solid #555555;
                    padding: 4px;
                }
                QPushButton {
                    background-color: #4a4a4a;
                    border: 1px solid #555555;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QPushButton[class="title-button"] {
                    font-weight: bold;
                    text-align: left;
                    border: none;
                    background-color: transparent;
                }
                QPushButton[class="title-button"][level="1"] {
                    font-size: 18px;
                    margin-top: 15px;
                    margin-bottom: 5px;
                    color: #87CEEB;
                }
                QPushButton[class="title-button"][level="2"] {
                    font-size: 14px;
                    margin-top: 10px;
                    padding-left: 15px;
                    color: #ADD8E6;
                }
            """)
        else:  # Light Mode
            self.setStyleSheet("""
                QMainWindow, QWidget {
                    background-color: #f5f5f5;
                    color: #212121;
                }
                QLabel[class="setting-label"] {
                    font-weight: bold;
                    margin-top: 5px;
                    color: #212121;
                }
                QLabel[class="description-label"] {
                    color: #666666;
                    padding-left: 5px;
                }
                QRadioButton {
                    color: #212121;
                }
                QLineEdit {
                    background-color: #ffffff;
                    color: #212121;
                    border: 1px solid #adadad;
                    padding: 4px;
                }
                QPushButton {
                    background-color: #e1e1e1;
                    border: 1px solid #adadad;
                    padding: 5px;
                }
                QPushButton:hover {
                    background-color: #cacaca;
                }
                QPushButton[class="title-button"] {
                    font-weight: bold;
                    text-align: left;
                    border: none;
                    background-color: transparent;
                }
                QPushButton[class="title-button"][level="1"] {
                    font-size: 18px;
                    margin-top: 15px;
                    margin-bottom: 5px;
                    color: #253D5B;
                }
                QPushButton[class="title-button"][level="2"] {
                    font-size: 14px;
                    margin-top: 10px;
                    padding-left: 15px;
                    color: #355882;
                }
            """)

    def load_descriptions(self):
        descriptions_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "lang",
            "setting_description.json",
        )
        if os.path.exists(descriptions_file):
            try:
                with open(descriptions_file, "rb") as f:
                    return orjson.loads(f.read())
            except (orjson.JSONDecodeError, UnicodeDecodeError) as e:
                showWarning(f"Error reading descriptions file: {e}")
        return {}

    def load_friendly_names(self):
        names_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "lang", "setting_name.json"
        )
        if os.path.exists(names_file):
            try:
                with open(names_file, "rb") as f:
                    return orjson.loads(f.read())
            except (orjson.JSONDecodeError, UnicodeDecodeError) as e:
                showWarning(f"Error reading friendly names file: {e}")
        return {}

    def _create_setting(self, setting_type, layout):
        key = setting_type.setting
        value = self.config[key]
        friendly_name = self.friendly_names[key]
        description = self.descriptions.get(key, "No description available.")

        created_widgets = []
        label = QLabel(friendly_name, self)
        label.setProperty("class", "setting-label")
        description_label = QLabel(description, self)
        description_label.setWordWrap(True)
        description_label.setProperty("class", "description-label")
        description_label.setMaximumWidth(self.width() - 50)
        layout.addWidget(label)
        layout.addWidget(description_label)
        created_widgets.extend([label, description_label])

        if isinstance(setting_type, Toggle):
            checkbox = QCheckBox(self)
            checkbox.setText("Enabled")
            checkbox.setChecked(value)
            checkbox.setStyleSheet("padding-left: 10px;")

            layout.addWidget(checkbox)
            created_widgets.append(checkbox)

            def get_input():
                return checkbox.isChecked()

            self.input_values[key] = get_input
        elif isinstance(setting_type, Text):
            line_edit = QLineEdit(str(value), self)
            layout.addWidget(line_edit)
            created_widgets.append(line_edit)

            def get_input():
                return line_edit.text()

            self.input_values[key] = get_input
        elif isinstance(setting_type, Integer):
            line_edit = QLineEdit(str(value), self)

            line_edit.setValidator(
                QIntValidator(
                    setting_type.minimum
                    if hasattr(setting_type, "minimum")
                    else -99967,
                    setting_type.maximum if hasattr(setting_type, "maximum") else 99967,
                    self,
                )
            )

            layout.addWidget(line_edit)
            created_widgets.append(line_edit)

            def get_input():
                return int(line_edit.text())

            self.input_values[key] = get_input

        elif isinstance(setting_type, Float):
            line_edit = QLineEdit(str(value), self)

            line_edit.setValidator(
                QDoubleValidator(
                    setting_type.minimum
                    if hasattr(setting_type, "minimum") is None
                    else -float("inf"),
                    setting_type.maximum
                    if hasattr(setting_type, "maximum") is None
                    else float("inf"),
                    -1,
                    self,
                )
            )

            layout.addWidget(line_edit)
            created_widgets.append(line_edit)

            def get_input():
                return float(line_edit.text())

            self.input_values[key] = get_input
        elif isinstance(setting_type, DropDown):
            names = setting_type.options.keys()

            combo_box = QComboBox(self)
            combo_box.addItems(names)

            index_to_name = {v: k for k, v in setting_type.options.items()}

            selected_name = index_to_name.get(value)
            if selected_name:
                index = combo_box.findText(str(selected_name))
                combo_box.setCurrentIndex(index)

            layout.addWidget(combo_box)
            created_widgets.append(combo_box)

            def get_input():
                return setting_type.options[combo_box.currentText()]

            self.input_values[key] = get_input

        return created_widgets, friendly_name, description

    def _create_title(self, text, level=1):
        button = QPushButton(f" {text}")
        button.setCheckable(True)
        button.setChecked(True)
        button.setProperty("class", "title-button")
        button.setProperty("level", str(level))
        return button

    def setup_ui(self):
        self.setMinimumSize(450, 600)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self._apply_stylesheet()

        layout = QVBoxLayout(central_widget)
        image_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "user_files",
            "web",
            "images",
            "ankimon_logo.png",
        )
        image_label = QLabel()
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            scaled_pixmap = pixmap.scaledToWidth(
                250, Qt.TransformationMode.SmoothTransformation
            )
            rounded_pixmap = create_rounded_pixmap(scaled_pixmap, 15)
            image_label.setPixmap(rounded_pixmap)
        else:
            image_label.setText("Ankimon Logo Not Found")
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(image_label)
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search settings...")
        self.search_bar.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_bar)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area_content = QWidget()
        scroll_area_layout = QVBoxLayout(scroll_area_content)
        scroll_area.setWidget(scroll_area_content)

        for l1_title, l1_data in setting_ui_structure.items():
            self.group_states[l1_title] = True
            l1_widgets = []
            l1_button = self._create_title(l1_title, level=1)
            scroll_area_layout.addWidget(l1_button)
            self.title_buttons[l1_title] = l1_button
            for setting_type in l1_data.get("settings", []):
                widgets, name, desc = self._create_setting(
                    setting_type, scroll_area_layout
                )
                if widgets:
                    l1_widgets.extend(widgets)
                    self.searchable_settings.append(
                        {
                            "widgets": widgets,
                            "friendly_name": name,
                            "description": desc,
                            "l1_title": l1_title,
                            "l2_title": None,
                        }
                    )
            if "subgroups" in l1_data:
                for l2_title, l2_data in l1_data["subgroups"].items():
                    self.group_states[l2_title] = True
                    l2_widgets = []
                    l2_button = self._create_title(l2_title, level=2)
                    scroll_area_layout.addWidget(l2_button)
                    self.title_buttons[l2_title] = l2_button
                    l1_widgets.append(l2_button)
                    for setting_type in l2_data.get("settings", []):
                        widgets, name, desc = self._create_setting(
                            setting_type, scroll_area_layout
                        )
                        if widgets:
                            l1_widgets.extend(widgets)
                            l2_widgets.extend(widgets)
                            self.searchable_settings.append(
                                {
                                    "widgets": widgets,
                                    "friendly_name": name,
                                    "description": desc,
                                    "l1_title": l1_title,
                                    "l2_title": l2_title,
                                }
                            )
                    self.group_widgets[l2_title] = l2_widgets
                    l2_button.clicked.connect(
                        lambda _, t=l2_title, b=l2_button: (
                            self._toggle_group_visibility(t, b)
                        )
                    )
            self.group_widgets[l1_title] = l1_widgets
            l1_button.clicked.connect(
                lambda _, t=l1_title, b=l1_button: self._toggle_group_visibility(t, b)
            )
        scroll_area_layout.addStretch()
        layout.addWidget(scroll_area)
        save_button = QPushButton("Save")
        save_button.setToolTip("Click to save your settings.")
        save_button.clicked.connect(self.on_save)
        layout.addWidget(save_button)

    def show_window(self):
        self._apply_stylesheet()
        self.config = self.load_config()
        self.show()
        self.raise_()

    def _on_search_changed(self, text):
        search_term = text.lower().strip()
        if not search_term:
            for setting in self.searchable_settings:
                for widget in setting["widgets"]:
                    widget.setVisible(True)
            for title, button in self.title_buttons.items():
                button.setVisible(True)
                is_expanded = self.group_states.get(title, True)
                for w in self.group_widgets.get(title, []):
                    w.setVisible(is_expanded)
            return

        for setting in self.searchable_settings:
            for widget in setting["widgets"]:
                widget.setVisible(False)
        for button in self.title_buttons.values():
            button.setVisible(False)

        titles_to_show = set()
        for setting in self.searchable_settings:
            name = setting["friendly_name"].lower()
            desc = setting["description"].lower()
            if search_term in name or search_term in desc:
                for widget in setting["widgets"]:
                    widget.setVisible(True)
                titles_to_show.add(setting["l1_title"])
                if setting["l2_title"]:
                    titles_to_show.add(setting["l2_title"])

        for title in titles_to_show:
            if title in self.title_buttons:
                self.title_buttons[title].setVisible(True)

    def _toggle_group_visibility(self, title, button):
        is_expanded = not self.group_states.get(title, True)
        self.group_states[title] = is_expanded
        if title in self.group_widgets:
            for widget in self.group_widgets[title]:
                widget.setVisible(is_expanded)

    def on_save(self):
        # Update self.config from the current state of all UI widgets
        for key, get_value in self.input_values.items():
            self.config[key] = get_value()

        # Now that self.config is up-to-date, call the save callback
        self.save_config_callback(self.config)

        # The rest is for showing the confirmation message
        excluded_patterns = {
            "mypokemon",
            "mainpokemon",
            "pokemon_collection",
            "trainer.cash",
            "misc.last_tip_index",
            "trainer.xp_share",
        }
        changed_settings = [
            key
            for key in self.config
            if not any(pattern in key for pattern in excluded_patterns)
            and self.config[key] != self.original_config.get(key)
        ]

        if changed_settings:
            changed_message = "\n".join(
                [
                    f"{self.friendly_names.get(k, k)}: {self.original_config.get(k)} -> {self.config[k]}"
                    for k in changed_settings
                ]
            )
            QMessageBox.information(
                self, "Settings Saved", "Your settings have been saved successfully."
            )
            QMessageBox.information(
                self, "Config changes", f"Changed settings:\n{changed_message}"
            )
            self.original_config = self.config.copy()
        else:
            QMessageBox.information(self, "No Changes", "No settings were changed.")
