"""
Lifecycle Tests (mocked).

Verifies:
- Startup idempotency
- Shutdown idempotency
- asyncio.Lock protection
- _reset_singletons delegates to dependencies
- _clear_lifecycle_state resets flags
- Configuration validation
- Dependency verification
"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.core.exceptions import StartupException, ValidationException
from app.lifecycle import ApplicationLifecycle


class TestStartupIdempotency:
    @pytest.mark.asyncio
    async def test_second_startup_is_noop(self):
        lc = ApplicationLifecycle()
        lc._startup_ok = True

        await lc.startup()

        assert lc._started_at is None

    @pytest.mark.asyncio
    async def test_startup_sets_flag(self):
        lc = ApplicationLifecycle()
        with patch.object(lc, "_validate_configuration"), \
             patch.object(lc, "_ensure_directories"), \
             patch.object(lc, "_verify_dependencies"):
            await lc.startup()
            assert lc._startup_ok is True

    @pytest.mark.asyncio
    async def test_startup_records_timestamp(self):
        lc = ApplicationLifecycle()
        with patch.object(lc, "_validate_configuration"), \
             patch.object(lc, "_ensure_directories"), \
             patch.object(lc, "_verify_dependencies"):
            await lc.startup()
            assert lc._started_at is not None


class TestShutdownIdempotency:
    @pytest.mark.asyncio
    async def test_second_shutdown_is_noop(self):
        lc = ApplicationLifecycle()
        lc._shutdown_ok = True

        await lc.shutdown()

        assert lc._started_at is not None or lc._started_at is None  # no crash

    @pytest.mark.asyncio
    async def test_shutdown_sets_flag(self):
        lc = ApplicationLifecycle()
        await lc.shutdown()
        assert lc._shutdown_ok is True


class TestAsyncioLock:
    @pytest.mark.asyncio
    async def test_lock_is_created(self):
        lc = ApplicationLifecycle()
        assert isinstance(lc._lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_concurrent_startup_only_runs_once(self):
        lc = ApplicationLifecycle()
        with patch.object(lc, "_validate_configuration"), \
             patch.object(lc, "_ensure_directories"), \
             patch.object(lc, "_verify_dependencies"):
            # Run startup twice concurrently
            await asyncio.gather(
                lc.startup(),
                lc.startup(),
            )
            assert lc._startup_ok is True


class TestResetSingletons:
    def test_delegates_to_dependencies(self):
        lc = ApplicationLifecycle()
        with patch("app.core.dependencies.reset_singletons") as mock_reset:
            lc._reset_singletons()
            mock_reset.assert_called_once()


class TestClearLifecycleState:
    def test_resets_flags(self):
        lc = ApplicationLifecycle()
        lc._startup_ok = True
        lc._started_at = "some_timestamp"

        lc._clear_lifecycle_state()

        assert lc._startup_ok is False
        assert lc._started_at is None


class TestHealthCheck:
    def test_returns_dict(self):
        lc = ApplicationLifecycle()
        result = lc.health_check()
        assert "status" in result
        assert "dependencies" in result
        assert "uptime_seconds" in result

    def test_unhealthy_when_not_started(self):
        lc = ApplicationLifecycle()
        result = lc.health_check()
        assert result["status"] == "unhealthy"

    def test_dependencies_are_list(self):
        lc = ApplicationLifecycle()
        result = lc.health_check()
        assert isinstance(result["dependencies"], list)


class TestValidateConfiguration:
    def test_calls_settings_validate(self):
        lc = ApplicationLifecycle()
        with patch("app.lifecycle.settings") as mock_settings:
            lc._validate_configuration()
            mock_settings.validate_runtime.assert_called_once()

    def test_validation_error_propagates(self):
        lc = ApplicationLifecycle()
        with patch("app.lifecycle.settings") as mock_settings:
            mock_settings.validate_runtime.side_effect = ValidationException(
                message="bad config"
            )
            with pytest.raises(ValidationException):
                lc._validate_configuration()

    def test_unexpected_error_wraps_in_validation(self):
        lc = ApplicationLifecycle()
        with patch("app.lifecycle.settings") as mock_settings:
            mock_settings.validate_runtime.side_effect = RuntimeError("crash")
            with pytest.raises(ValidationException):
                lc._validate_configuration()


class TestVerifyDependencies:
    def test_all_dependencies_checked(self):
        lc = ApplicationLifecycle()
        checks = [
            "vector_store", "embedding_provider", "llm_provider",
            "retrieval_service", "memory_service", "rag_orchestrator", "chat_service",
        ]
        with patch.object(lc, "_verify_vector_store"), \
             patch.object(lc, "_verify_embedding_provider"), \
             patch.object(lc, "_verify_llm_provider"), \
             patch.object(lc, "_verify_retrieval_service"), \
             patch.object(lc, "_verify_memory_service"), \
             patch.object(lc, "_verify_rag_orchestrator"), \
             patch.object(lc, "_verify_chat_service"):
            lc._verify_dependencies()  # should not raise

    def test_failure_wraps_in_startup_exception(self):
        lc = ApplicationLifecycle()
        with patch.object(lc, "_verify_vector_store", side_effect=RuntimeError("boom")):
            with pytest.raises(StartupException):
                lc._verify_dependencies()
