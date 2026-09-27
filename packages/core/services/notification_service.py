"""
Notification service for sending alerts via webhooks.

Supports Slack, Discord, and generic webhook formats.
"""

import ipaddress
import logging
import socket
from typing import Any
from urllib.parse import urlsplit

import httpx

logger = logging.getLogger(__name__)


class WebhookUrlError(ValueError):
    """Raised when a user-supplied webhook URL is not safe to request."""


def validate_webhook_url(url: str) -> None:
    """
    Reject webhook URLs that would let an authenticated user make the
    server issue requests to internal or cloud-metadata addresses (SSRF).

    `webhook_url` (saved search alerts, the /test-webhook endpoint) is
    entirely user-supplied and free-text (only `max_length` is validated at
    the API schema layer). Without this check, a user could set it to
    `http://169.254.169.254/latest/meta-data/...` (cloud instance metadata),
    `http://localhost:6379` (an internal service), or any other
    non-routable address and get the server to make that request on their
    behalf.

    This resolves the hostname and rejects it if any resolved address is
    private, loopback, link-local (includes the 169.254.169.254 metadata
    range), reserved, multicast, or unspecified. It also requires an
    http(s) scheme. This does not defend against DNS rebinding (the
    hostname could re-resolve to a different address between this check
    and the actual request) — closing that fully would mean pinning the
    resolved IP and connecting to it directly via a custom transport,
    which is out of scope for this fix; the check here blocks the direct,
    common exploitation path.

    Raises:
        WebhookUrlError: if the URL's scheme or resolved address is unsafe.
    """
    parsed = urlsplit(url)
    if parsed.scheme not in ("http", "https"):
        raise WebhookUrlError(f"Unsupported webhook URL scheme: {parsed.scheme!r}")
    if not parsed.hostname:
        raise WebhookUrlError("Webhook URL has no hostname")

    try:
        addr_infos = socket.getaddrinfo(parsed.hostname, None)
    except socket.gaierror as exc:
        raise WebhookUrlError(f"Could not resolve webhook host: {exc}") from exc

    for _family, _type, _proto, _canonname, sockaddr in addr_infos:
        ip_str = sockaddr[0]
        ip = ipaddress.ip_address(ip_str)
        if (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        ):
            raise WebhookUrlError(
                f"Webhook host {parsed.hostname!r} resolves to a "
                f"non-public address ({ip_str}); refusing to send"
            )


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

        try:
            validate_webhook_url(webhook_url)
        except WebhookUrlError as e:
            logger.warning(f"Refusing to send webhook to unsafe URL: {e}")
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
