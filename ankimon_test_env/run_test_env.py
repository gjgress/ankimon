import sys
import os
import types
import json
from pathlib import Path
from unittest.mock import MagicMock

def setup_anki_mocks():
    """Set up comprehensive Anki/AQT mocks in sys.modules"""
    print("Setting up Anki/AQT mocks...")
    
    # Create anki module and submodules
    mock_anki = types.ModuleType("anki")
    mock_anki.collection = types.ModuleType("anki.collection")
    mock_anki.cards = types.ModuleType("anki.cards")
    mock_anki.notes = types.ModuleType("anki.notes")
    mock_anki.sched = types.ModuleType("anki.sched")
    mock_anki.utils = types.ModuleType("anki.utils")
    mock_anki.hooks = types.ModuleType("anki.hooks")

    # Import after QApplication exists
    from mock_anki.collection import Collection, MockCard, MockNote, MockScheduler
    mock_anki.collection.Collection = Collection
    mock_anki.cards.Card = MockCard
    mock_anki.notes.Note = MockNote

    # Create aqt module and submodules
    mock_aqt = types.ModuleType("aqt")
    mock_aqt.main = types.ModuleType("aqt.main")
    mock_aqt.reviewer = types.ModuleType("aqt.reviewer")
    mock_aqt.utils = types.ModuleType("aqt.utils")
    mock_aqt.gui_hooks = types.ModuleType("aqt.gui_hooks")
    mock_aqt.qt = types.ModuleType("aqt.qt")
    mock_aqt.webview = types.ModuleType("aqt.webview")
    mock_aqt.operations = types.ModuleType("aqt.operations")
    mock_aqt.operations.scheduling = types.ModuleType("aqt.operations.scheduling")

    from mock_aqt.reviewer import EnhancedMockReviewer
    mock_aqt.reviewer.Reviewer = EnhancedMockReviewer

    # Mock aqt.utils functions
    def mock_qconnect(signal, slot):
        try:
            signal.connect(slot)
        except Exception as e:
            print(f"MockQConnect error: {e}")

    mock_aqt.utils.qconnect = mock_qconnect
    mock_aqt.utils.showWarning = lambda msg: print(f"MockWarning: {msg}")
    mock_aqt.utils.showInfo = lambda msg: print(f"MockInfo: {msg}")
    mock_aqt.utils.openLink = lambda url: print(f"MockOpenLink: {url}")

    # Mock GUI hooks - create empty lists that add-ons can append to
    mock_hooks = [
        'reviewer_did_show_question', 'reviewer_did_show_answer', 'reviewer_will_answer_card',
        'reviewer_did_answer_card', 'card_will_show', 'reviewer_will_end',
        'reviewer_will_show_context_menu', 'reviewer_will_init_answer_buttons'
    ]

    for hook_name in mock_hooks:
        setattr(mock_aqt.gui_hooks, hook_name, [])

    # Mock Qt classes
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QMainWindow, QMenu, QMenuBar, QDialog, QVBoxLayout,
        QHBoxLayout, QLabel, QPushButton, QFrame
    )

    from PyQt6.QtGui import QAction, QKeySequence

    mock_aqt.qt.QApplication = QApplication
    mock_aqt.qt.QMainWindow = QMainWindow
    mock_aqt.qt.QWidget = QWidget
    mock_aqt.qt.QAction = QAction
    mock_aqt.qt.QMenu = QMenu
    mock_aqt.qt.QMenuBar = QMenuBar
    mock_aqt.qt.QDialog = QDialog
    mock_aqt.qt.QVBoxLayout = QVBoxLayout
    mock_aqt.qt.QHBoxLayout = QHBoxLayout
    mock_aqt.qt.QLabel = QLabel
    mock_aqt.qt.QPushButton = QPushButton
    mock_aqt.qt.QFrame = QFrame
    mock_aqt.qt.QKeySequence = QKeySequence

    # Inject into sys.modules
    modules_to_inject = {
        "anki": mock_anki,
        "anki.collection": mock_anki.collection,
        "anki.cards": mock_anki.cards,
        "anki.notes": mock_anki.notes,
        "anki.sched": mock_anki.sched,
        "anki.utils": mock_anki.utils,
        "anki.hooks": mock_anki.hooks,
        "aqt": mock_aqt,
        "aqt.main": mock_aqt.main,
        "aqt.reviewer": mock_aqt.reviewer,
        "aqt.utils": mock_aqt.utils,
        "aqt.gui_hooks": mock_aqt.gui_hooks,
        "aqt.qt": mock_aqt.qt,
        "aqt.webview": mock_aqt.webview,
        "aqt.operations": mock_aqt.operations,
        "aqt.operations.scheduling": mock_aqt.operations.scheduling,
    }

    for module_name, module_obj in modules_to_inject.items():
        sys.modules[module_name] = module_obj

    print("Anki/AQT mocks injected into sys.modules")

