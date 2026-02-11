from mailersend import MailerSendClient, EmailBuilder

from app.constants.email import (
    CONFIRMATION_EMAIL_TEMPLATES,
    EN_CONFIRMATION_EMAIL_TEMPLATE_ID,
)
from app.tasks.broker import broker

ms = MailerSendClient()


@broker.task
def send_confirmation_email(
    to_email: str, confirmation_link: str, language: str | None = None
) -> str:
    """Sends a confirmation email to the specified email address."""
    email = (
        EmailBuilder()
        .to(email=to_email)
        .subject('Please confirm your email')
        .template(
            CONFIRMATION_EMAIL_TEMPLATES.get(
                language, EN_CONFIRMATION_EMAIL_TEMPLATE_ID
            )
        )
        .tracking(clicks=False, opens=False, content=False)
        .personalize(email=to_email, link=confirmation_link)
        .build()
    )
    return ms.emails.send(email)
