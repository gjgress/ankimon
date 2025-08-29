import sys
import json
from typing import Any, Callable
from PyQt6.QtWebEngineWidgets import QWebEngineView
import re # Added for regex parsing of JS bridge calls
import urllib.parse # Added for URL encoding
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
        self._bridge_command_handler: Callable[[str, str], None] | None = None # Updated type hint
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
        self.setHtml(full_html, base_url=self.web_assets_path) # Pass base_url
            
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
        # This pycmd will now call the pybridge function injected by set_bridge_command
        pycmd_script = """
        <script>
        function pycmd(cmd) {
            console.log('pycmd called with:', cmd);
            if (window.pybridge) {
                window.pybridge(cmd);
            } else {
                console.warn("JS: window.pybridge not found. pycmd will not reach Python.");
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
    <style>button {{ cursor: pointer; }}</style>
    {css_links}
    {pycmd_script}
</head>
<body>
    {body_html}
    {js_scripts}
</body>
</html>"""
        
        return full_html

    def setHtml(self, html, base_url: QUrl | None = None): # Added base_url parameter
        """Set HTML content"""
        if base_url:
            self.qwebengine_view.setHtml(html, base_url)
            print(f"EnhancedMockWebview.setHtml: Set HTML with base_url: {base_url.toString()} and length {len(html)}")
        else:
            self.qwebengine_view.setHtml(html)
            print(f"EnhancedMockWebview.setHtml: Set HTML with length {len(html)}")

    def eval(self, javascript):
        """Execute JavaScript in the webview and capture pycmd/anki.call for bridge"""
        print(f"EnhancedMockWebview.eval: Executing JS: {javascript[:100]}...")
            
        # First, attempt to capture pycmd or _anki.call from the JS being evaluated
        # This is a heuristic to simulate the bridge without full QtWebChannel setup.
        try:
            pycmd_match = re.search(r'pycmd\("([^"]+)"\)', javascript)
            if pycmd_match:
                full_arg = pycmd_match.group(1)
                parts = full_arg.split("::", 1)
                method = parts[0]
                arg = parts[1] if len(parts) > 1 else ""
                print(f"EnhancedMockWebview: Simulating pycmd('{full_arg}') -> method='{method}', arg='{arg}'")
                if self._bridge_command_handler:
                    self._bridge_command_handler(method, arg)
            else:
                anki_call_match = re.search(r'_anki\.call\("([^"]+)"(?:,\s*"([^"]*)")?\)', javascript)
                if anki_call_match:
                    method = anki_call_match.group(1)
                    arg = anki_call_match.group(2) if anki_call_match.group(2) is not None else ""
                    print(f"EnhancedMockWebview: Simulating _anki.call('{method}', '{arg}')")
                    if self._bridge_command_handler:
                        self._bridge_command_handler(method, arg)
        except Exception as e:
            print(f"EnhancedMockWebview: Error parsing/simulating JS bridge call: {e}")

        def js_callback(result):
            print(f"JavaScript execution result: {result}")
            
        # Execute JavaScript via QWebEngineView
        self.qwebengine_view.page().runJavaScript(javascript, js_callback)
            
        return True

    def set_bridge_command(self, handler, context=None):
        """Set up bridge command handler for pycmd calls"""
        self._bridge_command_handler = handler
        self._bridge_command_context = context # Store context if needed for the handler
        print(f"EnhancedMockWebview: Bridge command handler set for {self.name}")

        # Inject JavaScript to create a 'pybridge' function callable from HTML
        # This function will call a Python method through QtWebChannel
        # For simplicity in this mock, we'll simulate the call directly from eval.
        # In a full QtWebChannel setup, this would register a Python object to be exposed to JS.
        js_bridge_injection = """
        if (!window.pybridge) {
            window.pybridge = function(arg) {
                // This is where JS in the webview sends commands to Python.
                // In a real Anki setup, this would communicate via QtWebChannel.
                // For this mock, we capture it via eval and simulate the call.
                // The eval() method of the Python mock will detect and handle this.
                console.log("JS: pybridge called with:", arg);
            };
        }
        """
        self.qwebengine_view.page().runJavaScript(js_bridge_injection)

    def inject_js(self, js_content):
        """Inject JavaScript directly into the webview's current frame."""
        print(f"EnhancedMockWebview: Injecting JS (first 100 chars): {js_content[:100]}...")
        self.qwebengine_view.page().runJavaScript(js_content)

    def inject_css(self, css_content):
        """Inject CSS directly into the webview's current frame."""
        print(f"EnhancedMockWebview: Injecting CSS (first 100 chars): {css_content[:100]}...")
        # For CSS injection, we typically add a style tag to the head.
        # This is a common pattern in Anki add-ons.
        self.qwebengine_view.page().runJavaScript(
            f"""
            var style = document.createElement('style');
            style.type = 'text/css';
            style.innerHTML = `{css_content.replace('`', '\\`')}`; // Escape backticks
            document.head.appendChild(style);
            """
        )

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

        # Set up bridge commands after webviews are initialized
        self.web.set_bridge_command(self._on_js_bridge_command, context=self)
        self.bottom.web.set_bridge_command(self._on_js_bridge_command, context=self)

    def _on_js_bridge_command(self, method: str, arg: str):
        """Handle commands from JavaScript via the simulated bridge."""
        print(f"EnhancedMockReviewer: Received JS bridge command: method='{method}', arg='{arg}'")
        # Implement logic based on commands from Ankimon's JS, e.g.:
        if method == "ans": # "Show Answer" button
            self._showAnswer()
        elif method.startswith("ease"):
            try:
                ease = int(method[4:]) # Extract ease number from "easeX"
                self._answerCard(ease)
            except ValueError:
                print(f"Invalid ease command: {method}")
        elif method == "edit":
            print("Edit command received (mock)")
        elif method == "more":
            print("More command received (mock)")
        elif method.startswith("ankimon_button_click"): # Custom Ankimon buttons
            if arg == "defeat":
                print("Ankimon HUD: Defeat button clicked!")
                # You might want to trigger a hook here or simulate game logic
                # For now, let's just show the next card as a placeholder
                self.nextCard()
            elif arg == "catch":
                print("Ankimon HUD: Catch button clicked!")
                # Simulate catch logic
        else:
            print(f"Unknown pycmd command: {method}")


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
        
        # Bridge commands are now set in __init__ after webview creation.

    def show(self):
        """Start the review session"""
        print("EnhancedMockReviewer: Starting review session")
        if self.main_win:
            self.main_win.answer_btn.setEnabled(True)
            for btn in self.main_win.ease_btns:
                btn.setEnabled(True)
        
        # Trigger profile_did_open hook if Ankimon needs it for initialization
        # (This hook is often triggered when Anki's main window is ready)
        if hasattr(sys.modules.get('anki'), 'hooks') and hasattr(sys.modules['anki'].hooks, 'profile_did_open'):
            sys.modules['anki'].hooks.profile_did_open.run()
        
        # Start review via scheduler
        if self.mw and self.mw.col and self.mw.col.sched:
            self.mw.col.sched.startReview() # This should reset current_card_index
        
        # Get and display first card
        self.nextCard()
        
        # No need to trigger reviewer_did_show_question hook here; it's done in _showQuestion

    def nextCard(self):
        """Get and display the next card from the scheduler"""
        if not self.mw or not self.mw.col or not self.mw.col.sched:
            print("EnhancedMockReviewer: Mock Anki components not fully initialized. Cannot get next card.")
            return

        self.card = self.mw.col.sched.getCard() # Get card from scheduler

        if not self.card:
            print("EnhancedMockReviewer: No more cards to review from scheduler.")
            self.card = None
            self._reviewFinished()
        else:
            print(f"EnhancedMockReviewer: Retrieved card {self.card.id}: {self.card.question()}")
            self._showQuestion()

    def _reviewFinished(self):
        """Called when the review queue is empty."""
        self.web.eval("document.getElementById('qa').innerHTML = '<h1>Finished!</h1>';")
        self.bottom.web.eval("document.getElementById('middle').innerHTML = '';")
        if self.main_win:
            self.main_win.answer_btn.setEnabled(False)
            for btn in self.main_win.ease_btns:
                btn.setEnabled(False)

    def _showQuestion(self):
        """Display the question side of the current card with Ankimon HUD"""
        if not self.card:
            return
            
        self.state = "question"
        
        # Get Ankimon addon directory for file paths
        addon_dir = Path(self.mw.addonManager.addon_dir) if self.mw.addonManager else Path()
        encoded_addon_dir = urllib.parse.quote(str(addon_dir), safe='/:')

        # Basic card content
        card_html = f"""
        <div id="qa_content" style="font-size: 20px; padding: 20px; border: 1px solid #eee; margin: 20px; background: #f9f9f9;">
            <h2>Question:</h2>
            <div class="question">{self.card.question()}</div>
        </div>
        """

        # Construct Ankimon's HUD HTML
        # This is a placeholder; actual Ankimon HUD structure would be more complex.
        # It's assumed Ankimon's web assets are in src/Ankimon/user_files/web
        ankimon_hud_html = f"""
        <div id="ankimon-portal">
            <div id="ankimon-hud" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; z-index: 1000;">
                <h3>Ankimon HUD (Mock)</h3>
                <p>HP: [Mock HP: 100/100]</p>
                <p>XP: [Mock XP: 50/100]</p>
                <img src="file://{encoded_addon_dir}/user_files/web/sprites/pokemon/1.gif" alt="Pokemon" style="width: 50px; height: 50px; border: 1px solid white;">
                <br>
                <button onclick="pycmd('ankimon_button_click::defeat')" style="margin-top: 5px; padding: 5px 10px; cursor: pointer;">Defeat</button>
                <button onclick="pycmd('ankimon_button_click::catch')" style="margin-top: 5px; padding: 5px 10px; cursor: pointer;">Catch</button>
            </div>
        </div>
        """
        
        # Combine all HTML
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ankimon Reviewer (Mock)</title>
    <!-- Link Ankimon's CSS -->
    <link rel="stylesheet" type="text/css" href="file://{encoded_addon_dir}/user_files/web/styles.css">
    <style>
        body {{ font-family: sans-serif; text-align: center; margin: 0; padding: 0; }}
        button {{ cursor: pointer; }}
        #qa {{ display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; }}
        #ankimon-hud {{ border: 2px solid lightgray; }}
    </style>
