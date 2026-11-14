"""Focused tests for pynnacle.pynnacle.SendEmail.

The project package is expected to expose this module as
``pynnacle.pynnacle``. SMTP calls are mocked; no network access is used.
"""

from email.message import EmailMessage
from pathlib import Path
from unittest.mock import Mock

import pytest

from pynnacle.pynnacle import SendEmail


@pytest.fixture
def email_client():
    return SendEmail(
        service="custom",
        user_id="smtp-user",
        user_pass="smtp-secret",
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_encryption="no",
        smtp_authentication="no",
    )


@pytest.mark.parametrize(
    "address",
    [
        "person@example.com",
        "first.last+tag@example.co.uk",
        "user_name@example-domain.com",
    ],
)
def test_validate_email_accepts_valid_addresses(address):
    assert SendEmail._validate_email(address) is True


@pytest.mark.parametrize(
    "address",
    [
        "",
        "plain-text",
        "person@",
        "@example.com",
        "person@example",
        None,
        123,
    ],
)
def test_validate_email_rejects_invalid_addresses(address):
    assert SendEmail._validate_email(address) is False


def test_custom_service_uses_explicit_smtp_settings(email_client):
    assert email_client._smtp_server == "smtp.example.com"
    assert email_client._smtp_port == 587
    assert email_client._smtp_encryption == "no"
    assert email_client._smtp_authentication == "no"


def test_configured_service_loads_settings(monkeypatch):
    import pynnacle.pynnacle as email_module

    monkeypatch.setattr(
        email_module,
        "ini_config",
        {
            "example": {
                "smtp_server": "mail.example.com",
                "smtp_port": "465",
                "smtp_authentication": "yes",
                "smtp_encryption": "yes",
            }
        },
    )

    client = SendEmail(service="example")

    assert client._smtp_server == "mail.example.com"
    assert client._smtp_port == 465
    assert client._smtp_authentication == "yes"
    assert client._smtp_encryption == "yes"


def test_unknown_service_exits(monkeypatch):
    import pynnacle.pynnacle as email_module

    monkeypatch.setattr(email_module, "ini_config", {})
    with pytest.raises(SystemExit) as exc:
        SendEmail(service="missing")

    assert exc.value.code == 1


def test_smtp_set_updates_only_supplied_truthy_values(email_client):
    email_client.smtp_set(
        user_id="new-user",
        user_pass="new-secret",
        smtp_server="new.example.com",
        smtp_port=2525,
        smtp_encryption="yes",
        smtp_authentication="yes",
    )

    assert email_client._user_id == "new-user"
    assert email_client._user_pass == "new-secret"
    assert email_client._smtp_server == "new.example.com"
    assert email_client._smtp_port == 2525
    assert email_client._smtp_encryption == "yes"
    assert email_client._smtp_authentication == "yes"


def test_smtp_get_and_repr_do_not_expose_credentials(email_client):
    smtp_details = email_client.smtp_get()
    representation = repr(email_client)

    assert "smtp-secret" not in smtp_details
    assert "smtp-user" not in smtp_details
    assert "smtp-secret" not in representation
    assert "smtp-user" not in representation
    assert "Configured" in smtp_details
    assert "Configured" in representation


def test_message_send_builds_headers_and_body(email_client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        email_client, "_message_transmit", lambda message: sent.append(message)
    )

    email_client.message_send(
        subject="Build report",
        sender="sender@example.com",
        recipient="recipient@example.com",
        cc=["copy@example.com"],
        bcc=["blind@example.com"],
        body="The build passed.",
    )

    assert len(sent) == 1
    message = sent[0]
    assert isinstance(message, EmailMessage)
    assert message["Subject"] == "Build report"
    assert message["From"] == "sender@example.com"
    assert message["To"] == "recipient@example.com"
    assert message["CC"] == "copy@example.com"
    assert message["BCC"] == "blind@example.com"
    assert message.get_content() == "The build passed.\n"


