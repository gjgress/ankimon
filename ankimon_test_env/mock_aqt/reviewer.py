import sys
import json
from typing import Any, Callable
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pathlib import Path
from mock_anki.collection import MockCard, MockScheduler

class EnhancedMockWebview:
    """Enhanced mock for aqt.webview.AnkiWebView with full JavaScript support"""
    
    def __init__(self, mw, ankimon_root, name="", parent=None):
        self.mw = mw
        self.name = name
        self._bridge_command_handler: Callable[[str], None] | None = None
        self.allow_drops = False
        self.ankimon_root = ankimon_root
        
        # Create the actual QWebEngineView
        self.qwebengine_view = QWebEngineView(parent)
        self.web_assets_path = QUrl.fromLocalFile(
            str(Path(self.ankimon_root) / "src" / "Ankimon" / "aqt" / "data" / "web") + "/"
        )
        
        # Track loaded content
        self.current_html = ""
        self.current_css = []
        self.current_js = []
        
        print(f"EnhancedMockWebview '{name}' initialized with assets path: {self.web_assets_path}")

    def stdHtml(self, html, css=None, js=None, context=None):
        """Load HTML with CSS and JS assets similar to Anki's stdHtml"""
        css = css or []
        js = js or []
        
        self.current_html = html
        self.current_css = css
        self.current_js = js
        
        # Build full HTML with assets
        full_html = self._build_full_html(html, css, js)
        self.setHtml(full_html)
        
        print(f"EnhancedMockWebview.stdHtml called with HTML length: {len(html)}")
        return self

    def _build_full_html(self, body_html, css_files, js_files):
        """Build complete HTML document with CSS and JS"""
        
        # CSS links
        css_links = ""
        for css_file in css_files:
            css_path = Path(self.ankimon_root) / "src" / "Ankimon" / "aqt" / "data" / "web" / css_file
            if css_path.exists():
                css_links += f'<link rel="stylesheet" href="{css_path.as_uri()}">\n'
            else:
                print(f"Warning: CSS file not found: {css_path}")
        
        # JS scripts
        js_scripts = ""
        for js_file in js_files:
            js_path = Path(self.ankimon_root) / "src" / "Ankimon" / "aqt" / "data" / "web" / js_file
            if js_path.exists():
                js_scripts += f'<script src="{js_path.as_uri()}"></script>\n'
            else:
                print(f"Warning: JS file not found: {js_path}")
        
        # Add pycmd function for Anki compatibility
        pycmd_script = """
        <script>
        function pycmd(cmd) {
            console.log('pycmd called with:', cmd);
            // In a real Anki webview, this would send to Python
            if (window.pybridge) {
                window.pybridge(cmd);
            }
        }
        // Alias for compatibility
        function bridgeCommand(cmd) { pycmd(cmd); }
        </script>
        """
        
        # Complete HTML document
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ankimon Test Environment</title>
    {css_links}
    {pycmd_script}
</head>
<body>
    {body_html}
    {js_scripts}
