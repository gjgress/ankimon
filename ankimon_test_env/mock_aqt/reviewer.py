import json
from typing import Any, Callable
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from pathlib import Path
from mock_anki.collection import MockCard, MockQueuedCards, MockQueuedCard, MockSchedulingStates, MockCurrentState, MockNote, MockProgress, MockTimer, MockV3CardInfo, MockScheduler # Updated import

class MockWebview:
    def __init__(self, mw, ankimon_root, name="", parent=None):
        self.mw = mw
        self.name = name
        self._bridge_command_handler: Callable[[str], None] | None = None
        self.allow_drops = False
        
        # The actual QWebEngineView instance
        self.qwebengine_view = QWebEngineView(parent)
        self.ankimon_root = ankimon_root
        self.web_assets_path = QUrl.fromLocalFile(str(Path(self.ankimon_root) / "src" / "Ankimon" / "aqt" / "data" / "web") + "/")
        self.qwebengine_view.setHtml("<h1>Mock Webview: Initializing...</h1>", self.web_assets_path)
        self.qwebengine_view.hide()

    def stdHtml(self, html: str, css: list[str], js: list[str], context: Any):
        print(f"MockWebview ({self.name}): stdHtml called.")
        print(f"  HTML (truncated): {html[:200]}...")
        print(f"  CSS: {css}")
        print(f"  JS: {js}")
        print(f"  Context: {context.__class__.__name__}")
        self._current_html = html
        self._current_css = css
        self._current_js = js
        self._current_context = context
        
        # Set HTML on the actual QWebEngineView
        self.qwebengine_view.setHtml(html, self.web_assets_path)

    def set_bridge_command(self, handler: Callable[[str], None], context: Any):
        print(f"MockWebview ({self.name}): set_bridge_command called with handler {handler.__name__} and context {context.__class__.__name__}")
        self._bridge_command_handler = handler
        # Connect the QWebEngineView's bridge to our handler
        self.qwebengine_view.page().setHtml(self._current_html, self.web_assets_path) # Re-set HTML to ensure bridge is active
        self.qwebengine_view.page().javaScriptMessageReceived.connect(self._js_message_received)

    def _js_message_received(self, message: str):
        # This method will be called when JavaScript sends a message via pycmd
        print(f"MockWebview ({self.name}): JavaScript message received: {message}")
        if self._bridge_command_handler:
            self._bridge_command_handler(message)

    def eval(self, js_code: str):
        print(f"MockWebview ({self.name}): eval called with JS: {js_code[:200]}...")
        self.qwebengine_view.page().runJavaScript(js_code)

    def evalWithCallback(self, js_code: str, callback: Callable[[Any], None]):
        print(f"MockWebview ({self.name}): evalWithCallback called with JS: {js_code[:200]}... and callback {callback.__name__}")
        self.qwebengine_view.page().runJavaScript(js_code, callback)

    def show(self):
        self.qwebengine_view.show()

    def hide(self):
        self.qwebengine_view.hide()

class ReviewerBottomBar:
    def __init__(self, reviewer):
        self.reviewer = reviewer

