import json
from typing import Any, Callable
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl, pyqtSlot
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from pathlib import Path
from mock_anki.collection import MockCard, MockScheduler

class MockWebview:
    """Mock for aqt.webview.AnkiWebView"""
    
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
        
        # No explicit bridge setup needed, pycmd is in HTML
        
        print(f"MockWebview '{name}' initialized with assets path: {self.web_assets_path}")
    
    def stdHtml(self, html, css=None, js=None, context=None):
        """Load HTML with CSS and JS assets similar to Anki's stdHtml"""
        css = css or []
        js = js or []
        
        # Build full HTML with assets
        full_html = self._build_full_html(html, css, js)
        self.setHtml(full_html)
        
        print(f"MockWebview.stdHtml called with HTML length: {len(html)}")
        return self
    
    def _build_full_html(self, body_html, css_files, js_files):
        """Build complete HTML document with CSS and JS"""
        # CSS links
        css_links = ""
        for css_file in css_files:
            css_path = Path(self.ankimon_root) / "src" / "Ankimon" / "aqt" / "data" / "web" / css_file
            if css_path.exists():
                css_links += f'<link rel="stylesheet" href="file://{css_path}">\n'
            else:
                print(f"Warning: CSS file not found: {css_path}")
        
        # JS scripts
        js_scripts = ""
        for js_file in js_files:
            js_path = Path(self.ankimon_root) / "src" / "Ankimon" / "aqt" / "data" / "web" / js_file
            if js_path.exists():
                js_scripts += f'<script src="file://{js_path}"></script>\n'
            else:
                print(f"Warning: JS file not found: {js_path}")
        
        # Complete HTML document
        full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Ankimon Reviewer</title>
    {css_links}
</head>
<body class="ankidesktop">
    {body_html}
    {js_scripts}
    <script>
        window.pycmd = function(cmd) {{
            console.log('pycmd called with:', cmd);
            if (window.bridge) {{
                window.bridge.onMessage(cmd);
            }}
        }};
        window.bridgeCommand = window.pycmd; // Alias for compatibility

        // Set up bridge communication
        window.bridge = {{
            onMessage: function(cmd) {{
                console.log('Bridge received:', cmd);
                // Send to Python via Qt
                if (window.qt && window.qt.webChannelTransport) {{
                    // WebChannel approach
                }} else {{
                    // Fallback - we'll handle this in Python
                    document.title = 'pycmd:' + cmd;
                }}
            }}
        }};
        
        console.log('Ankimon reviewer webview initialized');
    </script>
