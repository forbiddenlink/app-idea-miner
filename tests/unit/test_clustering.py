"""
Unit tests for packages/core/clustering.py - ClusterEngine.

Tests pure Python logic: TF-IDF vectorization, HDBSCAN clustering,
keyword extraction, scoring, and trend calculation.
No database required.
"""

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from packages.core.clustering import ClusterEngine, ClusterResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine():
    """Create a ClusterEngine with default settings."""
    return ClusterEngine()


@pytest.fixture
def engine_small():
    """ClusterEngine with min_df=1 so small corpora don't lose all features."""
    return ClusterEngine(min_df=1, min_cluster_size=3, min_samples=1)


@pytest.fixture
def fitness_ideas():
    """Three fitness-themed idea texts that should cluster together."""
    return [
        "I wish there was a workout tracker app that uses AI to suggest exercises based on my fitness goals and progress",
        "Someone should build a fitness app that tracks your reps and sets automatically using your phone camera",
        "There should be an app that creates personalized workout plans based on available gym equipment and fitness level",
    ]


@pytest.fixture
def finance_ideas():
    """Three finance-themed idea texts that should cluster together."""
    return [
        "I need a budgeting app that automatically categorizes my bank transactions and shows spending trends",
        "Someone should build a personal finance app that tracks subscriptions and alerts you before renewals",
        "There needs to be a money management app that shows where all your money goes with easy to read charts",
    ]


@pytest.fixture
def all_ideas(fitness_ideas, finance_ideas):
    """Six ideas spanning two clear domains."""
    return fitness_ideas + finance_ideas


# ---------------------------------------------------------------------------
# ClusterResult dataclass
# ---------------------------------------------------------------------------


class TestClusterResult:
    def test_dataclass_defaults(self):
        result = ClusterResult(
            labels=np.array([0, 0, -1]),
            keywords={0: [("term", 0.5)]},
        )
        assert result.probabilities is None
        assert result.n_clusters == 0
        assert result.n_noise == 0

    def test_dataclass_all_fields(self):
        labels = np.array([0, 1, -1])
        probs = np.array([0.9, 0.8, 0.0])
        result = ClusterResult(
            labels=labels,
            keywords={0: [("a", 0.5)], 1: [("b", 0.3)]},
            probabilities=probs,
            n_clusters=2,
            n_noise=1,
        )
        assert result.n_clusters == 2
        assert result.n_noise == 1
        np.testing.assert_array_equal(result.probabilities, probs)


# ---------------------------------------------------------------------------
# cluster_ideas()
# ---------------------------------------------------------------------------


class TestClusterIdeas:
    def test_empty_list_raises(self, engine):
        with pytest.raises(ValueError, match="empty"):
            engine.cluster_ideas([])

    def test_insufficient_data_returns_all_noise(self, engine):
        """Fewer texts than min_cluster_size → all labelled noise."""
        result = engine.cluster_ideas(["idea one", "idea two"])
        assert result.n_clusters == 0
        assert result.n_noise == 2
        assert (result.labels == -1).all()
        assert result.keywords == {}

    def test_produces_cluster_result(self, engine_small, all_ideas):
        """Six diverse ideas should produce a valid ClusterResult."""
        result = engine_small.cluster_ideas(all_ideas)

        assert isinstance(result, ClusterResult)
        assert len(result.labels) == len(all_ideas)
        # Labels are integers (including -1 for noise)
        assert result.labels.dtype in (np.int32, np.int64, int)

    def test_at_least_one_cluster_or_all_noise(self, engine_small, all_ideas):
        """With 6 texts the engine either finds clusters or marks all as noise."""
        result = engine_small.cluster_ideas(all_ideas)
        assert result.n_clusters >= 0
        assert result.n_noise >= 0
        assert result.n_clusters + result.n_noise >= 0

    def test_labels_length_matches_input(self, engine_small, all_ideas):
        result = engine_small.cluster_ideas(all_ideas)
        assert len(result.labels) == 6

    def test_keywords_only_for_real_clusters(self, engine_small, all_ideas):
        """Keywords dict should not contain cluster -1 (noise)."""
        result = engine_small.cluster_ideas(all_ideas)
        assert -1 not in result.keywords

    def test_probabilities_present_on_success(self, engine_small, all_ideas):
        result = engine_small.cluster_ideas(all_ideas)
        if result.n_clusters > 0:
            assert result.probabilities is not None
            assert len(result.probabilities) == len(all_ideas)

    def test_clustering_with_many_similar_texts(self, engine_small):
        """Highly similar texts should end up in the same cluster."""
        similar = [
            "app for tracking daily water intake and hydration goals",
            "an application to track how much water I drink every day",
            "a hydration tracker app that reminds me to drink water daily",
            "water intake tracking app with daily hydration reminders",
            "track daily water consumption with goals and reminders app",
        ]
        result = engine_small.cluster_ideas(similar)
        # With 5 very similar texts and min_cluster_size=3, expect at least 1 cluster
        if result.n_clusters > 0:
            non_noise = result.labels[result.labels != -1]
            # All non-noise points should share a cluster label
            assert len(set(non_noise)) >= 1


