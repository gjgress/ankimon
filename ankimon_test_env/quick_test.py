#!/usr/bin/env python3
"""
Quick Test Script for Enhanced Ankimon Environment

This fixes the import issue and provides a complete working test environment.
"""

import sys

from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    print("=== Quick Ankimon Test Environment ===")

    # Import PyQt6 first
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Import our enhanced components
    from mock_aqt.reviewer import EnhancedMockReviewer
    from mock_anki.collection import MockCard, MockScheduler

    # Create enhanced scheduler with better cards
    class QuickScheduler:
        def __init__(self):
            self._queue = [
                MockCard(1, 
                    "<h3>🧮 Basic Math</h3><p>What is <strong>7 × 9</strong>?</p>", 
                    "<div style='text-align: center;'><h2 style='color: #4CAF50;'>63</h2><p><strong>Tip:</strong> 7 × 9 = 63<br><em>Think: 7 × 10 - 7 = 70 - 7 = 63</em></p></div>"
                ),
                MockCard(2, 
                    "<h3>🌍 Geography</h3><p>What is the capital of <strong>Australia</strong>?</p>", 
                    "<div style='text-align: center;'><h2 style='color: #2196F3;'>Canberra</h2><p><strong>Fun fact:</strong> Not Sydney or Melbourne!<br><em>Canberra was specifically planned as the capital city</em></p></div>"
                ),
                MockCard(3, 
                    "<h3>🔬 Science</h3><p>What gas makes up about <strong>78%</strong> of Earth's atmosphere?</p>", 
                    "<div style='text-align: center;'><h2 style='color: #FF9800;'>Nitrogen</h2><p><strong>Composition:</strong> 78% Nitrogen, 21% Oxygen<br><em>The remaining 1% includes argon, CO₂, and other gases</em></p></div>"
                ),
            ]
            self.current_card_index = -1
            self.new_count = len(self._queue)
            
        def get_next_card(self):
            self.current_card_index += 1
            if self.current_card_index < len(self._queue):
                return self._queue[self.current_card_index]
            return None
            
        def answerButtons(self, card):
            return 4
            
        def answerCard(self, card, ease):
            print(f"Card answered with ease {ease}")

    # Create simple main window
    from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
    from PyQt6.QtCore import Qt
    
    class QuickTestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Quick Ankimon Test - Enhanced Reviewer")
            self.setGeometry(200, 200, 1400, 800)
            
            # Dark theme
            self.setStyleSheet("""
                QMainWindow { 
                    background-color: #2b2b2b; 
                    color: #e0e0e0; 
                }
                QPushButton {
                    background-color: #4a4a4a;
                    color: white;
                    border: 1px solid #666;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-size: 14px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #5a5a5a;
                }
                QLabel {
                    color: #e0e0e0;
                    font-size: 14px;
                }
            """)
            
            # Setup UI
            central = QWidget()
            self.setCentralWidget(central)
            main_layout = QHBoxLayout(central)
            
            # Control panel
            controls = QWidget()
            controls.setFixedWidth(250)
            controls.setStyleSheet("background-color: #383838; border-radius: 8px; padding: 10px;")
            control_layout = QVBoxLayout(controls)
            
            title = QLabel("🎮 Quick Test Controls")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("font-size: 16px; font-weight: bold; color: #6495ed; margin-bottom: 15px;")
            control_layout.addWidget(title)
            
            self.start_btn = QPushButton("▶️ Start Review")
            self.next_btn = QPushButton("⏭️ Next Card") 
            self.answer_btn = QPushButton("💡 Show Answer")
            
            control_layout.addWidget(self.start_btn)
            control_layout.addWidget(self.next_btn)
            control_layout.addWidget(self.answer_btn)
            
            # Ease buttons
            control_layout.addWidget(QLabel("\n📊 Rate Difficulty:"))
            ease_layout = QVBoxLayout()
            
            self.ease1 = QPushButton("❌ Again")
            self.ease2 = QPushButton("🔶 Hard")
            self.ease3 = QPushButton("✅ Good") 
            self.ease4 = QPushButton("⚡ Easy")
            
            self.ease1.setStyleSheet("QPushButton { background-color: #dc3545; }")
            self.ease2.setStyleSheet("QPushButton { background-color: #fd7e14; }")
            self.ease3.setStyleSheet("QPushButton { background-color: #28a745; }")
            self.ease4.setStyleSheet("QPushButton { background-color: #007bff; }")
            
            ease_layout.addWidget(self.ease1)
            ease_layout.addWidget(self.ease2)
            ease_layout.addWidget(self.ease3)
            ease_layout.addWidget(self.ease4)
            
            control_layout.addLayout(ease_layout)
            control_layout.addStretch()
            
            # Reviewer area
            self.reviewer_area = QWidget()
            self.reviewer_layout = QVBoxLayout(self.reviewer_area)
            
            main_layout.addWidget(controls)
            main_layout.addWidget(self.reviewer_area, 1)
            
            # Setup reviewer
            self.setup_reviewer()
            
        def setup_reviewer(self):
            # Create mock mw object
            mw = type('MockMW', (), {})()
            mw.col = type('MockCol', (), {})()
            mw.col.sched = QuickScheduler()
            
            # Create reviewer
            self.reviewer = EnhancedMockReviewer(mw)
            self.reviewer.initialize_webviews(Path(__file__).parent.parent)
            
            # Add to layout
            self.reviewer_layout.addWidget(self.reviewer.web.qwebengine_view)
            self.reviewer.bottom.qwebengine_view.setMaximumHeight(100)
            self.reviewer_layout.addWidget(self.reviewer.bottom.qwebengine_view)
            
            # Connect buttons
            self.start_btn.clicked.connect(self.reviewer.show)
            self.next_btn.clicked.connect(self.reviewer.nextCard)
            self.answer_btn.clicked.connect(self.reviewer._showAnswer)
            
            self.ease1.clicked.connect(lambda: self.reviewer._answerCard(1))
            self.ease2.clicked.connect(lambda: self.reviewer._answerCard(2))
            self.ease3.clicked.connect(lambda: self.reviewer._answerCard(3))
            self.ease4.clicked.connect(lambda: self.reviewer._answerCard(4))
            
            print("Quick test reviewer setup complete!")

    # Show window
    window = QuickTestWindow()
    window.show()
    
    print("\n[OK] Quick Test Environment Ready!")
    print("* Features:")
    print("  • Dark themed interface")
    print("  • Enhanced sample cards with rich content")
    print("  • Full reviewer functionality")
    print("  • Proper answer buttons")
    print("\n-> Instructions:")
    print("  1. Click '> Start Review' to begin")
    print("  2. Click '* Show Answer' to see the answer")
    print("  3. Use difficulty buttons to rate and continue")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
