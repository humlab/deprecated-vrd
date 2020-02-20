import time

from decorator import decorator
from loguru import logger


@decorator
def timeit(func, *args, **kwargs):
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()

    execution_time = end - start

    logger.trace(
        "Function '{}' executed in {:f} s", func.__name__, execution_time
    )  # noqa: E501

    return result, execution_time
