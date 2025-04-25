"""
Icon lib UI is a standalone qt dialog that allows ui to browse and pick
icon from MHY package
"""
from mhy.qt.core import QtWidgets, QtGui, QtCore
from mhy.qt.icon_lib.ui.widget import IconLayoutWidget
import sys


def resolve_script(sub_dir, color=None):
    """
    Resolve a runnable script to get an icon or pixmap instance
    Args:
        sub_dir(str): A sub directory used to search image file from MHY_ICON_PATH env var
        color(None or str or list or tuple): If override color on top of original image

    Returns:
        str: A script snippet

    """
    if not color:
        script = "from mhy.qt.icon_lib.api import get_icon, get_pixmap\n\n" \
                  "icon = get_icon(sub_dir='{0}')\n\n" \
                  "pixmap = get_pixmap(sub_dir='{0}')".format(sub_dir)
    else:
        script = "from mhy.qt.icon_lib.api import get_icon, get_pixmap\n\n" \
                 "icon = get_icon(sub_dir='{0}', color={1})\n\n" \
                 "pixmap = get_pixmap(sub_dir='{0}', color={1})".format(sub_dir, color)
    return script


class MainWindow(QtWidgets.QDialog):
    def __init__(self, icon_containers):
        super(MainWindow, self).__init__()
        self.setWindowTitle("MHY Icon Library")
        main_layout = QtWidgets.QHBoxLayout(self)

        self.preview_overlay_color = QtGui.QColor(0, 0, 0)

        icon_browser = QtWidgets.QWidget(self)
        icon_browser_layout = QtWidgets.QVBoxLayout(icon_browser)

        self.search_text = QtWidgets.QLineEdit(self)
        self.search_text.setPlaceholderText("Search Icons By Names")

        self.all_containers = icon_containers
        self.selected_icon_data = dict()
        self.selected_icon_instance = None
        self.current_preview_pix = None

        self.icon_widget = IconLayoutWidget(self)

        icon_browser_layout.addWidget(self.search_text)
        icon_browser_layout.addWidget(self.icon_widget)

        icon_browser.setFixedWidth(595)
        icon_browser.setMinimumHeight(595)
        main_layout.addWidget(icon_browser)

        preview_layout = QtWidgets.QHBoxLayout()
        self.preview_icon = QtWidgets.QPushButton(self)
        self.preview_icon.setFixedSize(150, 150)

        preview_config_layout = QtWidgets.QGridLayout()
        format_label = QtWidgets.QLabel("Format:")
        format_label.setFixedWidth(80)
        self.format_combo = QtWidgets.QComboBox(self)
        preview_config_layout.addWidget(format_label, 0, 0)
        preview_config_layout.addWidget(self.format_combo, 0, 1)

        size_label = QtWidgets.QLabel("Size:")
        size_label.setFixedWidth(80)
        self.size_combo = QtWidgets.QComboBox(self)
        preview_config_layout.addWidget(size_label, 1, 0)
        preview_config_layout.addWidget(self.size_combo, 1, 1)

        color_label = QtWidgets.QLabel("Pick Color:")
        color_label.setFixedWidth(80)
        self.color_picker = QtWidgets.QPushButton(self)
        # self.color_picker.setFixedSize(40, 40)
        self.color_picker.setStyleSheet("background-color: black")
        preview_config_layout.addWidget(color_label, 2, 0)
        preview_config_layout.addWidget(self.color_picker, 2, 1)

        preview_layout.addWidget(self.preview_icon)
        preview_layout.addLayout(preview_config_layout)
        icon_browser_layout.addLayout(preview_layout)

        self.code_editor = QtWidgets.QTextEdit(self)
        self.code_editor.setFixedHeight(240)
        self.code_editor.setReadOnly(True)
        self.code_editor.setText(resolve_script('', None))
        icon_browser_layout.addWidget(self.code_editor)

        self.icon_widget.populate_items(self.all_containers)
        self.search_text.editingFinished.connect(self.update_search)
        self.icon_widget.sel_changed_signal.connect(self.update_preview_cb)
        self.color_picker.clicked.connect(self.launch_color_picker)
        self.format_combo.currentTextChanged.connect(self.refresh_size_options)
        self.size_combo.currentTextChanged.connect(self.icon_size_changed_cb)

    def launch_color_picker(self):
        color_picker = QtWidgets.QColorDialog(self)
        result = color_picker.exec_()
        if result:
            color = color_picker.selectedColor()
            self.preview_overlay_color = color
            self.color_picker.setStyleSheet("background-color:rgb({},{},{})".format(
                 color.red(), color.green(), color.blue()))

            if self.current_preview_pix:
                mask = self.current_preview_pix.mask()
                self.current_preview_pix.fill(self.preview_overlay_color)
                self.current_preview_pix.setMask(mask)
                self.preview_icon.setIcon(self.current_preview_pix)
            self.update_script_snippet()

    def update_search(self):
        search_text = self.search_text.text()
        if not search_text:
            items = self.all_containers
        else:
            items = [i for i in self.all_containers if search_text in i.name]
        self.icon_widget.populate_items(items)

    def update_preview_cb(self, inst):
        self.format_combo.blockSignals(True)
        self.size_combo.blockSignals(True)
        self.format_combo.clear()
        self.size_combo.clear()
        self.selected_icon_data = dict()
        self.preview_overlay_color = QtGui.QColor()
        if not inst:
            self.selected_icon_instance = None
            self.preview_icon.setIcon(QtGui.QIcon())
            self.current_preview_pix = None
            self.update_script_snippet()

        else:
            self.selected_icon_instance = inst
            scaled_map = inst.icon.scaled(QtCore.QSize(150, 150))
            self.preview_icon.setIconSize(QtCore.QSize(150, 150))
            self.preview_icon.setIcon(scaled_map)
            self.current_preview_pix = scaled_map

            for child in self.selected_icon_instance.container.children:
                ext = child.file_ext.replace('.', '')
                if ext not in self.selected_icon_data:
                    self.selected_icon_data[ext] = []
                if child.size is not None:
                    self.selected_icon_data[ext].append((child, child.size))
                else:
                    self.selected_icon_data[ext].append((child, None))

            self.format_combo.addItems(self.selected_icon_data.keys())
            self.refresh_size_options()

        self.color_picker.setStyleSheet("background-color: black")
        self.format_combo.blockSignals(False)
        self.size_combo.blockSignals(False)

    def refresh_size_options(self):
        self.size_combo.blockSignals(True)
        self.size_combo.clear()
        current_format = self.format_combo.currentText()
        supported_children = self.selected_icon_data.get(current_format, [])
        size_options = []
        for child in supported_children:
            if child[1] is not None:
                size_options.append(child[1])

        if not size_options:
            self.size_combo.setDisabled(True)
            self.update_script_snippet()
            return
        size_options.sort()
        size_options = [str(i) for i in size_options]
        self.size_combo.setEnabled(True)
        self.size_combo.addItems(size_options)
        self.update_script_snippet()
        self.size_combo.blockSignals(False)

    def icon_size_changed_cb(self):
        self.update_script_snippet()

    def update_script_snippet(self):
        format = self.format_combo.currentText()
        size = self.size_combo.currentText() or None
        icon = self.selected_icon_instance.find_child(format=format, size=size)
        color = [self.preview_overlay_color.red(),
                 self.preview_overlay_color.green(),
                 self.preview_overlay_color.blue()]
        if color == [0, 0, 0]:
            color = None
        self.code_editor.setText(resolve_script(icon.relative_path, color))


if __name__ == '__main__':
    import mhy.qt.icon_lib.api as api
    cache = api.start_cache()
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow(cache)
    window.show()
    sys.exit(app.exec_())