</body>
</html>"""
        
        return full_html

    def setHtml(self, html):
        """Set HTML content"""
        self.qwebengine_view.setHtml(html)
        print(f"EnhancedMockWebview.setHtml: Set HTML with length {len(html)}")

    def eval(self, javascript):
        """Execute JavaScript in the webview"""
        print(f"EnhancedMockWebview.eval: Executing JS: {javascript[:100]}...")
        
        def js_callback(result):
            print(f"JavaScript execution result: {result}")
        
        # Execute JavaScript via QWebEngineView
        self.qwebengine_view.page().runJavaScript(javascript, js_callback)
        
        return True

    def set_bridge_command(self, handler, context=None):
        """Set up bridge command handler for pycmd calls"""
        self._bridge_command_handler = handler
        print(f"EnhancedMockWebview: Bridge command handler set for {self.name}")

class EnhancedMockReviewer:
    """Enhanced MockReviewer with full HUD support and card simulation"""
    
    def __init__(self, mw, main_win=None):
        self.mw = mw
        self.main_win = main_win
        self.state = "question"  # Current reviewer state
        self.card = None
        self.previous_card = None
        
        # Create web views with enhanced functionality
        ankimon_root = Path(__file__).parent.parent.parent
        
        self.web = EnhancedMockWebview(mw, ankimon_root, "reviewer_main")
        self.bottom = type('BottomBar', (), {})()
        self.bottom.web = EnhancedMockWebview(mw, ankimon_root, "reviewer_bottom")
        
        # Card queue for testing
        self.card_queue = [
            MockCard(1, "What is 2+2?", "4"),
            MockCard(2, "What is the capital of France?", "Paris"),
            MockCard(3, "What is the largest planet?", "Jupiter"),
            MockCard(4, "What is the smallest prime number?", "2"),
            MockCard(5, "What is the color of the sky?", "Blue"),
        ]
        self.current_card_index = -1
        
        # Initialize reviewer HTML
        self._setup_initial_html()
        
        print("EnhancedMockReviewer initialized with full functionality")

    def _setup_initial_html(self):
        """Setup initial HTML for both main and bottom webviews"""
        
        # Main reviewer HTML (simplified version of Anki's revHtml)
        main_html = """
        <div id="_mark" hidden>★</div>
        <div id="_flag" hidden>🏁</div>
        <div id="qa"></div>
        <div id="ankimon-portal"></div>
        """
        
        # Bottom HTML (simplified version of Anki's _bottomHTML)
        bottom_html = """
        <center id="outer">
            <table id="innertable" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                    <td align="start" valign="top" class="stat">
                        <button onclick="pycmd('edit');">Edit</button>
                    </td>
                    <td align="center" valign="top" id="middle">
                        <!-- Answer buttons will go here -->
                    </td>
                    <td align="end" valign="top" class="stat">
                        <button onclick="pycmd('more');">More</button>
                        <span id="time" class="stattxt"></span>
                    </td>
                </tr>
            </table>
        </center>
        <div id="button-place"></div>
        """
        
        # Load HTML with CSS
        self.web.stdHtml(
            main_html, 
            css=["css/reviewer.css"], 
            js=["js/reviewer.js"]
        )
        
        self.bottom.web.stdHtml(
            bottom_html,
            css=["css/toolbar-bottom.css", "css/reviewer-bottom.css"],
            js=["js/reviewer-bottom.js"]
        )
        
        # Set up bridge commands
        self.web.set_bridge_command(self._linkHandler, self)
        self.bottom.web.set_bridge_command(self._linkHandler, self)

    def show(self):
        """Start the review session"""
        print("EnhancedMockReviewer: Starting review session")
        if self.main_win:
            self.main_win.answer_btn.setEnabled(True)
            for btn in self.main_win.ease_btns:
                btn.setEnabled(True)
        
        # Get first card
        self.nextCard()
        
        # Trigger GUI hooks
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            hook_obj = getattr(hooks, 'reviewer_did_show_question', None)
            if hook_obj:
                for hook_func in hook_obj.hooks:
                    try:
                        hook_func(self.card)
                    except Exception as e:
                        print(f"Hook error: {e}")

    def nextCard(self):
        """Get and display the next card"""
        self.current_card_index += 1
        
        if self.current_card_index < len(self.card_queue):
            self.card = self.card_queue[self.current_card_index]
            print(f"EnhancedMockReviewer: Showing card {self.card.id}: {self.card.question()}")
            
            self._showQuestion()
        else:
            print("EnhancedMockReviewer: No more cards to review")
            self.card = None
            self._reviewFinished()

    def _reviewFinished(self):
        """Called when the review queue is empty."""
        self.web.eval("document.getElementById('qa').innerHTML = '<h1>Finished!</h1>';")
        self.bottom.web.eval("document.getElementById('middle').innerHTML = '';")
        if self.main_win:
            self.main_win.answer_btn.setEnabled(False)
            for btn in self.main_win.ease_btns:
                btn.setEnabled(False)

    def _showQuestion(self):
        """Display the question side of the current card"""
        if not self.card:
            return
            
        self.state = "question"
        question_html = f"""
        <div class="card-content">
            <h2>Question:</h2>
            <div class="question">{self.card.question()}</div>
        </div>
        """
        
        # Update main webview
        js_code = f"""
        document.getElementById('qa').innerHTML = `{question_html}`;
        """
        self.web.eval(js_code)
        
        # Show answer button
        self._showAnswerButton()
        
        # Trigger hooks
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            hook_obj = getattr(hooks, 'reviewer_did_show_question', None)
            if hook_obj:
                for hook_func in hook_obj.hooks:
                    try:
                        hook_func(self.card)
                        print(f"Triggered reviewer_did_show_question hook")
                    except Exception as e:
                        print(f"Hook error: {e}")

    def _showAnswer(self):
        """Display the answer side of the current card"""
        if not self.card:
            return
            
        self.state = "answer"
        answer_html = f"""
        <div class="card-content">
            <h2>Question:</h2>
            <div class="question">{self.card.question()}</div>
            <h2>Answer:</h2>
            <div class="answer">{self.card.answer()}</div>
        </div>
        """
        
        # Update main webview
        js_code = f"""
        document.getElementById('qa').innerHTML = `{answer_html}`;
        """
        self.web.eval(js_code)
        
        # Show ease buttons
        self._showEaseButtons()
        
        # Trigger hooks
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            hook_obj = getattr(hooks, 'reviewer_did_show_answer', None)
            if hook_obj:
                for hook_func in hook_obj.hooks:
                    try:
                        hook_func(self.card)
                        print(f"Triggered reviewer_did_show_answer hook")
                    except Exception as e:
                        print(f"Hook error: {e}")

    def _showAnswerButton(self):
        """Show the 'Show Answer' button"""
        button_html = """
        <button onclick="pycmd('ans');" id="ansbut">Show Answer</button>
        """
        
        js_code = f"""
        document.getElementById('middle').innerHTML = `{button_html}`;
        """
        self.bottom.web.eval(js_code)

    def _showEaseButtons(self):
        """Show the ease rating buttons (Again, Hard, Good, Easy)"""
        buttons_html = """
        <button onclick="pycmd('ease1');" data-ease="1">Again</button>
        <button onclick="pycmd('ease2');" data-ease="2">Hard</button>
        <button onclick="pycmd('ease3');" data-ease="3">Good</button>
        <button onclick="pycmd('ease4');" data-ease="4">Easy</button>
        """
        
        js_code = f"""
        document.getElementById('middle').innerHTML = `{buttons_html}`;
        """
        self.bottom.web.eval(js_code)

    def _answerCard(self, ease):
        """Handle answering a card with the given ease rating"""
        if not self.card:
            return

        print(f"EnhancedMockReviewer: Answering card {self.card.id} with ease {ease}")
        
        # Trigger will_answer_card hook
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            hook_obj = getattr(hooks, 'reviewer_will_answer_card', None)
            if hook_obj:
                for hook_func in hook_obj.hooks:
                    try:
                        hook_func((True, ease), self, self.card)
                    except Exception as e:
                        print(f"Hook error: {e}")
        
        # Store previous card
        self.previous_card = self.card
        
        # Trigger did_answer_card hook (this is where the HUD gets updated!)
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            hook_obj = getattr(hooks, 'reviewer_did_answer_card', None)
            if hook_obj:
                for hook_func in hook_obj.hooks:
                    try:
                        hook_func(self, self.card, ease)
                        print(f"Triggered reviewer_did_answer_card hook - HUD should update!")
                    except Exception as e:
                        print(f"Hook error: {e}")
        
        # Move to next card after a short delay
        QTimer.singleShot(1000, self.nextCard)

    def _linkHandler(self, url):
        """Handle pycmd commands from the webview"""
        print(f"EnhancedMockReviewer: Received pycmd: {url}")
        
        if url == "ans":
            self._showAnswer()
        elif url.startswith("ease"):
            try:
                ease = int(url[4:])  # Extract ease number from "easeX"
                self._answerCard(ease)
            except ValueError:
                print(f"Invalid ease command: {url}")
        elif url == "edit":
            print("Edit command received (mock)")
        elif url == "more":
            print("More command received (mock)")
        else:
            print(f"Unknown command: {url}")

    def revHtml(self):
        """Get the main reviewer HTML template"""
        return """
        <div id="_mark" hidden>★</div>
        <div id="_flag" hidden>🏁</div>
        <div id="qa"></div>
        <div id="ankimon-portal"></div>
        """

    def _bottomHTML(self):
        """Get the bottom toolbar HTML template"""
        return """
        <center id="outer">
            <table id="innertable" width="100%" cellspacing="0" cellpadding="0">
                <tr>
                    <td align="start" valign="top" class="stat">
                        <button onclick="pycmd('edit');">Edit</button>
                    </td>
                    <td align="center" valign="top" id="middle">
                    </td>
                    <td align="end" valign="top" class="stat">
                        <button onclick="pycmd('more');">More</button>
                    </td>
                </tr>
            </table>
        </center>
        """