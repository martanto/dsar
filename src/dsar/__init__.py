#!/usr/bin/env python

from importlib.metadata import version

from dsar.sds import SDS
from dsar.core import DSAR
from dsar.plot import PlotDsar
from dsar.frequency_bands import FrequencyBands


__version__ = version("dsar")
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2024"
__url__ = "https://github.com/martanto/dsar"

__all__ = [
    "FrequencyBands",
    "DSAR",
    "PlotDsar",
    "SDS",
]
