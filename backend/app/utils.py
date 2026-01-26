from datetime import datetime, timezone


def is_word_available(lockout_ends_at: datetime | None) -> bool:
    """
    Check if a word is available for purchase.

    Args:
        lockout_ends_at: The timestamp when lockout expires

    Returns:
        True if word is available (never owned or lockout expired)
    """
    if lockout_ends_at is None:
        return True

    now = datetime.now(timezone.utc)
    return now >= lockout_ends_at
