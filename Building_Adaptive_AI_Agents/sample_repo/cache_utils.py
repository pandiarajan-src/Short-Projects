"""Tiny in-memory cache used to speed up repeated clip scoring."""

_CACHE = {}


def get_cached_score(clip_id):
    return _CACHE.get(clip_id)


def set_cached_score(clip_id, score):
    _CACHE[clip_id] = score


def clear_cache():
    """Wipe the cache. Useful when clip scores go stale."""
    _CACHE.clear()
# bump
