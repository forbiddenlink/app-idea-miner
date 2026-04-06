"""
Processing tasks for extracting and analyzing ideas from raw posts.
"""

import asyncio
import logging
import os
import re
from datetime import datetime
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.worker.celery_app import celery_app
from packages.core.competitors import extract_competitors
from packages.core.database import AsyncSessionLocal
from packages.core.models import IdeaCandidate, RawPost
from packages.core.nlp import (
    analyze_aspect_sentiment,
    analyze_sentiment,
    calculate_quality_score,
    detect_urgency_level,
    extract_domain,
    extract_features,
    extract_need_statements,
    generate_embedding,
    reset_llm_call_count,
)

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="apps.worker.tasks.processing.process_raw_posts",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=3,
)
def process_raw_posts(
    self, batch_size: int = 100, min_quality: float = 0.3
) -> dict[str, Any]:
    """
    Process unprocessed raw posts to extract ideas.

    This task:
    1. Fetches unprocessed RawPost records
    2. Extracts need statements using NLP
    3. Analyzes sentiment
    4. Calculates quality scores
    5. Creates IdeaCandidate records
    6. Marks posts as processed

    Args:
        batch_size: Maximum number of posts to process
        min_quality: Minimum quality score to save idea (0-1)

    Returns:
        Dict with processing statistics
    """
    logger.info(
        f"Starting post processing (batch_size={batch_size}, min_quality={min_quality})"
    )

    try:
        # Run async processing
        result = asyncio.run(_process_posts_async(batch_size, min_quality))

        logger.info(f"Processing complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Error processing posts: {e}", exc_info=True)
        raise


async def _process_posts_async(batch_size: int, min_quality: float) -> dict[str, Any]:
    """
    Async implementation of post processing.

    Args:
        batch_size: Maximum posts to process
        min_quality: Minimum quality threshold

    Returns:
        Processing statistics
    """
    stats = {
        "processed": 0,
        "ideas_created": 0,
        "ideas_from_llm": 0,
        "low_quality_skipped": 0,
        "errors": 0,
        "error_details": [],
    }

    # Reset LLM call counter at start of processing cycle
    reset_llm_call_count()

    # Check if LLM extraction is enabled
    use_llm = os.getenv("USE_LLM_EXTRACTION", "").lower() in ("1", "true", "yes")

    async with AsyncSessionLocal() as session:
        # Fetch unprocessed posts
        posts = await _fetch_unprocessed_posts(session, batch_size)

        if not posts:
            logger.info("No unprocessed posts found")
            return stats

        logger.info(f"Found {len(posts)} unprocessed posts (LLM={use_llm})")

        # Process each post with savepoint for atomic per-post commits
        for post in posts:
            try:
                # Use savepoint to ensure partial failures don't corrupt data
                async with session.begin_nested():
                    ideas_count, llm_count = await _process_single_post(
                        session, post, min_quality, use_llm=use_llm
                    )

                    if ideas_count == 0:
                        stats["low_quality_skipped"] += 1

                    # Only mark as processed after successful idea extraction
                    post.is_processed = True
                    stats["processed"] += 1
                    stats["ideas_created"] += ideas_count
                    stats["ideas_from_llm"] += llm_count

            except Exception as e:
                logger.error(f"Error processing post {post.id}: {e}", exc_info=True)
                stats["errors"] += 1
                stats["error_details"].append(
                    {
                        "post_id": str(post.id),
                        "error": str(e),
                    }
                )
                # Savepoint rollback happens automatically, post stays unprocessed

        # Commit all successful changes
        try:
            await session.commit()
            logger.info(f"Committed {stats['processed']} processed posts")
        except Exception as e:
            logger.error(f"Error committing changes: {e}", exc_info=True)
            await session.rollback()
            raise

    return stats


async def _fetch_unprocessed_posts(session: AsyncSession, limit: int) -> list[RawPost]:
    """
    Fetch unprocessed posts from database.

    Args:
        session: Database session
        limit: Maximum posts to fetch

    Returns:
        List of RawPost objects
    """
    stmt = (
        select(RawPost)
        .where(RawPost.is_processed == False)
        .order_by(RawPost.fetched_at.asc())
        .limit(limit)
    )

    result = await session.execute(stmt)
    posts = result.scalars().all()

    return list(posts)


