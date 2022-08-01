# Core Library modules

# Third party modules
import keyring

# First party modules
from pynnacle import pynnacle

service = "gmail"
user_id = keyring.get_password(service, "service_id")
user_pass = keyring.get_password(service, "service_password")
if user_id is None or user_pass is None:
    raise NameError("Email ID or Password do not exist in Keyring")


# ################ STEP 1 - Instantiate main class ##################
mailer = pynnacle.SendEmail(
    service="custom",
    user_id=user_id,
    user_pass=user_pass,
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_authentication="yes",
    smtp_encryption="yes",
)

# ################# STEP 2 - Now send a message #####################
mailer.message_send(
    subject="Attention!! - There is a problem...",
    sender=user_id,
    recipient="thesecuremailbox@gmail.com",
    body="""Dear sir \n\nThis is another test""",
    cc=[
        "stephen.ra.king@gmail.com",
        "junkmailcomplaints@gmail.com",
    ],
    bcc=[
        "stephen.ra.king@gmail.com",
        "junkmailcomplaints@gmail.com",
    ],
    attachments=[r"example_2.py"],
)
