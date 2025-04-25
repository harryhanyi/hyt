"""
General python utilities
"""
import re
import platform


def flatten_list(input_list):
    """Flatten a given list.

    Args:
        input_list (list, tuple): A list to flatten.

    Returns:
        list: The flattened list.
    """
    out_list = []

    if not isinstance(input_list, (list, tuple)):
        out_list.append(input_list)
    else:
        for each in input_list:
            if isinstance(each, (list, tuple)):
                out_list.extend(flatten_list(each))
            else:
                out_list.append(each)

    return out_list


def increment_name(name):
    def get_trailing_number(string_object):
        """
        Get the continuous numeric string at the end of the string
        Args:
            string_object: A string object

        Returns:
            int: Cast the numerical suffix into a real integer

        """
        m = re.search(r'\d+$', string_object)
        return int(m.group()) if m else None
    num = get_trailing_number(name)
    len_num = len(str(num))
    if num:
        new_name = '{0}{1}'.format(name[:-len_num], num + 1)
    else:
        new_name = name + '1'
    return new_name


def system():
    """
    Return the current platform in lowercase.

    Returns:

    """
    return platform.system().lower()


def is_linux():
    """
    Return True if the current OS is linux.

    Returns:
        bool: If current operation system is linux

    """

    return system().startswith("lin")
