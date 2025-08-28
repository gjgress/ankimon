import pytest
from ankimon_test_env.mock_anki.collection import Collection, MockScheduler, MockCard, MockNote, MockQueuedCards

@pytest.fixture
def mock_collection():
    return Collection()

@pytest.fixture
def mock_scheduler():
    return MockScheduler()

def test_collection_init(mock_collection):
    assert isinstance(mock_collection, Collection)
    assert len(mock_collection._cards) == 3
    assert mock_collection._notes == []
    assert mock_collection.conf == {}
    assert isinstance(mock_collection.sched, MockScheduler)

def test_collection_get_set_config(mock_collection):
    mock_collection.set_config("test_key", "test_value")
    assert mock_collection.get_config("test_key") == "test_value"
    assert mock_collection.get_config("non_existent_key") is None

def test_collection_add_all_notes(mock_collection):
    note1 = MockNote()
    note2 = MockNote()
    mock_collection.add_note(note1)
    mock_collection.add_note(note2)
    assert mock_collection.all_notes() == [note1, note2]

def test_collection_get_card(mock_collection):
    card1 = mock_collection.get_card(1)
    assert card1.id == 1
    assert card1.question() == "What is 2+2?"
    assert mock_collection.get_card(999) is None # Test non-existent card

def test_collection_sched_ver(mock_collection):
    assert mock_collection.sched_ver() == 3
    assert mock_collection.v3_scheduler() is True

def test_scheduler_init(mock_scheduler):
    assert isinstance(mock_scheduler, MockScheduler)
    assert len(mock_scheduler._queue) == 3
    assert mock_scheduler.new_count == 3
    assert mock_scheduler.learning_count == 0
    assert mock_scheduler.review_count == 0

def test_scheduler_get_queued_cards(mock_scheduler):
    queued_cards = mock_scheduler.get_queued_cards()
    assert isinstance(queued_cards, MockQueuedCards)
    assert queued_cards.new_count == 3
    assert queued_cards.learning_count == 0
    assert queued_cards.review_count == 0

def test_scheduler_answer_card_again(mock_scheduler):
    card = mock_scheduler._queue[0]
    initial_reps = card._reps
    initial_lapses = card._lapses
    
    mock_scheduler.answerCard(card, 1) # Ease 1: Again
    
    assert card._reps == initial_reps + 1
    assert card._lapses == initial_lapses + 1
    assert card._ivl == 1
    assert card._due == 0
    assert mock_scheduler.learning_count == 1 # Should increase learning count
    assert card in mock_scheduler._queue # Should be re-added to queue

def test_scheduler_answer_card_hard(mock_scheduler):
    card = mock_scheduler._queue[0]
    initial_reps = card._reps
    initial_ivl = card._ivl
    
    mock_scheduler.answerCard(card, 2) # Ease 2: Hard
    
    assert card._reps == initial_reps + 1
    assert card._ivl == max(1, int(initial_ivl * 1.2))
    assert card._due == card._ivl
    assert mock_scheduler.learning_count == 1 # Should increase learning count
    assert card not in mock_scheduler._queue # Should be removed from new queue

def test_scheduler_answer_card_good(mock_scheduler):
    card = mock_scheduler._queue[0]
    initial_reps = card._reps
    initial_ivl = card._ivl
    
    mock_scheduler.answerCard(card, 3) # Ease 3: Good
    
    assert card._reps == initial_reps + 1
    assert card._ivl == max(1, int(initial_ivl * 2.5))
    assert card._due == card._ivl
    assert mock_scheduler.review_count == 1 # Should increase review count
    assert card not in mock_scheduler._queue # Should be removed from new queue

def test_scheduler_answer_card_easy(mock_scheduler):
    card = mock_scheduler._queue[0]
    initial_reps = card._reps
    initial_ivl = card._ivl
    
    mock_scheduler.answerCard(card, 4) # Ease 4: Easy
    
    assert card._reps == initial_reps + 1
    assert card._ivl == max(1, int(initial_ivl * 3.5))
    assert card._due == card._ivl
    assert mock_scheduler.review_count == 1 # Should increase review count
    assert card not in mock_scheduler._queue # Should be removed from new queue

def test_scheduler_describe_next_states(mock_scheduler):
    # This mock is simple, just checks the return format
    states = mock_scheduler.describe_next_states(None)
    assert isinstance(states, list)
    assert len(states) == 4
    assert all(isinstance(s, str) for s in states)
