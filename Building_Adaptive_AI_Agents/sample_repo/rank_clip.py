"""Ranks candidate clips before they are shown in a feed."""

from cache_utils import get_cached_score, set_cached_score


def score_clip(clip_id):
    """Very small placeholder scoring function."""
    cached = get_cached_score(clip_id)
    if cached is not None:
        return cached
    score = len(clip_id) * 3.14  # pretend model score
    set_cached_score(clip_id, score)
    return score


def rank_clips(clip_ids):
    """Sort clips by score, highest first."""
    return sorted(clip_ids, key=score_clip, reverse=True)
# bump
# tweak
