import time
from customchecks import TooManyRequests


class Ratelimiter:

    def __init__(self):
        # give 5 call grace period. just in case
        self._ratelimit = 45
        # time when the last reset was
        self._last_reset = 0
        # reset period is 30 seconds (50 calls per 30 seconds)
        self._period = 30
        # wait time for when there are not enough calls
        self._wait_time = 0

    async def call(self):
        # if the current time is greater than the last reset time
        if time.time().__trunc__() > self._last_reset:
            self._ratelimit = 45
            self._last_reset = time.time().__trunc__() + self._period
        # subtract a call
        self._ratelimit -= 1
        # if there are 0 or fewer requests left, raise the exception
        if self._ratelimit <= 0:
            raise TooManyRequests(f"{self._period}")
