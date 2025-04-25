"""
This module is used to generate base main window classes for all
MHY tools to inherit.

Features:
    + App instance(s) tracking.
    + Default menu bar with a standard help menu
        (if the sub class provided _HELP_URL)
    + Standard launch method: window.launch().
    + Standard UI stylesheet.
    + App settings tracking.
    + Support loading Designer .ui files

TODO:
    + Standard exception handling and reporting.
    + Telemetry data reporting.

Usage:
.. code:: python
    from mhy.qt.core.base_main_window import get_window_class

    # get the base main window class
    base_class = get_window_class(app_name='my_app')


    # create the main window for my app
    class MyAppMainWindow(base_class):

        def setup_ui(self):
            # Builds ui elements.


    # launch my app
    if __name__ == '__main__':
        MyAppMainWindow.launch()
"""

import os
import inspect
import webbrowser
import __main__

from mhy.qt.core import QtCore, QtWidgets, QtCompat
import mhy.qt.core.utils as utils


__all__ = ['get_window_class']


_SINGLE_UI_KEY = __name__ + '_mhy_single_ui'
_MULT_UI_KEY = __name__ + '_mhy_multi_ui'
_ORG_NAME = 'MHY'


class MainWindowMixin(object):
    """
    A mixin class to combine with QMainWindow.
    """

    # the app name of this window (MUST be unique!)
    _APP_NAME = None

    # A link to the app's help webpage.
    # If not None, a help menu will be created.
    _HELP_URL = None

    # The default window size
    _DEFAULT_SIZE = (300, 300)

    # The default window position
    _DEFAULT_POSITION = (0, 0)

    # If True, only 1 window of this app is allowed at any time.
    # Otherwise users can instantiate as many windows as they want.
    _IS_SINGLETON = True

    # This works only with singleton instance deciding if a new instance
    # need to be created when class is called while an instance already exists
    _REUSE_SINGLETON = True

    # If True, app settings will be tracked ands stored on disk.
    _TRACK_SETTINGS = True

    # A .ui file to load on init.
    _UI_FILE = None

    def __init__(self, parent=None):
        """Initializes a main window object."""
        if not parent:
            parent = utils.get_root_window()

        super(MainWindowMixin, self).__init__(parent)
        if self._UI_FILE:
            QtCompat.loadUi(self._UI_FILE, self)

        self.__settings_loaded = False

        # load ui elements from the .ui file
        if hasattr(self, 'setupUi'):
            self.setupUi(self)
        # build user widgets
        self.setup_ui()
        # build default widgets
        self.__setup_default_menu_items()

        # set window title to be the app name
        self.setWindowTitle(self._APP_NAME)
        # load base stylesheet
        self.setStyleSheet(utils.get_stylesheet('dark'))

        # close this window when the parent app quits
        app = QtWidgets.QApplication.instance()
        if app:
            app.aboutToQuit.connect(self.close)

    def closeEvent(self, event):
        """
        The deleteOnClose attribute is set here so its only used when
        the window is actually closed, so the window is deleted and
        all its signals (like timers) are cleaned up.
        """
        if self._TRACK_SETTINGS:
            try:
                self.save_settings()
            except BaseException:
                print('Failed saving settings for {}'.format(self._APP_NAME))

    def showEvent(self, event):
        """Loads window settings."""
        if not self.__settings_loaded and self._TRACK_SETTINGS:
            self.load_settings()
            self.__settings_loaded = True

    # --- app settings

    @property
    def _qsettings(self):
        """Returns the QSettings object for this window"""
        return QtCore.QSettings(_ORG_NAME, self._APP_NAME)

    def save_settings(self):
        """Updates the app settings and saves it to disk.

        Returns:
            QSettings: The settings object.
        """
        settings = self._qsettings

        settings.beginGroup('main_window')
        maxed = self.isMaximized()
        settings.setValue('maximized', maxed)
        if maxed:
            self.showNormal()
            QtWidgets.QApplication.processEvents()
            QtCore.QCoreApplication.processEvents()
        settings.setValue('size', self.size())
        settings.setValue('position', self.pos())
        settings.endGroup()

        settings.sync()
        return settings

    def load_settings(self):
        """Loads the app settings.

        Returns:
            QSettings: The settings object.
        """
        settings = self._qsettings

        settings.beginGroup('main_window')
        size = settings.value(
            'size', QtCore.QSize(*self._DEFAULT_SIZE))
        self.resize(size)
        pos = settings.value(
            'position', QtCore.QPoint(*self._DEFAULT_POSITION))
        self.move(pos)
        if settings.value('maximized', 'false') == 'true':
            self.showMaximized()
        settings.endGroup()

        return settings

    # --- ui elements

    def __setup_default_menu_items(self):
        """Creates default menu items."""
        menu_bar = self.menuBar()
        if menu_bar and self._HELP_URL:
            menu = menu_bar.addMenu('Help')
            action = menu.addAction('Get Help', self.open_help)
            action.setIcon(utils.get_icon('help.png'))

    def setup_ui(self):
        """Creates user UI elements.
        Each sub-class should implement it.
        """
        pass

    def open_help(self):
        """Opens the help webpage in the default browser."""
        if self._HELP_URL:
            webbrowser.open(self._HELP_URL)

    # --- window launching and instance management

    @classmethod
    def _ui_key(cls):
        """Returns the key for this UI."""
        return '{}.{}'.format(cls._APP_NAME, cls.__name__)

    @classmethod
    def launch(cls, *args, **kwargs):
        """Creates an instance of this window and launch it.

        Args:
            *args: Window creation arguments.
            *kwargs: Window creation keyword arguments.

        Returns:
            QMainWindow: The launched window.
        """
        # First, find out if a QApp already exists.
        # If it does not, this is a standalone and the app should be managed
        app_key = __name__ + '_qtapp'
        no_app_found = False
        app = __main__.__dict__.setdefault(app_key, None)
        if not app:
            app = QtWidgets.QApplication.instance()
            if not app:
                no_app_found = True
                app = QtWidgets.QApplication([])
            __main__.__dict__[app_key] = app

        key = cls._ui_key()

        if cls._IS_SINGLETON:
            # find and close existing window
            data = __main__.__dict__.setdefault(_SINGLE_UI_KEY, {})
            instance = data.get(key)
            if not utils.is_widget_valid(instance):
                instance = None

            if not cls._REUSE_SINGLETON and instance:
                # Destroy existing window
                instance.close()
                instance.setParent(None)
                instance = None

            if not instance:
                # create a new window instance
                instance = cls(*args, **kwargs)
                data[key] = instance

            # Show and raise instance to top level
            instance.show()
            instance.raise_()

        else:
            data = __main__.__dict__.setdefault(_MULT_UI_KEY, {})
            windows = [x for x in data.get(key, []) if utils.is_widget_valid(x)]

            instance = cls(*args, **kwargs)
            instance.show()
            windows.append(instance)
            data[key] = windows

        if no_app_found:
            # no app found means this is the first window of the app, so hang
            # on the main loop
            app.exec_()

        return instance

    @classmethod
    def get_instances(cls, visible_only=False):
        """Returns the instances of this UI.

        Args:
            visible_only (bool): If True, only returns the visible instances.

        Returns:
            list: A list of window instances.
        """
        key = cls._ui_key()
        windows = []
        if cls._IS_SINGLETON:
            data = __main__.__dict__.get(_SINGLE_UI_KEY, {})
            window = data.get(key)
            if window:
                windows = [window]
        else:
            data = __main__.__dict__.get(_MULT_UI_KEY, {})
            windows = data.get(key, [])

        if visible_only:
            return [x for x in windows
                    if utils.is_widget_valid(x) and x.isVisible()]
        else:
            return [x for x in windows if utils.is_widget_valid(x)]

    @classmethod
    def close_instances(cls, visible_only=False):
        """Closes all instances of this UI.

        Args:
            visible_only (bool): If True, only closes the visible instances.

        Returns:
            None
        """
        for each in cls.get_instances(visible_only=visible_only):
            each.close()


