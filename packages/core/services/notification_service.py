"""
Notification service for sending alerts via webhooks.

Supports Slack, Discord, and generic webhook formats.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending webhook notifications."""

    # Timeout for webhook requests (seconds)
    WEBHOOK_TIMEOUT = 10.0

    async def send_alert(
        self,
        webhook_url: str,
        webhook_type: str,
        ideas: list[dict],
        search_name: str,
    ) -> bool:
        """
        Send alert to configured webhook.

        Args:
            webhook_url: Webhook endpoint URL
            webhook_type: 'slack', 'discord', or 'generic'
            ideas: List of idea dicts to include
            search_name: Name of the saved search

        Returns:
            True if successful, False otherwise
        """
        if not webhook_url:
            logger.warning("No webhook URL configured")
            return False

        if webhook_type == "slack":
            return await self.send_slack_alert(webhook_url, ideas, search_name)
        elif webhook_type == "discord":
            return await self.send_discord_alert(webhook_url, ideas, search_name)
        else:
            return await self.send_generic_alert(webhook_url, ideas, search_name)

    async def send_slack_alert(
        self,
        webhook_url: str,
        ideas: list[dict],
        search_name: str,
    ) -> bool:
        """
        Send Slack webhook with matched ideas.

        Uses Slack Block Kit for rich formatting.

        Args:
            webhook_url: Slack webhook URL
            ideas: List of idea dicts
            search_name: Name of the saved search

        Returns:
            True if successful
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"New App Ideas Matched: {search_name}",
                    "emoji": True,
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{len(ideas)} new idea{'s' if len(ideas) != 1 else ''}* matched your saved search.",
                },
            },
            {"type": "divider"},
        ]

        # Add up to 5 ideas
        for idea in ideas[:5]:
            idea_block = self._format_slack_idea_block(idea)
            blocks.append(idea_block)
            blocks.append({"type": "divider"})

        if len(ideas) > 5:
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_...and {len(ideas) - 5} more. View all in the dashboard._",
                    },
                }
            )

        payload = {"blocks": blocks}

        try:
            async with httpx.AsyncClient(timeout=self.WEBHOOK_TIMEOUT) as client:
                response = await client.post(webhook_url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Slack webhook sent successfully for '{search_name}'")
                    return True
                else:
                    logger.error(
                        f"Slack webhook failed: {response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Slack webhook error: {e}")
            return False

    def _format_slack_idea_block(self, idea: dict) -> dict:
        """Format a single idea as a Slack block."""
        problem = idea.get("problem_statement", "No problem statement")
        domain = idea.get("domain", "other")
        quality = idea.get("quality_score", 0)
        sentiment = idea.get("sentiment", "neutral")
        competitors = idea.get("competitors_mentioned", [])

        # Build fields
        fields = [
            {"type": "mrkdwn", "text": f"*Domain:* {domain}"},
            {"type": "mrkdwn", "text": f"*Quality:* {quality:.0%}"},
            {"type": "mrkdwn", "text": f"*Sentiment:* {sentiment}"},
        ]

        if competitors:
            fields.append(
                {
                    "type": "mrkdwn",
                    "text": f"*Competitors:* {', '.join(competitors[:3])}",
                }
            )

        return {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{problem[:200]}{'...' if len(problem) > 200 else ''}*",
            },
            "fields": fields,
        }

    async def send_discord_alert(
        self,
        webhook_url: str,
        ideas: list[dict],
        search_name: str,
    ) -> bool:
        """
        Send Discord webhook with matched ideas.

        Uses Discord embed format for rich content.

        Args:
            webhook_url: Discord webhook URL
            ideas: List of idea dicts
            search_name: Name of the saved search

        Returns:
            True if successful
        """
        embeds = []

        # Summary embed
        embeds.append(
            {
                "title": f"New App Ideas Matched: {search_name}",
                "description": f"**{len(ideas)}** new idea{'s' if len(ideas) != 1 else ''} matched your saved search.",
                "color": 0x5865F2,  # Discord blurple
            }
        )

        # Individual idea embeds (max 5)
        for idea in ideas[:5]:
            embed = self._format_discord_embed(idea)
            embeds.append(embed)

        if len(ideas) > 5:
            embeds.append(
                {
                    "description": f"_...and {len(ideas) - 5} more. View all in the dashboard._",
                    "color": 0x5865F2,
                }
            )

        payload = {"embeds": embeds}

        try:
            async with httpx.AsyncClient(timeout=self.WEBHOOK_TIMEOUT) as client:
                response = await client.post(webhook_url, json=payload)
                if response.status_code in (200, 204):
                    logger.info(
                        f"Discord webhook sent successfully for '{search_name}'"
                    )
                    return True
                else:
                    logger.error(
                        f"Discord webhook failed: {response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False

    def _format_discord_embed(self, idea: dict) -> dict:
        """Format a single idea as a Discord embed."""
        problem = idea.get("problem_statement", "No problem statement")
        domain = idea.get("domain", "other")
        quality = idea.get("quality_score", 0)
        sentiment = idea.get("sentiment", "neutral")
        competitors = idea.get("competitors_mentioned", [])

        # Color based on sentiment
        color_map = {
            "positive": 0x57F287,  # Green
            "negative": 0xED4245,  # Red
            "neutral": 0xFEE75C,  # Yellow
        }

        fields = [
            {"name": "Domain", "value": domain, "inline": True},
            {"name": "Quality", "value": f"{quality:.0%}", "inline": True},
            {"name": "Sentiment", "value": sentiment, "inline": True},
        ]

        if competitors:
            fields.append(
                {
                    "name": "Competitors Mentioned",
                    "value": ", ".join(competitors[:5]),
                    "inline": False,
                }
            )

        return {
            "title": problem[:256],
            "color": color_map.get(sentiment, 0x5865F2),
            "fields": fields,
        }

    async def send_generic_alert(
        self,
        webhook_url: str,
        ideas: list[dict],
        search_name: str,
    ) -> bool:
        """
        Send generic JSON webhook.

        Suitable for custom integrations, Zapier, Make, etc.

        Args:
            webhook_url: Generic webhook URL
            ideas: List of idea dicts
            search_name: Name of the saved search

        Returns:
            True if successful
        """
        payload = {
            "event": "new_ideas_matched",
            "search_name": search_name,
            "total_matches": len(ideas),
            "ideas": ideas[:10],  # Limit to 10 for payload size
        }

        try:
            async with httpx.AsyncClient(timeout=self.WEBHOOK_TIMEOUT) as client:
                response = await client.post(
                    webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code in (200, 201, 202, 204):
                    logger.info(
                        f"Generic webhook sent successfully for '{search_name}'"
                    )
                    return True
                else:
                    logger.error(
                        f"Generic webhook failed: {response.status_code} - {response.text}"
                    )
                    return False
        except Exception as e:
            logger.error(f"Generic webhook error: {e}")
            return False

    async def test_webhook(
        self,
        webhook_url: str,
        webhook_type: str,
    ) -> dict[str, Any]:
        """
        Send a test notification to verify webhook configuration.

        Args:
            webhook_url: Webhook endpoint URL
            webhook_type: 'slack', 'discord', or 'generic'

        Returns:
            Dict with 'success' bool and 'message' str
        """
        test_ideas = [
            {
                "problem_statement": "This is a test notification from App Idea Miner",
                "domain": "productivity",
                "quality_score": 0.85,
                "sentiment": "positive",
                "competitors_mentioned": ["notion", "todoist"],
            }
        ]

        success = await self.send_alert(
            webhook_url=webhook_url,
            webhook_type=webhook_type,
            ideas=test_ideas,
            search_name="Test Notification",
        )

        if success:
            return {
                "success": True,
                "message": f"Test notification sent successfully to {webhook_type} webhook",
            }
        else:
            return {
                "success": False,
                "message": f"Failed to send test notification. Check your {webhook_type} webhook URL.",
            }
