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
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import hdbscan
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from packages.core import env_is_truthy

logger = logging.getLogger(__name__)


@dataclass
class HierarchicalTopic:
    """Represents a topic in the hierarchy."""

    topic_id: int
    parent_id: int | None
    keywords: list[str]
    idea_count: int
    children: list["HierarchicalTopic"] | None = None


@dataclass
class ClusterResult:
    """Result of clustering operation."""

    labels: np.ndarray  # Cluster labels (-1 for noise)
    keywords: dict[int, list[tuple[str, float]]]  # cluster_id -> [(term, score), ...]
    probabilities: np.ndarray | None = None  # Cluster membership probabilities
    n_clusters: int = 0  # Number of clusters found
    n_noise: int = 0  # Number of noise points
    hierarchical_topics: list[HierarchicalTopic] | None = None  # BERTopic hierarchy
    topic_info: dict | None = None  # BERTopic topic metadata


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
        use_embeddings: bool = False,
        use_bertopic: bool = False,
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
            use_embeddings: If True, use sentence-transformers for vectorization instead of TF-IDF
            use_bertopic: If True, use BERTopic for clustering with hierarchical topics
        """
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.use_embeddings = use_embeddings
        self.use_bertopic = use_bertopic

        # Initialize components (will be fit during clustering)
        self.vectorizer: TfidfVectorizer | None = None
        self.clusterer: hdbscan.HDBSCAN | None = None
        self.tfidf_matrix = None
        self.embedding_matrix: np.ndarray | None = None
        self.bertopic_model = None
        self._last_texts: list[str] | None = None  # For hierarchy extraction

        logger.info(
            f"ClusterEngine initialized: max_features={max_features}, "
            f"ngram_range={ngram_range}, min_cluster_size={min_cluster_size}, "
            f"use_embeddings={use_embeddings}, use_bertopic={use_bertopic}"
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
                labels=np.array([-1] * len(texts)),
                keywords={},
                n_clusters=0,
                n_noise=len(texts),
            )

        # Use BERTopic if enabled
        if self.use_bertopic:
            return self._cluster_with_bertopic(texts)

        logger.info(f"Clustering {len(texts)} idea texts...")

        # Step 1a: Always run TF-IDF (needed for keyword extraction)
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
                labels=np.array([-1] * len(texts)),
                keywords={},
                n_clusters=0,
                n_noise=len(texts),
            )

        # Step 1b: Optionally compute sentence embeddings for clustering
        clustering_matrix = self.tfidf_matrix.toarray()
        self.embedding_matrix = None

        if self.use_embeddings:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(
                    "Using sentence embeddings (all-MiniLM-L6-v2) for clustering..."
                )
                model = SentenceTransformer("all-MiniLM-L6-v2")
                embeddings = model.encode(texts, show_progress_bar=False)
                # L2 normalize embeddings
                norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
                norms[norms == 0] = 1  # Avoid division by zero
                embeddings = embeddings / norms
                self.embedding_matrix = embeddings
                clustering_matrix = embeddings
                logger.debug(f"Embedding matrix shape: {embeddings.shape}")
            except ImportError:
                logger.warning(
                    "sentence-transformers not installed. "
                    "Falling back to TF-IDF for clustering. "
                    "Install with: pip install sentence-transformers"
                )

        # Step 2: Run HDBSCAN clustering
        logger.debug("Running HDBSCAN clustering...")
        self.clusterer = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric="euclidean",  # Euclidean works well with L2-normalized vectors
            cluster_selection_method="eom",  # Excess of Mass (stable)
            prediction_data=True,  # Enable soft clustering
        )

        try:
            labels = self.clusterer.fit_predict(clustering_matrix)
            probabilities = self.clusterer.probabilities_
        except Exception as e:
            logger.error(f"HDBSCAN clustering failed: {e}")
            return ClusterResult(
                labels=np.array([-1] * len(texts)),
                keywords={},
                n_clusters=0,
                n_noise=len(texts),
            )

        # Step 3: Extract keywords for each cluster
        unique_labels = set(labels)
        n_clusters = len([lbl for lbl in unique_labels if lbl != -1])
        n_noise = np.sum(labels == -1)

        logger.info(
            f"Clustering complete: {n_clusters} clusters, {n_noise} noise points"
        )

        keywords = self._extract_cluster_keywords(labels, top_n=10)

        return ClusterResult(
            labels=labels,
            keywords=keywords,
            probabilities=probabilities,
            n_clusters=n_clusters,
            n_noise=n_noise,
        )

    def _cluster_with_bertopic(self, texts: list[str]) -> ClusterResult:
        """
        Cluster using BERTopic for better topic coherence and hierarchical topics.

        Args:
            texts: List of problem statements or idea descriptions

        Returns:
            ClusterResult with labels, keywords, hierarchy, and metadata
        """
        try:
            from bertopic import BERTopic
            from sentence_transformers import SentenceTransformer
            from umap import UMAP
        except ImportError as e:
            logger.warning(
                f"BERTopic dependencies not installed: {e}. "
                "Falling back to HDBSCAN clustering."
            )
            self.use_bertopic = False
            return self.cluster_ideas(texts)

        logger.info(f"Clustering {len(texts)} texts with BERTopic...")
        self._last_texts = texts

        # Initialize embedding model
        embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        # Configure UMAP for dimensionality reduction
        umap_model = UMAP(
            n_components=5,
            n_neighbors=15,
            min_dist=0.0,
            metric="cosine",
            random_state=42,
        )

        # Configure HDBSCAN for BERTopic
        hdbscan_model = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples,
            metric="euclidean",
            cluster_selection_method="eom",
            prediction_data=True,
        )

        # Initialize BERTopic
        self.bertopic_model = BERTopic(
            embedding_model=embedding_model,
            umap_model=umap_model,
            hdbscan_model=hdbscan_model,
            nr_topics="auto",
            calculate_probabilities=True,
            verbose=False,
        )

        try:
            # Fit and transform
            topics, probs = self.bertopic_model.fit_transform(texts)
            topics = np.array(topics)
            probs = np.array(probs) if probs is not None else None

            # Get topic info
            topic_info = self.bertopic_model.get_topic_info()

            # Extract keywords for each topic
            keywords = {}
            for topic_id in set(topics):
                if topic_id == -1:
                    continue
                topic_words = self.bertopic_model.get_topic(topic_id)
                if topic_words:
                    keywords[topic_id] = [
                        (word, float(score)) for word, score in topic_words[:10]
                    ]

            # Count clusters and noise
            unique_topics = set(topics)
            n_clusters = len([t for t in unique_topics if t != -1])
            n_noise = int(np.sum(topics == -1))

            # Build hierarchical topics
            hierarchical_topics = self._extract_bertopic_hierarchy(texts)

            logger.info(
                f"BERTopic clustering complete: {n_clusters} topics, {n_noise} outliers"
            )

            return ClusterResult(
                labels=topics,
                keywords=keywords,
                probabilities=probs,
                n_clusters=n_clusters,
                n_noise=n_noise,
                hierarchical_topics=hierarchical_topics,
                topic_info=topic_info.to_dict() if topic_info is not None else None,
            )

        except Exception as e:
            logger.error(f"BERTopic clustering failed: {e}", exc_info=True)
            return ClusterResult(
                labels=np.array([-1] * len(texts)),
                keywords={},
                n_clusters=0,
                n_noise=len(texts),
            )

    def _extract_bertopic_hierarchy(
        self, texts: list[str]
    ) -> list[HierarchicalTopic] | None:
        """
        Extract hierarchical topic structure from BERTopic model.

        Returns:
            List of HierarchicalTopic objects representing the topic tree
        """
        if self.bertopic_model is None:
            return None

        try:
            # Get hierarchical topics DataFrame
            hierarchical_df = self.bertopic_model.hierarchical_topics(texts)

            if hierarchical_df is None or hierarchical_df.empty:
                return None

            # Build topic hierarchy
            topics_dict: dict[int, HierarchicalTopic] = {}
            topic_info = self.bertopic_model.get_topic_info()

            # Create nodes for each topic
            for topic_id in topic_info["Topic"].values:
                if topic_id == -1:
                    continue

                topic_words = self.bertopic_model.get_topic(topic_id)
                keywords = [word for word, _ in topic_words[:5]] if topic_words else []

                # Count docs in this topic
                topic_count = int(
                    topic_info[topic_info["Topic"] == topic_id]["Count"].iloc[0]
                )

                topics_dict[topic_id] = HierarchicalTopic(
                    topic_id=topic_id,
                    parent_id=None,
                    keywords=keywords,
                    idea_count=topic_count,
                    children=[],
                )

            # Parse hierarchy to establish parent-child relationships
            # The hierarchical_df has columns like Parent_ID, Parent_Name, Topics, etc.
            if "Parent_ID" in hierarchical_df.columns:
                for _, row in hierarchical_df.iterrows():
                    parent_id = row.get("Parent_ID")
                    child_topics = row.get("Topics", [])

                    if isinstance(child_topics, list):
                        for child_id in child_topics:
                            if child_id in topics_dict and parent_id != child_id:
                                topics_dict[child_id].parent_id = parent_id

            # Return root topics (those without parents) with their children populated
            root_topics = [t for t in topics_dict.values() if t.parent_id is None]

            # Populate children
            for topic in topics_dict.values():
                if topic.parent_id is not None and topic.parent_id in topics_dict:
                    parent = topics_dict[topic.parent_id]
                    if parent.children is None:
                        parent.children = []
                    parent.children.append(topic)

            return root_topics if root_topics else list(topics_dict.values())

        except Exception as e:
            logger.warning(f"Failed to extract topic hierarchy: {e}")
            return None

    def get_topic_hierarchy(self) -> list[HierarchicalTopic] | None:
        """
        Get the hierarchical topic structure from the last clustering operation.

        Returns:
            List of root HierarchicalTopic objects, or None if not available
        """
        if self.bertopic_model is None or self._last_texts is None:
            return None

        return self._extract_bertopic_hierarchy(self._last_texts)

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
        self,
        keywords: list[tuple[str, float]],
        texts: list[str] | None = None,
        label_strategy: str = "keywords",
    ) -> str:
        """
        Generate a human-readable label for a cluster.

        Args:
            keywords: List of (term, score) tuples
            texts: Optional list of texts in cluster (used by "representative" strategy)
            label_strategy: "keywords" (top 3 keywords joined) or "representative"
                (shortest representative idea under 60 chars, or truncated centroid-closest text)

        Returns:
            Human-readable cluster label
        """
        if not keywords:
            return "Uncategorized"

        if label_strategy == "representative" and texts:
            return self._representative_label(texts)

        # Default "keywords" strategy: top 3 keywords joined
        top_terms = [kw[0] for kw in keywords[:3]]
        label = " + ".join(term.title() for term in top_terms)
        return label

    # Common filler prefixes that add no label value
    _FILLER_PREFIXES: tuple[str, ...] = (
        "i wish there was an app that ",
        "i wish there was an app for ",
        "i wish there was an app to ",
        "i wish there was an app ",
        "there should be an app that ",
        "there should be an app for ",
        "there should be an app to ",
        "there should be an app ",
        "why isn't there an app that ",
        "why isn't there an app for ",
        "why isn't there an app to ",
        "why isn't there an app ",
        "why is there no app that ",
        "why is there no app for ",
        "why is there no app ",
        "someone should build an app that ",
        "someone should build an app for ",
        "someone should build an app to ",
        "someone should build an app ",
        "i want an app that ",
        "i want an app for ",
        "i want an app to ",
        "i want an app ",
        "there needs to be an app that ",
        "there needs to be an app for ",
        "there needs to be an app ",
        "why don't we have an app that ",
        "why don't we have an app for ",
        "why don't we have an app ",
        "why don't we have an app that ",
    )

    def _strip_filler_prefix(self, text: str) -> str:
        """Strip common 'I wish there was an app' filler prefixes from text."""
        lower = text.lower()
        for prefix in self._FILLER_PREFIXES:
            if lower.startswith(prefix):
                remainder = text[len(prefix) :].strip()
                if remainder:
                    return remainder[0].upper() + remainder[1:]
        return text

    def _representative_label(self, texts: list[str], max_length: int = 60) -> str:
        """
        Pick the most representative text from a cluster as the label.

        Strategy: Find the text closest to the cluster centroid. If any cluster
        text fits under max_length, prefer the shortest one among the top-3
        closest-to-centroid; otherwise truncate the closest.

        Args:
            texts: Texts belonging to this cluster
            max_length: Maximum label length

        Returns:
            Representative label string
        """
        if len(texts) == 1:
            text = self._strip_filler_prefix(texts[0])
            return text if len(text) <= max_length else text[: max_length - 3] + "..."

        # Vectorize cluster texts with a simple TF-IDF to find centroid
        try:
            vec = TfidfVectorizer(stop_words="english", norm="l2")
            matrix = vec.fit_transform(texts).toarray()
        except ValueError:
            return (
                texts[0][: max_length - 3] + "..."
                if len(texts[0]) > max_length
                else texts[0]
            )

        centroid = matrix.mean(axis=0)
        # Cosine similarity (vectors are L2-normed, so dot product = cosine)
        similarities = matrix @ centroid
        ranked_indices = np.argsort(similarities)[::-1]

        # Among top-3 closest to centroid, prefer one that fits under max_length
        top_candidates = ranked_indices[: min(3, len(ranked_indices))]
        for idx in top_candidates:
            cleaned = self._strip_filler_prefix(texts[idx])
            if len(cleaned) <= max_length:
                return cleaned

        # Truncate the closest-to-centroid text
        best = self._strip_filler_prefix(texts[ranked_indices[0]])
        return best if len(best) <= max_length else best[: max_length - 3] + "..."

    def score_cluster(
        self,
        size: int,
        avg_sentiment: float,
        avg_quality: float,
        trend_score: float = 0.0,
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

    def calculate_trend_score(
        self, idea_timestamps: list[datetime], window_days: int = 7
    ) -> float:
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

        # Use timezone-aware datetime
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=window_days)

        # Count recent vs. total
        recent_count = sum(1 for ts in idea_timestamps if ts >= cutoff)
        total_count = len(idea_timestamps)

        # Trend score is proportion of recent ideas
        trend_score = recent_count / total_count if total_count > 0 else 0.0

        return float(trend_score)

    def calculate_trend_velocity(
        self, timestamps: list[datetime], window_days: int = 7
    ) -> float:
        """
        Calculate week-over-week growth rate.

        Args:
            timestamps: List of creation timestamps
            window_days: Time window for comparison

        Returns:
            Velocity score from 0 to 1 (capped at 5x growth = 1.0)
        """
        if not timestamps:
            return 0.0

        now = datetime.now(UTC)
        this_week = len(
            [t for t in timestamps if t > now - timedelta(days=window_days)]
        )
        last_week = len(
            [
                t
                for t in timestamps
                if now - timedelta(days=window_days * 2)
                < t
                <= now - timedelta(days=window_days)
            ]
        )

        if last_week == 0:
            return 1.0 if this_week > 0 else 0.0

        velocity = this_week / last_week
        return min(velocity, 5.0) / 5.0  # Normalize to 0-1

    def assign_to_existing_clusters(
        self,
        new_texts: list[str],
        cluster_centroids: dict[str, np.ndarray],
        similarity_threshold: float = 0.7,
    ) -> dict[int, str | None]:
        """
        Assign new ideas to existing clusters by embedding similarity.

        This enables incremental clustering - assigning new ideas to existing clusters
        without needing a full re-cluster operation.

        Args:
            new_texts: List of new idea texts to assign
            cluster_centroids: Dict mapping cluster_id (str) to centroid embedding (np array)
            similarity_threshold: Minimum cosine similarity to assign (default 0.7)

        Returns:
            Dict mapping text index to cluster_id (or None if no match)
        """
        if not new_texts or not cluster_centroids:
            return dict.fromkeys(range(len(new_texts)))

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Cannot do incremental assignment."
            )
            return dict.fromkeys(range(len(new_texts)))

        # Generate embeddings for new texts
        logger.info(f"Generating embeddings for {len(new_texts)} new ideas...")
        model = SentenceTransformer("all-MiniLM-L6-v2")
        new_embeddings = model.encode(new_texts, normalize_embeddings=True)

        assignments: dict[int, str | None] = {}

        for i, embedding in enumerate(new_embeddings):
            best_cluster_id = None
            best_similarity = 0.0

            for cluster_id, centroid in cluster_centroids.items():
                # Cosine similarity (embeddings are normalized, so dot product = cosine)
                similarity = float(np.dot(embedding, centroid))

                if similarity > best_similarity and similarity >= similarity_threshold:
                    best_similarity = similarity
                    best_cluster_id = cluster_id

            assignments[i] = best_cluster_id

            if best_cluster_id:
                logger.debug(
                    f"Assigned text {i} to cluster {best_cluster_id} "
                    f"(similarity: {best_similarity:.3f})"
                )
            else:
                logger.debug(
                    f"Text {i} did not match any cluster (best: {best_similarity:.3f})"
                )

        assigned_count = sum(1 for v in assignments.values() if v is not None)
        logger.info(
            f"Incremental assignment complete: {assigned_count}/{len(new_texts)} "
            f"assigned to existing clusters"
        )

        return assignments


# Singleton instance for convenience
_cluster_engine: ClusterEngine | None = None


def get_cluster_engine(**kwargs) -> ClusterEngine:
    """
    Get or create singleton cluster engine instance.

    Reads environment variables to configure the engine:
    - ``USE_SENTENCE_EMBEDDINGS``: Enable sentence-transformer embeddings
    - ``USE_BERTOPIC``: Enable BERTopic for clustering with hierarchical topics

    Explicit kwargs always take precedence over environment variables.

    Args:
        **kwargs: Optional configuration parameters for ClusterEngine

    Returns:
        Singleton ClusterEngine instance
    """
    global _cluster_engine

    if _cluster_engine is None:
        if "use_embeddings" not in kwargs:
            kwargs["use_embeddings"] = env_is_truthy("USE_SENTENCE_EMBEDDINGS")
        if "use_bertopic" not in kwargs:
            kwargs["use_bertopic"] = env_is_truthy("USE_BERTOPIC")
        _cluster_engine = ClusterEngine(**kwargs)

    return _cluster_engine


# Convenience functions
def cluster_ideas(texts: list[str], **kwargs) -> ClusterResult:
    """
    Cluster a list of idea texts (convenience function).

    Args:
        texts: List of problem statements
        **kwargs: Optional clustering parameters (including use_embeddings)

    Returns:
        ClusterResult
    """
    # Reset singleton when config changes to avoid stale state
    global _cluster_engine
    if kwargs:
        _cluster_engine = None
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
            max_features=engine.max_features,
            ngram_range=engine.ngram_range,
            stop_words="english",
        )
        engine.tfidf_matrix = engine.vectorizer.fit_transform(texts)

    return engine._extract_cluster_keywords(labels, top_n=top_n)
