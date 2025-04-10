
from time import sleep
from decorator import decorator
import logging as logger
from rich import print as rprint

# ------------------------------------------------------------------------------------------------------------------
def singleton(cls):
    """
    Decorator that makes a class follow the Singleton design pattern.
    In other words, there can be at-most one object instance of the class,
    and the repeated call to the constructor will yield the same object instance.
    """
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance
# ------------------------------------------------------------------------------------------------------------------
@decorator
def log_time_taken(func, *args, **kwargs):
    """
    Decorator that logs the time taken by the decorated function.
    """
    import time
    start = time.time()
    result = func(*args, **kwargs)
    end = time.time()
    border = "-" * 100 
    message ='\n'.join ([border, 
                         f" Time taken by {func.__name__}: {end - start} seconds", 
                         border])
    logger.info(message)
    rprint(message)
    return result

# ------------------------------------------------------------------------------------------------------------------

@log_time_taken
def test_function():
    sleep(2)
    rprint("Hello, World!")

if __name__ == "__main__":
    test_function()