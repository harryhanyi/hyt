"""
This module create a maya model panel as a qt widget instance
"""
import os
import logging
import shiboken2

from PySide2 import QtCore, QtWidgets
import maya.cmds as cmds
import maya.OpenMayaUI as OpenMayaUI
from mhy.python.core.utils import increment_name, is_linux


__all__ = ["ModelPanelWidget", "ThumbnailWidget"]

logger = logging.getLogger(__name__)

DEFAULT_PLAYBLAST_RENDERER = None


class ModelPanelWidget(QtWidgets.QWidget):
    def __init__(self, name="modelPanelWidget", parent=None):
        super(ModelPanelWidget, self).__init__(parent=parent)
        unique_name = get_unique_name(name)
        self.setParent(parent)
        self.setObjectName(unique_name)
        self.main_layout = QtWidgets.QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setObjectName("modelPanelWidgetLayout")
        self.setLayout(self.main_layout)
        self.init_model_panel()

    def init_model_panel(self):
        full_name = self.get_full_name()
        self.__model_panel = cmds.modelPanel(parent=full_name)
        self.set_model_panel_options()
        # Hide the icon bar
        self.hide_icon_bar()

    def set_model_panel_options(self):

        model_panel = self.name()

        cmds.modelEditor(model_panel, edit=True, allObjects=False)
        cmds.modelEditor(model_panel, edit=True, grid=False)
        cmds.modelEditor(model_panel, edit=True, dynamics=False)
        cmds.modelEditor(model_panel, edit=True, activeOnly=False)
        cmds.modelEditor(model_panel, edit=True, manipulators=False)
        cmds.modelEditor(model_panel, edit=True, headsUpDisplay=False)
        cmds.modelEditor(model_panel, edit=True, selectionHiliteDisplay=False)

        cmds.modelEditor(model_panel, edit=True, polymeshes=True)
        cmds.modelEditor(model_panel, edit=True, nurbsSurfaces=True)
        cmds.modelEditor(model_panel, edit=True, subdivSurfaces=True)
        cmds.modelEditor(model_panel, edit=True, displayTextures=True)
        cmds.modelEditor(model_panel, edit=True, displayAppearance="smoothShaded")

        current_panel = current_model_panel()

        if current_panel:
            camera = cmds.modelEditor(
                current_panel,
                query=True,
                camera=True)
            display_lights = cmds.modelEditor(
                current_panel,
                query=True,
                displayLights=True)
            display_textures = cmds.modelEditor(
                current_panel,
                query=True,
                displayTextures=True)

            cmds.modelEditor(
                model_panel,
                edit=True,
                camera=camera)
            cmds.modelEditor(
                model_panel,
                edit=True,
                displayLights=display_lights)
            cmds.modelEditor(
                model_panel,
                edit=True,
                displayTextures=display_textures)

    # =================================
    # Icon bar methods
    # =================================

    @property
    def icon_bar(self):
        """
        Get the icon bar widget
        Returns:
            QtWidget: Icon bar widget
        """
        return self.model_panel().parent().children()[1]

    def hide_icon_bar(self):
        """ Hide icon bar """
        self.icon_bar.hide()

    def show_icon_bar(self):
        """ Show icon bar """
        self.icon_bar.show()

    def icon_bar_height(self):
        """
        Get the height of the icon bar widget
        Returns:
            int: The icon bar height
        """
        return self.icon_bar.height()

    def get_full_name(self):
        """
        Get the full, hierarchical name of this widget.
        This is the name which uniquely identifies the widget within maya
        and can be passed to Maya's UI commands
        Returns:

        """
        full_name = OpenMayaUI.MQtUtil.fullName(
            int(shiboken2.getCppPointer(self)[-1]))
        return full_name

    def name(self):
        """
        Get the object name of the created model panel
        Returns:
            str: The name
        """
        return self.__model_panel

    def model_panel(self):
        """
        Cast the model panel to a QWidget
        Returns:
            QtWidgets.QWidget:
        """
        ptr = OpenMayaUI.MQtUtil.findControl(self.__model_panel)
        return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)

    def bar_layout(self):
        name = cmds.modelPanel(self.__model_panel, query=True, barLayout=True)
        ptr = OpenMayaUI.MQtUtil.findControl(name)
        return shiboken2.wrapInstance(int(ptr), QtCore.QObject)

    def hide_bar_layout(self):
        self.bar_layout().hide()

    def hide_menu_bar(self):
        """ Hide the menu bar of this model panel """
        cmds.modelPanel(self.__model_panel, edit=True, menuBarVisible=False)

    def show_menu_bar(self):
        """ Show the menu bar of this model panel """
        cmds.modelPanel(self.__model_panel, edit=True, menuBarVisible=True)

    def set_camera(self, name):
        """
        Set the active camera of this model panel
        Args:
            name(str): The name of the camera

        """
        cmds.modelPanel(self.__model_panel, edit=True, cam=name)

    def do_playblast(self,
                     file_name,
                     start_frame,
                     end_frame,
                     width,
                     height,
                     step=1
                     ):

        """
            Wrapper for Maya's Playblast command.
        Args:
            file_name(str): The output file path
            start_frame(int or None):
            end_frame(int or None):
            width(int):
            height(int):
            step:

        Returns:

        """
        logger.info(u"Playblasting '{filename}'".format(filename=file_name))
        # Force output jpg image format
        cmds.setAttr('defaultRenderGlobals.imageFormat', 8)

        if start_frame == end_frame and os.path.exists(file_name):
            os.remove(file_name)

        frame = [i for i in range(start_frame, end_frame + 1, step)]

        model_panel = self.name()
        if cmds.modelPanel(model_panel, query=True, exists=True):
            cmds.setFocus(model_panel)
            if DEFAULT_PLAYBLAST_RENDERER:
                cmds.modelEditor(
                    model_panel,
                    edit=True,
                    rendererName=DEFAULT_PLAYBLAST_RENDERER
                )
        off_screen = is_linux()
        path = cmds.playblast(
            format="image",
            viewer=False,
            percent=100,
            quality=100,
            frame=frame,
            width=width,
            height=height,
            filename=file_name,
            endTime=end_frame,
            startTime=start_frame,
            offScreen=off_screen,
            forceOverwrite=True,
            showOrnaments=False,
        )

        if not path:
            raise PlayblastError("Playblast was canceled")

        src = path.replace("####", str(int(0)).rjust(4, "0"))

        if start_frame == end_frame:
            dst = src.replace(".0000.", ".")
            logger.info("Renaming '{}' => '{}".format(src, dst))
            os.rename(src, dst)
            src = dst

        logger.info(u"Playblasted '{}'".format(src))
        return src


