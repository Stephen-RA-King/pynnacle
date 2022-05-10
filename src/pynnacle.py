"""module docstring - short summary
If the description is long, the first line should be a short summary that makes
sense on its own, separated from the rest by a newline
"""
# Core Library modules
import mimetypes
import re
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import Any


class SendEmail:
    def __init__(
        self,
        user_id: Any = None,
        user_pass: Any = None,
        smtp_server: Any = None,
        smtp_port: int = 0,
        smtp_encryption: str = "yes",
        smtp_authentication: str = "yes",
    ):
        self._user_id: Any = user_id
        self._user_pass: Any = user_pass
        self._display_password: Any = None
        self._display_id: Any = None

        self._smtp_server: Any = smtp_server
        self._smtp_port: int = smtp_port
        self._smtp_encryption: str = smtp_encryption
        self._smtp_authentication: str = smtp_authentication

        self._test_sender: Any = None
        self._test_recipient: Any = None
        self._subject: Any = None
        self._sender: Any = None
        self._recipient: Any = None
        self._cc: list = []
        self._validated_cc: list = []
        self._bcc: list = []
        self._validated_bcc: list = []
        self._body: Any = None
        self._msg: Any = None
        self._msg_test: Any = None
        self._attachments: list = []
        self._msg = EmailMessage()

    @staticmethod
    def _validate_email(email: str) -> bool:
        _email_pattern = (
            r"[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:"
            r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"
        )
        if isinstance(email, str) and re.search(_email_pattern, email):
            return True
        else:
            print(f"email '{email}', is not properly formatted")
            return False

    def _attach(self, file: Path) -> None:
        filename = file.name
        ctype, encoding = mimetypes.guess_type(file)
        if ctype is None or encoding is not None:
            ctype = "application/octet-stream"
        maintype, subtype = ctype.split("/", 1)
        with open(file, "rb") as fp:
            self._msg.add_attachment(
                fp.read(), maintype=maintype, subtype=subtype, filename=filename
            )

    def __repr__(self) -> str:
        if self._user_id:
            self._display_id = "************ (Configured)"
        else:
            self._display_id = ""
        return f"""
            {self.__class__.__name__},
            User ID: {self._display_id!r},
            Server:  {self._smtp_server!r},
            Port:    {self._smtp_port}
            SUBJECT: {self._subject},
            FROM:    {self._sender},
            TO:      {self._recipient},
            CC:      {self._validated_cc},
            BCC:     {self._validated_bcc},
            BODY:    {self._body}
        """

    def smtp_set(
        self,
        user_id: Any = None,
        user_pass: Any = None,
        smtp_server: Any = None,
        smtp_port: int = 0,
        smtp_encryption: str = "yes",
        smtp_authentication: str = "yes",
    ) -> None:
        if user_id:
            self._user_id = user_id
        if user_pass:
            self._user_pass = user_pass
        if smtp_server:
            self._smtp_server = smtp_server
        if smtp_port:
            self._smtp_port = smtp_port
        if smtp_encryption:
            self._smtp_encryption = smtp_encryption
        if smtp_authentication:
            self._smtp_authentication = smtp_authentication

    def smtp_get(self) -> str:
        if self._user_pass:
            self._display_password = "************ (Configured)"
        else:
            self._display_password = None
        if self._user_id:
            self._display_id = "************ (Configured)"
        else:
            self._display_id = None
        return f"""
            User ID:             {self._display_id},
            User Password:       {self._display_password},
            SMTP Server:(*)      {self._smtp_server},
            SMTP Port:(*)        {self._smtp_port},
            SMTP Encryption:     {self._smtp_encryption}
            SMTP Authentication: {self._smtp_authentication}
            * = Required
            """

    def smtp_test(self, sender: str, recipient: str) -> None:
        self._msg_test = EmailMessage()
        if self._validate_email(sender):
            self._test_sender = sender
        else:
            return
        if self._validate_email(recipient):
            self._test_recipient = recipient
        else:
            return
        self._msg_test["Subject"] = "----- TEST MESSAGE -----"
        self._msg_test["From"] = self._test_sender
        self._msg_test["To"] = self._test_recipient
        self._msg_test["CC"] = []
        self._msg_test["BCC"] = []
        self._msg_test.set_content(
            "This is a test message......Your SMTP settings are correct!"
        )
        self._message_transmit(self._msg)

    def message_send(
        self,
        subject: Any = None,
        sender: Any = None,
        recipient: Any = None,
        cc: Any = None,
        bcc: Any = None,
        body: str = "",
        attachments: Any = None,
    ) -> None:
        self._validated_cc = []
        self._validated_bcc = []
        if subject:
            self._subject = subject
        if sender and self._validate_email(sender):
            self._sender = sender
        else:
            return
        if recipient and self._validate_email(recipient):
            self._recipient = recipient
        else:
            return
        if cc:
            self._cc = cc
            for i in self._cc:
                if self._validate_email(i):
                    self._validated_cc.append(i)
        if bcc:
            self._bcc = bcc
            for i in self._bcc:
                if self._validate_email(i):
                    self._validated_bcc.append(i)
        if body:
            self._body = body
        self._msg["Subject"] = self._subject
        self._msg["From"] = self._sender
        self._msg["To"] = self._recipient
        self._msg["CC"] = self._validated_cc
        self._msg["BCC"] = self._validated_bcc
        self._msg.set_content(self._body)
        if attachments:
            self._attachments = attachments
            for file in self._attachments:
                file = Path(file)
                if file.exists():
                    self._attach(file)
                continue
        self._message_transmit(self._msg)

    def message_get(self) -> str:
        return f"""
            c = Compulsory
            SUBJECT:(c) {self._subject },
            FROM:(c)    {self._sender},
            TO:(c)      {self._recipient},
            CC:         {self._validated_cc},
            BCC:        {self._validated_bcc},
            BODY:       {self._body}
        """

    def message_clear(self) -> None:
        if self._msg:
            self._msg.clear()

    def _message_transmit(self, message: Any) -> None:
        if not self._smtp_server or not self._smtp_port:
            print("Some SMTP server details are missing")
            print(self.smtp_get())
            return
        if not self._msg["Subject"] or not self._msg["From"] or not self._msg["To"]:
            print("Some Message details are missing")
            print(self.message_get())
            return

        with smtplib.SMTP(self._smtp_server, self._smtp_port) as server:
            if self._smtp_encryption == "yes":
                server.starttls()
            # server.ehlo()
            if self._smtp_authentication == "yes":
                server.login(self._user_id, self._user_pass)
            try:
                server.send_message(message)
            except smtplib.SMTPResponseException as e:
                error_code = str(e.smtp_code)
                error_message = str(e.smtp_error)
                print(f"Error Code: {error_code}:  {error_message}")
