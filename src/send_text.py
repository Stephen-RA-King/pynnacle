# Core Library modules
import configparser

# Third party modules
import keyring

# First party modules
import pynnacle

# Get SMTP Settings from Config file and Credentials from Keyring
service = "gmail"
ini = configparser.ConfigParser()
ini.read("config.ini")
server = ini.get(service, "smtp_server")
port = int(ini.get(service, "smtp_port"))
auth = ini.get(service, "smtp_authentication")
encrypt = ini.get(service, "smtp_encryption")
if auth == "yes":
    user_id = keyring.get_password(service, "service_id")
    user_pass = keyring.get_password(service, "service_password")
    if user_id is None or user_pass is None:
        raise NameError("Email ID or Password do not exist in Keyring")
else:
    user_id, user_pass = None, None


# STEP 1 - Configure SMTP ##################
mailer = pynnacle.SendEmail(
    user_id=user_id,
    user_pass=user_pass,
    smtp_server=server,
    smtp_port=port,
    smtp_authentication=auth,
    smtp_encryption=encrypt,
)

# STEP 2 - set message details #############
subject = "Attention!! - There is a problem..."
sender = user_id
recipient = "stephen.ra.king@gmail.com"
body = """Dear sir \n\nThis is another test"""
cc = []
bcc = []
attachments = [r"D:\PYTHON PROJECT\MY PROGS\EMAIL_TOOLS\send\files\cat.jpg"]


# STEP 3 - Now send message ################
mailer.message_send(
    subject=subject,
    sender=sender,
    recipient=recipient,
    body=body,
    cc=cc,
    bcc=bcc,
    attachments=attachments,
)