class ThumbnailWidget(QtWidgets.QDialog):
    """
    This widget provide a minimum interface for user to export playblast
    sequence to a local disk

    Example:
        # User can either define output at initializing:
        ThumbnailWidget(out_directory=r"C:\tmp", file_name="img").show()

        # Or user can update the explicitly data after ui is initialized:
        ui = ThumbnailWidget()
        ui.set_config(out_directory=r"C:\tmp", file_name="img")
        ui.show()

        # Also, there's a convenient way to do one-line playblast
        ThumbnailWidget().do_playblast(out_directory=r"C:\tmp", file_name="img", start_frame=1, end_frame=50)
        # optional you can also set camera argument to do_play


    """

    thumb_nail_update_signal = QtCore.Signal(str)

    def __init__(self,
                 static=False,
                 width=500,
                 height=500,
                 out_directory=None,
                 file_name=None,
                 parent=None
                 ):
        super(ThumbnailWidget, self).__init__(parent=parent)
        self.setWindowTitle("Thumbnail Snapshot")
        unique_name = get_unique_name("thumbnailSnapshot")
        self.setObjectName(unique_name)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setObjectName("thumbnailSnapshotLayout")

        # Init playblast arguments
        self.set_config(file_name=file_name, )
        self.out_directory = None
        self.file_name = 'thumbnail'
        self.start_frame = None
        self.end_frame = None
        self.width = 500
        self.height = 500
        self.step = 1

        self.set_config(
            width=width,
            height=height,
            out_directory=out_directory,
            file_name=file_name)

        # Insert model panel widget
        self.snap_shot_view = ModelPanelWidget(parent=self)

        main_layout.addWidget(self.snap_shot_view)

        self.snap_shot_view.setFixedSize(
            self.width,
            self.height
        )

        config_group = QtWidgets.QGroupBox(self.tr("Timeline Options:"), self)
        v_layout = QtWidgets.QGridLayout(config_group)

        self.single_image_radio = QtWidgets.QRadioButton("Still Frame")
        self.time_line_radio = QtWidgets.QRadioButton("Whole Time Line")
        self.custom_range_radio = QtWidgets.QRadioButton("Custom Frame Range")

        v_layout.addWidget(self.single_image_radio, 0, 0)
        v_layout.addWidget(self.time_line_radio, 1, 0)
        v_layout.addWidget(self.custom_range_radio, 2, 0)

        self.start_frame_edit = QtWidgets.QLineEdit()
        self.to_label = QtWidgets.QLabel("-")
        self.end_frame_edit = QtWidgets.QLineEdit()

        self.start_frame = int(cmds.playbackOptions(minTime=True, query=True))
        self.end_frame = int(cmds.playbackOptions(maxTime=True, query=True))
        self.start_frame_edit.setText(str(self.start_frame))
        self.end_frame_edit.setText(str(self.end_frame))

        v_layout.addWidget(self.start_frame_edit, 2, 1)
        v_layout.addWidget(self.to_label, 2, 2)
        v_layout.addWidget(self.end_frame_edit, 2, 3)

        main_layout.addWidget(config_group)

        self.button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        v_layout.addWidget(self.button_box, 3, 0, 4, 0)

        self.connect_signals()

        if static:
            self.single_image_radio.setChecked(True)
        else:
            self.time_line_radio.setChecked(True)
        self.custom_frame_range_toggled_cb(False)

    def connect_signals(self):
        self.button_box.accepted.connect(self.create_thumbnails)
        self.button_box.rejected.connect(self.close)
        self.custom_range_radio.toggled.connect(
            self.custom_frame_range_toggled_cb)
        self.single_image_radio.toggled.connect(self.update_frame_range_cb)

        self.time_line_radio.toggled.connect(self.update_frame_range_cb)
        self.start_frame_edit.editingFinished.connect(
            self.update_frame_range_cb)
        self.end_frame_edit.editingFinished.connect(self.update_frame_range_cb)

    def set_config(self, **kwargs):
        for key, val in kwargs.items():
            if val is None:
                continue
            setattr(self, key, val)

    @QtCore.Slot()
    def custom_frame_range_toggled_cb(self, state):
        self.start_frame_edit.setEnabled(state)
        self.to_label.setEnabled(state)
        self.end_frame_edit.setEnabled(state)
        self.update_frame_range()

    @QtCore.Slot()
    def update_frame_range_cb(self):
        self.update_frame_range()

    def update_frame_range(self):
        if self.single_image_radio.isChecked():
            current_frame = int(cmds.currentTime(query=True))
            self.start_frame = current_frame
            self.end_frame = current_frame
            return
        if self.custom_range_radio.isChecked():
            self.start_frame = int(self.start_frame_edit.text())
            self.end_frame = int(self.end_frame_edit.text())
        else:
            self.start_frame = int(cmds.playbackOptions(
                minTime=True, query=True))
            self.end_frame = int(cmds.playbackOptions(
                maxTime=True, query=True))

    def create_thumbnails(self):
        """ Do playblast """
        if not (self.out_directory and self.file_name):
            raise PlayblastError(
                "Output directory or file name has not been initialized"
            )

        for img in os.listdir(self.out_directory):
            base_name = img.split('.')[0]
            if base_name == self.file_name:
                img_path = os.path.join(self.out_directory, img)
                os.remove(img_path)

        file_name = os.path.join(self.out_directory, self.file_name)
        self.snap_shot_view.do_playblast(
            file_name=file_name,
            start_frame=self.start_frame,
            end_frame=self.end_frame,
            width=self.width,
            height=self.height
        )
        self.thumb_nail_update_signal.emit(self.out_directory)
        self.close()

    def do_playblast(self,
                     out_directory,
                     file_name,
                     start_frame,
                     end_frame,
                     width=None,
                     height=None,
                     step=1,
                     camera=None):
        """
        Convenient method to playblast sequence images from this model panel
        to a given path
        Args:
            out_directory(str):
            file_name(str): Base name of exported image
            start_frame(int): The first frame
            end_frame(int): The last frame
            width(int): The width of exported image
            height(int): The height of exported image
            step(int): Playblast step
            camera(str): Force set camera for playblast

        """
        self.show()
        self.set_config(
            out_directory=out_directory,
            file_name=file_name,
            start_frame=start_frame,
            end_frame=end_frame,
            width=width,
            height=height,
            step=step)
        if camera is not None:
            self.snap_shot_view.set_camera(camera)
        self.create_thumbnails()


def current_model_panel():
    """
    Get the current model panel name.

    Returns:
        str: The name of the active model panel
    """
    current_panel = cmds.getPanel(withFocus=True)
    current_panel_type = cmds.getPanel(typeOf=current_panel)

    if current_panel_type not in ['modelPanel']:
        return None

    return current_panel


def get_unique_name(name):
    """

    Args:
        name:

    Returns:

    """
    ptr = OpenMayaUI.MQtUtil.findControl(name)
    if ptr:
        new_name = increment_name(name)
        return get_unique_name(new_name)

    return name


class PlayblastError(Exception):
    """Base class for exceptions in this module."""
    pass


if __name__ == "__main__":
    widget = ModelPanelWidget("modelPanel", None)
    widget.show()
