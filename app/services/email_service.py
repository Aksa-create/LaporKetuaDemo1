
import os
import resend
from dotenv import load_dotenv

load_dotenv()

def send_email(to, subject, html):
    """Mengirim email melalui Resend API."""

    api_key = os.getenv("RESEND_API_KEY")
    sender = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "onboarding@resend.dev"
    )

    if not api_key:
        raise RuntimeError("RESEND_API_KEY belum dikonfigurasi.")

    resend.api_key = api_key

    params = {
        "from": sender,
        "to": [to],
        "subject": subject,
        "html": html,
    }

    return resend.Emails.send(params)