</body>
</html>
        """
        return full_html
    
    def setHtml(self, html, base_url=None):
        """Set HTML content"""
        if base_url is None:
            base_url = self.web_assets_path
        self.qwebengine_view.setHtml(html, base_url)
        print(f"MockWebview.setHtml called with {len(html)} characters")
    
    def eval(self, js_code):
        """Execute JavaScript code"""
        print(f"MockWebview.eval: {js_code[:100]}...")
        self.qwebengine_view.page().runJavaScript(js_code)
    
    def set_bridge_command(self, handler, context=None):
        """Set the Python handler for pycmd calls"""
        self._bridge_command_handler = handler
        print(f"Bridge command handler set: {handler.__name__ if handler else None}")
        
        # Monitor title changes for pycmd communication
        self.qwebengine_view.titleChanged.connect(self._handle_title_change)
    
    def _handle_title_change(self, title):
        """Handle pycmd communication via title changes"""
        if title.startswith('pycmd:') and self._bridge_command_handler:
            cmd = title[6:]  # Remove 'pycmd:' prefix
            print(f"Handling pycmd: {cmd}")
            self._bridge_command_handler(cmd)

class MockReviewer:
    """High-fidelity mock of aqt.reviewer.Reviewer"""
    
    def __init__(self, mw):
        self.mw = mw
        self.card = None
        self.previous_card = None
        self.state = "initial"  # "question", "answer", "transition"
        self._answeredIds = []
        
        # Create web views
        self.web = MockWebview(mw, Path(__file__).parent.parent.parent, "reviewer", None)
        self.bottom = type('Bottom', (), {})()  # Simple namespace
        self.bottom.web = MockWebview(mw, Path(__file__).parent.parent.parent, "reviewer-bottom", None)
        
        # Set up bridge handlers
        self.web.set_bridge_command(self._linkHandler, self)
        self.bottom.web.set_bridge_command(self._linkHandler, self)
        
        print("MockReviewer initialized")
    
    def show(self):
        """Show the reviewer and start review session"""
        print("MockReviewer.show() called")
        self.state = "transition"
        
        # Initialize web views with HTML
        self._initWeb()
        
        # Get first card and show question
        self.nextCard()
    
    def _initWeb(self):
        """Initialize web views with base HTML, CSS, and JS"""
        print("MockReviewer._initWeb() called")
        
        # Main reviewer HTML
        main_html = self.revHtml()
        self.web.stdHtml(
            main_html,
            css=["css/reviewer.css", "css/reviewer-bottom.css"],
            js=["js/reviewer.js", "js/reviewer-bottom.js"],
            context=self
        )
        
        # Bottom bar HTML  
        bottom_html = self._bottomHTML()
        self.bottom.web.stdHtml(
            bottom_html,
            css=["css/toolbar-bottom.css", "css/reviewer-bottom.css"],
            js=["js/vendor/jquery.min.js", "js/reviewer-bottom.js"],
            context=self
        )
    
    def revHtml(self):
        """Generate main reviewer HTML similar to Anki's revHtml()"""
        # Get any extra HTML from collection config
        extra = self.mw.col.get_config("reviewExtra") or ""
        
        # Add Ankimon HUD container to extra
        ankimon_hud = '<div id="ankimon-hud"></div>'
        extra = ankimon_hud + extra
        
        html = f"""
<div id="_mark" hidden>★</div>
<div id="_flag" hidden>🚩</div>
<div id="qa"></div>
{extra}
        """
        return html
    
    def _bottomHTML(self):
        """Generate bottom toolbar HTML similar to Anki's _bottomHTML()"""
        time_taken = self.card.time_taken() // 1000 if self.card else 0
        
        html = f"""
<center id=outer>
<table id=innertable width=100% cellspacing=0 cellpadding=0>
<tr>
<td align=start valign=top class=stat>
<button title="Edit (E)" onclick="pycmd('edit');">Edit</button></td>
<td align=center valign=top id=middle>
</td>
<td align=end valign=top class=stat>
<button title="More (M)" onclick="pycmd('more');">
More ▼
<span id=time class=stattxt></span>
</button>
</td>
</tr>
</table>
</center>
<script>
time = {time_taken};
timerStopped = false;
</script>
        """
        return html
    
    def nextCard(self):
        """Get and display the next card"""
        print("MockReviewer.nextCard() called")
        
        # Get next card from scheduler
        if hasattr(self.mw.col, 'sched') and self.mw.col.sched:
            next_card = self.mw.col.sched.get_next_card()
            if next_card:
                self.card = next_card
                self._showQuestion()
            else:
                self._noMoreCards()
        else:
            print("Warning: No scheduler available")
    
    def _showQuestion(self):
        """Display the question side of the current card"""
        if not self.card:
            return
        
        print(f"MockReviewer._showQuestion() for card {self.card.id}")
        self.state = "question"
        
        # Get question HTML
        question_html = self.card.question()
        
        # Execute JavaScript to show question
        js_code = f"""
if (typeof showQuestion === 'function') {{
    showQuestion(`{self._escape_js(question_html)}`, 0);
}} else {{
    if (document.getElementById('qa')) {{
        document.getElementById('qa').innerHTML = `{self._escape_js(question_html)}`;
    }}
}}
        """
        self.web.eval(js_code)
        
        # Show the "Show Answer" button
        self._showAnswerButton()
        
        # Inject Ankimon HUD if available
        self._injectAnkimonHUD()
    
    def _showAnswer(self):
        """Display the answer side of the current card"""
        if not self.card:
            return
        
        print(f"MockReviewer._showAnswer() for card {self.card.id}")
        self.state = "answer"
        
        # Get answer HTML
        answer_html = self.card.answer()
        
        # Execute JavaScript to show answer
        js_code = f"""
if (typeof showAnswer === 'function') {{
    showAnswer(`{self._escape_js(answer_html)}`, true);
}} else {{
    if (document.getElementById('qa')) {{
        document.getElementById('qa').innerHTML = `{self._escape_js(answer_html)}`;
    }}
}}
        """
        self.web.eval(js_code)
        
        # Show ease buttons
        self._showEaseButtons()
    
    def _showAnswerButton(self):
        """Show the 'Show Answer' button"""
        button_html = '<button id="ansbut" onclick="pycmd(\'ans\');">Show Answer</button>'
        js_code = f"if (document.getElementById('middle')) {{ document.getElementById('middle').innerHTML = `{button_html}`; }}"
        self.bottom.web.eval(js_code)
    
    def _showEaseButtons(self):
        """Show ease rating buttons (Again/Hard/Good/Easy)"""
        if not self.card or not hasattr(self.mw.col, 'sched'):
            return
        
        # Get number of buttons from scheduler
        button_count = self.mw.col.sched.answerButtons(self.card)
        
        # Generate buttons based on count
        if button_count == 2:
            buttons = [
                (1, "Again"),
                (2, "Good")
            ]
        elif button_count == 3:
            buttons = [
                (1, "Again"),
                (2, "Good"), 
                (3, "Easy")
            ]
        else:  # 4 buttons
            buttons = [
                (1, "Again"),
                (2, "Hard"),
                (3, "Good"),
                (4, "Easy")
            ]
        
        # Generate button HTML
        button_html = ""
        for ease, label in buttons:
            button_html += f'<button data-ease="{ease}" onclick="pycmd(\'ease{ease}\');">{label}</button>'
        
        # Insert buttons
        js_code = f"if (document.getElementById('middle')) {{ document.getElementById('middle').innerHTML = `{button_html}`; }}"
        self.bottom.web.eval(js_code)
    
    def _answerCard(self, ease):
        """Handle answering a card with the given ease"""
        if not self.card:
            return
        
        print(f"MockReviewer._answerCard() ease={ease} for card {self.card.id}")
        
        # Add to answered cards list
        self._answeredIds.append(self.card.id)
        self.previous_card = self.card
        
        # Update scheduler
        if hasattr(self.mw.col, 'sched') and self.mw.col.sched:
            self.mw.col.sched.answerCard(self.card, ease)
        
        # Move to next card
        self.nextCard()
    
    def _noMoreCards(self):
        """Handle case when no more cards are available"""
        print("MockReviewer._noMoreCards() - Review session complete")
        self.card = None
        self.state = "complete"
        
        # Show completion message
        completion_html = "<div>Review Complete!<br>No more cards to review.</div>"
        js_code = f"if (document.getElementById('qa')) {{ document.getElementById('qa').innerHTML = `{completion_html}`; }}"
        self.web.eval(js_code)
        
        # Clear bottom buttons
        js_code = "document.getElementById('middle').innerHTML = '';"
        self.bottom.web.eval(js_code)
    
    def _linkHandler(self, url):
        """Handle pycmd calls from JavaScript"""
        print(f"MockReviewer._linkHandler received: {url}")
        
        if url == "ans":
            # Show Answer button clicked
            self._showAnswer()
        elif url.startswith("ease"):
            # Ease button clicked
            try:
                ease = int(url[4:])  # Extract number from "ease1", "ease2", etc.
                self._answerCard(ease)
            except (ValueError, IndexError):
                print(f"Invalid ease command: {url}")
        elif url == "edit":
            print("Edit button clicked (not implemented)")
        elif url == "more":
            print("More button clicked (not implemented)")
        else:
            print(f"Unknown pycmd: {url}")
    
    def _injectAnkimonHUD(self):
        """Inject Ankimon HUD CSS and elements if available"""
        try:
            # Try to import Ankimon's HUD creation functions
            # This would be dynamically loaded based on the actual add-on
            
            # For now, inject a basic HUD structure
            hud_css = """
            <style>
            #ankimon-hud {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                pointer-events: none;
                z-index: 9999;
            }
            #ankimon-hud > * {
                pointer-events: auto;
            }
            </style>
            """
            
            js_code = f"""
            // Inject Ankimon HUD CSS
            var style = document.createElement('style');
            style.textContent = `{hud_css.replace('`', '\\`')}`;
            document.head.appendChild(style);
            
            // Create HUD container if it doesn't exist
            if (!document.getElementById('ankimon-hud')) {{
                var hud = document.createElement('div');
                hud.id = 'ankimon-hud';
                document.body.appendChild(hud);
                console.log('Ankimon HUD container created');
            }}
            """
            
            self.web.eval(js_code)
            print("Ankimon HUD injected")
            
        except Exception as e:
            print(f"Failed to inject Ankimon HUD: {e}")
    
    def _escape_js(self, text):
        """Escape text for safe insertion into JavaScript"""
        if not text:
            return ""
        # Basic escaping - in production you'd want more robust escaping
        return text.replace('`', '\\`').replace('\\', '\\\\').replace('\n', '\\n').replace('\r', '\\r')
