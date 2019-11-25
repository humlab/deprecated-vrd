import time

from decorator import decorator
from loguru import logger


@decorator
def timeit(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()

    logger.debug(
        "Function '{}' executed in {:f} s", func.__name__, end - start
    )  # noqa: E501

    return result
