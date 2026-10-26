"""Share remote reads only during one validation; never retain stale ticket data."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from subprocess import TimeoutExpired

_reads = ContextVar("record_reads", default=None)


@contextmanager
def reading():
    """Nested validators share results and failures, then discard them at the boundary."""
    token = _reads.set({}) if _reads.get() is None else None
    try:
        yield
    finally:
        if token is not None:
            _reads.reset(token)


def validation(function):
    """Give direct callers and CLI checks the same invocation-local read lifetime."""
    @wraps(function)
    def checked(*args, **kwargs):
        with reading():
            return function(*args, **kwargs)
    return checked


def once(function):
    """A failed read is also cached, so another validator cannot hide it or retry it."""
    @wraps(function)
    def read(*args):
        cache = _reads.get()
        if cache is None:
            return function(*args)
        key = (function.__name__, args)
        if key not in cache:
            try:
                cache[key] = (function(*args), None)
            except (OSError, ValueError, RuntimeError, TypeError, AttributeError, TimeoutExpired) as error:
                cache[key] = (None, error)
        value, error = cache[key]
        if error is not None:
            raise error
        return value
    return read
