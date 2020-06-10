# Copyright (c) Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Twisted Python: Utilities and Enhancements for Python.
"""



# Deprecating twisted.python.constants.
from .compat import str
from .versions import Version
from .deprecate import deprecatedModuleAttribute

deprecatedModuleAttribute(
    Version("Twisted", 16, 5, 0),
    "Please use constantly from PyPI instead.",
    "twisted.python", "constants")

del Version
del deprecatedModuleAttribute
del str
