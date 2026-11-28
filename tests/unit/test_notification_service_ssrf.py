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


def _fake_getaddrinfo(*addrs):
    """Build a socket.getaddrinfo stand-in returning the given IPs."""
    import socket

    def fake(host, port, *args, **kwargs):
        return [
            (
                socket.AF_INET6 if ":" in a else socket.AF_INET,
                socket.SOCK_STREAM,
                6,
                "",
                (a, 0, 0, 0) if ":" in a else (a, 0),
            )
            for a in addrs
        ]

    return fake


class TestValidateWebhookUrlHardening:
    @pytest.mark.parametrize(
        "url",
        [
            "http://[::1]/",
            "http://[fc00::1]/",
            "http://[fd12:3456::1]/",
            "http://[fe80::1]/",
            "http://[::ffff:127.0.0.1]/",
            "http://[::ffff:169.254.169.254]/",
            "http://0.0.0.0/",
            "http://100.64.0.1/",
            "http://172.16.0.1/",
            "http://172.31.255.255/",
        ],
    )
    def test_rejects_private_ranges_including_ipv6(self, url):
        with pytest.raises(WebhookUrlError, match="non-public"):
            validate_webhook_url(url)

    def test_rejects_when_any_resolved_address_is_private(self):
        with patch(
            "socket.getaddrinfo", _fake_getaddrinfo("93.184.216.34", "10.0.0.1")
        ):
            with pytest.raises(WebhookUrlError, match="non-public"):
                validate_webhook_url("https://mixed.example.com/")

    def test_rejects_hostname_resolving_to_ipv6_loopback(self):
        with patch("socket.getaddrinfo", _fake_getaddrinfo("::1")):
            with pytest.raises(WebhookUrlError, match="non-public"):
                validate_webhook_url("https://evil.example.com/")

    def test_accepts_public_ipv6(self):
        with patch("socket.getaddrinfo", _fake_getaddrinfo("2606:4700::1111")):
            validate_webhook_url("https://ok.example.com/")


class TestSendMethodsRevalidateAtSink:
    """Each send_* method is public, so each must guard its own request."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "method", ["send_slack_alert", "send_discord_alert", "send_generic_alert"]
    )
    async def test_direct_call_to_metadata_url_makes_no_request(self, method):
        service = NotificationService()
        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            result = await getattr(service, method)(
                "http://169.254.169.254/latest/meta-data/", [], "t"
            )
        assert result is False
        mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_dns_rebinding_between_check_and_send_is_rejected(self):
        """Save-time check sees a public IP; send-time re-check sees private."""
        import socket

        calls = {"n": 0}
        public = _fake_getaddrinfo("93.184.216.34")
        private = _fake_getaddrinfo("127.0.0.1")

        def flip(*a, **k):
            calls["n"] += 1
            return public(*a, **k) if calls["n"] == 1 else private(*a, **k)

        service = NotificationService()
        with (
            patch.object(socket, "getaddrinfo", flip),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        ):
            validate_webhook_url("https://rebind.example.com/hook")  # save time
            result = await service.send_alert(
                "https://rebind.example.com/hook", "generic", [], "t"
            )
        assert result is False
        mock_post.assert_not_called()

    @pytest.mark.asyncio
    async def test_redirects_are_not_followed(self):
        captured = {}
        real_init = __import__("httpx").AsyncClient.__init__

        def spy(self, *a, **k):
            captured.update(k)
            real_init(self, *a, **k)

        with (
            patch("socket.getaddrinfo", _fake_getaddrinfo("93.184.216.34")),
            patch("httpx.AsyncClient.__init__", spy),
            patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post,
        ):
            mock_post.return_value.status_code = 200
            await NotificationService().send_generic_alert(
                "https://ok.example.com/h", [], "t"
            )
        assert captured.get("follow_redirects") is False


class TestSaveTimeValidation:
    def test_create_schema_rejects_private_webhook(self):
        from pydantic import ValidationError

        from apps.api.app.schemas.saved_searches import SavedSearchCreateRequest

        with pytest.raises(ValidationError):
            SavedSearchCreateRequest(
                name="x",
                query_params={},
                webhook_url="http://169.254.169.254/",
                webhook_type="generic",
            )

    def test_update_schema_rejects_private_webhook(self):
        from pydantic import ValidationError

        from apps.api.app.schemas.saved_searches import SavedSearchUpdateRequest

        with pytest.raises(ValidationError):
            SavedSearchUpdateRequest(webhook_url="http://[::1]/")

    def test_test_webhook_schema_rejects_private_webhook(self):
        from pydantic import ValidationError

        from apps.api.app.schemas.saved_searches import WebhookTestRequest

        with pytest.raises(ValidationError):
            WebhookTestRequest(webhook_url="http://10.0.0.1/", webhook_type="slack")
