import os
import webbrowser
from functools import wraps

import maya.api.OpenMaya as om
import maya.cmds as cmds


def load_plugin_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            res = func(*args, **kwargs)
        except:
            om.MGlobal.displayError( "Unable to load 'nsrigSmooth', please make sure the plugin exists in 'MAYA_PLUG_IN_PATH'" )
        return res

    return wrapper


class NsRigOptionsWindow(object):
    """Base class"""

    help_url = os.getenv(
        "NsRigSmooth_HELP_URL", "https://km.mihoyo.com/articleBase/767/194700"
    )

    @classmethod
    def show_ui(cls):
        win = cls()
        win.create()
        return win

    def __init__(self):
        self.window = "NsOptionsWindow"
        self.title = "nsRig Options"
        self.size = (546, 350)
        self.supportsToolAction = False
        self.actionName = "Apply and Close"

    def create(self):
        if cmds.window(self.window, exists=True):
            cmds.deleteUI(self.window, window=True)
        self.window = cmds.window(
            self.window, title=self.title, widthHeight=self.size, menuBar=True
        )
        self.mainForm = cmds.formLayout(nd=100)
        # NOTES(pinngzhang):create menu items and buttons
        self.common_menu()
        self.common_buttons()
        self.options_border = cmds.tabLayout(
            scrollable=True,
            tabsVisible=False,
            height=1,
            childResizable=True,
            innerMarginWidth=300,
        )
        cmds.formLayout(
            self.mainForm,
            e=True,
            attachForm=(
                [self.options_border, "top", 0],
                [self.options_border, "left", 2],
                [self.options_border, "right", 2],
            ),
            attachControl=([self.options_border, "bottom", 5, self.apply_btn]),
        )

        self.display_options()

        cmds.showWindow()

    def common_menu(self):
        self.edit_menu = cmds.menu(label="Edit")
        self.edit_menu_save = cmds.menuItem(
            label="Save Settings", command=self.edit_menu_save_cmd
        )
        self.edit_menu_reset = cmds.menuItem(
            label="Reset Settings", command=self.edit_menu_reset_cmd
        )
        self.edit_menu_div = cmds.menuItem(d=True)
        self.edit_menu_radio = cmds.radioMenuItemCollection()
        self.edit_menu_tool = cmds.menuItem(
            label="As Tool",
            radioButton=True,
            enable=self.supportsToolAction,
            command=self.edit_menu_tool_cmd,
        )
        self.edit_menu_action = cmds.menuItem(
            label="As Action",
            radioButton=True,
            enable=self.supportsToolAction,
            command=self.edit_menu_action_cmd,
        )
        self.help_menu = cmds.menu(label="Help")
        self.help_menu_item = cmds.menuItem(
            label="Help on %s" % self.title, command=self.help_menu_cmd
        )

    def help_menu_cmd(self, *args):
        webbrowser.open_new(self.help_url)

    def edit_menu_save_cmd(self, *args):
        raise NotImplementedError

    def edit_menu_reset_cmd(self, *args):
        raise NotImplementedError

    def edit_menu_tool_cmd(self, *args):
        raise NotImplementedError

    def edit_menu_action_cmd(self, *args):
        raise NotImplementedError

    def action_btn_cmd(self, *args):
        self.apply_btn_cmd()
        self.close_btn_cmd()

    def apply_btn_cmd(self, *args):
        raise NotImplementedError

    def close_btn_cmd(self, *args):
        cmds.deleteUI(self.window, window=True)

    def common_buttons(self):
        self.common_btn_size = ((self.size[0] - 18) / 3, 26)
        self.action_btn = cmds.button(
            label=self.actionName,
            height=self.common_btn_size[1],
            command=self.action_btn_cmd,
        )
        self.apply_btn = cmds.button(
            label="Apply", height=self.common_btn_size[1], command=self.apply_btn_cmd
        )
        self.close_btn = cmds.button(
            label="Close", height=self.common_btn_size[1], command=self.close_btn_cmd
        )
        cmds.formLayout(
            self.mainForm,
            e=True,
            attachForm=(
                [self.action_btn, "left", 5],
                [self.action_btn, "bottom", 5],
                [self.apply_btn, "bottom", 5],
                [self.close_btn, "bottom", 5],
                [self.close_btn, "right", 5],
            ),
            attachPosition=(
                [self.action_btn, "right", 1, 33],
                [self.close_btn, "left", 0, 67],
            ),
            attachControl=(
                [self.apply_btn, "left", 4, self.action_btn],
                [self.apply_btn, "right", 4, self.close_btn],
            ),
            attachNone=(
                [self.action_btn, "top"],
                [self.apply_btn, "top"],
                [self.close_btn, "top"],
            ),
        )

    def display_options(self):
        cmds.setUITemplate("DefaultTemplate", pushTemplate=1)
        self.options_content()
        cmds.setUITemplate(popTemplate=True)

    def options_content(self):
        raise NotImplementedError