class Reviewer:
    def __init__(self, mw) -> None:
        self.mw = mw
        # Pass the parent (mw.form) to MockWebview for proper QWebEngineView parenting
        self.web = MockWebview(self.mw, "main", parent=self.mw.form)
        self.bottom = ReviewerBottomBar(self) # This will be replaced by a proper BottomBar mock later
        self.card: MockCard | None = None
        self.state: str | None = None
        self._answeredIds: list = []
        self._v3 = None # Placeholder for V3CardInfo

    def show(self) -> None:
        print("Reviewer: show() called")
        self.mw.setStateShortcuts([]) # Placeholder
        self.web.set_bridge_command(self._linkHandler, self)
        # Assuming bottom.web exists and has set_bridge_command
        self.mw.bottomWeb.set_bridge_command(self._linkHandler, ReviewerBottomBar(self))
        self.nextCard()

    def nextCard(self) -> None:
        print("Reviewer: nextCard() called")
        # Simulate getting a card from the scheduler
        self.card = self.mw.col.sched.get_next_card()
        if self.card:
            self._v3 = MockV3CardInfo(self.card) # Initialize _v3
            self._initWeb()
            self._showQuestion()
        else:
            print("Reviewer: No more cards from scheduler.")
            self.web.qwebengine_view.setHtml("<h1>No more cards to review!</h1>")

    def _initWeb(self) -> None:
        print("Reviewer: _initWeb() called")
        self.web.stdHtml(
            self.revHtml(self.card), # Updated call
            css=["css/reviewer.css"],
            js=["js/mathjax.js", "js/vendor/mathjax/tex-chtml-full.js", "js/reviewer.js"],
            context=self,
        )
        self.mw.bottomWeb.stdHtml(
            self._bottomHTML(),
            css=["css/toolbar-bottom.css", "css/reviewer-bottom.css"],
            js=["js/vendor/jquery.min.js", "js/reviewer-bottom.js"],
            context=ReviewerBottomBar(self),
        )

    def revHtml(self, card: MockCard) -> str:
        print("Reviewer: revHtml() called")
        # Basic HTML structure, similar to real Anki
        # Simulate rendering card fields
        question_html = card.question()
        answer_html = card.answer()

        return """
<div id="_mark" hidden>&#x2605;</div>
<div id="_flag" hidden>&#x2691;</div>
<div id="qa">
    <div id="question">{question_html}</div>
    <div id="answer" style="display: none;">{answer_html}</div>
</div>
<script>
function pycmd(cmd) {
    qt.webChannelTransport.send(cmd);
}
function showQuestion() {
    document.getElementById('question').style.display = 'block';
    document.getElementById('answer').style.display = 'none';
}
function showAnswer() {
    document.getElementById('question').style.display = 'none';
    document.getElementById('answer').style.display = 'block';
}
</script>
""".format(question_html=question_html, answer_html=answer_html)

    def _bottomHTML(self) -> str:
        print("Reviewer: _bottomHTML() called")
        # Basic HTML for the bottom bar
        return """
<center id=outer>
<table id=innertable width=100%% cellspacing=0 cellpadding=0>
<tr>
<td align=start valign=top class=stat>
<button title="Edit" onclick="pycmd('edit');">Edit</button></td>
<td align=center valign=top id=middle>
</td>
<td align=end valign=top class=stat>
<button title="More" onclick="pycmd('more');">
More
<span id=time class=stattxt></span>
</button>
</td>
</tr>
</table>
</center>
<script>
function pycmd(cmd) {
    qt.webChannelTransport.send(cmd);
}
function showQuestion(html, maxTime) {
    document.getElementById('middle').innerHTML = html;
}
function showAnswer(html, stopTimerOnAnswer) {
    document.getElementById('middle').innerHTML = html;
}
</script>
"""

    def _showQuestion(self) -> None:
        print("Reviewer: _showQuestion() called")
        self.state = "question"
        q = self.card.question()
        # Simulate card text preparation and hooks
        q = self._mungeQA(q)
        # In real Anki, this would involve gui_hooks.card_will_show
        bodyclass = "card-ord-0" # Placeholder
        a = self.card.answer() # Get answer for JS eval
        self.web.eval(f"_showQuestion({json.dumps(q)}, {json.dumps(a)}, '{bodyclass}');")
        self._showAnswerButton()

    def _showAnswer(self) -> None:
        print("Reviewer: _showAnswer() called")
        self.state = "answer"
        a = self.card.answer()
        a = self._mungeQA(a)
        self.web.eval(f"_showAnswer({json.dumps(a)});")
        self._showEaseButtons()

    def _mungeQA(self, buf: str) -> str:
        # Simplified version of the real _mungeQA
        # In real Anki, this handles type-in-the-answer fields and media
        return buf

    def _showAnswerButton(self) -> None:
        print("Reviewer: _showAnswerButton() called")
        middle = """
<button title="Show Answer" id="ansbut" onclick='pycmd("ans");'>Show Answer<span class=stattxt></span></button>
"""
        self.mw.bottomWeb.eval(f"showQuestion({json.dumps(middle)}, 0);")

    def _showEaseButtons(self) -> None:
        print("Reviewer: _showEaseButtons() called")
        middle = self._answerButtons()
        conf = {"stopTimerOnAnswer": False} # Placeholder for deck config
        self.mw.bottomWeb.eval(f"showAnswer({json.dumps(middle)}, {json.dumps(conf['stopTimerOnAnswer'])});")

    def _answerButtons(self) -> str:
        print("Reviewer: _answerButtons() called")
        # Simplified answer buttons
        return """
<center><table cellpadding=0 cellspacing=0><tr>
<td align=center><button data-ease="1" onclick='pycmd("ease1");'>Again</button></td>
<td align=center><button data-ease="2" onclick='pycmd("ease2");'>Hard</button></td>
<td align=center><button data-ease="3" onclick='pycmd("ease3");'>Good</button></td>
<td align=center><button data-ease="4" onclick='pycmd("ease4");'>Easy</button></td>
</tr></table></center>
"""

    def _linkHandler(self, url: str) -> None:
        print(f"Reviewer: _linkHandler() called with URL: {url}")
        if url == "ans":
            print("  -> Handling 'ans' (Show Answer)")
            self._showAnswer()
        elif url.startswith("ease"):
            ease = int(url[4:])
            print(f"  -> Handling 'ease{ease}' (Answer Card with ease {ease})")
            self._answerCard(ease)
        elif url == "edit":
            print("  -> Handling 'edit' (Edit Current)")
            # self.mw.onEditCurrent() # Placeholder
        elif url == "more":
            print("  -> Handling 'more' (Show Context Menu)")
            # self.showContextMenu() # Placeholder
        elif url.startswith("play:"):
            print(f"  -> Handling 'play:' (Play Audio: {url[5:]})")
            # play_clicked_audio(url, self.card) # Placeholder
        elif url == "statesMutated":
            print("  -> Handling 'statesMutated'")
            # self._states_mutated = True # Placeholder
        else:
            print(f"  -> Unrecognized Anki link: {url}")

    def _answerCard(self, ease: int) -> None:
        print(f"Reviewer: _answerCard() called with ease: {ease}")
        # Simulate answering the card and moving to the next
        self.mw.col.sched.answerCard(self.card, ease) # Call the scheduler's answerCard
        self._answeredIds.append(self.card.id)
        self.nextCard()