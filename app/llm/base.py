"""
LLM Provider – Abstract base class for language model integrations.

Defines the interface that all LLM providers must implement.
The RAG orchestrator depends only on this abstraction, never on
concrete SDK implementations.

Usage:
    from app.llm.base import LLMProvider

    class MyProvider(LLMProvider):
        def generate(self, prompt: str) -> str:
            ...
        @property
        def model_name(self) -> str:
            ...
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for language model providers.

    All LLM implementations must conform to this interface.
    The RAG orchestrator uses only this abstraction via dependency injection.
    """

    @abstractmethod
    def generate(self, prompt: str) -> str:
        """Generate a text response from the language model.

        Args:
            prompt: The fully constructed prompt to send to the model.

        Returns:
            The model's generated text response.

        Raises:
            LLMException: If the model call fails or times out.
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the identifier of the underlying model.

        Returns:
            A string like ``"gemini-1.5-flash"`` or ``"gpt-4"``.
        """
        ...
