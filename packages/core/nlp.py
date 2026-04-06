"""
Natural Language Processing utilities for App-Idea Miner.
Handles text extraction, sentiment analysis, quality scoring, and embedding generation.
"""

import logging
import os
import re
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

logger = logging.getLogger(__name__)

# Embedding model singleton
_embedding_model = None

# Embedding dimension for all-MiniLM-L6-v2
EMBEDDING_DIM = 384


def get_embedding_model():
    """
    Get or create singleton embedding model.

    Returns:
        SentenceTransformer model instance, or None if unavailable
    """
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer

            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Loaded embedding model: all-MiniLM-L6-v2")
        except ImportError:
            logger.warning(
                "sentence-transformers not installed. Embeddings disabled. "
                "Install with: pip install sentence-transformers"
            )
            return None
    return _embedding_model


def generate_embedding(text: str) -> list[float] | None:
    """
    Generate 384-dimensional embedding for text.

    Uses all-MiniLM-L6-v2 model which produces normalized embeddings
    suitable for cosine similarity comparisons.

    Args:
        text: Text to embed

    Returns:
        List of 384 floats (normalized embedding), or None if model unavailable
    """
    if os.getenv("GENERATE_EMBEDDINGS", "").lower() not in ("1", "true", "yes"):
        return None

    model = get_embedding_model()
    if model is None:
        return None

    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None


def generate_embeddings_batch(texts: list[str]) -> list[list[float] | None]:
    """
    Generate embeddings for multiple texts efficiently.

    Uses batch encoding for better performance.

    Args:
        texts: List of texts to embed

    Returns:
        List of embeddings (384 floats each), None entries for failures
    """
    if os.getenv("GENERATE_EMBEDDINGS", "").lower() not in ("1", "true", "yes"):
        return [None] * len(texts)

    model = get_embedding_model()
    if model is None:
        return [None] * len(texts)

    try:
        embeddings = model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return [emb.tolist() for emb in embeddings]
    except Exception as e:
        logger.error(f"Error generating batch embeddings: {e}")
        return [None] * len(texts)


# LLM extraction state
_llm_call_count = 0
_LLM_MAX_CALLS_PER_CYCLE = 100  # Cost control: max LLM calls per ingestion cycle


def reset_llm_call_count():
    """Reset LLM call counter (call at start of ingestion cycle)."""
    global _llm_call_count
    _llm_call_count = 0


def extract_ideas_llm(text: str) -> list[dict]:
    """
    Extract ideas using Claude Haiku for better recall.

    Uses LLM to identify app ideas and pain points that regex patterns miss.
    Includes cost controls: skips if text too short/long or quota exceeded.

    Args:
        text: Text content to analyze

    Returns:
        List of dicts with problem_statement, target_user, urgency, confidence
    """
    global _llm_call_count

    # Check if LLM extraction is enabled
    if os.getenv("USE_LLM_EXTRACTION", "").lower() not in ("1", "true", "yes"):
        return []

    # Cost control: skip if quota exceeded
    if _llm_call_count >= _LLM_MAX_CALLS_PER_CYCLE:
        logger.debug("LLM call quota exceeded for this cycle")
        return []

    # Cost control: skip if text too short or too long
    text_len = len(text)
    if text_len < 50:
        logger.debug("Text too short for LLM extraction")
        return []
    if text_len > 5000:
        logger.debug("Text too long for LLM extraction, truncating")
        text = text[:5000]

    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, LLM extraction disabled")
        return []

    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": f"""Analyze this post and extract any app/software ideas or user pain points.
Look for:
- Explicit wishes for apps or tools
- Frustrations that could be solved by software
- Feature requests or improvements to existing tools
- Unmet needs that suggest opportunities

Post:
{text}

Return a JSON array (no markdown, just raw JSON):
[{{
  "problem_statement": "clear description of the problem or need",
  "target_user": "who has this problem",
  "urgency": "low|medium|high",
  "confidence": 0.0-1.0
}}]

