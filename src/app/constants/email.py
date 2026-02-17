from enum import StrEnum
from types import MappingProxyType

EN_CONFIRMATION_EMAIL_TEMPLATE_ID = 'x2p0347jzey4zdrn'
CONFIRMATION_EMAIL_TEMPLATES = MappingProxyType(
    {
        'ru': '3yxj6lje975gdo2r',
        'en': EN_CONFIRMATION_EMAIL_TEMPLATE_ID,
        'de': 'zr6ke4nq10v4on12',
    }
)
CONFIRMATION_EMAIL_LINK = (
    'https://plants-bot.com/email-confirmation.html?token={token}'
)

TOKEN_LENGTH = 32
EMAIL_CONFIRMATION_TTL = 60 * 60 * 24
CONFIRM_USER_PREFIX = 'email_confirmation_user:'
CONFIRM_TOKEN_PREFIX = 'email_confirmation:'
EMAIL_CONFIRMATION_DB_TTL = 2592000


class EmailMessage(StrEnum):
    email_confirmation_sent = 'Confirmation email sent'
    email_confirmed = 'Email confirmed'
