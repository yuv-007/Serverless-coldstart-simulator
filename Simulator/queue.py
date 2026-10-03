from collections import deque


class RequestQueue:
    """Simple queue abstraction for pending requests."""

    def __init__(self):
        self._items = deque()

    def enqueue(self, request):
        self._items.append(request)

    def dequeue(self):
        if not self._items:
            return None
        return self._items.popleft()

    def __len__(self):
        return len(self._items)

    def empty(self):
        return len(self._items) == 0
