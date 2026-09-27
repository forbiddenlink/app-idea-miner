"""
Regression tests for the webhook-URL SSRF guard in
packages.core.services.notification_service.

`webhook_url` (saved search alerts, and the /saved-searches/test-webhook
endpoint) is entirely user-supplied and only length-validated at the API
schema layer. Without a check, an authenticated user could point it at an
internal service or the cloud instance metadata endpoint
(169.254.169.254) and get the server to make that request on their behalf.
"""

from unittest.mock import AsyncMock, patch

import pytest

from packages.core.services.notification_service import (
    NotificationService,
    WebhookUrlError,
    validate_webhook_url,
)


class TestValidateWebhookUrl:
    def test_rejects_non_http_scheme(self):
        with pytest.raises(WebhookUrlError, match="scheme"):
            validate_webhook_url("file:///etc/passwd")

    def test_rejects_url_with_no_hostname(self):
        with pytest.raises(WebhookUrlError, match="hostname"):
            validate_webhook_url("http:///path")

    def test_rejects_loopback(self):
        with pytest.raises(WebhookUrlError, match="non-public"):
            validate_webhook_url("http://127.0.0.1:6379/")

    def test_rejects_localhost_hostname(self):
        with pytest.raises(WebhookUrlError, match="non-public"):
            validate_webhook_url("http://localhost/")

    def test_rejects_cloud_metadata_address(self):
        # 169.254.169.254 is link-local and is where AWS/GCP/Azure serve
        # instance metadata (including IAM credentials) with no auth.
        with pytest.raises(WebhookUrlError, match="non-public"):
            validate_webhook_url("http://169.254.169.254/latest/meta-data/")

    def test_rejects_private_rfc1918_address(self):
        with pytest.raises(WebhookUrlError, match="non-public"):
            validate_webhook_url("http://10.0.0.5/")
        with pytest.raises(WebhookUrlError, match="non-public"):
            validate_webhook_url("http://192.168.1.1/")

    def test_allows_public_https_hostname(self):
        # hooks.slack.com resolves publicly; this must not raise.
        validate_webhook_url("https://hooks.slack.com/services/x/y/z")


class TestSendAlertRefusesUnsafeUrls:
    @pytest.mark.asyncio
    async def test_send_alert_returns_false_for_ssrf_target_without_network_call(
        self,
    ):
        service = NotificationService()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            result = await service.send_alert(
                webhook_url="http://169.254.169.254/latest/meta-data/",
                webhook_type="generic",
                ideas=[],
                search_name="test",
            )
        assert result is False
        mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_send_alert_still_sends_for_safe_url(self):
        service = NotificationService()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value.status_code = 200
            result = await service.send_alert(
                webhook_url="https://hooks.slack.com/services/x/y/z",
                webhook_type="slack",
                ideas=[],
                search_name="test",
            )
        assert result is True
        mock_post.assert_called_once()
