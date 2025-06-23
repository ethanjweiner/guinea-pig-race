import smtplib
from email.mime.text import MIMEText
import os

sender = os.getenv("EMAIL_SENDER")
password = os.getenv("EMAIL_PASSWORD")

def send_email(subject, body, recipients):
    """
    Send an email to the given recipients.
    """
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
       smtp_server.login(sender, password)
       smtp_server.sendmail(sender, recipients, msg.as_string())

