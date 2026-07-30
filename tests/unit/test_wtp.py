"""
Unit tests for packages/core/nlp.py - detect_willingness_to_pay().

Tests detection of monetization-intent / willingness-to-pay (WTP) signals in
post text: explicit price patterns ($X/month), and common WTP phrases
("would pay", "take my money", "happy to pay", etc). No database required.
"""

from packages.core.nlp import detect_willingness_to_pay

# ---------------------------------------------------------------------------
# Explicit phrase signals
# ---------------------------------------------------------------------------


class TestPhraseSignals:
    def test_would_pay(self):
        result = detect_willingness_to_pay("I would pay for this in a heartbeat.")
        assert result["has_wtp_signal"] is True
        assert result["wtp_score"] > 0.0

    def test_take_my_money(self):
        result = detect_willingness_to_pay("Shut up and take my money!")
        assert result["has_wtp_signal"] is True
        assert any("take my money" in p.lower() for p in result["matched_phrases"])

    def test_happy_to_pay(self):
        result = detect_willingness_to_pay("I'd be happy to pay for something like this.")
        assert result["has_wtp_signal"] is True

    def test_worth_paying_for(self):
        result = detect_willingness_to_pay("This is definitely worth paying for.")
        assert result["has_wtp_signal"] is True

    def test_id_subscribe_no_apostrophe(self):
        result = detect_willingness_to_pay("id subscribe to this immediately")
        assert result["has_wtp_signal"] is True
        assert any("subscribe" in p.lower() for p in result["matched_phrases"])

    def test_willing_to_pay(self):
        result = detect_willingness_to_pay("I'm willing to pay a premium for this.")
        assert result["has_wtp_signal"] is True


# ---------------------------------------------------------------------------
# Price patterns
# ---------------------------------------------------------------------------


class TestPricePatterns:
    def test_dollar_per_month(self):
        result = detect_willingness_to_pay("I'd pay $5/month for this app.")
        assert result["has_wtp_signal"] is True
        assert any("$5/month" in p for p in result["matched_phrases"])

    def test_dollar_amount_only(self):
        result = detect_willingness_to_pay("Would pay around $20 for a lifetime license.")
        assert result["has_wtp_signal"] is True

    def test_number_slash_mo(self):
        result = detect_willingness_to_pay("Something like 10/mo would be reasonable.")
        assert result["has_wtp_signal"] is True

    def test_number_a_month(self):
        result = detect_willingness_to_pay("I could see paying 10 a month for this.")
        assert result["has_wtp_signal"] is True


# ---------------------------------------------------------------------------
# Negatives / no signal
# ---------------------------------------------------------------------------


class TestNoSignal:
    def test_free_only_no_signal(self):
        result = detect_willingness_to_pay("This should just be free honestly.")
        assert result["has_wtp_signal"] is False
        assert result["matched_phrases"] == []
        assert result["wtp_score"] == 0.0

    def test_unrelated_text_no_signal(self):
        result = detect_willingness_to_pay("I went for a walk and saw a dog.")
        assert result["has_wtp_signal"] is False
        assert result["wtp_score"] == 0.0

    def test_word_boundary_no_false_positive(self):
        # "mint" shouldn't match anything, and "paying" shouldn't false-positive
        # "would pay" if the pieces aren't contiguous
        result = detect_willingness_to_pay(
            "I wouldn't pay for this, it's overpriced and I'm playing devil's advocate."
        )
        assert result["has_wtp_signal"] is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string(self):
        result = detect_willingness_to_pay("")
        assert result == {
            "has_wtp_signal": False,
            "matched_phrases": [],
            "wtp_score": 0.0,
        }

    def test_case_insensitivity(self):
        lower = detect_willingness_to_pay("i would pay for this")
        upper = detect_willingness_to_pay("I WOULD PAY FOR THIS")
        mixed = detect_willingness_to_pay("I Would Pay For This")
        assert lower["has_wtp_signal"] is True
        assert upper["has_wtp_signal"] is True
        assert mixed["has_wtp_signal"] is True

    def test_score_bounded_between_zero_and_one(self):
        result = detect_willingness_to_pay(
            "Shut up and take my money! I would pay $5/month, "
            "happy to pay, worth paying for, willing to pay, take my money."
        )
        assert 0.0 <= result["wtp_score"] <= 1.0

    def test_return_shape(self):
        result = detect_willingness_to_pay("I would pay for this.")
        assert set(result.keys()) == {"has_wtp_signal", "matched_phrases", "wtp_score"}
        assert isinstance(result["has_wtp_signal"], bool)
        assert isinstance(result["matched_phrases"], list)
        assert isinstance(result["wtp_score"], float)


# ---------------------------------------------------------------------------
# Wired into extraction path
# ---------------------------------------------------------------------------


class TestWiredIntoExtraction:
    def test_extract_need_statements_carries_wtp_fields(self):
        from packages.core.nlp import extract_need_statements

        text = "I wish there was an app for this. I would pay $5/month for it."
        ideas = extract_need_statements(text)
        assert len(ideas) >= 1
        for idea in ideas:
            assert "has_wtp_signal" in idea
            assert "matched_phrases" in idea
            assert "wtp_score" in idea
        assert any(idea["has_wtp_signal"] for idea in ideas)

    def test_extract_need_statements_no_signal_stays_false(self):
        from packages.core.nlp import extract_need_statements

        text = "I wish there was an app that tracks my daily water intake."
        ideas = extract_need_statements(text)
        assert len(ideas) >= 1
        for idea in ideas:
            assert idea["has_wtp_signal"] is False
            assert idea["wtp_score"] == 0.0
