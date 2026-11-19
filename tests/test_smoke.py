
from app.storage import ChatStorage
from app.subject_manager import SubjectManager


def test_chat_storage_creates_and_retrieves_conversation(tmp_path):
    storage = ChatStorage(str(tmp_path / "test_chat.db"))

    conversation_id = storage.create_conversation(
        subject="DBMS",
        title="Test conversation"
    )

    storage.add_message(
        conversation_id=conversation_id,
        role="user",
        content="What is DBMS?"
    )

    messages = storage.get_messages(conversation_id)

    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "What is DBMS?"


def test_chat_storage_deletes_conversation(tmp_path):
    storage = ChatStorage(str(tmp_path / "test_chat.db"))

    conversation_id = storage.create_conversation(
        subject="DBMS",
        title="Delete test"
    )

    storage.delete_conversation(conversation_id)

    assert storage.get_conversation(conversation_id) is None


def test_subject_manager_creates_unique_subject(tmp_path, monkeypatch):
    import app.subject_manager as subject_module

    monkeypatch.setattr(
        subject_module,
        "SUBJECTS_FILE",
        tmp_path / "subjects.json"
    )

    manager = SubjectManager()

    subject = manager.add_subject("Computer Networks")

    assert subject["name"] == "Computer Networks"
    assert subject["slug"] == "computer_networks"
    assert subject["status"] == "pending"


def test_subject_manager_updates_status(tmp_path, monkeypatch):
    import app.subject_manager as subject_module

    monkeypatch.setattr(
        subject_module,
        "SUBJECTS_FILE",
        tmp_path / "subjects.json"
    )

    manager = SubjectManager()

    subject = manager.add_subject("Operating Systems")

    updated = manager.update_status(
        subject["slug"],
        "ready"
    )

    assert updated["status"] == "ready"


def test_subject_manager_rejects_duplicate_subject(tmp_path, monkeypatch):
    import app.subject_manager as subject_module

    monkeypatch.setattr(
        subject_module,
        "SUBJECTS_FILE",
        tmp_path / "subjects.json"
    )

    manager = SubjectManager()

    manager.add_subject("Computer Networks")

    try:
        manager.add_subject("Computer Networks")
        assert False, "Duplicate subject should be rejected."
    except ValueError as error:
        assert "already exists" in str(error)
