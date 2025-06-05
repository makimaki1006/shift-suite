import logging
import os
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """Configure root logger.

    The log level can be overridden by the ``SHIFT_SUITE_LOG_LEVEL``
    environment variable.  Values may be numeric (e.g. ``10``) or one of
    the standard logging level names such as ``DEBUG`` or ``INFO``.
    """
    if logging.getLogger().hasHandlers():
        return

    env_level = os.getenv("SHIFT_SUITE_LOG_LEVEL")
    if env_level:
        if env_level.isdigit():
            level = int(env_level)
        else:
            level = getattr(logging, env_level.upper(), level)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s [%(module)s.%(funcName)s:%(lineno)d] - %(message)s"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)
