"""
Universal Data Normalization Specification (UDNS) v1.0
Data Cleaning Module - Core architecture and interfaces.
"""

from .base import BaseCleaner, CleaningContext, CleanResult, CleaningOperation, CleaningStats
from .pipeline import CleaningPipeline
from .registry import CleaningPluginRegistry

__version__ = "1.0.0"
__author__ = "Eduard Bateiko"

__all__ = [
    "BaseCleaner",
    "CleaningContext", 
    "CleanResult",
    "CleaningOperation",
    "CleaningStats",
    "CleaningPipeline",
    "CleaningPluginRegistry"
]