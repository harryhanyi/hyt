"""
Custom data types
"""


def Enum(**enums):
    """A simple enum type."""
    return type('Enum', (), enums)
