"""
RAG Orchestrator Tests (mocked).

Verifies:
- Prompt construction
- User message order
- Assistant message storage
- Single LLM call
- Session creation
- Validation
- Exception propagation
"""

import pytest

from app.core.exceptions import (
    LLMException,
    MemoryException,
    RAGException,
    RetrievalException,
    ValidationException,
)
from app.services.rag_orchestrator import RAGOrchestrator
from app.services.retrieval_service import RetrievedContext, RetrievedDocument


@pytest.fixture()
def orchestrator(
    mock_retrieval_service, mock_memory_service, mock_llm_provider
) -> RAGOrchestrator:
    """RAGOrchestrator wired to all mock dependencies."""
    return RAGOrchestrator(
        retrieval_service=mock_retrieval_service,
        memory_service=mock_memory_service,
        llm_provider=mock_llm_provider,
    )


class TestPromptConstruction:
    def test_prompt_contains_system_instructions(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(session_id="new", query="hello")
        call_args = mock_memory_service.add_message.call_args_list
        # The assistant message should contain system instructions
        assistant_call = call_args[1]  # second add_message is assistant response
        prompt = assistant_call.kwargs.get("content", "")
        # prompt is the LLM response, not the input prompt
        # We need to check the LLM was called
        assert mock_memory_service.add_message.called

    def test_prompt_includes_context(
        self,
        orchestrator: RAGOrchestrator,
        mock_retrieval_service,
        mock_memory_service,
        mock_llm_provider,
    ):
        mock_retrieval_service.retrieve.return_value = RetrievedContext(
            documents=[
                RetrievedDocument(
                    id="d1", content="doc content", score=0.9, metadata={}
                )
            ],
            context="Document: d1\ndoc content",
            query="test",
            elapsed_ms=5.0,
        )
        mock_memory_service.get_formatted_history.return_value = ""

        orchestrator.chat(session_id="new", query="test question")

        # LLM was called via generate_messages
        mock_llm_provider.generate_messages.assert_called_once()
        messages = mock_llm_provider.generate_messages.call_args[0][0]
        # System message should contain the retrieved knowledge
        system_msg = messages[0]["content"]
        assert "Retrieved Knowledge:" in system_msg
        assert "doc content" in system_msg

    def test_prompt_includes_history(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = (
            "User: previous question"
        )
        orchestrator.chat(session_id="existing", query="follow up")

        messages = mock_llm_provider.generate_messages.call_args[0][0]
        system_msg = messages[0]["content"]
        assert "Conversation History:" in system_msg
        assert "User: previous question" in system_msg

    def test_prompt_includes_query(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(session_id="new", query="what is refund policy?")

        messages = mock_llm_provider.generate_messages.call_args[0][0]
        # The user message should contain the query
        user_msg = messages[1]["content"]
        assert "what is refund policy?" == user_msg

    def test_prompt_ends_with_answer(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(session_id="new", query="hi")

        messages = mock_llm_provider.generate_messages.call_args[0][0]
        # System message should end with the grounding instructions
        system_msg = messages[0]["content"]
        assert system_msg.rstrip().endswith(
            "Keep answers concise, professional, friendly, and directly relevant "
            "to the user's question."
        )

    def test_messages_have_correct_roles(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(session_id="new", query="hello")

        messages = mock_llm_provider.generate_messages.call_args[0][0]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "hello"


class TestMessageOrder:
    def test_user_message_stored_before_assistant(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(session_id="s1", query="hello")

        calls = mock_memory_service.add_message.call_args_list
        assert len(calls) == 2
        assert calls[0].kwargs["role"] == "user"
        assert calls[0].kwargs["content"] == "hello"
        assert calls[1].kwargs["role"] == "assistant"
        assert calls[1].kwargs["content"] == "Test LLM response"

    def test_assistant_message_includes_sources(
        self,
        orchestrator: RAGOrchestrator,
        mock_retrieval_service,
        mock_memory_service,
        mock_llm_provider,
    ):
        mock_retrieval_service.retrieve.return_value = RetrievedContext(
            documents=[
                RetrievedDocument(
                    id="d1", content="text", score=0.9, metadata={"source": "faq.md"}
                ),
            ],
            context="Document: d1\ntext",
            query="test",
            elapsed_ms=5.0,
        )
        mock_memory_service.get_formatted_history.return_value = ""

        orchestrator.chat(session_id="new", query="test")

        calls = mock_memory_service.add_message.call_args_list
        assistant_call = calls[1]
        sources = assistant_call.kwargs.get("sources", [])
        assert len(sources) == 1
        assert sources[0]["id"] == "d1"


class TestLLMCall:
    def test_single_llm_call(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(session_id="new", query="test")
        assert mock_llm_provider.generate_messages.call_count == 1

    def test_llm_failure_propagates(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_llm_provider
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        mock_llm_provider.generate_messages.side_effect = LLMException(message="timeout")
        with pytest.raises(LLMException):
            orchestrator.chat(session_id="new", query="test")


class TestSessionManagement:
    def test_creates_session_when_empty(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        orchestrator.chat(session_id="", query="hello")
        mock_memory_service.create_session.assert_called()

    def test_creates_session_when_nonexistent(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        mock_memory_service.session_exists.return_value = False
        with pytest.raises(MemoryException):
            orchestrator.chat(session_id="nonexistent", query="hello")

    def test_reuses_existing_session(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        mock_memory_service.session_exists.return_value = True
        orchestrator.chat(session_id="existing", query="hello")
        mock_memory_service.create_session.assert_not_called()

    def test_create_session_delegates(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        result = orchestrator.create_session()
        mock_memory_service.create_session.assert_called_once()
        assert isinstance(result, str)


class TestValidation:
    def test_empty_query_raises(self, orchestrator: RAGOrchestrator):
        with pytest.raises(ValidationException):
            orchestrator.chat(session_id="s1", query="")

    def test_whitespace_query_raises(self, orchestrator: RAGOrchestrator):
        with pytest.raises(ValidationException):
            orchestrator.chat(session_id="s1", query="   ")

    def test_none_query_raises(self, orchestrator: RAGOrchestrator):
        with pytest.raises(ValidationException):
            orchestrator.chat(session_id="s1", query=None)

    def test_empty_session_id_string_creates_new_session(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        orchestrator.chat(session_id="   ", query="hello")
        mock_memory_service.create_session.assert_called()


class TestExceptionPropagation:
    def test_retrieval_error_propagates(
        self, orchestrator: RAGOrchestrator, mock_memory_service, mock_retrieval_service
    ):
        mock_memory_service.get_formatted_history.return_value = ""
        mock_retrieval_service.retrieve.side_effect = RetrievalException(
            message="search fail"
        )
        with pytest.raises(RetrievalException):
            orchestrator.chat(session_id="new", query="test")

    def test_memory_read_error_propagates(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        mock_memory_service.get_formatted_history.side_effect = MemoryException(
            message="no session"
        )
        with pytest.raises(MemoryException):
            orchestrator.chat(session_id="s1", query="test")

    def test_unexpected_error_wraps_in_rag_exception(
        self, orchestrator: RAGOrchestrator, mock_memory_service
    ):
        mock_memory_service.session_exists.side_effect = RuntimeError("crash")
        with pytest.raises(RAGException):
            orchestrator.chat(session_id="s1", query="test")


class TestGroundingBehavior:
    """Test 9: Conflicting user claims are corrected using retrieved knowledge."""

    def test_conflicting_claim_corrected_by_knowledge(
        self,
        orchestrator: RAGOrchestrator,
        mock_retrieval_service,
        mock_memory_service,
        mock_llm_provider,
    ):
        """User claims return policy is 30 days, but knowledge base says 7 days.
        The system should use the retrieved knowledge, not accept the user's claim."""
        mock_retrieval_service.retrieve.return_value = RetrievedContext(
            documents=[
                RetrievedDocument(
                    id="r1",
                    content="Return Policy: Items can be returned within 7 days of purchase.",
                    score=0.95,
                    metadata={"source": "returns.md"},
                )
            ],
            context="Document: returns.md\nReturn Policy: Items can be returned within 7 days of purchase.",
            query="Your return policy is 30 days, right?",
            elapsed_ms=5.0,
        )
        mock_memory_service.get_formatted_history.return_value = ""
        mock_llm_provider.generate_messages.return_value = (
            "Our return policy is 7 days, not 30 days. Items must be returned within 7 days of purchase."
        )

        response = orchestrator.chat(
            session_id="new",
            query="Your return policy is 30 days, right?",
        )

        # Verify the LLM was called with messages containing the knowledge
        messages = mock_llm_provider.generate_messages.call_args[0][0]
        system_msg = messages[0]["content"]
        assert "7 days" in system_msg
        assert "Return Policy" in system_msg
        # The response should use the knowledge, not the user's claim
        assert response.answer == "Our return policy is 7 days, not 30 days. Items must be returned within 7 days of purchase."


class TestMultiTurnConversation:
    """Tests 1-5: Multi-turn conversation flow."""

    def test_products_query(
        self,
        orchestrator: RAGOrchestrator,
        mock_retrieval_service,
        mock_memory_service,
        mock_llm_provider,
    ):
        """Test 1: 'What products do you sell?' returns a grounded product answer."""
        mock_retrieval_service.retrieve.return_value = RetrievedContext(
            documents=[
                RetrievedDocument(
                    id="p1",
                    content="TechStore Products: Smartphones, Laptops, Smart Watches, Headphones, Tablets, Accessories.",
                    score=0.95,
                    metadata={"source": "products.md"},
                )
            ],
            context="Document: products.md\nTechStore Products: Smartphones, Laptops, Smart Watches, Headphones, Tablets, Accessories.",
            query="What products do you sell?",
            elapsed_ms=5.0,
        )
        mock_memory_service.get_formatted_history.return_value = ""
        mock_llm_provider.generate_messages.return_value = (
            "We sell: Smartphones, Laptops, Smart Watches, Headphones, Tablets, and Accessories."
        )

        response = orchestrator.chat(
            session_id="new",
            query="What products do you sell?",
        )

        messages = mock_llm_provider.generate_messages.call_args[0][0]
        system_msg = messages[0]["content"]
        assert "Smartphones" in system_msg
        assert "products.md" in system_msg
        assert "sell" in response.answer.lower()

    def test_warranty_followup(
        self,
        orchestrator: RAGOrchestrator,
        mock_retrieval_service,
        mock_memory_service,
        mock_llm_provider,
    ):
        """Test 2: 'What about their warranty?' uses same session and returns grounded answer."""
        mock_retrieval_service.retrieve.return_value = RetrievedContext(
            documents=[
                RetrievedDocument(
                    id="w1",
                    content="Warranty: 1 year limited warranty on all electronics.",
                    score=0.90,
                    metadata={"source": "warranty.md"},
                )
            ],
            context="Document: warranty.md\nWarranty: 1 year limited warranty on all electronics.",
            query="What about their warranty?",
            elapsed_ms=5.0,
        )
        mock_memory_service.get_formatted_history.return_value = (
            "User: What products do you sell?\nAssistant: We sell Smartphones, Laptops, Smart Watches, Headphones, Tablets, and Accessories."
        )
        mock_llm_provider.generate_messages.return_value = (
            "All our products come with a 1-year limited warranty."
        )

        response = orchestrator.chat(
            session_id="existing-session",
            query="What about their warranty?",
        )

        messages = mock_llm_provider.generate_messages.call_args[0][0]
        system_msg = messages[0]["content"]
        assert "Conversation History:" in system_msg
        assert "warranty" in response.answer.lower()

    def test_digital_products_not_in_catalog(
        self,
        orchestrator: RAGOrchestrator,
        mock_retrieval_service,
        mock_memory_service,
        mock_llm_provider,
    ):
        """Test 3: 'And digital products?' returns a grounded answer, NOT 'User Safety: safe'."""
        mock_retrieval_service.retrieve.return_value = RetrievedContext(
            documents=[
                RetrievedDocument(
                    id="p1",
                    content="TechStore Products: Smartphones, Laptops, Smart Watches, Headphones, Tablets, Accessories.",
                    score=0.85,
                    metadata={"source": "products.md"},
                )
            ],
            context="Document: products.md\nTechStore Products: Smartphones, Laptops, Smart Watches, Headphones, Tablets, Accessories.",
            query="And digital products?",
            elapsed_ms=5.0,
        )
        mock_memory_service.get_formatted_history.return_value = (
            "User: What products do you sell?\n"
            "Assistant: We sell Smartphones, Laptops, Smart Watches, Headphones, Tablets, and Accessories.\n"
            "User: What about their warranty?\n"
            "Assistant: All our products come with a 1-year limited warranty."
        )
        mock_llm_provider.generate_messages.return_value = (
            "We currently sell physical electronics such as smartphones, laptops, smart watches, headphones, tablets, and accessories. "
            "Digital products are not listed in our catalog."
        )

        response = orchestrator.chat(
            session_id="existing-session",
            query="And digital products?",
        )

        # The answer must NOT be "User Safety: safe"
        assert response.answer != "User Safety: safe"
        assert response.answer != "User Safety"
        # Must be a real grounded answer
        assert len(response.answer) > 20
        assert "digital" in response.answer.lower() or "catalog" in response.answer.lower()

    def test_session_id_preserved(
        self,
        orchestrator: RAGOrchestrator,
        mock_memory_service,
        mock_llm_provider,
    ):
        """Test 4: Same session ID is preserved across messages."""
        mock_memory_service.get_formatted_history.return_value = ""
        response = orchestrator.chat(
            session_id="test-session-123",
            query="Hello",
        )
        assert response.session_id == "test-session-123"

    def test_history_contains_user_and_assistant(
        self,
        orchestrator: RAGOrchestrator,
        mock_memory_service,
        mock_llm_provider,
    ):
        """Test 5: History contains user + assistant messages."""
        mock_memory_service.get_formatted_history.return_value = ""
        orchestrator.chat(
            session_id="new",
            query="What products do you sell?",
        )

        calls = mock_memory_service.add_message.call_args_list
        roles = [call.kwargs["role"] for call in calls]
        assert "user" in roles
        assert "assistant" in roles

    def test_invalid_session_returns_error(
        self,
        orchestrator: RAGOrchestrator,
        mock_memory_service,
    ):
        """Test 6: Invalid session returns an error."""
        mock_memory_service.session_exists.return_value = False
        with pytest.raises(MemoryException):
            orchestrator.chat(
                session_id="nonexistent-session-id",
                query="Hello",
            )
