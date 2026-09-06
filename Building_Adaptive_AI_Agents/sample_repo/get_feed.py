"""Fetches the raw list of candidate clips for a user's feed."""


def fetch_candidate_clips(user_id):
    """Return a list of clip ids that could be shown to this user."""
    # In a real app this would hit a database / search index.
    return [f"clip_{i}" for i in range(user_id, user_id + 20)]


def get_feed(user_id):
    """Build the ranked feed for a user."""
    from rank_clip import rank_clips

    candidates = fetch_candidate_clips(user_id)
    return rank_clips(candidates)
# tweak