def get_window_class(app_name, ui_file=None, track_settings=True):
    """Dynamically builds and a main window class.

    Args:
        app_name (str): Name of the app to inherit the main window.
            It MUST be unique!
        ui_file (str): If not None, load ui from this .ui file.
            Supports absolute path or relative path to the caller module.
        track_settings (bool): If True, saves widget settings on close
            and loads them back up on open.

    Returns:
        BaseMainWindow: The class built.
    """
    if ui_file:
        if not ui_file.endswith('.ui'):
            ui_file += '.ui'

        if not os.path.isfile(ui_file) or not os.path.isabs(ui_file):
            # resolve partial path into full path based on the call stack
            #
            # back up one from the current frame
            frame = inspect.currentframe().f_back
            # grab the filename from the code object
            modpath = frame.f_code.co_filename
            base_directory = os.path.dirname(modpath)
            resolve_path = os.path.join(base_directory, ui_file)

            if os.path.isfile(resolve_path):
                ui_file = resolve_path
            else:
                raise ValueError(
                    'UI file not found or not valid: {}'.format(ui_file))

    class DynBaseWindow(MainWindowMixin, QtWidgets.QMainWindow):

        _APP_NAME = app_name
        _TRACK_SETTINGS = track_settings
        _UI_FILE = ui_file

    return DynBaseWindow