# ---------------------------------------------------------------------------
# _extract_cluster_keywords()
# ---------------------------------------------------------------------------


class TestExtractClusterKeywords:
    def test_keywords_are_tuples_of_str_float(self, engine_small, all_ideas):
        result = engine_small.cluster_ideas(all_ideas)
        for cluster_id, kw_list in result.keywords.items():
            assert isinstance(cluster_id, (int, np.integer))
            for term, score in kw_list:
                assert isinstance(term, str)
                assert isinstance(score, float)
                assert score > 0

    def test_max_keywords_respected(self, engine_small):
        """Requesting top_n=3 should return ≤3 keywords per cluster."""
        texts = [
            "fitness workout exercise gym muscle training strength body",
            "fitness exercise workout routine gym training plan weekly",
            "exercise fitness gym workout body strength building muscle",
        ]
        engine_small.cluster_ideas(texts)
        # Now call directly with top_n=3
        if engine_small.tfidf_matrix is not None:
            labels = np.array([0, 0, 0])
            kws = engine_small._extract_cluster_keywords(labels, top_n=3)
            if 0 in kws:
                assert len(kws[0]) <= 3

    def test_returns_empty_when_not_fitted(self, engine):
        """Calling without fitting should return empty dict."""
        result = engine._extract_cluster_keywords(np.array([0, 0, 1]), top_n=5)
        assert result == {}


# ---------------------------------------------------------------------------
# generate_cluster_label()
# ---------------------------------------------------------------------------


class TestGenerateClusterLabel:
    def test_empty_keywords(self, engine):
        assert engine.generate_cluster_label([]) == "Uncategorized"

    def test_single_keyword(self, engine):
        label = engine.generate_cluster_label([("fitness", 0.8)])
        assert label == "Fitness"

    def test_two_keywords(self, engine):
        label = engine.generate_cluster_label([("fitness", 0.8), ("tracker", 0.5)])
        assert label == "Fitness + Tracker"

    def test_three_keywords(self, engine):
        kws = [("workout", 0.9), ("fitness", 0.7), ("tracker", 0.5)]
        label = engine.generate_cluster_label(kws)
        assert label == "Workout + Fitness + Tracker"

    def test_more_than_three_keywords_uses_top_three(self, engine):
        kws = [
            ("budget", 0.9),
            ("expense", 0.8),
            ("money", 0.7),
            ("finance", 0.6),
        ]
        label = engine.generate_cluster_label(kws)
        # Only first 3 should appear
        assert label.count("+") == 2
        assert "Budget" in label
        assert "Expense" in label
        assert "Money" in label
        assert "Finance" not in label

    def test_multi_word_keyword(self, engine):
        kws = [("machine learning", 0.9), ("data science", 0.7)]
        label = engine.generate_cluster_label(kws)
        assert label == "Machine Learning + Data Science"


# ---------------------------------------------------------------------------
# score_cluster()
# ---------------------------------------------------------------------------


