#!/usr/bin/env python
# -*- coding: utf-8 -*-

from .frequency_bands import FrequencyBands
from .dsar import DSAR
from pkg_resources import get_distribution

__version__ = get_distribution("magma-rsam").version
__author__ = "Martanto"
__author_email__ = "martanto@live.com"
__license__ = "MIT"
__copyright__ = "Copyright (c) 2024"
__url__ = "https://github.com/martanto/dsar"

__all__ = [
    "FrequencyBands",
    "DSAR",
]