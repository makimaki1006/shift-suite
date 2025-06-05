import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger with a unified format if not already configured."""
    if logging.getLogger().hasHandlers():
        return

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d] - %(message)s"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

