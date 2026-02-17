from enum import StrEnum

LINKING_CODE_SYMBOLS = 'ABCDEFGHJKMNPQRTUVWXYZ2345679'
QR_LINK = 'tg://resolve?domain=plants_w_f_bot&start={code}'
BOT_LINK = 'https://t.me/plants_w_f_bot?start={code}'
CODE_LENGTH = 6
LINK_CODE = 'tg:link:code:'
LINK_USER = 'tg:link:user:'


MIN_TTL_SECONDS = 30


class LinkMessage(StrEnum):
    user_unlink = 'User deleted successfully'
    user_link = 'Telegram linked successfully'
