import builtins
import math
import os
import time
from functools import wraps


_ORIGINAL_PRINT = builtins.print


def safe_print(*args, **kwargs):
    """Print text safely on terminals with limited encodings."""
    try:
        _ORIGINAL_PRINT(*args, **kwargs)
    except UnicodeEncodeError:
        sanitized = []
        for arg in args:
            text = str(arg).encode("ascii", errors="replace").decode("ascii")
            sanitized.append(text)
        _ORIGINAL_PRINT(*sanitized, **kwargs)


builtins.print = safe_print


def timer(func):
    """Decorator to measure execution time"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[TIMER] {func.__name__} took {end-start:.6f} seconds")
        return result

    return wrapper


def log_conversion(rate):
    """Convert rate to log weight"""
    return -math.log(rate)


def inverse_log(weight):
    """Convert log weight back to rate"""
    return math.exp(-weight)


def calculate_profit(cycle_rates):
    """Calculate total profit from a cycle of rates"""
    product = 1.0
    for rate in cycle_rates:
        product *= rate
    return product - 1


def validate_rates(rates):
    """Validate exchange rates"""
    for rate in rates:
        if rate <= 0:
            raise ValueError(f"Invalid exchange rate: {rate}")
    return True


def ensure_directory(path):
    """Create a directory when it does not exist."""
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except PermissionError:
        normalized = os.path.normpath(path)
        fallback = os.path.dirname(normalized)
        while fallback and not os.path.isdir(fallback):
            parent = os.path.dirname(fallback)
            if parent == fallback:
                break
            fallback = parent
        return fallback or "."


def get_output_dir(subdir: str = "") -> str:
    """Return a project-relative output/reports path, creating it if needed.

    Anchors to the project root (parent of the currency_arbitrage package
    directory) so exports always land in output/reports/ regardless of
    which module calls this function.
    """
    # __file__ is currency_arbitrage/utils.py  → parent is the project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    base = os.path.join(project_root, "output", "reports")
    path = os.path.join(base, subdir) if subdir else base
    os.makedirs(path, exist_ok=True)
    return path
