"""
Memory Service Tests.

Verifies:
- Session creation
- Message order
- Message limit enforcement
- Formatted history
- Clear session
- Delete session
- List sessions
- Validation (empty session_id, invalid role, empty content)
"""

import uuid

import pytest

from app.core.exceptions import MemoryException, ValidationException
from app.services.memory_service import MemoryService


@pytest.fixture()
def memory() -> MemoryService:
    """Fresh MemoryService instance for each test."""
    return MemoryService(max_messages=5)


class TestSessionCreation:
    def test_create_session_returns_uuid(self, memory: MemoryService):
        session_id = memory.create_session()
        assert isinstance(session_id, str)
        uuid.UUID(session_id)  # validates UUID format

    def test_create_multiple_sessions(self, memory: MemoryService):
        s1 = memory.create_session()
        s2 = memory.create_session()
        assert s1 != s2

    def test_session_exists_after_creation(self, memory: MemoryService):
        sid = memory.create_session()
        assert memory.session_exists(sid)

    def test_session_count(self, memory: MemoryService):
        assert memory.session_count() == 0
        memory.create_session()
        memory.create_session()
        assert memory.session_count() == 2


class TestMessageOrder:
    def test_messages_added_in_order(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "Hello")
        memory.add_message(sid, "assistant", "Hi")
        memory.add_message(sid, "user", "Thanks")

        messages = memory.get_messages(sid)
        assert len(messages) == 3
        assert messages[0].role == "user"
        assert messages[0].content == "Hello"
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hi"
        assert messages[2].role == "user"
        assert messages[2].content == "Thanks"


class TestMessageLimit:
    def test_exceeding_limit_trims_oldest(self, memory: MemoryService):
        sid = memory.create_session()
        for i in range(10):
            memory.add_message(sid, "user", f"msg-{i}")

        messages = memory.get_messages(sid)
        assert len(messages) == 5
        assert messages[0].content == "msg-5"
        assert messages[4].content == "msg-9"

    def test_limit_with_mixed_roles(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "q1")
        memory.add_message(sid, "assistant", "a1")
        memory.add_message(sid, "user", "q2")
        memory.add_message(sid, "assistant", "a2")
        memory.add_message(sid, "user", "q3")
        memory.add_message(sid, "assistant", "a3")
        memory.add_message(sid, "user", "q4")

        messages = memory.get_messages(sid)
        assert len(messages) == 5
        # After 7 messages with limit=5, oldest 2 (q1, a1) are trimmed
        assert messages[0].content == "q2"
        assert messages[-1].content == "q4"


class TestFormattedHistory:
    def test_empty_session_returns_empty(self, memory: MemoryService):
        sid = memory.create_session()
        result = memory.get_formatted_history(sid)
        assert result == ""

    def test_formatted_history(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "How do refunds work?")
        memory.add_message(sid, "assistant", "Refunds are available for 30 days.")

        result = memory.get_formatted_history(sid)
        assert "User: How do refunds work?" in result
        assert "Assistant: Refunds are available for 30 days." in result

    def test_formatted_history_order(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "first")
        memory.add_message(sid, "assistant", "second")

        result = memory.get_formatted_history(sid)
        lines = result.split("\n")
        assert lines[0] == "User: first"
        assert lines[1] == "Assistant: second"


class TestClearSession:
    def test_clear_removes_messages(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "Hello")
        memory.add_message(sid, "assistant", "Hi")
        memory.clear_session(sid)

        messages = memory.get_messages(sid)
        assert len(messages) == 0

    def test_clear_preserves_session(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "Hello")
        memory.clear_session(sid)

        assert memory.session_exists(sid)

    def test_clear_nonexistent_session_raises(self, memory: MemoryService):
        with pytest.raises(MemoryException):
            memory.clear_session("nonexistent-id")


class TestDeleteSession:
    def test_delete_removes_session(self, memory: MemoryService):
        sid = memory.create_session()
        memory.add_message(sid, "user", "Hello")
        memory.delete_session(sid)
        assert not memory.session_exists(sid)

    def test_delete_nonexistent_raises(self, memory: MemoryService):
        with pytest.raises(MemoryException):
            memory.delete_session("nonexistent-id")

    def test_delete_reduces_count(self, memory: MemoryService):
        sid = memory.create_session()
        assert memory.session_count() == 1
        memory.delete_session(sid)
        assert memory.session_count() == 0


class TestListSessions:
    def test_list_empty(self, memory: MemoryService):
        assert memory.list_sessions() == []

    def test_list_returns_ids(self, memory: MemoryService):
        s1 = memory.create_session()
        s2 = memory.create_session()
        sessions = memory.list_sessions()
        assert set(sessions) == {s1, s2}

    def test_list_after_delete(self, memory: MemoryService):
        s1 = memory.create_session()
        s2 = memory.create_session()
        memory.delete_session(s1)
        assert memory.list_sessions() == [s2]


class TestRecentMessages:
    def test_recent_with_limit(self, memory: MemoryService):
        sid = memory.create_session()
        for i in range(8):
            memory.add_message(sid, "user", f"msg-{i}")

        recent = memory.get_recent_messages(sid, limit=3)
        assert len(recent) == 3
        assert recent[0].content == "msg-5"

    def test_recent_negative_limit_raises(self, memory: MemoryService):
        sid = memory.create_session()
        with pytest.raises(ValidationException):
            memory.get_recent_messages(sid, limit=-1)


class TestValidation:
    def test_empty_session_id_raises(self, memory: MemoryService):
        with pytest.raises(ValidationException):
            memory.add_message("", "user", "hello")

    def test_blank_session_id_raises(self, memory: MemoryService):
        with pytest.raises(ValidationException):
            memory.add_message("   ", "user", "hello")

    def test_invalid_role_raises(self, memory: MemoryService):
        sid = memory.create_session()
        with pytest.raises(ValidationException):
            memory.add_message(sid, "admin", "hello")

    def test_empty_content_raises(self, memory: MemoryService):
        sid = memory.create_session()
        with pytest.raises(ValidationException):
            memory.add_message(sid, "user", "")

    def test_blank_content_raises(self, memory: MemoryService):
        sid = memory.create_session()
        with pytest.raises(ValidationException):
            memory.add_message(sid, "user", "   ")

    def test_session_not_found_raises(self, memory: MemoryService):
        with pytest.raises(MemoryException):
            memory.get_messages("nonexistent-id")

    def test_add_to_nonexistent_session_raises(self, memory: MemoryService):
        with pytest.raises(MemoryException):
            memory.add_message("nonexistent-id", "user", "hello")
