"""Deterministic demonstration responder; no external model providers are configured."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Ideal Body Weight Calculator"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return (
            f"[{self.system_name} demonstration responder] "
            "No independent clinical assessment was performed. "
            f"Received query: {prompt[:60]!r}"
        )


class LLMFactory:
    """Only the offline demonstration provider is implemented."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Ideal Body Weight Calculator"):
        if str(provider).lower() in ("mock", "deterministic", "test"):
            return MockLLM(system_name)
        raise ValueError(
            f"Provider {provider!r} is not implemented; use 'mock'."
        )
