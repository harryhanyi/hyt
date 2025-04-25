"""
This module contains functions for logging and managing output.

Printing out simple strings looks like:

>>> logger.info('Some info message')
>>> logger.warn('Some warning message')
"""

import logging
import sys
import os
import re
import _io


_USE_COLOR = isinstance(sys.stdout, _io.TextIOWrapper)

# Define convenient names for TTY colors
COLORS = {
    # Styles
    "{normal}": "\033[0m",
    "{bold}": "\033[1m",
    "{underline}": "\033[4m",
    "{inverse}": "\033[7m",
    "{reset}": "\033[0m",

    # Foreground colors
    "{black}": "\033[30m",
    "{blue}": "\033[34m",
    "{cyan}": "\033[36m",
    "{green}": "\033[32m",
    "{magenta}": "\033[35m",
    "{red}": "\033[31m",
    "{white}": "\033[37m",
    "{yellow}": "\033[33m",

    # Background colors
    "{bg_black}": "\033[40m",
    "{bg_blue}": "\033[44m",
    "{bg_cyan}": "\033[46m",
    "{bg_green}": "\033[42m",
    "{bg_magenta}": "\033[45m",
    "{bg_red}": "\033[41m",
    "{bg_white}": "\033[47m",
    "{bg_yellow}": "\033[43m"
}


def _set_logger_level(logger):
    """Sets the log level based upon the current environment.
    The default level is INFO.
    """
    if 'DEBUG' in os.environ:
        level = logging.DEBUG
    elif 'WARN' in os.environ:
        level = logging.WARN
    elif 'NOWARN' in os.environ:
        level = logging.ERROR
    else:
        level = logging.INFO
    logger.setLevel(level)


def _get_caller_info():
    """Returns the caller's file name and line number."""

    # Get info about what called the function that called this.
    try:
        frame = sys._getframe(4)
    except ValueError:
        # handle for the case where a client calls getLogger() directly
        frame = sys._getframe(3)

    # Get the filename (full path) and then use that to get the module name.
    fileName = frame.f_code.co_filename
    lineNumber = frame.f_lineno

    return '{}, at line {}'.format(fileName, lineNumber)


def _get_logger_without_handlers(log_name=None):
    """Returns a logger without handlers or formatters."""
    if not log_name:
        log_name = _get_caller_info()
    logger = logging.getLogger(log_name)
    return logger, logger.getEffectiveLevel()


class ColorFormatter(logging.Formatter):

    _colorRegex = re.compile(r"{\w+}")

    def __init__(self, *args, **kwargs):
        self.__use_color = None
        if 'use_color' in kwargs:
            self.__use_color = kwargs.pop('use_color')
        super(ColorFormatter, self).__init__(*args, **kwargs)

    def _color_replacer(self, match):
        """Replaces anything matching _colorRegex with something from COLORS,
        or return it as-is if it isn't in COLORS.
        """
        if self.__use_color is not None and not self.__use_color:
            return ''
        elif self.__use_color is None and not _USE_COLOR:
            return ''

        key = match.group(0)
        if key in COLORS:
            return COLORS[key]
        else:
            return ''

    def format(self, record):
        """Swaps out color placeholders. Example:

        "{red}Hello{reset} World"

        would print out a red "Hello" followed by the terminal's default
        color for "World".
        """
        s = super(ColorFormatter, self).format(record)
        return self._colorRegex.sub(self._color_replacer, s)


def get_logger(
        log_name=None, log_file=None, force_new=False,
        use_color=None, format_='concise'):
    """Returns a logger for the given log name, format, and/or log file.

    Args:
        log_name (str): The logger name. If None, a default name is generated.
        log_file (str): A path to the log file. If None, log to stream output.
        force_new (bool): Force creating a new logger?
        use_color (bool): Using colored output?
            If None, only use colored output in terminal.
        format (str): The logger format string or one of the following presets:
                + "simple" - The simplest format including only the message.
                + "concise" - A concise format including level name and message.
                + "full" - The most verbose format.
            Logging to file will always use the "full" preset.

    Returns:
        Logger: the logger.
    """
    if log_file or format_ == 'full':
        format_ = '[%(levelname)s] (%(name)s): %(message)s'
    elif format_ == 'concise':
        format_ = '[%(levelname)s]: %(message)s'
    elif format_ == 'simple':
        format_ = '%(message)s'

    logger, level = _get_logger_without_handlers(log_name=log_name)

    # Log to file
    if log_file:
        # Create file handler and formatter
        log_file = os.path.abspath(log_file)
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(format_)

        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # Log to stream
    else:
        if logging.getLogger().handlers and not force_new:
            # logger should have already been configured, but in case some
            # other code initialized the root logger, we set the log level here
            _set_logger_level(logger)
            formatter = ColorFormatter(format_, use_color=use_color)
            for h in logging.getLogger().handlers:
                h.setFormatter(formatter)
            return logger
        else:
            # Set up the root logger for the first time - all child loggers
            # will pick up this configuration
            root_stream_logger = logging.getLogger()

            # Forces a new logger if requested
            if root_stream_logger.handlers and force_new:
                root_stream_logger.handlers = []

            # Create stream handler and formatter
            handler = logging.StreamHandler()
            formatter = ColorFormatter(format_, use_color=use_color)

            handler.setFormatter(formatter)
            root_stream_logger.addHandler(handler)
            _set_logger_level(root_stream_logger)

        logger.info('New logger created via: {}'.format(_get_caller_info()))
        return logger


# --- Convenience functions

def critical(msg, **kwargs):
    get_logger(**kwargs).critical('{{red}}{}{{reset}}'.format(msg))


def error(msg, **kwargs):
    get_logger(**kwargs).error('{{red}}{}{{reset}}'.format(msg))


def warn(msg, **kwargs):
    get_logger(**kwargs).warning('{{yellow}}{}{{reset}}'.format(msg))


def info(msg, **kwargs):
    get_logger(**kwargs).info(msg)


def debug(msg, **kwargs):
    get_logger(**kwargs).debug('{{blue}}{}{{reset}}'.format(msg))
