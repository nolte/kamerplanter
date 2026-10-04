"""#2108 — one thumbnail-task dispatch per attachment and window.

A thumbnail GET that finds no rendition dispatches ``generate_thumbnails`` and
answers 202. Before #2108 it did so on **every** such GET: a client polling a
missing rendition — or a member looping over one — queued one full decode and
re-encode per request, each retried three times on failure.

The dispatch is therefore gated by an atomic **claim** per attachment: the first
caller in a window dispatches, every other caller inside it gets the 202 without
queueing anything. A single claim rather than a get/set pair because two
requests may find the same rendition missing at the same instant, and
"read, decide, write" would let both dispatch.
"""

from abc import ABC, abstractmethod


class IRenditionDispatchClaims(ABC):
    """Bookkeeping for "was the thumbnail task for this attachment queued recently?"."""

    @abstractmethod
    def claim(self, attachment_id: str) -> bool:
        """Atomically claim the dispatch slot of ``attachment_id`` for one window.

        Returns:
            ``True`` when the caller may dispatch — the slot was free and is now
            taken. ``False`` when a dispatch was already claimed in the window.
        """
        ...
