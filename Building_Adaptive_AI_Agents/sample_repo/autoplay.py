"""Handles the autoplay-next-clip button in the app."""

from get_feed import get_feed
from rank_clip import score_clip


def press_autoplay(user_id, current_clip_id):
    """User pressed autoplay: fetch the next best clip after the current one."""
    feed = get_clip_after(user_id, current_clip_id)
    return get_id(feed)


def get_clip_after(user_id, current_clip_id):
    feed = get_feed(user_id)
    if current_clip_id in feed:
        idx = feed.index(current_clip_id)
        return feed[idx + 1:] or feed
    return feed


def get_id(feed):
    return feed[0] if feed else None
# tweak