Return empty array [] if no clear app ideas or pain points found.
Only include items where confidence >= 0.5.""",
                }
            ],
        )

        _llm_call_count += 1

        # Parse JSON response
        import json

        response_text = response.content[0].text.strip()

        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            # Extract JSON from code block
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.startswith("```") and not in_json:
                    in_json = True
                    continue
                elif line.startswith("```") and in_json:
                    break
                elif in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        ideas = json.loads(response_text)

        # Validate and filter
        valid_ideas = []
        for idea in ideas:
            if isinstance(idea, dict) and "problem_statement" in idea:
                confidence = idea.get("confidence", 0.5)
                if confidence >= 0.5:
                    valid_ideas.append(
                        {
                            "problem_statement": idea["problem_statement"],
                            "target_user": idea.get("target_user", ""),
                            "urgency": idea.get("urgency", "medium"),
                            "confidence": confidence,
                            "source": "llm",
                        }
                    )

        logger.debug(f"LLM extracted {len(valid_ideas)} ideas from text")
        return valid_ideas

    except ImportError:
        logger.warning(
            "anthropic package not installed. LLM extraction disabled. "
            "Install with: pip install anthropic"
        )
        return []
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        return []


def _merge_ideas(regex_ideas: list[dict], llm_ideas: list[dict]) -> list[dict]:
    """
    Merge ideas from regex and LLM extraction, removing duplicates.

    Uses text similarity to detect duplicates between sources.

    Args:
        regex_ideas: Ideas from regex extraction
        llm_ideas: Ideas from LLM extraction

    Returns:
        Merged list of unique ideas
    """
    if not llm_ideas:
        return regex_ideas
    if not regex_ideas:
        return [
            {"statement": idea["problem_statement"], "context": "", **idea}
            for idea in llm_ideas
        ]

    merged = list(regex_ideas)
    seen_statements = {idea["statement"].lower() for idea in regex_ideas}

    for llm_idea in llm_ideas:
        statement = llm_idea["problem_statement"]
        statement_lower = statement.lower()

        # Check for duplicates using substring matching
        is_duplicate = False
        for seen in seen_statements:
            # If one is substring of other (>50% overlap), consider duplicate
            if statement_lower in seen or seen in statement_lower:
                is_duplicate = True
                break
            # Simple word overlap check
            seen_words = set(seen.split())
            new_words = set(statement_lower.split())
            if (
                len(seen_words & new_words) / max(len(seen_words), len(new_words), 1)
                > 0.6
            ):
                is_duplicate = True
                break

        if not is_duplicate:
            merged.append(
                {
                    "statement": statement,
                    "context": "",
                    "source": "llm",
                    "confidence": llm_idea.get("confidence", 0.5),
                    "target_user": llm_idea.get("target_user", ""),
                    "urgency": llm_idea.get("urgency", "medium"),
                }
            )
            seen_statements.add(statement_lower)

    return merged


class TextProcessor:
    """
    Processes raw text to extract user needs and analyze content.
    """

    # Regex patterns for need statement extraction
    NEED_PATTERNS = [
        # "I wish there was/were an/a app..."
        r"I wish there (?:was|were) (?:an? )?(.+?)(?:[.!?]|$)",
        r"I wish we had (?:an? )?(.+?)(?:[.!?]|$)",
        # "We/I need an/a app..."
        r"(?:We|I) need (?:an? )?(.+?)(?:[.!?]|$)",
        r"(?:We|I) want (?:an? )?(.+?)(?:[.!?]|$)",
        # "Why isn't/doesn't there an/a app..."
        r"Why (?:isn't|doesn't|don't) there (?:an? )?(.+?)\?",
        r"Why (?:is|does) no one make (?:an? )?(.+?)\?",
        # "There should be an/a app..."
        r"There should be (?:an? )?(.+?)(?:[.!?]|$)",
        r"Someone (?:should|needs to) (?:build|make|create) (?:an? )?(.+?)(?:[.!?]|$)",
        # "App idea: ..."
        r"App idea:? ?(.+?)(?:[.!?]|$)",
        r"App for (.+?)(?:[.!?]|$)",
        # Questions about apps
        r"(?:Is|Are) there (?:any )?apps? (?:that|to) (.+?)\?",
        r"(?:Does|Do) anyone know (?:of )?(?:an? )?apps? (?:that|to) (.+?)\?",
    ]

    def __init__(self):
        """Initialize text processor with sentiment analyzer."""
        self.sentiment_analyzer = SentimentIntensityAnalyzer()

    def extract_need_statements(
        self, text: str, context_chars: int = 100
    ) -> list[dict[str, str]]:
        """
        Extract need statements from text using regex patterns.

        Args:
            text: Raw text content
            context_chars: Number of characters of surrounding context to include

        Returns:
            List of dicts with 'statement' and 'context' keys
        """
        statements = []
        seen = set()  # Avoid duplicates

        # Split into sentences for better processing
        sentences = self._split_sentences(text)

        for sentence in sentences:
            for pattern in self.NEED_PATTERNS:
                matches = re.finditer(pattern, sentence, re.IGNORECASE)

                for match in matches:
                    statement = match.group(1).strip()

                    # Skip if too short or already seen
                    if len(statement) < 10 or statement.lower() in seen:
                        continue

                    # Clean up the statement
                    statement = self._clean_statement(statement)

                    # Extract context
                    context = self._extract_context(
                        text, match.start(), match.end(), context_chars
                    )

                    statements.append(
                        {
                            "statement": statement,
                            "context": context,
                        }
                    )

                    seen.add(statement.lower())

        return statements

    def _split_sentences(self, text: str) -> list[str]:
        """
        Split text into sentences.

        Args:
            text: Input text

        Returns:
            List of sentences
        """
        # Simple sentence splitting (can be improved with nltk.sent_tokenize)
        sentences = re.split(r"[.!?]+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _clean_statement(self, statement: str) -> str:
        """
        Clean extracted statement.

        Args:
            statement: Raw extracted statement

        Returns:
            Cleaned statement
        """
        # Remove leading articles
        statement = re.sub(r"^(?:an?|the)\s+", "", statement, flags=re.IGNORECASE)

        # Remove trailing punctuation
        statement = statement.rstrip(".,;:!?")

        # Normalize whitespace
        statement = re.sub(r"\s+", " ", statement).strip()

        return statement

    def _extract_context(
        self, text: str, start: int, end: int, context_chars: int
    ) -> str:
        """
        Extract surrounding context from text.

        Args:
            text: Full text
            start: Match start position
            end: Match end position
            context_chars: Characters to include before/after

        Returns:
            Context string
        """
        context_start = max(0, start - context_chars)
        context_end = min(len(text), end + context_chars)

        context = text[context_start:context_end].strip()

        # Add ellipsis if truncated
        if context_start > 0:
            context = "..." + context
        if context_end < len(text):
            context = context + "..."

        return context

    def analyze_sentiment(self, text: str) -> dict[str, Any]:
        """
        Analyze sentiment using VADER.

        Args:
            text: Text to analyze

        Returns:
            Dict with sentiment label, score, and emotion breakdown
        """
        # Get VADER scores
        scores = self.sentiment_analyzer.polarity_scores(text)
        compound = scores["compound"]

        # Classify sentiment
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        # Detect emotions (simple keyword-based)
        emotions = self._detect_emotions(text.lower())

        return {
            "label": label,
            "score": compound,
            "positive": scores["pos"],
            "neutral": scores["neu"],
            "negative": scores["neg"],
            "emotions": emotions,
        }

    def _detect_emotions(self, text: str) -> dict[str, float]:
        """
        Detect emotions using keyword matching.

        Args:
            text: Text to analyze (lowercase)

        Returns:
            Dict of emotion scores (0-1)
        """
        emotions = {
            "frustration": 0.0,
            "hope": 0.0,
            "urgency": 0.0,
        }

        # Frustration keywords
        frustration_words = [
            "annoying",
            "frustrated",
            "annoyed",
            "hate",
            "tired of",
            "sick of",
            "struggle",
            "difficult",
            "hard",
            "pain",
            "painful",
        ]
        frustration_count = sum(1 for word in frustration_words if word in text)
        emotions["frustration"] = min(frustration_count / 3.0, 1.0)

        # Hope keywords
        hope_words = [
            "wish",
            "hope",
            "would love",
            "dream",
            "imagine",
            "excited",
            "looking forward",
            "can't wait",
            "hopefully",
        ]
        hope_count = sum(1 for word in hope_words if word in text)
        emotions["hope"] = min(hope_count / 3.0, 1.0)

        # Urgency keywords
        urgency_words = [
            "need",
            "must",
            "asap",
            "urgent",
            "immediately",
            "now",
            "critical",
            "essential",
            "crucial",
            "desperately",
        ]
        urgency_count = sum(1 for word in urgency_words if word in text)
        emotions["urgency"] = min(urgency_count / 3.0, 1.0)

        return emotions

    def calculate_quality_score(self, text: str) -> float:
        """
        Calculate quality score based on specificity, actionability, and clarity.

        Args:
            text: Problem statement or idea text

        Returns:
            Quality score (0-1)
        """
        scores = {
            "specificity": self._score_specificity(text),
            "actionability": self._score_actionability(text),
            "clarity": self._score_clarity(text),
        }

        # Weighted average
        weights = {
            "specificity": 0.4,
            "actionability": 0.3,
            "clarity": 0.3,
        }

        quality = sum(scores[key] * weights[key] for key in scores)

        return round(quality, 2)

    def _score_specificity(self, text: str) -> float:
        """
        Score how specific the idea is.

        Higher scores for:
        - Concrete features mentioned
        - Specific use cases
        - Detailed requirements

        Args:
            text: Text to score

        Returns:
            Specificity score (0-1)
        """
        score = 0.0

        # Length bonus (longer = more specific, up to a point)
        word_count = len(text.split())
        if word_count >= 15:
            score += 0.3
        elif word_count >= 10:
            score += 0.2
        elif word_count >= 5:
            score += 0.1

        # Feature indicators
        feature_words = ["with", "that", "which", "using", "via", "through", "by"]
        if any(word in text.lower() for word in feature_words):
            score += 0.2

        # Specific technologies/concepts mentioned
        tech_patterns = [
            r"\b(?:AI|ML|API|OCR|GPS|AR|VR|blockchain|cloud)\b",
            r"\b(?:Android|iOS|web|mobile|desktop)\b",
            r"\b(?:calendar|notification|photo|camera|location)\b",
        ]
        for pattern in tech_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                score += 0.15
                break

        # Numbers/measurements indicate specificity
        if re.search(r"\b\d+\b", text):
            score += 0.15

        # Cap at 1.0
        return min(score, 1.0)

    def _score_actionability(self, text: str) -> float:
        """
        Score how actionable/buildable the idea is.

        Higher scores for:
        - Clear problem to solve
        - Defined target audience
        - Understandable requirements

        Args:
            text: Text to score

        Returns:
            Actionability score (0-1)
        """
        score = 0.5  # Start at neutral

        # Action verbs indicate clear goal
        action_verbs = [
            "track",
            "manage",
            "organize",
            "find",
            "search",
            "create",
            "share",
            "analyze",
            "monitor",
            "schedule",
            "plan",
            "calculate",
        ]
        if any(verb in text.lower() for verb in action_verbs):
            score += 0.2

        # Problem framing
        problem_words = ["problem", "issue", "challenge", "difficulty", "need"]
        if any(word in text.lower() for word in problem_words):
            score += 0.1

        # Clear target audience
        audience_words = ["users", "people", "developers", "students", "professionals"]
        if any(word in text.lower() for word in audience_words):
            score += 0.1

        # Too vague = lower score
        vague_words = ["something", "somehow", "whatever", "stuff", "things"]
        if any(word in text.lower() for word in vague_words):
            score -= 0.2

        return max(0.0, min(score, 1.0))

    def _score_clarity(self, text: str) -> float:
        """
        Score how clear and understandable the idea is.

        Higher scores for:
        - Proper grammar
        - Complete sentences
        - No excessive jargon

        Args:
            text: Text to score

        Returns:
            Clarity score (0-1)
        """
        score = 0.5  # Start at neutral

        # Reasonable length (not too short, not too long)
        word_count = len(text.split())
        if 8 <= word_count <= 30:
            score += 0.3
        elif word_count < 5:
            score -= 0.2
        elif word_count > 50:
            score -= 0.1

        # Complete sentence indicators
        if text[0].isupper() and text[-1] in ".!?":
            score += 0.1

        # Excessive punctuation = unclear
        punct_ratio = sum(1 for c in text if c in "!?...") / max(len(text), 1)
        if punct_ratio > 0.1:
            score -= 0.2

        # ALL CAPS = unclear
        if text.isupper():
            score -= 0.3

        return max(0.0, min(score, 1.0))

    def extract_domain(self, text: str) -> str:
        """
        Extract domain/category from text.

        Args:
            text: Text to analyze

        Returns:
            Domain category string
        """
        text_lower = text.lower()

        # Domain keyword mapping
        domains = {
            "productivity": [
                "productivity",
                "task",
                "todo",
                "organize",
                "schedule",
                "calendar",
                "note",
                "reminder",
            ],
            "health": [
                "health",
                "fitness",
                "workout",
                "exercise",
                "nutrition",
                "diet",
                "wellness",
                "medical",
            ],
            "finance": [
                "finance",
                "budget",
                "expense",
                "money",
                "payment",
                "invest",
                "bank",
                "crypto",
            ],
            "social": [
                "social",
                "friend",
                "community",
                "chat",
                "message",
                "dating",
                "network",
                "share",
            ],
            "education": [
                "education",
                "learn",
                "study",
                "course",
                "teach",
                "school",
                "language",
                "skill",
            ],
            "entertainment": [
                "entertainment",
                "game",
                "movie",
                "music",
                "podcast",
                "video",
                "streaming",
            ],
            "travel": [
                "travel",
                "trip",
                "vacation",
                "hotel",
                "flight",
                "destination",
                "tourism",
            ],
            "shopping": [
                "shopping",
                "buy",
                "purchase",
                "store",
                "product",
                "ecommerce",
                "retail",
            ],
        }

        # Count matches for each domain
        domain_scores = {}
        for domain, keywords in domains.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score

        # Return domain with highest score, or 'other'
        if domain_scores:
            return max(domain_scores, key=domain_scores.get)
        return "other"

    def extract_features(self, text: str) -> list[str]:
        """
        Extract mentioned features/technologies from text.

        Args:
            text: Text to analyze

        Returns:
            List of feature keywords
        """
        features = []

        # Common feature keywords
        feature_keywords = [
            "AI",
            "ML",
            "machine learning",
            "automation",
            "API",
            "integration",
            "OCR",
            "voice",
            "speech",
            "image recognition",
            "computer vision",
            "notification",
            "reminder",
            "calendar",
            "GPS",
            "location",
            "map",
            "chat",
            "messaging",
            "photo",
            "camera",
            "analytics",
            "dashboard",
            "social",
            "sharing",
            "collaboration",
            "real-time",
            "offline",
            "cloud",
            "sync",
            "backup",
            "export",
            "import",
            "search",
            "filter",
        ]

        text_lower = text.lower()
        for keyword in feature_keywords:
            if keyword.lower() in text_lower:
                features.append(keyword)

        return features[:10]  # Limit to top 10

    def extract_keywords(self, text: str, top_n: int = 5) -> list[str]:
        """
        Extract top keywords/keyphrases from text using NLTK.

        Args:
            text: Text to analyze
            top_n: Number of keywords to return

        Returns:
            List of keywords
        """
        import os

        import nltk
        from nltk.corpus import stopwords
        from nltk.tokenize import word_tokenize

        # Configure NLTK to use a writable directory in serverless environments
        nltk_data_path = os.path.join("/tmp", "nltk_data")
        if not os.path.exists(nltk_data_path):
            os.makedirs(nltk_data_path, exist_ok=True)

        # Add to search paths
        if nltk_data_path not in nltk.data.path:
            nltk.data.path.append(nltk_data_path)

        # Ensure resources are available
        try:
            nltk.data.find("tokenizers/punkt")
            nltk.data.find("taggers/averaged_perceptron_tagger")
            nltk.data.find("corpora/stopwords")
        except LookupError:
            nltk.download("punkt", download_dir=nltk_data_path, quiet=True)
            nltk.download(
                "averaged_perceptron_tagger", download_dir=nltk_data_path, quiet=True
            )
            nltk.download("stopwords", download_dir=nltk_data_path, quiet=True)

        # 1. Tokenize and POS Tag
        tokens = word_tokenize(text.lower())
        stop_words = set(stopwords.words("english"))

        # Filter out stopwords and non-alphanumeric
        filtered_tokens = [
            word
            for word in tokens
            if word.isalnum() and word not in stop_words and len(word) > 2
        ]

        # 2. Extract Noun Phrases (using simple chunking or just nouns)
        # For simplicity and speed, we'll focus on high-frequency Nouns and Adjective-Noun pairs
        pos_tags = nltk.pos_tag(filtered_tokens)

        candidates = []
        for word, tag in pos_tags:
            if tag.startswith("NN") or tag.startswith("JJ"):
                candidates.append(word)

        # 3. Frequency Distribution
        freq_dist = nltk.FreqDist(candidates)

        return [word for word, _ in freq_dist.most_common(top_n)]


# Singleton instance
text_processor = TextProcessor()


# Convenience functions
def extract_need_statements(text: str, use_llm: bool = False) -> list[dict[str, str]]:
    """
    Extract need statements using regex, optionally enhanced with LLM.

    Args:
        text: Text to analyze
        use_llm: If True and USE_LLM_EXTRACTION env var is set, also use LLM

    Returns:
        List of dicts with 'statement' and 'context' keys
    """
    regex_ideas = text_processor.extract_need_statements(text)

    if use_llm and os.getenv("USE_LLM_EXTRACTION", "").lower() in ("1", "true", "yes"):
        llm_ideas = extract_ideas_llm(text)
        return _merge_ideas(regex_ideas, llm_ideas)

    return regex_ideas


def analyze_sentiment(text: str) -> dict[str, Any]:
    """Analyze sentiment using singleton processor."""
    return text_processor.analyze_sentiment(text)


def calculate_quality_score(text: str) -> float:
    """Calculate quality score using singleton processor."""
    return text_processor.calculate_quality_score(text)


def extract_domain(text: str) -> str:
    """Extract domain using singleton processor."""
    return text_processor.extract_domain(text)


def extract_features(text: str) -> list[str]:
    """Extract features using singleton processor."""
    return text_processor.extract_features(text)


def extract_keywords(text: str, top_n: int = 5) -> list[str]:
    """Extract keywords using singleton processor."""
    return text_processor.extract_keywords(text, top_n)


# Default aspects for aspect-based sentiment analysis
DEFAULT_ASPECTS = [
    "usability",
    "price",
    "features",
    "support",
    "performance",
    "design",
    "reliability",
]


def analyze_aspect_sentiment(
    text: str, aspects: list[str] | None = None
) -> dict[str, float]:
    """
    Analyze sentiment per aspect mentioned in text.

    Uses sentence-level VADER sentiment on sentences containing each aspect.

    Args:
        text: Text to analyze
        aspects: List of aspects to check (defaults to DEFAULT_ASPECTS)

    Returns:
        Dict mapping aspect name to average sentiment score (-1 to 1)
    """
    if aspects is None:
        aspects = DEFAULT_ASPECTS

    results: dict[str, float] = {}

    # Split into sentences
    try:
        import nltk

        sentences = nltk.sent_tokenize(text)
    except (ImportError, LookupError):
        # Fallback to simple splitting
        sentences = re.split(r"[.!?]+", text)
        sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return results

    for aspect in aspects:
        aspect_lower = aspect.lower()

        # Find sentences containing this aspect
        aspect_sentences = [s for s in sentences if aspect_lower in s.lower()]

        if aspect_sentences:
            # Analyze sentiment of each sentence
            sentiments = [analyze_sentiment(s)["score"] for s in aspect_sentences]
            # Average sentiment for this aspect
            results[aspect] = sum(sentiments) / len(sentiments)

    return results


def extract_aspect_sentiments_batch(
    texts: list[str], aspects: list[str] | None = None
) -> list[dict[str, float]]:
    """
    Extract aspect sentiments for multiple texts.

    Args:
        texts: List of texts to analyze
        aspects: List of aspects to check

    Returns:
        List of dicts with aspect sentiments for each text
    """
    return [analyze_aspect_sentiment(text, aspects) for text in texts]


def detect_urgency_level(text: str) -> str:
    """
    Detect urgency level from text content.

    Args:
        text: Text to analyze

    Returns:
        'low', 'medium', or 'high'
    """
    text_lower = text.lower()

    # High urgency indicators
    high_urgency_words = [
        "urgent",
        "asap",
        "immediately",
        "critical",
        "emergency",
        "desperately",
        "right now",
        "today",
        "can't wait",
        "must have",
        "essential",
    ]

    # Medium urgency indicators
    medium_urgency_words = [
        "need",
        "should",
        "important",
        "soon",
        "would help",
        "want",
        "looking for",
        "searching for",
    ]

    high_count = sum(1 for word in high_urgency_words if word in text_lower)
    medium_count = sum(1 for word in medium_urgency_words if word in text_lower)

    if high_count >= 2 or (high_count >= 1 and medium_count >= 2):
        return "high"
    elif medium_count >= 2 or high_count >= 1:
        return "medium"
    else:
        return "low"
