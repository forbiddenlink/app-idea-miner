"""
Unit tests for packages/core/nlp.py - extract_ideas_llm().

The Anthropic client is mocked: no network calls, no API spend.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from packages.core import nlp
from packages.core.nlp import LLMIdea, LLMIdeas, extract_ideas_llm

POST = "I really wish there was an app that tracked my houseplant watering schedule automatically."


@pytest.fixture(autouse=True)
def llm_env(monkeypatch):
    monkeypatch.setenv("USE_LLM_EXTRACTION", "true")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    nlp.reset_llm_call_count()


def _mock_client(parsed_output, stop_reason="end_turn"):
    client = MagicMock()
    client.messages.parse.return_value = SimpleNamespace(
        parsed_output=parsed_output, stop_reason=stop_reason
    )
    return client


def _ideas(*items):
    return LLMIdeas(ideas=[LLMIdea(**i) for i in items])


class TestExtractIdeasLlm:
    def test_disabled_without_env_flag(self, monkeypatch):
        monkeypatch.delenv("USE_LLM_EXTRACTION")
        assert extract_ideas_llm(POST) == []

    def test_requests_structured_output_schema(self):
        client = _mock_client(_ideas())
        with patch("anthropic.Anthropic", return_value=client):
            extract_ideas_llm(POST)
        kwargs = client.messages.parse.call_args.kwargs
        assert kwargs["output_format"] is LLMIdeas
        assert kwargs["model"] == "claude-haiku-4-5"
        client.messages.create.assert_not_called()

    def test_maps_parsed_ideas_and_filters_low_confidence(self):
        parsed = _ideas(
            {
                "problem_statement": "Track plant watering",
                "target_user": "plant owners",
                "urgency": "high",
                "confidence": 0.9,
            },
            {
                "problem_statement": "Vague gripe",
                "target_user": "anyone",
                "urgency": "low",
                "confidence": 0.3,
            },
        )
        with patch("anthropic.Anthropic", return_value=_mock_client(parsed)):
            result = extract_ideas_llm(POST)
        assert result == [
            {
                "problem_statement": "Track plant watering",
                "target_user": "plant owners",
                "urgency": "high",
                "confidence": 0.9,
                "source": "llm",
            }
        ]

    def test_refusal_returns_empty(self):
        client = _mock_client(None, stop_reason="refusal")
        with patch("anthropic.Anthropic", return_value=client):
            assert extract_ideas_llm(POST) == []

    def test_api_error_returns_empty(self):
        client = MagicMock()
        client.messages.parse.side_effect = RuntimeError("boom")
        with patch("anthropic.Anthropic", return_value=client):
            assert extract_ideas_llm(POST) == []

    def test_counts_calls_against_quota(self):
        with patch("anthropic.Anthropic", return_value=_mock_client(_ideas())):
            extract_ideas_llm(POST)
        assert nlp._llm_call_count == 1
