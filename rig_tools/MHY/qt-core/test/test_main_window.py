import unittest

from mhy.qt.core import QtCore, QtWidgets, QtGui, QtCompat

import mhy.python.core.compatible as compat
import mhy.qt.core.utils as utils
import mhy.qt.core.base_main_window as mw


class TestMainWindow(unittest.TestCase):
    """
    Test the main window.
    """

    def setUp(self):
        import mhy.qt.core.utils as utils
        import mhy.qt.core.base_main_window as mw
        compat.reload(utils)
        compat.reload(mw)

    def test_stylesheet(self):
        if utils.RES_PATH:
            self.assertEqual(utils.list_stylesheet(), ['dark'])

    def test_launch_window(self):
        base_class = mw.get_window_class(
            app_name='my_app', track_settings=False)

        class MyMainWindow(base_class):

            _HELP_URL = 'https://git.woa.com/MHY/qt-core'

            def setup_ui(self):
                central_widget = QtWidgets.QScrollArea()
                central_widget.setWidgetResizable(True)
                central_widget.setAlignment(QtCore.Qt.AlignCenter)
                main_widget = QtWidgets.QGroupBox('Group')
                main_widget.setCheckable(True)
                central_widget.setWidget(main_widget)
                main_layout = QtWidgets.QVBoxLayout()
                main_widget.setLayout(main_layout)
                self.setCentralWidget(central_widget)

                icon = utils.get_icon('refresh', QtGui.QColor(255, 200, 12))
                btn = QtWidgets.QPushButton(icon, "Icon Button")
                btn.setToolTip('test button')
                main_layout.addWidget(btn)

                cb = QtWidgets.QCheckBox('Test Check Box')
                main_layout.addWidget(cb)

                rb = QtWidgets.QRadioButton('radio 1')
                main_layout.addWidget(rb)
                rb = QtWidgets.QRadioButton('radio 2')
                main_layout.addWidget(rb)

                menu_bar = self.menuBar()
                menu = menu_bar.addMenu('Menu')
                action = menu.addAction('Action1')
                action.setToolTip('action 1')
                menu.addSeparator()
                menu.addAction('Action2')

        win = MyMainWindow.launch()

        print('host: {}'.format(utils.HOST))
        if utils.HOST == 'maya':
            parent_widget = win.parentWidget()
            ptr = utils.OpenMayaUI.MQtUtil.mainWindow()
            maya_win = QtCompat.wrapInstance(
                compat.long(ptr), parent_widget.__class__)
            self.assertEqual(parent_widget, maya_win)

    def test_launch_window_from_ui(self):
        base_class = mw.get_window_class(
            app_name='my_app_with_ui', ui_file='test', track_settings=False)

        class MyMainWindow(base_class):

            _HELP_URL = 'https://git.woa.com/MHY/qt-core'

            def setup_ui(self):
                btn = QtWidgets.QPushButton('Test Button')
                btn.setToolTip('test button')
                self.centralLayout.addWidget(btn)

        MyMainWindow.launch()


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestMainWindow))
    unittest.TextTestRunner(failfast=True).run(suite)
