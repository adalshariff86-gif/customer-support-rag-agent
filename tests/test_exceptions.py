"""
Exception Hierarchy Tests.

Verifies every custom exception class in the hierarchy:
- AppException base
- ValidationException (422)
- ConfigurationException (500)
- LLMException (502)
- VectorStoreException (500)
- MemoryException (500)
- DocumentException (500)
- EmbeddingException (500)
- RetrievalException (500)
- ChatException (500)
- StartupException (503)
- RAGException (500)
"""

import pytest

from app.core.exceptions import (
    AppException,
    ChatException,
    ConfigurationException,
    DocumentException,
    EmbeddingException,
    LLMException,
    MemoryException,
    RAGException,
    RetrievalException,
    StartupException,
    ValidationException,
    VectorStoreException,
)


class TestAppException:
    """Tests for the base AppException class."""

    def test_default_attributes(self):
        exc = AppException()
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.message == "An unexpected error occurred."
        assert exc.details == {}

    def test_custom_message(self):
        exc = AppException(message="Something broke")
        assert exc.message == "Something broke"
        assert str(exc) == "Something broke"

    def test_custom_details(self):
        exc = AppException(message="err", details={"key": "val"})
        assert exc.details == {"key": "val"}

    def test_custom_status_and_error_code(self):
        exc = AppException(message="err", status_code=418, error_code="TEAPOT")
        assert exc.status_code == 418
        assert exc.error_code == "TEAPOT"

    def test_to_dict(self):
        exc = AppException(message="err", status_code=400, error_code="BAD_REQ")
        d = exc.to_dict()
        assert d["type"] == "errors/bad_req"
        assert d["title"] == "Bad Req"
        assert d["status"] == 400
        assert d["detail"] == "err"

    def test_to_dict_none_errors(self):
        exc = AppException(message="err")
        d = exc.to_dict()
        assert d["errors"] is None

    def test_to_dict_with_details(self):
        exc = AppException(message="err", details={"x": 1})
        d = exc.to_dict()
        assert d["errors"] == {"x": 1}


class TestValidationException:
    def test_default_status_code(self):
        exc = ValidationException(message="bad input")
        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"
        assert exc.message == "bad input"

    def test_inherits_app_exception(self):
        assert issubclass(ValidationException, AppException)


class TestConfigurationException:
    def test_default_status_code(self):
        exc = ConfigurationException(message="missing key")
        assert exc.status_code == 500
        assert exc.error_code == "CONFIGURATION_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(ConfigurationException, AppException)


class TestLLMException:
    def test_default_status_code(self):
        exc = LLMException(message="LLM failed")
        assert exc.status_code == 502
        assert exc.error_code == "LLM_ERROR"

    def test_custom_status_code(self):
        exc = LLMException(message="timeout", status_code=504)
        assert exc.status_code == 504

    def test_inherits_app_exception(self):
        assert issubclass(LLMException, AppException)


class TestVectorStoreException:
    def test_default_status_code(self):
        exc = VectorStoreException(message="db error")
        assert exc.status_code == 500
        assert exc.error_code == "VECTOR_STORE_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(VectorStoreException, AppException)


class TestMemoryException:
    def test_default_status_code(self):
        exc = MemoryException(message="session missing")
        assert exc.status_code == 500
        assert exc.error_code == "MEMORY_ERROR"

    def test_custom_status_code(self):
        exc = MemoryException(message="not found", status_code=404)
        assert exc.status_code == 404

    def test_inherits_app_exception(self):
        assert issubclass(MemoryException, AppException)


class TestDocumentException:
    def test_default_status_code(self):
        exc = DocumentException(message="parse error")
        assert exc.status_code == 500
        assert exc.error_code == "DOCUMENT_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(DocumentException, AppException)


class TestEmbeddingException:
    def test_default_status_code(self):
        exc = EmbeddingException(message="model failed")
        assert exc.status_code == 500
        assert exc.error_code == "EMBEDDING_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(EmbeddingException, AppException)


class TestRetrievalException:
    def test_default_status_code(self):
        exc = RetrievalException(message="search failed")
        assert exc.status_code == 500
        assert exc.error_code == "RETRIEVAL_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(RetrievalException, AppException)


class TestChatException:
    def test_default_status_code(self):
        exc = ChatException(message="chat error")
        assert exc.status_code == 500
        assert exc.error_code == "CHAT_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(ChatException, AppException)


class TestStartupException:
    def test_default_status_code(self):
        exc = StartupException(message="boot failed")
        assert exc.status_code == 503
        assert exc.error_code == "STARTUP_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(StartupException, AppException)


class TestRAGException:
    def test_default_status_code(self):
        exc = RAGException(message="rag error")
        assert exc.status_code == 500
        assert exc.error_code == "RAG_ERROR"

    def test_inherits_app_exception(self):
        assert issubclass(RAGException, AppException)


class TestExceptionHierarchy:
    """Verify the full inheritance tree."""

    def test_all_inherit_app_exception(self):
        classes = [
            ValidationException,
            ConfigurationException,
            LLMException,
            VectorStoreException,
            MemoryException,
            DocumentException,
            EmbeddingException,
            RetrievalException,
            ChatException,
            StartupException,
            RAGException,
        ]
        for cls in classes:
            assert issubclass(cls, AppException), f"{cls.__name__} must inherit AppException"

    def test_all_inherit_exception(self):
        classes = [
            AppException,
            ValidationException,
            LLMException,
            VectorStoreException,
            MemoryException,
            StartupException,
        ]
        for cls in classes:
            assert issubclass(cls, Exception), f"{cls.__name__} must inherit Exception"
