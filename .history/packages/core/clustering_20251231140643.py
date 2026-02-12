"""
Clustering engine for grouping similar app ideas.

Uses HDBSCAN (Hierarchical Density-Based Spatial Clustering) with TF-IDF vectorization
to automatically discover clusters of related ideas without needing to specify the number
of clusters in advance.

Key components:
- TF-IDF vectorization: Converts text to numerical vectors (500 features, 1-3 grams)
- HDBSCAN: Density-based clustering that handles noise and varying cluster sizes
- Keyword extraction: Identifies top terms that characterize each cluster
- Cluster scoring: Ranks clusters by quality, size, sentiment, and trend
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import hdbscan
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

logger = logging.getLogger(__name__)


@dataclass
class ClusterResult:
    """Result of clustering operation."""

    labels: np.ndarray  # Cluster labels (-1 for noise)
    keywords: dict[int, list[tuple[str, float]]]  # cluster_id -> [(term, score), ...]
    probabilities: np.ndarray | None = None  # Cluster membership probabilities
    n_clusters: int = 0  # Number of clusters found
    n_noise: int = 0  # Number of noise points


class ClusterEngine:
    """
    Intelligent clustering engine for app ideas.

    Uses TF-IDF + HDBSCAN to discover patterns in user needs without
    requiring manual specification of cluster count.

    Configuration:
    - TF-IDF: 500 features, 1-3 grams, cosine similarity
    - HDBSCAN: min_cluster_size=3, min_samples=2, cosine metric
    """

    def __init__(
        self,
        max_features: int = 500,
        ngram_range: tuple[int, int] = (1, 3),
        min_df: int = 2,
        max_df: float = 0.85,
        min_cluster_size: int = 3,
        min_samples: int = 2,
    ):
        """
        Initialize clustering engine.

        Args:
            max_features: Maximum number of TF-IDF features
            ngram_range: Range of n-grams to extract (1-3 = unigrams, bigrams, trigrams)
            min_df: Minimum document frequency (ignore terms appearing in < min_df docs)
            max_df: Maximum document frequency (ignore terms appearing in > max_df * n_docs)
            min_cluster_size: Minimum number of points to form a cluster
            min_samples: Number of neighbors for a point to be considered a core point
        """
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples

        # Initialize components (will be fit during clustering)
        self.vectorizer: TfidfVectorizer | None = None
        self.clusterer: hdbscan.HDBSCAN | None = None
        self.tfidf_matrix = None

        logger.info(
            f"ClusterEngine initialized: max_features={max_features}, "
            f"ngram_range={ngram_range}, min_cluster_size={min_cluster_size}"
        )

    def cluster_ideas(self, texts: list[str]) -> ClusterResult:
        """
        Cluster a list of idea texts.

        Args:
            texts: List of problem statements or idea descriptions

        Returns:
            ClusterResult with labels, keywords, and metadata

        Raises:
            ValueError: If texts is empty or too small to cluster
        """
        if not texts:
            raise ValueError("Cannot cluster empty list of texts")

        if len(texts) < self.min_cluster_size:
            logger.warning(
                f"Only {len(texts)} texts provided, less than min_cluster_size={self.min_cluster_size}. "
                "All will be marked as noise."
            )
            return ClusterResult(
                labels=np.array([-1] * len(texts)), keywords={}, n_clusters=0, n_noise=len(texts)
            )

        logger.info(f"Clustering {len(texts)} idea texts...")

        # Step 1: Vectorize texts with TF-IDF
        logger.debug("Vectorizing texts with TF-IDF...")
        self.vectorizer = TfidfVectorizer(
            max_features=self.max_features,
            ngram_range=self.ngram_range,
            stop_words="english",
            min_df=self.min_df,
            max_df=self.max_df,
            sublinear_tf=True,  # Use log scaling for term frequency
            norm="l2",  # L2 normalization
        )

        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
            logger.debug(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
        except ValueError as e:
            logger.error(f"TF-IDF vectorization failed: {e}")
            # Fall back to marking all as noise
            return ClusterResult(
                labels=np.array([-1] * len(texts)), keywords={}, n_clusters=0, n_noise=len(texts)
            )

        # Step 2: Run HDBSCAN clustering
        logger.debug("Running HDBSCAN clustering...")
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric="cosine",  # Good for text data
            cluster_selection_method="eom",  # Excess of Mass (stable)
            prediction_data=True,  # Enable soft clustering
        )

        try:
            labels = self.clusterer.fit_predict(self.tfidf_matrix.toarray())
            probabilities = self.clusterer.probabilities_
        except Exception as e:
            logger.error(f"HDBSCAN clustering failed: {e}")
            return ClusterResult(
                labels=np.array([-1] * len(texts)), keywords={}, n_clusters=0, n_noise=len(texts)
            )

        # Step 3: Extract keywords for each cluster
        unique_labels = set(labels)
        n_clusters = len([l for l in unique_labels if l != -1])
        n_noise = np.sum(labels == -1)

        logger.info(f"Clustering complete: {n_clusters} clusters, {n_noise} noise points")

        keywords = self._extract_cluster_keywords(labels, top_n=10)

        return ClusterResult(
            labels=labels,
            keywords=keywords,
            probabilities=probabilities,
            n_clusters=n_clusters,
            n_noise=n_noise,
        )

    def _extract_cluster_keywords(
        self, labels: np.ndarray, top_n: int = 10
    ) -> dict[int, list[tuple[str, float]]]:
        """
        Extract top keywords for each cluster.

        Uses average TF-IDF scores across all documents in a cluster
        to identify the most characteristic terms.

        Args:
            labels: Cluster labels for each document
            top_n: Number of top keywords to extract per cluster

        Returns:
            Dictionary mapping cluster_id to list of (term, score) tuples
        """
        if self.tfidf_matrix is None or self.vectorizer is None:
            logger.error("Cannot extract keywords: vectorizer not fitted")
            return {}

        keywords = {}
        feature_names = self.vectorizer.get_feature_names_out()

        for cluster_id in set(labels):
            if cluster_id == -1:  # Skip noise
                continue

            # Get all documents in this cluster
            cluster_mask = labels == cluster_id
            cluster_vectors = self.tfidf_matrix[cluster_mask]

            # Average TF-IDF scores across cluster
            avg_scores = np.asarray(cluster_vectors.mean(axis=0)).flatten()

            # Get top N terms
            top_indices = avg_scores.argsort()[-top_n:][::-1]

            cluster_keywords = [
                (feature_names[i], float(avg_scores[i]))
                for i in top_indices
                if avg_scores[i] > 0  # Only include non-zero scores
            ]

            keywords[cluster_id] = cluster_keywords
            logger.debug(
                f"Cluster {cluster_id} top keywords: {[kw[0] for kw in cluster_keywords[:5]]}"
            )

        return keywords

    def generate_cluster_label(
        self, keywords: list[tuple[str, float]], texts: list[str] | None = None
    ) -> str:
        """
        Generate a human-readable label for a cluster.

        Strategy: Use top 3 keywords, capitalize and join with ' + '

        Args:
            keywords: List of (term, score) tuples
            texts: Optional list of texts in cluster (for alternative labeling)

        Returns:
            Human-readable cluster label
        """
        if not keywords:
            return "Uncategorized"

        # Take top 3 keywords
        top_terms = [kw[0] for kw in keywords[:3]]

        # Capitalize and join
        label = " + ".join(term.title() for term in top_terms)

        return label

    def score_cluster(
        self, size: int, avg_sentiment: float, avg_quality: float, trend_score: float = 0.0
    ) -> float:
        """
        Calculate composite quality score for a cluster.

        Combines multiple factors:
        - Size: Larger clusters = more demand (40% weight)
        - Sentiment: Positive sentiment = easier to build (20% weight)
        - Quality: Clear problem statements (30% weight)
        - Trend: Growing interest over time (10% weight)

        Args:
            size: Number of ideas in cluster
            avg_sentiment: Average sentiment score (-1 to 1)
            avg_quality: Average quality score (0 to 1)
            trend_score: Temporal growth score (0 to 1)

        Returns:
            Composite score from 0 to 1
        """
        # Normalize size (cap at 50 ideas)
        size_score = min(size / 50.0, 1.0)

        # Normalize sentiment (-1 to 1 → 0 to 1)
        sentiment_score = (avg_sentiment + 1) / 2.0

        # Quality is already 0-1
        quality_score = avg_quality

        # Trend is already 0-1

        # Weighted combination
        weights = {"size": 0.4, "sentiment": 0.2, "quality": 0.3, "trend": 0.1}

        total_score = (
            weights["size"] * size_score
            + weights["sentiment"] * sentiment_score
            + weights["quality"] * quality_score
            + weights["trend"] * trend_score
        )

        return float(total_score)

    def calculate_trend_score(self, idea_timestamps: list[datetime], window_days: int = 7) -> float:
        """
        Calculate trend score based on temporal distribution of ideas.

        Higher score = more recent ideas, indicating growing interest.

        Args:
            idea_timestamps: List of creation/extraction timestamps
            window_days: Time window to consider for trend (default 7 days)

        Returns:
            Trend score from 0 to 1
        """
        if not idea_timestamps:
            return 0.0

        now = datetime.utcnow()
        cutoff = now - timedelta(days=window_days)

        # Count recent vs. total
        recent_count = sum(1 for ts in idea_timestamps if ts >= cutoff)
        total_count = len(idea_timestamps)

        # Trend score is proportion of recent ideas
        trend_score = recent_count / total_count if total_count > 0 else 0.0

        return float(trend_score)


# Singleton instance for convenience
_cluster_engine: ClusterEngine | None = None


def get_cluster_engine(**kwargs) -> ClusterEngine:
    """
    Get or create singleton cluster engine instance.

    Args:
        **kwargs: Optional configuration parameters for ClusterEngine

    Returns:
        Singleton ClusterEngine instance
    """
    global _cluster_engine

    if _cluster_engine is None:
        _cluster_engine = ClusterEngine(**kwargs)

    return _cluster_engine


# Convenience functions
def cluster_ideas(texts: list[str], **kwargs) -> ClusterResult:
    """
    Cluster a list of idea texts (convenience function).

    Args:
        texts: List of problem statements
        **kwargs: Optional clustering parameters

    Returns:
        ClusterResult
    """
    engine = get_cluster_engine(**kwargs)
    return engine.cluster_ideas(texts)


def extract_keywords(
    texts: list[str], labels: np.ndarray, top_n: int = 10
) -> dict[int, list[tuple[str, float]]]:
    """
    Extract keywords from clustered texts (convenience function).

    Args:
        texts: List of texts
        labels: Cluster labels
        top_n: Number of keywords per cluster

    Returns:
        Dictionary of cluster keywords
    """
    engine = get_cluster_engine()
    # Re-vectorize if needed
    if engine.tfidf_matrix is None:
        engine.vectorizer = TfidfVectorizer(
            max_features=engine.max_features, ngram_range=engine.ngram_range, stop_words="english"
        )
        engine.tfidf_matrix = engine.vectorizer.fit_transform(texts)

    return engine._extract_cluster_keywords(labels, top_n=top_n)
