__version__ = "1.0.0"
__author__ = "bartcctv"
__license__ = "MIT"

from .core import (
    RequestManager,
    ContentExtractor,
    RobotsHandler,
    AuthHandler
)

__all__ = [
    'RequestManager',
    'ContentExtractor',
    'RobotsHandler',
    'AuthHandler'
]