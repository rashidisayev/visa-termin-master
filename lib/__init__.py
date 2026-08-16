"""
Visa Appointment Helper Library
Modular package for German visa appointment automation.
"""

__version__ = "2.0.0"
__author__ = "Visa Appointment Helper Contributors"

from . import config
from . import utils
from . import extractors
from . import notifications

__all__ = [
    "config",
    "utils",
    "extractors",
    "notifications",
]
