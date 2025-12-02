# -*- coding: utf-8 -*-
"""
Reviewer show question/answer handlers for Ankimon.

These functions handle events when questions and answers are shown in the reviewer.
"""

from aqt import gui_hooks, mw


def setup_reviewer_handlers(ankimon_tracker_obj, reviewer_obj):
    """
    Set up the reviewer show question/answer handlers.
    
    Args:
        ankimon_tracker_obj: The Ankimon tracker object for timing
        reviewer_obj: The reviewer object for UI updates
    """
    
    def on_show_question(card):
        """
        Called when a question is shown.
        Starts the card timer for tracking answer time.
        """
        ankimon_tracker_obj.start_card_timer()

    def on_show_answer(card):
        """
        Called when an answer is shown.
        Stops the card timer.
        """
        ankimon_tracker_obj.stop_card_timer()

    def on_reviewer_did_show_question(card):
        """
        Called after the reviewer shows a question.
        Updates the life bar display.
        """
        reviewer_obj.update_life_bar(mw.reviewer, None, None)

    # Register the hooks
    gui_hooks.reviewer_did_show_question.append(on_show_question)
    gui_hooks.reviewer_did_show_answer.append(on_show_answer)
    gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)