def test_message_send_filters_invalid_cc_and_bcc(email_client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        email_client, "_message_transmit", lambda message: sent.append(message)
    )

    email_client.message_send(
        subject="Report",
        sender="sender@example.com",
        recipient="recipient@example.com",
        cc=["valid-copy@example.com", "not-an-address"],
        bcc=["valid-blind@example.com", "invalid"],
        body="Done",
    )

    assert len(sent) == 1
    assert email_client._validated_cc == ["valid-copy@example.com"]
    assert email_client._validated_bcc == ["valid-blind@example.com"]


@pytest.mark.parametrize(
    ("sender", "recipient"),
    [
        ("bad-sender", "recipient@example.com"),
        ("sender@example.com", "bad-recipient"),
        (None, "recipient@example.com"),
        ("sender@example.com", None),
    ],
)
def test_message_send_does_not_transmit_with_invalid_addresses(
    email_client, monkeypatch, sender, recipient
):
    transmit = Mock()
    monkeypatch.setattr(email_client, "_message_transmit", transmit)

    email_client.message_send(
        subject="Report",
        sender=sender,
        recipient=recipient,
        body="Body",
    )

    transmit.assert_not_called()


def test_message_send_attaches_existing_file_and_skips_missing_file(
    email_client, monkeypatch, tmp_path
):
    attachment = tmp_path / "report.txt"
    attachment.write_bytes(b"report contents")
    missing = tmp_path / "missing.txt"
    sent = []
    monkeypatch.setattr(
        email_client, "_message_transmit", lambda message: sent.append(message)
    )

    email_client.message_send(
        subject="With attachment",
        sender="sender@example.com",
        recipient="recipient@example.com",
        body="See attached.",
        attachments=[attachment, missing],
    )

    assert len(sent) == 1
    parts = list(sent[0].iter_attachments())
    assert len(parts) == 1
    assert parts[0].get_filename() == "report.txt"
    assert parts[0].get_content() == "report contents"


def test_message_clear_removes_message_headers(email_client):
    email_client._msg["Subject"] = "Old subject"
    email_client._msg["From"] = "sender@example.com"
    email_client._msg["To"] = "recipient@example.com"

    email_client.message_clear()

    assert len(email_client._msg) == 0


class FakeSMTP:
    def __init__(self, server, port):
        self.server = server
        self.port = port
        self.started_tls = False
        self.login_args = None
        self.sent_message = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def starttls(self):
        self.started_tls = True

    def login(self, user, password):
        self.login_args = (user, password)

    def send_message(self, message):
        self.sent_message = message


def test_message_transmit_does_not_connect_without_smtp_configuration(
    email_client, monkeypatch, capsys
):
    import pynnacle.pynnacle as email_module

    smtp_factory = Mock()
    monkeypatch.setattr(email_module.smtplib, "SMTP", smtp_factory)
    email_client._smtp_server = None

    message = EmailMessage()
    message["Subject"] = "Test"
    message["From"] = "sender@example.com"
    message["To"] = "recipient@example.com"

    email_client._message_transmit(message)

    smtp_factory.assert_not_called()
    assert "SMTP server details are missing" in capsys.readouterr().out


def test_message_transmit_does_not_send_incomplete_message(
    email_client, monkeypatch, capsys
):
    import pynnacle.pynnacle as email_module

    smtp_factory = Mock()
    monkeypatch.setattr(email_module.smtplib, "SMTP", smtp_factory)

    email_client._message_transmit(EmailMessage())

    smtp_factory.assert_not_called()
    assert "Message details are missing" in capsys.readouterr().out


@pytest.mark.xfail(
    strict=True,
    reason="smtp_test currently transmits self._msg instead of the test message",
)
def test_smtp_test_transmits_the_test_message(email_client, monkeypatch):
    sent = []
    monkeypatch.setattr(
        email_client, "_message_transmit", lambda message: sent.append(message)
    )

    email_client.smtp_test("sender@example.com", "recipient@example.com")

    assert len(sent) == 1
    assert sent[0]["Subject"] == "----- TEST MESSAGE -----"
    assert sent[0]["From"] == "sender@example.com"
    assert sent[0]["To"] == "recipient@example.com"