class NsRigSmoothOptionsWindow(NsRigOptionsWindow):
    def __init__(self):
        super(NsRigSmoothOptionsWindow, self).__init__()

        self.title = "nsrigSmooth Options"
        self.actionName = "Create"
        self.smooth_iter_value = 20
        self.plugin_name = "nsrigSmooth"

    @load_plugin_error
    def load_plugin(self, plugin):
        cmds.loadPlugin(plugin, qt=1)

    def options_content(self):
        cmds.columnLayout(adjustableColumn=1, columnAttach=("right", 20))

        # NOTES(pinngzhang):nsrigSmooth Node
        self.node_name = cmds.textFieldGrp(label="nsrigSmooth Node: ")

        # NOTES(pinngzhang):Reference Geometry
        self.ref_geometry = cmds.checkBoxGrp(
            label="Create Reference Geometry: ", ncb=1, v1=1
        )

        # NOTES(pinngzhang):Weighting Scheme
        self.weight_scheme = cmds.optionMenuGrp(label="Weighting Scheme: ")
        cmds.menuItem(label="Uniform")
        cmds.menuItem(label="Cotangent")
        cmds.menuItem(label="Span-Aware")

        # NOTES(pinngzhang):Smoothing Direction
        self.smooth_direction = cmds.optionMenuGrp(label="Smoothing Direction: ")
        cmds.menuItem(label="Surrouding")
        cmds.menuItem(label="UV")

        # NOTES(pinngzhang):Smoothing Iteration
        self.smooth_iterations = cmds.intSliderGrp(
            label="Smoothing Iterations: ",
            minValue=0,
            maxValue=100,
            v=self.smooth_iter_value,
            field=True,
        )

    def apply_btn_cmd(self, *args):
        # NOTES(pinngzhang): get settings
        node_name = cmds.textFieldGrp(self.node_name, q=True, text=True)
        weight_scheme = cmds.optionMenuGrp(self.weight_scheme, q=True, select=True)
        smooth_dire = cmds.optionMenuGrp(self.smooth_direction, q=True, select=True)
        smooth_iter = cmds.intSliderGrp(self.smooth_iterations, q=True, value=True)
        ref_geo = cmds.checkBoxGrp(self.ref_geometry, q=True, value1=True)
        self.create_deformer(
            node_name,
            weight_scheme,
            smooth_dire,
            smooth_iter,
            ref_geo,
        )

    def create_deformer(
        self,
        node_name=None,
        weight_scheme=None,
        smooth_dire=None,
        smooth_iter=None,
        ref_geo=True,
    ):
        self.load_plugin(self.plugin_name)

        selected_objs = cmds.ls(sl=1)
        if len(selected_objs) < 1:
            cmds.headsUpMessage("Please select mesh(es) to create deformer.", t=0.8)

        for obj in selected_objs:
            # NOTES(pinngzhang):create defult reference geometry
            if ref_geo:
                m_obj = self.get_depend_node(obj)
                dup_obj = self.duplicate_reference(m_obj)
                new_name = self.rename_reference(dup_obj, obj)

            # NOTES(pinngzhang):set settings
            kwargs = {"n": node_name} if node_name else {}
            deformer = cmds.deformer(obj, type="nsrigSmooth", **kwargs)
            cmds.setAttr(
                "%s.%s" % (deformer[0], "weightingScheme"),
                weight_scheme - 1 if weight_scheme else 1,
            )
            cmds.setAttr(
                "%s.%s" % (deformer[0], "smoothingDirection"),
                smooth_dire - 1 if smooth_dire else 1,
            )
            cmds.setAttr(
                "%s.%s" % (deformer[0], "smoothingIterations"),
                smooth_iter if smooth_iter else self.smooth_iter_value,
            )
            if ref_geo:
                cmds.connectAttr(
                    "%s.%s" % (new_name, "outMesh"),
                    "%s.%s" % (deformer[0], "referenceGeometry"),
                )

    def get_depend_node(self, name):
        if cmds.objExists(name):
            selection = om.MSelectionList()
            selection.add(name)
            return selection.getDependNode(0)

    def duplicate_reference(self, obj):
        dag_node = om.MFnDagNode(obj)
        dup_obj = dag_node.duplicate()
        dup_dag_node = om.MFnDagNode(dup_obj)
        cmds.hide(dup_dag_node.name())

        return dup_obj

    def rename_reference(self, dup_obj, name):
        dg_modifier = om.MDGModifier()
        new_name = name + "Ref"
        dg_modifier.renameNode(dup_obj, new_name)
        dg_modifier.doIt()
        return new_name

    def edit_menu_reset_cmd(self, *args):
        cmds.textFieldGrp(self.node_name, e=True, text="")
        cmds.optionMenuGrp(self.weight_scheme, e=True, select=1)
        cmds.optionMenuGrp(self.smooth_direction, e=True, select=1)
        cmds.intSliderGrp(self.smooth_iterations, e=True, value=self.smooth_iter_value)
        cmds.checkBoxGrp(self.ref_geometry, e=True, v1=1)
