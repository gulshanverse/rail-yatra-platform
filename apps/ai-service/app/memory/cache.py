"""
Eviction policies (LRU, FIFO) and quota/limit enforcement
for conversational sessions.
"""

from collections import OrderedDict
from typing import List, Dict, Optional


def count_tokens(text: str) -> int:
    """Estimates the token count of a given string using standard characters-to-words rule."""
    words = text.split()
    return max(1, int(len(words) * 1.33) + 1)


class MemoryCachePolicy:
    """Tracks session priorities and selects victims for eviction based on LRU or FIFO."""

    def __init__(self, max_sessions: int = 5, policy: str = "LRU"):
        self.max_sessions = max_sessions
        self.policy = policy.upper()
        self.sessions: Dict[
            str, OrderedDict
        ] = {}  # maps user_id -> OrderedDict of session_ids

    def record_access(self, user_id: str, session_id: str) -> None:
        """Logs an access event to update eviction queues."""
        if user_id not in self.sessions:
            self.sessions[user_id] = OrderedDict()

        user_queue = self.sessions[user_id]
        if self.policy == "LRU":
            if session_id in user_queue:
                user_queue.move_to_end(session_id)
            else:
                user_queue[session_id] = True
        elif self.policy == "FIFO":
            if session_id not in user_queue:
                user_queue[session_id] = True

    def evict_if_needed(self, user_id: str, session_id: str) -> Optional[List[str]]:
        """
        Records the session access and returns list of evicted session IDs
        if user session count exceeds configured max.
        """
        self.record_access(user_id, session_id)
        user_queue = self.sessions.get(user_id)
        if not user_queue:
            return None

        evicted = []
        while len(user_queue) > self.max_sessions:
            # Pop the oldest session
            victim_session_id, _ = user_queue.popitem(last=False)
            evicted.append(victim_session_id)
        return evicted if evicted else None

    def remove_session(self, user_id: str, session_id: str) -> None:
        """Removes a session explicitly when deleted."""
        if user_id in self.sessions:
            self.sessions[user_id].pop(session_id, None)
