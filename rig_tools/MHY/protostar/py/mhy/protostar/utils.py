"""
Utility functions
"""
import re
import json
from collections import OrderedDict

import mhy.protostar.constants as const


def sanitize_name(name):
    # Remove all non-word characters (everything except numbers and letters)
    name = re.sub(r"[^\w\s]", '', str(name))
    # Replace all runs of whitespace with a underscore
    name = re.sub(r"\s+", '_', name)
    return name


def match_name(name, pattern):
    """Checks if a name matches a pattern.

    Args:
        name (str): A name string to check.
        pattern (str): A pattern string to match.
            The pattern support wild card *.

    Returns:
        bool
    """
    # remove all non-word characters (everything except numbers, letters, and *)
    pattern = re.sub(r"[^\w\s\*]", '', str(pattern))
    # convert wildcard * to regex, also add wildcard at 2 ends
    pattern = '.*' + pattern.replace('*', '.*') + '.*'
    return bool(re.search(r'{}'.format(pattern.lower()), name.lower()))


def format_doc(docstring, indent=3, prefix='| '):
    """Cleans and formats a docstring."""
    if not docstring:
        docstring = const.DEFAULT_DOC

    lines = []
    for line in docstring.splitlines():
        if not line.isspace():
            line = prefix + line.rstrip().strip() + '\n'
            lines.append(' ' * indent + line)
    docstring = ''.join(lines)
    return docstring.rstrip('\n').strip('\n')


def is_jsonable(obj):
    """Checks if an object is json serializable."""
    try:
        json.dumps(obj)
        return True
    except BaseException:
        return False


def primitify_list(value):
    """Returns a copy of the input list,
    force all items to be json serializable primitive types."""
    result = []
    for each in value:
        if isinstance(each, (list, tuple)):
            result.append(primitify_list(each))
        elif isinstance(each, dict):
            result.append(primitify_dict(each))
        elif not is_jsonable(each):
            result.append(str(each))
        else:
            result.append(each)
    return result


def primitify_dict(value):
    """Returns a ordered copy of the input dict,
    force all items to be json serializable primitive types."""
    result = OrderedDict()
    for key, val in value.items():
        if not is_jsonable(key):
            key = str(key)

        if isinstance(val, (list, tuple)):
            result[key] = primitify_list(val)
        elif isinstance(val, dict):
            result[key] = primitify_dict(val)
        elif not is_jsonable(val):
            result[key] = str(val)
        else:
            result[key] = val
    return result


def vector_equal(a, b, tol=.0001):
    """Checks if 2 vectors are the same."""
    for x, y in zip(a, b):
        if x > y + tol or x < y - tol:
            return False
    return True
