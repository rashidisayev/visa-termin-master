"""
Visa Appointment Helper Library
Modular package for German visa appointment automation.
Supports multiple visa types with universal, self-configuring system.
"""

__version__ = "2.1.0"
__author__ = "Visa Appointment Helper Contributors"

from . import config
from . import utils
from . import visa_types
from . import booking_process
from . import extractors
from . import notifications

__all__ = [
    "config",
    "utils",
    "visa_types",
    "booking_process",
    "extractors",
    "notifications",
]
