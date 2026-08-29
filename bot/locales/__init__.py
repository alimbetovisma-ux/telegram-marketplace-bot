from bot.locales.en import STRINGS as EN
from bot.locales.ru import STRINGS as RU
from bot.locales.uz import STRINGS as UZ

LOCALES = {"uz": UZ, "ru": RU, "en": EN}
DEFAULT_LANG = "uz"


def t(lang: str, key: str, **kwargs) -> str:
    strings = LOCALES.get(lang, LOCALES[DEFAULT_LANG])
    template = strings.get(key) or LOCALES[DEFAULT_LANG].get(key) or key
    return template.format(**kwargs) if kwargs else template