def setup_global_mw():
    """Set up the global mw object that Ankimon expects"""
    # Import Collection after mocks are set up
    from mock_anki.collection import Collection, MockScheduler
    
    # Create a simple mock mw first
    mw = type('MockMainWindow', (), {})()
    
    # Add basic properties
    mw.col = Collection()
    mw.addonManager = type('MockAddonManager', (), {
        'getConfig': lambda self, addon_id: {},
        'writeConfig': lambda self, addon_id, config: print(f"Writing config for {addon_id}: {config}"),
        'addonsFolder': lambda self: Path(__file__).parent.parent / "src",
        'addonFromModule': lambda self, module_name: "ankimon"
    })()

    mw.pm = type('MockProfileManager', (), {
        'openProfile': lambda self, name: print(f"Opening profile: {name}"),
        'video_driver': lambda self: 'Software'
    })()

    from PyQt6.QtWidgets import QApplication
    mw.app = QApplication.instance()

    # Set in modules
    sys.modules['aqt'].mw = mw
    sys.modules['aqt.main'].mw = mw

    return mw

def create_mock_data_files():
    """Create necessary mock data files for Ankimon"""
    print("Creating mock data files...")
    
    # Determine the Ankimon path
    ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
    user_files_path = ankimon_path / "user_files"
    user_files_path.mkdir(parents=True, exist_ok=True)
    
    # Create mock mypokemon.json
    mypokemon_path = user_files_path / "mypokemon.json"
    if not mypokemon_path.exists():
        mock_pokemon_data = [
            {
                "id": 25,
                "name": "Pikachu", 
                "level": 50,
                "hp": 100,
                "max_hp": 100,
                "stats": {"hp": 100, "atk": 80, "def": 70, "spa": 90, "spd": 80, "spe": 120},
                "shiny": False,
                "gender": "M",
                "attacks": ["Thunderbolt", "Quick Attack", "Thunder Wave", "Agility"]
            }
        ]
        with open(mypokemon_path, 'w', encoding='utf-8') as f:
            json.dump(mock_pokemon_data, f, indent=2)
        print(f"Created mock Pokemon data: {mypokemon_path}")
    
    # Create mock itembag.json
    itembag_path = user_files_path / "itembag.json"
    if not itembag_path.exists():
        with open(itembag_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
        print(f"Created mock itembag: {itembag_path}")
    
    # Create mock config.json
    config_path = user_files_path / "config.json"
    if not config_path.exists():
        mock_config = {
            "gui.show_mainpkmn_in_reviewer": 2,  # Show both Pokemon
            "battle.hp_bar_thickness": 4,
            "gui.reviewer_image_gif": 1,
            "gui.reviewer_text_message_box": True,
            "misc.language": 9
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(mock_config, f, indent=2)
        print(f"Created mock config: {config_path}")

def load_ankimon_singletons():
    """Load and create all Ankimon singleton objects"""
    print("Loading Ankimon singletons...")
    try:
        ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
        if str(ankimon_path) not in sys.path:
            sys.path.insert(0, str(ankimon_path))

        # Create mock files first
        create_mock_data_files()

        # Import and create Ankimon objects
        from singletons import (
            settings_obj, translator, logger, main_pokemon, enemy_pokemon,
            trainer_card, ankimon_tracker_obj, test_window, achievement_bag,
            data_handler_obj, data_handler_window, shop_manager, ankimon_tracker_window,
            pokedex_window, reviewer_obj, eff_chart, gen_id_chart, license, credits,
            version_dialog, item_window, pokecollection_win, pokemon_pc
        )

        print(f"Successfully loaded Ankimon objects:")
        print(f"  Main Pokemon: {main_pokemon.name} (Level {main_pokemon.level})")
        print(f"  Enemy Pokemon: {enemy_pokemon.name} (Level {enemy_pokemon.level})")
        print(f"  Settings loaded: {settings_obj is not None}")
        print(f"  Reviewer loaded: {reviewer_obj is not None}")

        return {
            'settings_obj': settings_obj,
            'translator': translator,
            'logger': logger,
            'main_pokemon': main_pokemon,
            'enemy_pokemon': enemy_pokemon,
            'trainer_card': trainer_card,
            'ankimon_tracker_obj': ankimon_tracker_obj,
            'test_window': test_window,
            'achievement_bag': achievement_bag,
            'data_handler_obj': data_handler_obj,
            'data_handler_window': data_handler_window,
            'shop_manager': shop_manager,
            'ankimon_tracker_window': ankimon_tracker_window,
            'pokedex_window': pokedex_window,
            'reviewer_obj': reviewer_obj,
            'eff_chart': eff_chart,
            'gen_id_chart': gen_id_chart,
            'license': license,
            'credits': credits,
            'version_dialog': version_dialog,
            'item_window': item_window,
            'pokecollection_win': pokecollection_win,
            'pokemon_pc': pokemon_pc,
        }

    except Exception as e:
        print(f"Error loading Ankimon singletons: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_ankimon_menu(mw, ankimon_objects):
    """Load and initialize Ankimon menu"""
    print("Loading Ankimon menu...")
    try:
        from menu_buttons import create_menu_actions
        print("Successfully imported menu_buttons")

        # Create mock functions for menu callbacks
        def mock_callback(name):
            return lambda: print(f"Mock callback: {name}")

        # Prepare the parameters for create_menu_actions
        menu_params = {
            'database_complete': True,
            'online_connectivity': False,
            'pokecollection_win': ankimon_objects.get('pokecollection_win'),
            'item_window': ankimon_objects.get('item_window'),
            'test_window': ankimon_objects.get('test_window'),
            'achievement_bag': ankimon_objects.get('achievement_bag'),
            'open_team_builder': mock_callback("Team Builder"),
            'export_to_pkmn_showdown': mock_callback("Export to Showdown"),
            'export_all_pkmn_showdown': mock_callback("Export All to Showdown"),
            'flex_pokemon_collection': mock_callback("Flex Collection"),
            'eff_chart': ankimon_objects.get('eff_chart'),
            'gen_id_chart': ankimon_objects.get('gen_id_chart'),
            'credits': ankimon_objects.get('credits'),
            'license': ankimon_objects.get('license'),
            'open_help_window': lambda connectivity: print("Help window opened"),
            'report_bug': mock_callback("Bug Report"),
            'rate_addon_url': mock_callback("Rate Addon"),
            'version_dialog': ankimon_objects.get('version_dialog'),
            'trainer_card': ankimon_objects.get('trainer_card'),
            'ankimon_tracker_window': ankimon_objects.get('ankimon_tracker_window'),
            'logger': ankimon_objects.get('logger'),
            'data_handler_window': ankimon_objects.get('data_handler_window'),
            'settings_window': type('MockSettingsWindow', (), {
                'show_window': mock_callback("Settings Window")
            })(),
            'shop_manager': ankimon_objects.get('shop_manager'),
            'pokedex_window': ankimon_objects.get('pokedex_window'),
            'ankimon_key': 'Ctrl+K',
            'join_discord_url': mock_callback("Join Discord"),
            'open_leaderboard_url': mock_callback("Open Leaderboard"),
            'settings_obj': ankimon_objects.get('settings_obj'),
            'addon_dir': Path(__file__).parent.parent / "src" / "Ankimon",
            'data_handler_obj': ankimon_objects.get('data_handler_obj'),
            'pokemon_pc': ankimon_objects.get('pokemon_pc'),
        }

        create_menu_actions(**menu_params)
        print("Ankimon menu actions created successfully")

    except Exception as e:
        print(f"Error loading Ankimon menu: {e}")
        import traceback
        traceback.print_exc()

class FixedTestEnvironmentMainWindow:
    """Fixed main window for the Ankimon test environment with proper HUD support"""

    def __init__(self, ankimon_objects):
        from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMenuBar, QPushButton, QHBoxLayout
        
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("Ankimon Test Environment - Fixed Version")
        self.main_window.setGeometry(100, 100, 1400, 900)

        # Create central widget with side controls
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left control panel
        control_panel = QWidget()
        control_panel.setFixedWidth(300)
        control_layout = QVBoxLayout(control_panel)
        
        # Add control buttons
        self.start_btn = QPushButton("Start Review")
        self.next_btn = QPushButton("Next Card")
        self.hud_btn = QPushButton("Show Ankimon HUD")
        self.answer_btn = QPushButton("Show Answer")
        
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.next_btn)
        control_layout.addWidget(self.hud_btn)
        control_layout.addWidget(self.answer_btn)
        
        # Add ease buttons
        ease_layout = QHBoxLayout()
        self.ease_btns = []
        for i, label in enumerate(["Again", "Hard", "Good", "Easy"], 1):
            btn = QPushButton(label)
            ease_layout.addWidget(btn)
            self.ease_btns.append(btn)
        
        control_layout.addLayout(ease_layout)
        control_layout.addStretch()

        # Right reviewer area
        self.reviewer_container = QWidget()
        self.reviewer_layout = QVBoxLayout(self.reviewer_container)

        # Add to main layout
        main_layout.addWidget(control_panel)
        main_layout.addWidget(self.reviewer_container, 1)

        # Setup menubar
        self.menubar = QMenuBar(self.main_window)
        self.main_window.setMenuBar(self.menubar)

        # Store Ankimon objects
        self.ankimon_objects = ankimon_objects

        print("FixedTestEnvironmentMainWindow initialized")

    def setup_reviewer(self, reviewer):
        """Setup reviewer with full HUD support"""
        # Add webviews to layout
        self.reviewer_layout.addWidget(reviewer.web.qwebengine_view)
        reviewer.bottom.web.qwebengine_view.setMaximumHeight(100)
        self.reviewer_layout.addWidget(reviewer.bottom.web.qwebengine_view)

        # Connect buttons to reviewer actions
        self.start_btn.clicked.connect(reviewer.show)
        self.next_btn.clicked.connect(reviewer.nextCard)
        self.answer_btn.clicked.connect(reviewer._showAnswer)
        
        # Connect ease buttons
        for i, btn in enumerate(self.ease_btns, 1):
            btn.clicked.connect(lambda checked, ease=i: reviewer._answerCard(ease))

        # Connect the reviewer to Ankimon's HUD system
        if 'reviewer_obj' in self.ankimon_objects:
            reviewer_manager = self.ankimon_objects['reviewer_obj']
            
            def trigger_hud_update():
                """Trigger HUD update"""
                try:
                    if hasattr(reviewer_manager, 'update_life_bar'):
                        # Create a mock card for the update
                        from mock_anki.collection import MockCard
                        mock_card = MockCard(1, "Sample Question", "Sample Answer")
                        reviewer_manager.update_life_bar(reviewer, mock_card, 3)
                        print("HUD update triggered successfully")
                except Exception as e:
                    print(f"Error triggering HUD: {e}")

            # Connect HUD button
            self.hud_btn.clicked.connect(trigger_hud_update)
            
            # Store the trigger function in reviewer for later use
            reviewer.trigger_hud_update = trigger_hud_update

        print("Reviewer setup with HUD integration complete")

    def show(self):
        self.main_window.show()

    @property
    def menuBar(self):
        return self.main_window.menuBar()

def main():
    print("=== Fixed Ankimon Test Environment Starting ===")

    # 1. Import PyQt6 widgets and create QApplication FIRST
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import Qt
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings

    app = QApplication(sys.argv)

    # 2. Setup mocks and global mw
    setup_anki_mocks()
    mw = setup_global_mw()

    # 3. Load Ankimon objects
    ankimon_objects = load_ankimon_singletons()
    if not ankimon_objects:
        print("Failed to load Ankimon objects, creating minimal fallback")
        ankimon_objects = {}

    # 4. Create fixed main window
    main_window = FixedTestEnvironmentMainWindow(ankimon_objects)

    # 5. Setup reviewer with enhanced mocks
    from mock_aqt.reviewer import EnhancedMockReviewer
    from mock_anki.collection import MockScheduler

    ankimon_root = Path(__file__).parent.parent
    reviewer = EnhancedMockReviewer(None)
    reviewer.web.ankimon_root = ankimon_root
    reviewer.bottom.web.ankimon_root = ankimon_root

    # Connect reviewer to mw
    mw.form = main_window
    mw.col.sched = MockScheduler(mw)
    mw.reviewer = reviewer
    reviewer.mw = mw

    # Setup reviewer in main window with HUD integration
    main_window.setup_reviewer(reviewer)

    # 6. Load Ankimon menu
    load_ankimon_menu(mw, ankimon_objects)

    # Add Ankimon menu to menubar if it exists
    if hasattr(mw, 'pokemenu') and mw.pokemenu:
        main_window.menuBar.addMenu(mw.pokemenu)
        print("Ankimon menu added to menubar")

    # 7. Add fallback test menu
    test_menu = main_window.menuBar.addMenu("Test Controls")
    
    # Battle demonstration action
    def demo_battle():
        print("=== Battle Demo ===")
        reviewer.show()
        if hasattr(reviewer, 'trigger_hud_update'):
            reviewer.trigger_hud_update()
        print("Battle demo started - you should see Pokemon HUD!")
    
    demo_action = test_menu.addAction("Demo Battle with HUD")
    demo_action.triggered.connect(demo_battle)

    # Show main window
    main_window.show()

    print("\n=== Fixed Ankimon Test Environment Ready ===")
    print("Available features:")
    print("- Full Ankimon menu system")
    print("- Pokemon battle HUD overlay") 
    print("- Interactive reviewer with card progression")
    print("- Test Controls menu for demonstrations")
    print("\nClick 'Demo Battle with HUD' to see the full Pokemon experience!")
    
    if ankimon_objects and 'main_pokemon' in ankimon_objects:
        print(f"Ready to battle with {ankimon_objects['main_pokemon'].name}!")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()