</head>
<body>
    <div id="qa">
        {card_html}
        {ankimon_hud_html}
    </div>
    <!-- Ankimon's main JS scripts would typically be loaded here -->
    <script src="file://{encoded_addon_dir}/user_files/web/player.js"></script>
    <script src="file://{encoded_addon_dir}/user_files/web/poketeam_front.js"></script>
</body>
</html>"""
            
        self.web.setHtml(full_html, base_url=QUrl.fromLocalFile(str(addon_dir) + "/user_files/web/"))
            
        # Show answer button
        self._showAnswerButton()
            
        # Trigger hooks
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            # anki.hooks also exists. Ankimon may register to anki.hooks.reviewer_did_show_question
            anki_hooks = sys.modules.get('anki').hooks if hasattr(sys.modules.get('anki'), 'hooks') else None

            if hasattr(hooks, 'reviewer_did_show_question') and hooks.reviewer_did_show_question:
                hooks.reviewer_did_show_question.run(self.card)
                print(f"Triggered aqt.gui_hooks.reviewer_did_show_question hook")
            if anki_hooks and hasattr(anki_hooks, 'reviewer_did_show_question') and anki_hooks.reviewer_did_show_question:
                anki_hooks.reviewer_did_show_question.run(self.card)
                print(f"Triggered anki.hooks.reviewer_did_show_question hook")

    def _showAnswer(self):
        """Display the answer side of the current card with Ankimon HUD"""
        if not self.card:
            return
            
        self.state = "answer"

        # Get Ankimon addon directory for file paths
        addon_dir = Path(self.mw.addonManager.addon_dir) if self.mw.addonManager else Path()
        encoded_addon_dir = urllib.parse.quote(str(addon_dir), safe='/:')

        # Basic card content including answer
        card_html = f"""
        <div id="qa_content" style="font-size: 20px; padding: 20px; border: 1px solid #eee; margin: 20px; background: #f9f9f9;">
            <h2>Question:</h2>
            <div class="question">{self.card.question()}</div>
            <h2>Answer:</h2>
            <div class="answer">{self.card.answer()}</div>
        </div>
        """

        # Construct Ankimon's HUD HTML (can be the same as question side or updated)
        ankimon_hud_html = f"""
        <div id="ankimon-portal">
            <div id="ankimon-hud" style="position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.7); color: white; padding: 10px; border-radius: 5px; z-index: 1000;">
                <h3>Ankimon HUD (Mock Answer)</h3>
                <p>HP: [Mock HP: 90/100]</p>
                <p>XP: [Mock XP: 55/100]</p>
                <img src="file://{encoded_addon_dir}/user_files/web/sprites/pokemon/1.gif" alt="Pokemon" style="width: 50px; height: 50px; border: 1px solid white;">
                <br>
                <button onclick="pycmd('ankimon_button_click::defeat')" style="margin-top: 5px; padding: 5px 10px; cursor: pointer;">Defeat</button>
                <button onclick="pycmd('ankimon_button_click::catch')" style="margin-top: 5px; padding: 5px 10px; cursor: pointer;">Catch</button>
            </div>
        </div>
        """

        # Combine all HTML
        full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ankimon Reviewer (Mock)</title>
    <!-- Link Ankimon's CSS -->
    <link rel="stylesheet" type="text/css" href="file://{encoded_addon_dir}/user_files/web/styles.css">
    <style>
        body {{ font-family: sans-serif; text-align: center; margin: 0; padding: 0; }}
        button {{ cursor: pointer; }}
        #qa {{ display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 400px; }}
        #ankimon-hud {{ border: 2px solid lightgray; }}
    </style>
</head>
<body>
    <div id="qa">
        {card_html}
        {ankimon_hud_html}
    </div>
    <!-- Ankimon's main JS scripts would typically be loaded here -->
    <script src="file://{encoded_addon_dir}/user_files/web/player.js"></script>
    <script src="file://{encoded_addon_dir}/user_files/web/poketeam_front.js"></script>
</body>
</html>"""
            
        self.web.setHtml(full_html, base_url=QUrl.fromLocalFile(str(addon_dir) + "/user_files/web/"))
            
        # Show ease buttons
        self._showEaseButtons()
            
        # Trigger hooks
        if hasattr(sys.modules.get('aqt'), 'gui_hooks'):
            hooks = sys.modules['aqt'].gui_hooks
            anki_hooks = sys.modules.get('anki').hooks if hasattr(sys.modules.get('anki'), 'hooks') else None

            if hasattr(hooks, 'reviewer_did_show_answer') and hooks.reviewer_did_show_answer:
                hooks.reviewer_did_show_answer.run(self.card)
                print(f"Triggered aqt.gui_hooks.reviewer_did_show_answer hook")
            if anki_hooks and hasattr(anki_hooks, 'reviewer_did_show_answer') and anki_hooks.reviewer_did_show_answer:
                anki_hooks.reviewer_did_show_answer.run(self.card)
                print(f"Triggered anki.hooks.reviewer_did_show_answer hook")

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

