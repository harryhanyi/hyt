"""
Extend python's built-in math utilities
"""

from math import *


def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
    """This is the same implementation as math.isclose() in Python3
    Python2 doesn't have it.

    Args:
        a, b (float): 2 floats to compare.
        rel_tol (float): Relative tolerance, it is multiplied by the greater
            of the magnitudes of the two arguments; as the values get larger,
            so does the allowed difference between them while still considering
            them equal.
        abs_tol (float): absolute tolerance that is applied as-is in all cases.
            If the difference is less than either of those tolerances,
            the values are considered equal.

    Returns:
        bool: the equality status.
    """
    return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)
