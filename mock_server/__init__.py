import sys


is_before_python3 = sys.version_info[0] < 3

if is_before_python3:  # python2
    from .ordereddict import OrderedDict
else:
    from collections import OrderedDict


__version__ = "0.3.9"
