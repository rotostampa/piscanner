from piscanner.core.cleanup import cleanup_coroutines
from piscanner.core.lights import lights_coroutines
from piscanner.core.sender import sender_coroutines
from piscanner.utils.lights import setup_gpio


def worker_coroutines(*args, **opts):
    setup_gpio()

    yield from lights_coroutines(*args, **opts)
    yield from cleanup_coroutines(*args, **opts)
    yield from sender_coroutines(*args, **opts)
