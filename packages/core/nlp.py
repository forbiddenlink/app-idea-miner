"""
Natural Language Processing utilities for App-Idea Miner.
Handles text extraction, sentiment analysis, and quality scoring.
"""

import re
from typing import Any

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


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


# Singleton instance
text_processor = TextProcessor()


# Convenience functions
def extract_need_statements(text: str) -> list[dict[str, str]]:
    """Extract need statements using singleton processor."""
    return text_processor.extract_need_statements(text)


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
