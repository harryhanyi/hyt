from functools import partial

from maya import cmds, OpenMaya

from mhy.qt.core import QtGui, QtCore, QtWidgets
from mhy.qt.core.widgets.buttons import ColorPushButton

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
from mhy.maya.utils import undoable, repeatable

import mhy.maya.rig.constants as const
import mhy.maya.rig.rig_global as rg


ENUM_ATTRS = ('shapeType',)
BOOL_ATTRS = ('xrayMode',)


class CtrlShapeWidget(QtWidgets.QWidget):
    """
    A widget for modifying ctrl shapes.
    """

    def __init__(self, *args, **kwargs):
        super(CtrlShapeWidget, self).__init__(*args, **kwargs)

        central_layout = QtWidgets.QVBoxLayout()
        self.setLayout(central_layout)

        # settings
        grid = QtWidgets.QGridLayout()
        central_layout.addLayout(grid)

        self.lb_sel = QtWidgets.QLineEdit()
        self.lb_sel.setReadOnly(True)
        grid.addWidget(QtWidgets.QLabel('Selection: '), 0, 0, 1, 1)
        grid.addWidget(self.lb_sel, 0, 1, 1, 1)

        i = 1
        for attr in ENUM_ATTRS:
            cbx = QtWidgets.QComboBox()
            setattr(self, attr, cbx)
            cbx.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            cbx.currentIndexChanged.connect(partial(self.set_attr, attr))
            grid.addWidget(QtWidgets.QLabel(attr + ': '), i, 0, 1, 1)
            grid.addWidget(cbx, i, 1, 1, 1)
            i += 1

        # toggles
        for attr in BOOL_ATTRS:
            cbx = QtWidgets.QCheckBox()
            setattr(self, attr, cbx)
            cbx.toggled.connect(partial(self.set_attr, attr))
            grid.addWidget(QtWidgets.QLabel(attr + ': '), i, 0, 1, 1)
            grid.addWidget(cbx, i, 1, 1, 1)
            i += 1

        # color
        hbox = QtWidgets.QHBoxLayout()
        grid.addWidget(QtWidgets.QLabel('Color: '), i, 0, 1, 1)
        grid.addLayout(hbox, i, 1, 1, 1)

        self.btn_color = ColorPushButton(default=QtGui.QColor(30, 30, 30))
        self.btn_color.color_changed.connect(self.set_color)
        self.btn_color.setMaximumWidth(100)
        hbox.addWidget(self.btn_color)

        self.btn_color_auto = QtWidgets.QPushButton('Auto')
        self.btn_color_auto.clicked.connect(self.set_color_auto)
        self.btn_color_auto.setMaximumWidth(100)
        hbox.addWidget(self.btn_color_auto)
        hbox.addStretch(10)

        # transform
        gbx = QtWidgets.QGroupBox('Transform')
        central_layout.addWidget(gbx)
        grid = QtWidgets.QGridLayout()
        gbx.setLayout(grid)

        grid.addWidget(QtWidgets.QLabel('Space: '), 0, 0, 1, 1)
        hbox = QtWidgets.QHBoxLayout()
        grid.addLayout(hbox, 0, 1, 1, 1)
        self.rb_local = QtWidgets.QRadioButton('Local')
        hbox.addWidget(self.rb_local)
        self.rb_world = QtWidgets.QRadioButton('World')
        hbox.addWidget(self.rb_world)
        self.rb_local.setChecked(True)
        self.rb_world.toggled.connect(self.refresh)
        hbox.addStretch(10)

        i = 1
        for attr, step, icon in zip(
                ('Position', 'Rotate', 'Scale'),
                (1, 10, .5),
                ('HIKCustomRigToolTranslate',
                 'HIKCustomRigToolRotate',
                 'polyScaleUV')):
            lb = QtWidgets.QLabel()
            lb.setPixmap(QtGui.QPixmap(':/{}.png'.format(icon)))
            grid.addWidget(lb, i, 0, 1, 1)

            sbx = QtWidgets.QDoubleSpinBox()
            sbx.setPrefix('Step: ')
            sbx.setRange(0, 99999)
            sbx.setValue(step)
            sbx.setSingleStep(step)
            sbx.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding,
                QtWidgets.QSizePolicy.Expanding)
            grid.addWidget(sbx, i, 1, 1, 1)
            sbx.valueChanged.connect(
                partial(self.update_step, attr))
            setattr(self, attr, sbx)

            j = 2
            for ax, color in zip(
                    'XYZ', ((66, 33, 28), (28, 66, 40), (28, 36, 66))):
                sbx = QtWidgets.QDoubleSpinBox()
                sbx.setRange(-99999, 99999)
                sbx.setPrefix(ax + ': ')
                sbx.setSingleStep(step)
                sbx.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Expanding)
                grid.addWidget(sbx, i, j, 1, 1)
                sbx.setStyleSheet(
                    ('QDoubleSpinBox{{'
                     'background-color: rgb({}, {}, {});}}').format(*color))
                sbx.valueChanged.connect(
                    partial(self.xform_ctrl, attr))
                setattr(self, attr + ax, sbx)
                j += 1

            i += 1

            if attr == 'Scale':
                lb = QtWidgets.QLabel('')
                lb.setPixmap(QtGui.QPixmap(':/{}.png'.format(icon)))
                grid.addWidget(lb, i, 0, 1, 1)

                btn = QtWidgets.QPushButton()
                btn.setIcon(QtGui.QIcon(':/moveUVUp.png'))
                grid.addWidget(btn, i, 1, 1, 1)
                btn.clicked.connect(partial(self.scale_all, False))
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Expanding)

                btn = QtWidgets.QPushButton()
                btn.setIcon(QtGui.QIcon(':/moveUVDown.png'))
                grid.addWidget(btn, i, 2, 1, 1)
                btn.clicked.connect(partial(self.scale_all, True))
                btn.setSizePolicy(
                    QtWidgets.QSizePolicy.Expanding,
                    QtWidgets.QSizePolicy.Expanding)

            i += 1

        # mirror
        hbox = QtWidgets.QHBoxLayout()
        central_layout.addLayout(hbox)

        self.btn_mirror_sel = QtWidgets.QPushButton('Mirror Selected')
        self.btn_mirror_sel.clicked.connect(partial(self.mirror, sel=True))
        self.btn_mirror_sel.setFixedHeight(30)
        hbox.addWidget(self.btn_mirror_sel)
        self.btn_mirror_all = QtWidgets.QPushButton('Mirror All')
        self.btn_mirror_all.clicked.connect(partial(self.mirror, sel=False))
        self.btn_mirror_all.setFixedHeight(30)
        hbox.addWidget(self.btn_mirror_all)

        self.refresh()

    def enterEvent(self, event):
        """Refreshes this UI on cursor enter, based on current selection."""
        self.refresh()
        return super(CtrlShapeWidget, self).enterEvent(event)

    def get_ctrl_shapes(self, sel=True):
        """Returns a list of ctrl shape nodes.

        Args:
            sel (bool): If True, return selected shapes only.
                Otherwise return all ctrl shapes in the scene.

        Returns:
           list: ctrl shapes.
        """
        if sel:
            shape_set = set()
            shape_list = []
            for each in cmds.ls(selection=True, long=True):
                if each.rfind('.') != -1:
                    continue
                each = Node(each)
                if each.type_name == 'mhyController' and each not in shape_set:
                    shape_set.add(each)
                    shape_list.append(each)
                elif each.custom_type_name == 'MHYCtrl':
                    for shape in each.shapes:
                        if shape and shape not in shape_set:
                            shape_set.add(shape)
                            shape_list.append(shape)

            return shape_list

        shapes = []
        for ctrl in rg.RigGlobal().get_ctrls():
            shapes += ctrl.shapes
        return shapes

    def _set_signal_blocked(self, blocked):
        for each in ENUM_ATTRS + BOOL_ATTRS:
            getattr(self, each).blockSignals(blocked)
        for attr in ('Position', 'Rotate', 'Scale'):
            for ax in 'XYZ':
                getattr(self, attr + ax).blockSignals(blocked)
        self.btn_color.blockSignals(blocked)

    def reset(self):
        """Resets the entire UI."""
        self._set_signal_blocked(True)
        self.lb_sel.setText('None')
        for each in ENUM_ATTRS:
            getattr(self, each).clear()
        for each in BOOL_ATTRS:
            getattr(self, each).setChecked(False)
        self.btn_color.reset()
        for attr in ('Position', 'Rotate', 'Scale'):
            for ax in 'XYZ':
                getattr(self, attr + ax).setValue(0)
        self._set_signal_blocked(False)

    def refresh(self, *args, **kwargs):
        """Refresh the entire UI."""
        self.reset()

        self._set_signal_blocked(True)

        for each in ENUM_ATTRS + BOOL_ATTRS:
            getattr(self, each).blockSignals(True)

        shapes = self.get_ctrl_shapes(sel=True)
        if not shapes:
            return
        shape = shapes[-1]

        if len(shapes) > 1:
            self.lb_sel.setText('... ' + shape.name)
        else:
            self.lb_sel.setText(shape.name)

        for attr in ENUM_ATTRS:
            cbx = getattr(self, attr)
            attr = shape.attr(attr)
            cbx.addItems(attr.enum_names)
            cbx.setCurrentIndex(attr.value)

        for attr in BOOL_ATTRS:
            cbx = getattr(self, attr)
            cbx.setChecked(shape.attr(attr).value)

        # update color
        color = shape.attr('color').value
        color = QtGui.QColor(*[x * 255 for x in color])
        self.btn_color.color = color

        # update xform
        for attr in ('Position', 'Rotate', 'Scale'):
            val = None
            if self.rb_world.isChecked():
                if attr == 'Position':
                    val = shape.get_translation(space='world')
                elif attr == 'Rotate':
                    val = shape.get_rotation(space='world')
            if not val:
                val = shape.get_attr('local' + attr)

            for i, ax in enumerate('XYZ'):
                sbx = getattr(self, attr + ax)
                sbx.setValue(val[i])

        self._set_signal_blocked(False)

    @undoable
    @repeatable
    @QtCore.Slot()
    def set_attr(self, attr, val):
        for shape in self.get_ctrl_shapes(sel=True):
            shape.attr(attr).value = val

    @QtCore.Slot()
    def update_step(self, attr, step):
        for ax in 'XYZ':
            getattr(self, attr + ax).setSingleStep(step)

    @undoable
    @repeatable
    @QtCore.Slot()
    def set_color(self, color):
        """Sets the selected shape color.

        Args:
            color (QColor or tuple): A color to set.
                If tuple is used, it's range must be from 0 ~ 1.

        Returns:
            None
        """
        if isinstance(color, QtGui.QColor):
            color = [
                color.red() / 255.0,
                color.green() / 255.0,
                color.blue() / 255.0]
        for shape in self.get_ctrl_shapes(sel=True):
            shape.attr('color').value = color

    @undoable
    @repeatable
    @QtCore.Slot()
    def set_color_auto(self):
        """Auto sets the selected shape color.

        Returns:
            None
        """
        for shape in self.get_ctrl_shapes(sel=True):
            if NodeName.is_valid(shape):
                name = NodeName(shape)
                color = None
                if name.is_left:
                    color = const.COLOR_L
                elif name.is_right:
                    color = const.COLOR_R
                elif name.is_middle:
                    color = const.COLOR_M

                if color:
                    shape.attr('color').value = color
                    color = QtGui.QColor(*[x * 255 for x in color])
                    self.btn_color.color = color

    @undoable
    @repeatable
    @QtCore.Slot()
    def xform_ctrl(self, attr, *args):
        """Transforms the selected ctrls.

        Args:
            attr (str): An attribute to set.
            val (str): the value to set.

        Returns:
            None
        """
        space = 'world' if self.rb_world.isChecked() else 'object'

        shapes = self.get_ctrl_shapes(sel=True)
        new_value = []
        for ax in 'XYZ':
            new_value.append(getattr(self, attr + ax).value())
        new_value = OpenMaya.MVector(*new_value)

        if attr.startswith('Position'):
            old_value = shapes[-1].get_translation(space=space, as_tuple=True)
        elif attr.startswith('Rotate'):
            old_value = shapes[-1].get_rotation(space=space, as_tuple=True)
        else:
            old_value = shapes[-1].get_scale(space=space, as_tuple=True)
        old_value = OpenMaya.MVector(*old_value)

        delta = new_value - old_value

        for shape in shapes:
            if attr.startswith('Position'):
                value = shape.get_translation(space=space, as_tuple=True)
            elif attr.startswith('Rotate'):
                value = shape.get_rotation(space=space, as_tuple=True)
            else:
                value = shape.get_scale(space=space, as_tuple=True)
            value = OpenMaya.MVector(*value)

            value += delta

            if attr.startswith('Position'):
                shape.set_translation(value, space=space)
            elif attr.startswith('Rotate'):
                shape.set_rotation(value, space=space)
            else:
                shape.set_scale(value, space=space)

    @undoable
    @repeatable
    @QtCore.Slot()
    def scale_all(self, reverse=False):
        """Scales all channels.

        Returns:
            None
        """
        step = getattr(self, 'Scale').value()
        if reverse:
            step *= -1
        for ax in 'XYZ':
            sbx = getattr(self, 'Scale' + ax)
            sbx.setValue(sbx.value() + step)

    @undoable
    @repeatable
    @QtCore.Slot()
    def mirror(self, sel=False):
        is_world = self.rb_world.isChecked()
        ctrls = set()
        rig = rg.RigGlobal()

        if not rig.has_mirror_data:
            cmds.warning(
                ('Ctrl mirror data not found! '
                 'Measuring mirror axis... '
                 'Rig must be at bind pose!'))

        for shape in self.get_ctrl_shapes(sel=sel):
            ctrl = shape.get_parent()

            if ctrl in ctrls:
                continue
            if not NodeName.is_valid(ctrl):
                continue
            if not sel and not NodeName(ctrl).is_left:
                continue

            m_ctrl = NodeName(ctrl).flip()
            if not cmds.objExists(m_ctrl):
                continue
            m_ctrl = Node(m_ctrl)
            ctrls.add(ctrl)
            ctrls.add(m_ctrl)

            shape_count = len(ctrl.shapes)
            m_shape_count = len(m_ctrl.shapes)
            # TODO auto remove/create shapes
            if shape_count != m_shape_count:
                cmds.warning(
                    'Ctrl shape count doesn\'t match: {} - {}'.format(
                        ctrl, m_ctrl))
                continue

            mirror_data = None
            if not is_world:
                mirror_data = rig.get_ctrl_mirror_axis(ctrl)
                if mirror_data is None:
                    mirror_data = rg.measure_ctrl_mirror_axis(
                        ctrl, skip_locked=False)

            m_shapes = m_ctrl.shapes
            for i, shape in enumerate(ctrl.shapes):
                for attr in ENUM_ATTRS + BOOL_ATTRS:
                    m_shapes[i].attr(attr).value = shape.attr(attr).value

                color = shape.shape_color
                qcolor = QtGui.QColor(*[x * 255 for x in color])
                if qcolor == QtGui.QColor(*[x * 255 for x in const.COLOR_L]):
                    color = const.COLOR_R
                if qcolor == QtGui.QColor(*[x * 255 for x in const.COLOR_R]):
                    color = const.COLOR_L
                m_shapes[i].shape_color = color

                if is_world:
                    pos = list(
                        shape.get_translation(space='world', as_tuple=True))
                    pos[0] *= -1
                    m_shapes[i].set_translation(pos, space='world')
                    rot = list(shape.get_rotation(space='world', as_tuple=True))
                    rot[1] *= -1
                    rot[2] *= -1
                    m_shapes[i].set_rotation(rot, space='world')
                    scl = shape.get_scale(space='world', as_tuple=True)
                    m_shapes[i].set_scale(scl, space='world')

                elif not mirror_data:
                    continue
                else:
                    pos = list(shape.local_position)
                    rot = list(shape.local_rotate)
                    scl = shape.local_scale
                    for j, ax in enumerate('xyz'):
                        if ax in mirror_data[0]:
                            pos[j] *= -1
                        if ax in mirror_data[1]:
                            rot[j] *= -1
                    m_shapes[i].local_position = pos
                    m_shapes[i].local_rotate = rot
                    m_shapes[i].local_scale = scl
