from email.message import EmailMessage

from app.config import settings
from app.services import auth as auth_service


def test_auth_email_links_are_built_from_frontend_base_url(monkeypatch):
    monkeypatch.setattr(
        settings, "FRONTEND_BASE_URL", "https://stellalink.example/app/"
    )

    assert (
        auth_service.build_email_verification_url("abc+/=")
        == "https://stellalink.example/app/auth/verify-email?token=abc%2B%2F%3D"
    )
    assert (
        auth_service.build_password_reset_url("reset token")
        == "https://stellalink.example/app/auth/reset-password?token=reset+token"
    )


def test_send_email_uses_starttls_login_and_html_alternative(monkeypatch):
    sent: dict[str, object] = {}

    class FakeSMTP:
        def __init__(self, host: str, port: int, timeout: int):
            sent["host"] = host
            sent["port"] = port
            sent["timeout"] = timeout
            sent["starttls"] = False
            sent["login"] = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            sent["starttls"] = True

        def login(self, username: str, password: str):
            sent["login"] = (username, password)

        def send_message(self, msg: EmailMessage):
            sent["message"] = msg

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 587)
    monkeypatch.setattr(settings, "SMTP_TIMEOUT_SECONDS", 12)
    monkeypatch.setattr(settings, "SMTP_USERNAME", "smtp-user")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp-pass")
    monkeypatch.setattr(settings, "SMTP_USE_SSL", False)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(settings, "SMTP_FROM", "no-reply@stellalink.app")
    monkeypatch.setattr(settings, "SMTP_FROM_NAME", "Stellalink")
    monkeypatch.setattr(auth_service.smtplib, "SMTP", FakeSMTP)

    auth_service._send_email_sync(
        "user@example.com",
        "Subject",
        "Plain body",
        "<p>HTML body</p>",
    )

    msg = sent["message"]
    assert sent["host"] == "smtp.example.com"
    assert sent["port"] == 587
    assert sent["timeout"] == 12
    assert sent["starttls"] is True
    assert sent["login"] == ("smtp-user", "smtp-pass")
    assert isinstance(msg, EmailMessage)
    assert msg["From"] == "Stellalink <no-reply@stellalink.app>"
    assert msg["To"] == "user@example.com"
    assert msg.get_body(("plain",)).get_content() == "Plain body\n"
    assert "HTML body" in msg.get_body(("html",)).get_content()


def test_send_email_uses_smtp_ssl_without_starttls(monkeypatch):
    sent: dict[str, object] = {}

    class FakeSMTPSSL:
        def __init__(self, host: str, port: int, timeout: int):
            sent["host"] = host
            sent["port"] = port
            sent["timeout"] = timeout
            sent["starttls"] = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            sent["starttls"] = True

        def send_message(self, msg: EmailMessage):
            sent["message"] = msg

    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr(settings, "SMTP_PORT", 465)
    monkeypatch.setattr(settings, "SMTP_TIMEOUT_SECONDS", 20)
    monkeypatch.setattr(settings, "SMTP_USERNAME", None)
    monkeypatch.setattr(settings, "SMTP_PASSWORD", None)
    monkeypatch.setattr(settings, "SMTP_USE_SSL", True)
    monkeypatch.setattr(settings, "SMTP_USE_TLS", True)
    monkeypatch.setattr(auth_service.smtplib, "SMTP_SSL", FakeSMTPSSL)

    auth_service._send_email_sync("user@example.com", "Subject", "Plain body")

    assert sent["host"] == "smtp.example.com"
    assert sent["port"] == 465
    assert sent["timeout"] == 20
    assert sent["starttls"] is False
    assert isinstance(sent["message"], EmailMessage)