async def _process_single_post(
    session: AsyncSession, post: RawPost, min_quality: float, use_llm: bool = False
) -> tuple[int, int]:
    """
    Process a single post to extract ideas.

    Args:
        session: Database session
        post: RawPost to process
        min_quality: Minimum quality threshold
        use_llm: Whether to use LLM for enhanced extraction

    Returns:
        Tuple of (total ideas created, ideas from LLM)
    """
    # Combine title and content for analysis
    full_text = f"{post.title}\n\n{post.content or ''}"

    # Extract need statements (optionally using LLM)
    need_statements = extract_need_statements(full_text, use_llm=use_llm)

    if not need_statements:
        logger.debug(f"No need statements found in post {post.id}")
        return 0, 0

    logger.debug(f"Found {len(need_statements)} need statements in post {post.id}")

    ideas_created = 0
    llm_ideas_created = 0

    # Process each need statement
    for statement_data in need_statements:
        problem_statement = statement_data["statement"]
        context = statement_data.get("context", "")
        is_from_llm = statement_data.get("source") == "llm"

        # Analyze sentiment
        sentiment_data = analyze_sentiment(context or problem_statement)

        # Calculate quality score
        quality_score = calculate_quality_score(problem_statement)

        # Skip low quality ideas
        if quality_score < min_quality:
            logger.debug(
                f"Skipping low quality idea (score={quality_score}): {problem_statement[:50]}"
            )
            continue

        # Extract domain and features
        domain = extract_domain(problem_statement)
        features = extract_features(problem_statement)

        # Extract competitor mentions from problem statement and context
        combined_text = f"{problem_statement} {context}"
        competitors = extract_competitors(combined_text, domain=domain)

        # Analyze aspect-based sentiment
        aspect_sentiments = analyze_aspect_sentiment(combined_text)

        # Detect urgency level
        urgency = detect_urgency_level(combined_text)

        # Generate embedding for similarity search
        embedding = generate_embedding(problem_statement)

        # Create IdeaCandidate
        idea = IdeaCandidate(
            raw_post_id=post.id,
            problem_statement=problem_statement,
            context=context,  # Store full context
            domain=domain,
            sentiment=sentiment_data["label"],
            sentiment_score=sentiment_data["score"],
            emotions=sentiment_data.get("emotions", {}),
            quality_score=quality_score,
            features_mentioned=features,
            competitors_mentioned=competitors if competitors else None,
            aspect_sentiments=aspect_sentiments if aspect_sentiments else {},
            urgency_level=urgency,
            idea_vector=embedding,
            extracted_at=datetime.utcnow(),
        )

        session.add(idea)
        ideas_created += 1
        if is_from_llm:
            llm_ideas_created += 1

        logger.debug(
            f"Created idea: domain={domain}, sentiment={sentiment_data['label']}, "
            f"quality={quality_score:.2f}, source={'llm' if is_from_llm else 'regex'}, "
            f"statement={problem_statement[:50]}..."
        )

    return ideas_created, llm_ideas_created


def _extract_solution_hint(problem_statement: str, context: str) -> str:
    """
    Extract solution hint from problem statement or context.

    Args:
        problem_statement: The main problem statement
        context: Surrounding context

    Returns:
        Solution hint or empty string
    """
    # Look for "with", "using", "that has" patterns
    hint_patterns = [
        r"(?:with|using|via|through)\s+(.+?)(?:[.!?]|$)",
        r"that (?:has|includes|provides|offers)\s+(.+?)(?:[.!?]|$)",
        r"like (.+?)(?:[.!?]|$)",
    ]

    text = f"{problem_statement} {context}"

    for pattern in hint_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            hint = match.group(1).strip()
            # Clean up and return if reasonable length
            if 5 <= len(hint) <= 200:
                return hint

    return ""


@celery_app.task(bind=True, name="apps.worker.tasks.processing.reprocess_failed_posts")
def reprocess_failed_posts(self) -> dict[str, Any]:
    """
    Reprocess posts that were processed but produced no ideas.

    This can be used to retry with different parameters or after
    improving the NLP extraction logic.

    Returns:
        Processing statistics
    """
    logger.info("Starting reprocessing of failed posts")

    try:
        result = asyncio.run(_reprocess_failed_async())
        logger.info(f"Reprocessing complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Error reprocessing failed posts: {e}", exc_info=True)
        raise


async def _reprocess_failed_async() -> dict[str, Any]:
    """
    Async implementation of reprocessing.

    Returns:
        Processing statistics
    """
    async with AsyncSessionLocal() as session:
        # Find processed posts with no ideas
        stmt = (
            select(RawPost.id)
            .select_from(RawPost)
            .outerjoin(IdeaCandidate, RawPost.id == IdeaCandidate.raw_post_id)
            .where(RawPost.is_processed == True)
            .group_by(RawPost.id)
            .having(func.count(IdeaCandidate.id) == 0)
            .limit(50)
        )

        result = await session.execute(stmt)
        post_ids = [row[0] for row in result.fetchall()]

        if not post_ids:
            return {"reprocessed": 0, "ideas_created": 0}

        # Mark as unprocessed
        update_stmt = (
            update(RawPost).where(RawPost.id.in_(post_ids)).values(is_processed=False)
        )
        await session.execute(update_stmt)
        await session.commit()

        logger.info(f"Marked {len(post_ids)} posts for reprocessing")

        # Process them
        return await _process_posts_async(len(post_ids), min_quality=0.3)
