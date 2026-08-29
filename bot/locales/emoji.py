"""Premium (custom) emoji support.

Telegram lets any bot render a Premium custom emoji inside a message via a
`custom_emoji` MessageEntity, as long as you know the emoji's numeric
`custom_emoji_id`. You don't need a Premium bot account for this — only the
IDs themselves, which you collect once by forwarding a message that contains
the desired premium emoji to @userinfobot / @RawDataBot (or via
`bot.get_forwarded_from` -> entities) and copying the `custom_emoji_id`.

Until you fill PREMIUM_EMOJI_IDS in below, every helper here falls back to a
plain unicode emoji, so the bot works correctly out of the box.
"""

from aiogram.types import MessageEntity

# name -> (unicode fallback, custom_emoji_id or None)
PREMIUM_EMOJI_IDS: dict[str, tuple[str, str | None]] = {
    "diamond": ("💎", None),
    "star": ("⭐️", None),
    "gift": ("🎁", None),
    "phone": ("📱", None),
    "key": ("🔑", None),
    "wallet": ("👛", None),
    "fire": ("🔥", None),
    "check": ("✅", None),
}


def emoji(name: str) -> str:
    fallback, _ = PREMIUM_EMOJI_IDS.get(name, ("", None))
    return fallback


def build_entities(text: str, names_at_offsets: list[tuple[int, str]]) -> list[MessageEntity]:
    """Build custom_emoji entities for the given (utf16_offset, emoji_name) pairs.

    Only emits an entity when a real custom_emoji_id is configured; otherwise
    the unicode fallback already embedded in `text` is left as plain text.
    """
    entities: list[MessageEntity] = []
    for offset, name in names_at_offsets:
        fallback, custom_id = PREMIUM_EMOJI_IDS.get(name, ("", None))
        if not custom_id:
            continue
        entities.append(
            MessageEntity(
                type="custom_emoji",
                offset=offset,
                length=len(fallback),
                custom_emoji_id=custom_id,
            )
        )
    return entities