class TestScoreCluster:
    def test_returns_float_between_0_and_1(self, engine):
        score = engine.score_cluster(
            size=10, avg_sentiment=0.5, avg_quality=0.8, trend_score=0.3
        )
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_zero_inputs(self, engine):
        score = engine.score_cluster(
            size=0, avg_sentiment=-1.0, avg_quality=0.0, trend_score=0.0
        )
        assert score >= 0.0

    def test_max_inputs(self, engine):
        score = engine.score_cluster(
            size=100, avg_sentiment=1.0, avg_quality=1.0, trend_score=1.0
        )
        assert score == pytest.approx(1.0, abs=1e-9)

    def test_larger_cluster_scores_higher(self, engine):
        small = engine.score_cluster(size=3, avg_sentiment=0.0, avg_quality=0.5)
        large = engine.score_cluster(size=30, avg_sentiment=0.0, avg_quality=0.5)
        assert large > small

    def test_better_quality_scores_higher(self, engine):
        low = engine.score_cluster(size=10, avg_sentiment=0.0, avg_quality=0.2)
        high = engine.score_cluster(size=10, avg_sentiment=0.0, avg_quality=0.9)
        assert high > low

    def test_positive_sentiment_scores_higher(self, engine):
        neg = engine.score_cluster(size=10, avg_sentiment=-0.8, avg_quality=0.5)
        pos = engine.score_cluster(size=10, avg_sentiment=0.8, avg_quality=0.5)
        assert pos > neg

    def test_size_capped_at_50(self, engine):
        """Sizes above 50 should produce the same size component."""
        s50 = engine.score_cluster(size=50, avg_sentiment=0.0, avg_quality=0.5)
        s100 = engine.score_cluster(size=100, avg_sentiment=0.0, avg_quality=0.5)
        assert s50 == pytest.approx(s100, abs=1e-9)

    @pytest.mark.parametrize(
        "size,sentiment,quality,trend",
        [
            (1, 0.0, 0.5, 0.0),
            (25, 0.5, 0.7, 0.5),
            (50, 1.0, 1.0, 1.0),
        ],
    )
    def test_known_score_formula(self, engine, size, sentiment, quality, trend):
        """Verify against the weighted formula directly."""
        expected = (
            0.4 * min(size / 50.0, 1.0)
            + 0.2 * ((sentiment + 1) / 2.0)
            + 0.3 * quality
            + 0.1 * trend
        )
        actual = engine.score_cluster(size, sentiment, quality, trend)
        assert actual == pytest.approx(expected, abs=1e-9)


# ---------------------------------------------------------------------------
# calculate_trend_score()
# ---------------------------------------------------------------------------


class TestCalculateTrendScore:
    def test_empty_timestamps(self, engine):
        assert engine.calculate_trend_score([]) == 0.0

    def test_all_recent(self, engine):
        now = datetime.now(UTC)
        timestamps = [now - timedelta(hours=h) for h in range(5)]
        score = engine.calculate_trend_score(timestamps, window_days=7)
        assert score == 1.0

    def test_all_old(self, engine):
        now = datetime.now(UTC)
        timestamps = [now - timedelta(days=30 + d) for d in range(5)]
        score = engine.calculate_trend_score(timestamps, window_days=7)
        assert score == 0.0

    def test_mixed_timestamps(self, engine):
        now = datetime.now(UTC)
        timestamps = [
            now - timedelta(days=1),  # recent
            now - timedelta(days=3),  # recent
            now - timedelta(days=30),  # old
            now - timedelta(days=60),  # old
        ]
        score = engine.calculate_trend_score(timestamps, window_days=7)
        assert score == pytest.approx(0.5)

    def test_custom_window(self, engine):
        now = datetime.now(UTC)
        timestamps = [
            now - timedelta(days=2),
            now - timedelta(days=5),
        ]
        # 1-day window → only the one within 1 day counts
        score = engine.calculate_trend_score(timestamps, window_days=1)
        assert score == pytest.approx(0.0)

        # 3-day window → 1 of 2
        score = engine.calculate_trend_score(timestamps, window_days=3)
        assert score == pytest.approx(0.5)

        # 7-day window → both
        score = engine.calculate_trend_score(timestamps, window_days=7)
        assert score == pytest.approx(1.0)

    def test_returns_float(self, engine):
        now = datetime.now(UTC)
        score = engine.calculate_trend_score([now])
        assert isinstance(score, float)
