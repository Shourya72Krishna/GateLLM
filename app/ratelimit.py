import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.config import settings

WINDOW_SECONDS = 60.0
_hits: dict[str, deque] = defaultdict(deque)


def check_rate_limit(key: str) -> None:
    now = time.monotonic()
    q = _hits[key]
    while q and now - q[0] > WINDOW_SECONDS:
        q.popleft()
    if len(q) >= settings.rate_limit_per_min:
        retry_after = int(WINDOW_SECONDS - (now - q[0])) + 1
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
    q.append(now)