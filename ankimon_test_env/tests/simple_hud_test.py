#!/usr/bin/env python3
"""
Simple Ankimon HUD Test Environment

This is a minimal test environment that focuses specifically on displaying
the Ankimon HUD (Pokemon sprites, HP bars, etc.) without all the complex
menu loading and singleton management.

Run this to quickly test the Pokemon overlay system.
"""

import sys
import os
import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QWebEngineView
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineCore import QWebEnginePage

def create_minimal_hud_html():
    """Create a simple HTML page with Ankimon-style HUD"""
    
    # Sample Pokemon data
    main_pokemon = {
        'name': 'Pikachu',
        'level': 50,
        'hp': 85,
        'max_hp': 100,
        'sprite_url': 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'  # Transparent 1x1 GIF
    }
    
    enemy_pokemon = {
        'name': 'Rattata', 
        'level': 5,
        'hp': 25,
        'max_hp': 30,
        'sprite_url': 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7'  # Transparent 1x1 GIF
    }
    
    # Calculate HP percentages
    main_hp_percent = (main_pokemon['hp'] / main_pokemon['max_hp']) * 100
    enemy_hp_percent = (enemy_pokemon['hp'] / enemy_pokemon['max_hp']) * 100
    
    # Determine HP bar colors
    def get_hp_color(percent):
        if percent <= 25:
            return "rgba(255, 0, 0, 0.85)"  # Red
        elif percent <= 50:
            return "rgba(255, 255, 0, 0.85)"  # Yellow
        else:
            return "rgba(114, 230, 96, 0.85)"  # Green
    
    main_hp_color = get_hp_color(main_hp_percent)
    enemy_hp_color = get_hp_color(enemy_hp_percent)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Ankimon HUD Test</title>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: Arial, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                position: relative;
            }}
            
            .card-content {{
                background: white;
                border-radius: 10px;
                padding: 40px;
                margin: 20px;
                box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                text-align: center;
            }}
            
            .question {{
                font-size: 24px;
                margin-bottom: 20px;
                color: #333;
            }}
            
            .answer {{
                font-size: 20px;
                color: #666;
                margin-top: 20px;
                display: none;
            }}
            
            /* Ankimon HUD Styles */
            #ankimon-hud {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                z-index: 9999;
                font-family: monospace;
            }}
            
            /* Pokemon Sprites */
            #ankimon-hud #MyPokeImage {{
                position: fixed;
                bottom: 80px;
                left: 20px;
                width: 80px;
                height: 80px;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="40" fill="%23FFD700"/><circle cx="35" cy="40" r="5" fill="black"/><circle cx="65" cy="40" r="5" fill="black"/><path d="M30 60 Q50 80 70 60" stroke="red" stroke-width="3" fill="none"/><text x="50" y="90" text-anchor="middle" font-size="8" fill="red">⚡</text></svg>') no-repeat center;
                background-size: contain;
                z-index: 9999;
            }}
            
            #ankimon-hud #PokeImage {{
                position: fixed;
                bottom: 150px;
                right: 20px;
                width: 60px;
                height: 60px;
                background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="35" fill="%23A0522D"/><circle cx="40" cy="45" r="3" fill="black"/><circle cx="60" cy="45" r="3" fill="black"/><path d="M40 65 Q50 70 60 65" stroke="black" stroke-width="2" fill="none"/></svg>') no-repeat center;
                background-size: contain;
                z-index: 9999;
                transform: scaleX(-1);
            }}
            
            /* HP Bars */
            #ankimon-hud #mylife-bar {{
                position: fixed;
                bottom: 40px;
                left: 10px;
                width: {main_hp_percent * 2}px;
                max-width: 200px;
                height: 8px;
                background: {main_hp_color};
                border-radius: 4px;
                border: 2px solid white;
                z-index: 9999;
            }}
            
            #ankimon-hud #life-bar {{
                position: fixed;
                bottom: 200px;
                right: 10px;
                width: {enemy_hp_percent * 2}px;
                max-width: 200px;
                height: 8px;
                background: {enemy_hp_color};
                border-radius: 4px;
                border: 2px solid white;
                z-index: 9999;
            }}
            
            /* Pokemon Info Pills */
            .ankimon-pill {{
                position: fixed;
                z-index: 9999;
                color: white;
                font-size: 14px;
                font-weight: bold;
                background-color: rgba(0, 0, 0, 0.8);
                border: 2px solid white;
                border-radius: 6px;
                padding: 4px 8px;
            }}
            
            #ankimon-hud #myname-display {{
                bottom: 55px;
                left: 10px;
            }}
            
            #ankimon-hud #myhp-display {{
                bottom: 55px;
                right: 60%;
            }}
            
            #ankimon-hud #name-display {{
                bottom: 220px;
                right: 10px;
            }}
            
            #ankimon-hud #hp-display {{
                bottom: 220px;
                left: 60%;
            }}
            
            /* Animation for battles */
            @keyframes shake {{
                0%, 100% {{ transform: translateX(0); }}
                25% {{ transform: translateX(-2px); }}
                75% {{ transform: translateX(2px); }}
            }}
            
            .battle-hit {{
                animation: shake 0.5s ease-in-out;
            }}
            
            /* Controls */
            .controls {{
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 10000;
            }}
            
            .controls button {{
                margin: 2px;
                padding: 8px 12px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                pointer-events: all;
            }}
            
            .controls button:hover {{
                background: #45a049;
            }}
        </style>
    </head>
    <body>
        <!-- Main Card Content -->
        <div class="card-content">
            <div class="question">What is 2 + 2?</div>
            <div class="answer" id="answer">The answer is 4!</div>
            
            <div style="margin-top: 30px;">
                <button onclick="showAnswer()" style="padding: 10px 20px; font-size: 16px;">Show Answer</button>
            </div>
        </div>
        
        <!-- Ankimon HUD Overlay -->
        <div id="ankimon-hud">
            <!-- My Pokemon (bottom-left) -->
            <div id="MyPokeImage"></div>
            <div id="mylife-bar"></div>
            <div class="ankimon-pill" id="myname-display">{main_pokemon['name']} Lv.{main_pokemon['level']}</div>
            <div class="ankimon-pill" id="myhp-display">{main_pokemon['hp']}/{main_pokemon['max_hp']}</div>
            
            <!-- Enemy Pokemon (top-right) -->
            <div id="PokeImage"></div>
            <div id="life-bar"></div>
            <div class="ankimon-pill" id="name-display">{enemy_pokemon['name']} Lv.{enemy_pokemon['level']}</div>
            <div class="ankimon-pill" id="hp-display">{enemy_pokemon['hp']}/{enemy_pokemon['max_hp']}</div>
        </div>
        
        <!-- Controls -->
        <div class="controls">
            <button onclick="toggleHUD()">Toggle HUD</button>
            <button onclick="simulateBattle()">Battle Demo</button>
            <button onclick="healPokemon()">Heal All</button>
        </div>
        
        <script>
            let hudVisible = true;
            let mainHP = {main_pokemon['hp']};
            let maxMainHP = {main_pokemon['max_hp']};
            let enemyHP = {enemy_pokemon['hp']};
            let maxEnemyHP = {enemy_pokemon['max_hp']};
            
            function showAnswer() {{
                document.getElementById('answer').style.display = 'block';
                // Trigger battle effect when answer is shown
                setTimeout(() => simulateBattle(), 500);
            }}
            
            function toggleHUD() {{
                const hud = document.getElementById('ankimon-hud');
                hudVisible = !hudVisible;
                hud.style.display = hudVisible ? 'block' : 'none';
                console.log('HUD toggled:', hudVisible ? 'visible' : 'hidden');
            }}
            
            function updateHP(pokemon, newHP, maxHP) {{
                const percent = (newHP / maxHP) * 100;
                let color;
                
                if (percent <= 25) {{
                    color = 'rgba(255, 0, 0, 0.85)';
                }} else if (percent <= 50) {{
                    color = 'rgba(255, 255, 0, 0.85)';
                }} else {{
                    color = 'rgba(114, 230, 96, 0.85)';
                }}
                
                if (pokemon === 'main') {{
                    document.getElementById('mylife-bar').style.width = (percent * 2) + 'px';
                    document.getElementById('mylife-bar').style.background = color;
                    document.getElementById('myhp-display').textContent = newHP + '/' + maxHP;
                    mainHP = newHP;
                }} else {{
                    document.getElementById('life-bar').style.width = (percent * 2) + 'px';
                    document.getElementById('life-bar').style.background = color;
                    document.getElementById('hp-display').textContent = newHP + '/' + maxHP;
                    enemyHP = newHP;
                }}
                
                console.log(`Updated ${{pokemon}} HP: ${{newHP}}/${{maxHP}} (${{percent.toFixed(1)}}%)`);
            }}
            
            function simulateBattle() {{
                console.log('=== Battle Demo Started ===');
                
                // Enemy attacks main pokemon
                const mainDamage = Math.floor(Math.random() * 15) + 5;
                const newMainHP = Math.max(0, mainHP - mainDamage);
                
                // Add battle animation
                document.getElementById('MyPokeImage').classList.add('battle-hit');
                setTimeout(() => {{
                    document.getElementById('MyPokeImage').classList.remove('battle-hit');
                }}, 500);
                
                updateHP('main', newMainHP, maxMainHP);
                console.log(`Enemy attacks! ${{mainDamage}} damage to Pikachu`);
                
                // Counter-attack after a delay
                setTimeout(() => {{
                    const enemyDamage = Math.floor(Math.random() * 20) + 10;
                    const newEnemyHP = Math.max(0, enemyHP - enemyDamage);
                    
                    document.getElementById('PokeImage').classList.add('battle-hit');
                    setTimeout(() => {{
                        document.getElementById('PokeImage').classList.remove('battle-hit');
                    }}, 500);
                    
                    updateHP('enemy', newEnemyHP, maxEnemyHP);
                    console.log(`Pikachu counter-attacks! ${{enemyDamage}} damage to Rattata`);
                    
                    if (newEnemyHP <= 0) {{
                        setTimeout(() => {{
                            alert('Victory! Rattata fainted!');
                            console.log('Battle won!');
                        }}, 800);
                    }} else if (newMainHP <= 0) {{
                        setTimeout(() => {{
                            alert('Defeat! Pikachu fainted!');
                            console.log('Battle lost!');
                        }}, 800);
                    }}
                }}, 1000);
            }}
            
            function healPokemon() {{
                updateHP('main', maxMainHP, maxMainHP);
                updateHP('enemy', maxEnemyHP, maxEnemyHP);
                console.log('All Pokemon healed!');
            }}
            
            // Auto-show HUD on load
            console.log('Ankimon HUD Test Environment loaded');
            console.log('Available commands: toggleHUD(), simulateBattle(), healPokemon()');
            console.log('Current Pokemon: Pikachu vs Rattata');
        </script>
    </body>
    </html>
    """
    
    return html

class SimpleHUDTestWindow(QMainWindow):
    """Simple test window for Ankimon HUD"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ankimon HUD Test - Simple Version")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add info label
        info_label = QLabel("Ankimon HUD Test Environment")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px;")
        layout.addWidget(info_label)
        
        # Create webview
        self.webview = QWebEngineView()
        layout.addWidget(self.webview)
        
        # Create control buttons
        button_layout = QHBoxLayout()
        
        reload_btn = QPushButton("Reload HUD")
        reload_btn.clicked.connect(self.load_hud)
        button_layout.addWidget(reload_btn)
        
        battle_btn = QPushButton("Trigger Battle")
        battle_btn.clicked.connect(self.trigger_battle)
        button_layout.addWidget(battle_btn)
        
        toggle_btn = QPushButton("Toggle HUD")
        toggle_btn.clicked.connect(self.toggle_hud)
        button_layout.addWidget(toggle_btn)
        
        layout.addLayout(button_layout)
        
        # Load initial HUD
        self.load_hud()
    
    def load_hud(self):
        """Load the HUD HTML into the webview"""
        html = create_minimal_hud_html()
        self.webview.setHtml(html)
        print("HUD loaded into webview")
    
    def trigger_battle(self):
        """Trigger a battle animation via JavaScript"""
        self.webview.page().runJavaScript("simulateBattle();")
        print("Battle triggered!")
    
    def toggle_hud(self):
        """Toggle HUD visibility"""
        self.webview.page().runJavaScript("toggleHUD();")
        print("HUD toggled!")

def main():
    print("=== Simple Ankimon HUD Test Environment ===")
    
    # Create application
    app = QApplication(sys.argv)
    
    # Create and show window
    window = SimpleHUDTestWindow()
    window.show()
    
    print("Test environment ready!")
    print("Expected features:")
    print("- Pokemon sprites (Pikachu vs Rattata)")
    print("- HP bars that change color")
    print("- Pokemon names and levels")
    print("- Battle animations")
    print("- Interactive controls")
    print("")
    print("Try clicking 'Trigger Battle' to see the battle system in action!")
    
    # Run application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()