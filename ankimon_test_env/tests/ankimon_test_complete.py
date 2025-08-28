#!/usr/bin/env python3
"""
Complete Ankimon Test Environment
This script provides the full Ankimon reviewer experience with HUD, menus, and Pokemon functionality
"""

import sys
import os
import json
import types
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QPushButton, QLabel, QFrame
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QAction

class AnkimonTestEnvironment:
    """Complete Ankimon test environment with full HUD support"""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Ankimon Test Environment")
        
        # Setup mocks and paths
        self.setup_mocks()
        self.setup_ankimon_files()
        
        # Create main window
        self.main_window = QMainWindow()
        self.main_window.setWindowTitle("Ankimon Reviewer Test Environment")
        self.main_window.setGeometry(100, 100, 1400, 900)
        
        # Initialize components
        self.ankimon_objects = None
        self.reviewer_manager = None
        self.current_card_index = 0
        
        self.setup_ui()
        self.load_ankimon()
        
    def setup_mocks(self):
        """Setup all necessary mocks for Ankimon"""
        print("Setting up comprehensive mocks...")
        
        # Create anki mocks
        mock_anki = types.ModuleType("anki")
        mock_anki.collection = types.ModuleType("anki.collection")
        mock_anki.cards = types.ModuleType("anki.cards")
        mock_anki.utils = types.ModuleType("anki.utils")
        mock_anki.hooks = types.ModuleType("anki.hooks")
        
        # Import collection classes
        sys.path.insert(0, str(Path(__file__).parent))
        from mock_anki.collection import Collection, MockCard
        mock_anki.collection.Collection = Collection
        mock_anki.cards.Card = MockCard
        
        # Create aqt mocks
        mock_aqt = types.ModuleType("aqt")
        mock_aqt.utils = types.ModuleType("aqt.utils")
        mock_aqt.gui_hooks = types.ModuleType("aqt.gui_hooks")
        mock_aqt.qt = types.ModuleType("aqt.qt")
        
        # Mock functions
        mock_aqt.utils.showInfo = lambda x: print(f"ShowInfo: {x}")
        mock_aqt.utils.showWarning = lambda x: print(f"ShowWarning: {x}")
        mock_aqt.utils.qconnect = lambda signal, slot: signal.connect(slot)
        
        # Mock GUI hooks
        hook_names = [
            'reviewer_did_show_question', 'reviewer_did_show_answer', 
            'reviewer_will_answer_card', 'reviewer_did_answer_card',
            'reviewer_will_end', 'card_will_show'
        ]
        for hook_name in hook_names:
            setattr(mock_aqt.gui_hooks, hook_name, [])
        
        # Mock Qt classes
        mock_aqt.qt.QMenu = QMenu
        mock_aqt.qt.QAction = QAction
        mock_aqt.qt.QKeySequence = lambda x: x
        
        # Create main window mock
        mw = types.SimpleNamespace()
        mw.col = Collection()
        mw.app = self.app
        mw.addonManager = types.SimpleNamespace()
        mw.addonManager.addonFromModule = lambda x: "ankimon"
        mw.addonManager.addonsFolder = lambda: Path(__file__).parent.parent / "src"
        
        mock_aqt.mw = mw
        
        # Inject all mocks
        modules = {
            "anki": mock_anki, "anki.collection": mock_anki.collection,
            "anki.cards": mock_anki.cards, "anki.utils": mock_anki.utils,
            "anki.hooks": mock_anki.hooks, "aqt": mock_aqt,
            "aqt.utils": mock_aqt.utils, "aqt.gui_hooks": mock_aqt.gui_hooks,
            "aqt.qt": mock_aqt.qt, "aqt.main": mock_aqt
        }
        
        for name, module in modules.items():
            sys.modules[name] = module
        
        self.mw = mw
        print("Mocks setup complete")
    
    def setup_ankimon_files(self):
        """Setup necessary Ankimon files and directories"""
        print("Setting up Ankimon files...")
        
        ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
        user_files = ankimon_path / "user_files"
        user_files.mkdir(parents=True, exist_ok=True)
        
        # Create Pokemon data
        pokemon_data = [
            {
                "id": 25, "name": "Pikachu", "level": 50, "hp": 85, "max_hp": 100,
                "stats": {"hp": 100, "atk": 80, "def": 70, "spa": 90, "spd": 80, "spe": 120},
                "shiny": False, "gender": "M", "attacks": ["Thunderbolt", "Quick Attack"]
            }
        ]
        
        with open(user_files / "mypokemon.json", "w") as f:
            json.dump(pokemon_data, f)
        
        # Create settings
        settings_data = {
            "gui.show_mainpkmn_in_reviewer": 2,  # Show both Pokemon
            "battle.hp_bar_thickness": 4,
            "gui.reviewer_image_gif": 1,
            "gui.reviewer_text_message_box": True,
            "misc.language": 9
        }
        
        with open(user_files / "config.json", "w") as f:
            json.dump(settings_data, f)
        
        # Create empty itembag
        with open(user_files / "itembag.json", "w") as f:
            json.dump({}, f)
    
    def setup_ui(self):
        """Setup the main UI"""
        print("Setting up UI...")
        
        # Central widget
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        
        # Left panel for controls
        control_panel = QFrame()
        control_panel.setFixedWidth(300)
        control_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        control_layout = QVBoxLayout(control_panel)
        
        # Title
        title = QLabel("Ankimon Test Environment")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        control_layout.addWidget(title)
        
        # Status
        self.status_label = QLabel("Loading Ankimon...")
        control_layout.addWidget(self.status_label)
        
        # Buttons
        self.start_btn = QPushButton("Start Review")
        self.start_btn.clicked.connect(self.start_review)
        control_layout.addWidget(self.start_btn)
        
        self.next_btn = QPushButton("Next Card")
        self.next_btn.clicked.connect(self.next_card)
        control_layout.addWidget(self.next_btn)
        
        self.show_hud_btn = QPushButton("Show HUD")
        self.show_hud_btn.clicked.connect(self.show_hud)
        control_layout.addWidget(self.show_hud_btn)
        
        self.answer_btn = QPushButton("Show Answer")
        self.answer_btn.clicked.connect(self.show_answer)
        control_layout.addWidget(self.answer_btn)
        
        # Ease buttons
        ease_layout = QHBoxLayout()
        self.ease_btns = []
        for i, label in enumerate(["Again", "Hard", "Good", "Easy"], 1):
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, ease=i: self.answer_card(ease))
            ease_layout.addWidget(btn)
            self.ease_btns.append(btn)
        
        control_layout.addLayout(ease_layout)
        control_layout.addStretch()
        
        # Right panel for reviewer
        reviewer_panel = QWidget()
        reviewer_layout = QVBoxLayout(reviewer_panel)
        
        # Main webview (card content)
        self.main_webview = QWebEngineView()
        self.main_webview.setHtml("""
        <html>
            <head>
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        background: #f5f5f5;
                    }
                    .card { 
                        background: white; 
                        padding: 20px; 
                        border-radius: 10px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                        text-align: center;
                    }
                    .question { color: #333; font-size: 18px; }
                    .answer { color: #0066cc; font-size: 16px; margin-top: 15px; }
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="question">Click "Start Review" to begin</div>
                    <div id="ankimon-hud-container"></div>
                </div>
            </body>
        </html>
        """)
        
        reviewer_layout.addWidget(self.main_webview)
        
        # Bottom webview (controls)
        self.bottom_webview = QWebEngineView()
        self.bottom_webview.setFixedHeight(80)
        self.bottom_webview.setHtml("""
        <html>
            <body style="margin:0; padding:10px; background:#e0e0e0; text-align:center;">
                <div id="controls">Ankimon HUD will appear here</div>
            </body>
        </html>
        """)
        reviewer_layout.addWidget(self.bottom_webview)
        
        # Add panels to main layout
        main_layout.addWidget(control_panel)
        main_layout.addWidget(reviewer_panel, 1)
        
        # Setup menu
        self.setup_menu()
        
    def setup_menu(self):
        """Setup the menu bar"""
        menubar = self.main_window.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        exit_action = file_menu.addAction("Exit")
        exit_action.triggered.connect(self.app.quit)
        
        # Ankimon menu (will be populated when Ankimon loads)
        self.ankimon_menu = menubar.addMenu("Ankimon")
        loading_action = self.ankimon_menu.addAction("Loading...")
        loading_action.setEnabled(False)
    
    def load_ankimon(self):
        """Load all Ankimon components"""
        print("Loading Ankimon components...")
        
        try:
            # Add Ankimon to path
            ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
            if str(ankimon_path) not in sys.path:
                sys.path.insert(0, str(ankimon_path))
            
            # Load Ankimon singletons
            from singletons import (
                settings_obj, main_pokemon, enemy_pokemon, reviewer_obj,
                test_window, logger
            )
            
            self.settings_obj = settings_obj
            self.main_pokemon = main_pokemon
            self.enemy_pokemon = enemy_pokemon
            self.reviewer_manager = reviewer_obj
            self.test_window = test_window
            self.logger = logger
            
            # Update mw reference
            self.mw.reviewer = self
            self.mw.form = self.main_window
            
            # Load menu
            self.load_menu()
            
            self.status_label.setText(f"Loaded! Main: {main_pokemon.name}, Enemy: {enemy_pokemon.name}")
            print(f"Successfully loaded Ankimon with {main_pokemon.name} vs {enemy_pokemon.name}")
            
        except Exception as e:
            self.status_label.setText(f"Error loading Ankimon: {str(e)}")
            print(f"Error loading Ankimon: {e}")
            import traceback
            traceback.print_exc()
    
    def load_menu(self):
        """Load the Ankimon menu"""
        try:
            # Clear loading message
            self.ankimon_menu.clear()
            
            # Add some basic Ankimon actions
            collection_action = self.ankimon_menu.addAction("Pokemon Collection")
            collection_action.triggered.connect(lambda: print("Pokemon Collection opened"))
            
            battle_action = self.ankimon_menu.addAction("Battle Window")
            battle_action.triggered.connect(self.open_battle_window)
            
            settings_action = self.ankimon_menu.addAction("Settings")
            settings_action.triggered.connect(lambda: print("Settings opened"))
            
            print("Menu loaded successfully")
            
        except Exception as e:
            print(f"Error loading menu: {e}")
    
    def open_battle_window(self):
        """Open the Ankimon battle window"""
        try:
            if hasattr(self, 'test_window') and self.test_window:
                self.test_window.show()
            else:
                print("Battle window not available")
        except Exception as e:
            print(f"Error opening battle window: {e}")
    
    def start_review(self):
        """Start the review session"""
        print("Starting review session...")
        
        # Sample cards
        self.cards = [
            {"question": "What is 2 + 2?", "answer": "4"},
            {"question": "What is the capital of France?", "answer": "Paris"},
            {"question": "What is the largest planet?", "answer": "Jupiter"},
            {"question": "What color is the sky?", "answer": "Blue"},
            {"question": "How many sides does a triangle have?", "answer": "3"}
        ]
        
        self.current_card_index = 0
        self.show_question()
        
        # Trigger HUD display
        QTimer.singleShot(500, self.show_hud)
    
    def show_question(self):
        """Show current question"""
        if self.current_card_index >= len(self.cards):
            self.main_webview.setHtml("""
            <html><body style="text-align:center; padding:50px;">
                <h2>Review Complete!</h2>
                <p>No more cards to review.</p>
            </body></html>
            """)
            return
        
        card = self.cards[self.current_card_index]
        html = f"""
        <html>
            <head>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        background: #f0f8ff;
                        position: relative;
                    }}
                    .card {{ 
                        background: white; 
                        padding: 30px; 
                        border-radius: 15px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        text-align: center;
                        margin-bottom: 20px;
                    }}
                    .question {{ 
                        color: #2c3e50; 
                        font-size: 24px; 
                        font-weight: bold;
                        margin-bottom: 20px;
                    }}
                    .card-number {{
                        color: #7f8c8d;
                        font-size: 14px;
                        margin-bottom: 15px;
                    }}
                    #ankimon-hud-container {{
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        pointer-events: none;
                        z-index: 9999;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="card-number">Card {self.current_card_index + 1} of {len(self.cards)}</div>
                    <div class="question">{card['question']}</div>
                </div>
                <div id="ankimon-hud-container"></div>
            </body>
        </html>
        """
        
        self.main_webview.setHtml(html)
    
    def show_answer(self):
        """Show the answer for current card"""
        if self.current_card_index >= len(self.cards):
            return
        
        card = self.cards[self.current_card_index]
        html = f"""
        <html>
            <head>
                <style>
                    body {{ 
                        font-family: Arial, sans-serif; 
                        margin: 20px; 
                        background: #f0fff0;
                        position: relative;
                    }}
                    .card {{ 
                        background: white; 
                        padding: 30px; 
                        border-radius: 15px; 
                        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                        text-align: center;
                    }}
                    .question {{ 
                        color: #2c3e50; 
                        font-size: 20px; 
                        margin-bottom: 20px;
                    }}
                    .answer {{ 
                        color: #27ae60; 
                        font-size: 24px; 
                        font-weight: bold;
                        margin-top: 20px;
                        padding: 15px;
                        background: #ecf0f1;
                        border-radius: 10px;
                    }}
                    .card-number {{
                        color: #7f8c8d;
                        font-size: 14px;
                        margin-bottom: 15px;
                    }}
                    #ankimon-hud-container {{
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        pointer-events: none;
                        z-index: 9999;
                    }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="card-number">Card {self.current_card_index + 1} of {len(self.cards)}</div>
                    <div class="question">{card['question']}</div>
                    <div class="answer">{card['answer']}</div>
                </div>
                <div id="ankimon-hud-container"></div>
            </body>
        </html>
        """
        
        self.main_webview.setHtml(html)
    
    def show_hud(self):
        """Show the Ankimon HUD overlay"""
        print("Showing Ankimon HUD...")
        
        if not self.reviewer_manager:
            print("No reviewer manager available")
            return
        
        try:
            # Create a mock reviewer for the HUD system
            mock_reviewer = types.SimpleNamespace()
            mock_reviewer.web = types.SimpleNamespace()
            
            # Capture JavaScript execution
            def mock_eval(js_code):
                print(f"HUD JavaScript: {js_code[:200]}...")
                # Inject the HUD into our webview
                self.main_webview.page().runJavaScript(js_code)
            
            mock_reviewer.web.eval = mock_eval
            
            # Create mock card
            from mock_anki.collection import MockCard
            mock_card = MockCard(
                self.current_card_index + 1,
                self.cards[self.current_card_index]["question"] if self.current_card_index < len(self.cards) else "No more cards",
                self.cards[self.current_card_index]["answer"] if self.current_card_index < len(self.cards) else ""
            )
            
            # Trigger HUD update
            self.reviewer_manager.update_life_bar(mock_reviewer, mock_card, 3)
            
            # Update status
            self.status_label.setText(f"HUD Active - {self.main_pokemon.name} HP: {self.main_pokemon.hp}/{self.main_pokemon.max_hp}")
            
        except Exception as e:
            print(f"Error showing HUD: {e}")
            import traceback
            traceback.print_exc()
    
    def answer_card(self, ease):
        """Answer the current card with given ease"""
        print(f"Answering card with ease: {ease}")
        
        # Simulate battle damage based on ease
        if ease == 1:  # Again - enemy attacks
            damage = 15
            self.main_pokemon.hp = max(0, self.main_pokemon.hp - damage)
            print(f"{self.main_pokemon.name} takes {damage} damage!")
        elif ease == 4:  # Easy - player attacks
            damage = 20
            self.enemy_pokemon.hp = max(0, self.enemy_pokemon.hp - damage)
            print(f"{self.enemy_pokemon.name} takes {damage} damage!")
        
        # Move to next card
        QTimer.singleShot(1000, self.next_card)
        
        # Update HUD
        QTimer.singleShot(500, self.show_hud)
    
    def next_card(self):
        """Move to the next card"""
        self.current_card_index += 1
        self.show_question()
        
        # Auto-show HUD for next card
        QTimer.singleShot(500, self.show_hud)
    
    def run(self):
        """Run the application"""
        print("Starting Ankimon Test Environment...")
        self.main_window.show()
        return self.app.exec()

def main():
    """Main entry point"""
    print("=== Ankimon Complete Test Environment ===")
    
    env = AnkimonTestEnvironment()
    
    print("\nInstructions:")
    print("1. Click 'Start Review' to begin")
    print("2. Click 'Show HUD' to display Pokemon HUD overlay")
    print("3. Click 'Show Answer' to reveal answers")
    print("4. Use ease buttons to answer cards and trigger battle effects")
    print("5. Check the Ankimon menu for additional features")
    print("\nThe HUD should show Pokemon sprites, HP bars, and battle effects!")
    
    return env.run()

if __name__ == "__main__":
    sys.exit(main())