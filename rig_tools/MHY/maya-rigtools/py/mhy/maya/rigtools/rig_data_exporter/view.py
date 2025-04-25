from PySide2 import QtWidgets

from mhy.qt.core.base_main_window import get_window_class

import mhy.maya.rigtools.rig_data_exporter.data_widget as dw
import mhy.maya.rigtools.rig_data_exporter.ctrl_shape_widget as csw
import mhy.maya.rigtools.rig_data_exporter.export_set_widget as expw

# get the base main window class
base_class = get_window_class(app_name='MHY Rig Data Exporter')


class RigDataWindow(base_class):

    _REUSE_SINGLETON = False

    def setup_ui(self):
        self.central_widget = QtWidgets.QTabWidget()
        self.setCentralWidget(self.central_widget)

        self.data_tab = dw.DataWidget()
        self.central_widget.addTab(self.data_tab, 'Data')

        self.ctrl_tab = csw.CtrlShapeWidget()
        self.central_widget.addTab(self.ctrl_tab, 'Ctrl Shape')

        self.tag_tab = expw.ExportSetWidget()
        self.central_widget.addTab(self.tag_tab, 'Export Set')

    def save_settings(self):
        """Updates the app settings and saves it to disk.

        Returns:
            QSettings: The settings object.
        """
        settings = super(RigDataWindow, self).save_settings()

        settings.beginGroup('project')
        settings.setValue('workarea', self.data_tab.le_workarea.text())
        settings.setValue('project', self.data_tab.le_project.text())
        settings.setValue('char', self.data_tab.le_char.text())
        settings.setValue('is_body', self.data_tab.rb_type_body.isChecked())
        settings.endGroup()

        settings.beginGroup('deformer_io')
        settings.setValue(
            'export_method', self.data_tab.cbx_export_method.currentIndex())
        settings.setValue(
            'import_method', self.data_tab.cbx_import_method.currentIndex())
        settings.endGroup()

        settings.sync()
        return settings

    def load_settings(self):
        """Loads the app settings.

        Returns:
            QSettings: The settings object.
        """
        settings = super(RigDataWindow, self).load_settings()

        settings.beginGroup('project')
        self.data_tab.le_workarea.setText(settings.value('workarea', ''))
        self.data_tab.le_project.setText(settings.value('project', ''))
        self.data_tab.le_char.setText(settings.value('char', ''))
        is_body = settings.value('is_body', 'true')
        is_body = True if is_body == 'true' else False
        self.data_tab.rb_type_body.setChecked(is_body)
        self.data_tab.rb_type_face.setChecked(not is_body)
        settings.endGroup()

        settings.beginGroup('deformer_io')
        try:
            val = settings.value('export_method', 0)
            self.data_tab.cbx_export_method.setCurrentIndex(val)
        except BaseException:
            pass
        try:
            val = settings.value('import_method', 0)
            self.data_tab.cbx_import_method.setCurrentIndex(val)
        except BaseException:
            pass
        settings.endGroup()

        return settings


def launch():
    RigDataWindow.launch()
