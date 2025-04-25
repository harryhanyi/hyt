import webbrowser
from imp import reload

import maya.cmds
import maya.internal.common.cmd.base as cmdbase
import maya.internal.common.utils.ui as ui_utils
import maya.mel

import nsrigProximityMapUtils as utils

reload(utils)

HELP_DOC_URL = "https://km.mihoyo.com/articleBase/767/223440"


def open_help_doc(*args):
    webbrowser.open_new(HELP_DOC_URL)


# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------
class Command(cmdbase.Command):
    def __init__(self):
        super(Command, self).__init__()

        self.commandName = utils.NODE_TYPE_NAME
        self.commandHelpTag = utils.NODE_TYPE_NAME
        self.commandTitle = "%s Options" % utils.NODE_TYPE_NAME
        self.optionVarPrefix = utils.NODE_TYPE_NAME

        self.optionVarDefaults.update(
            {
                "radius": utils.DEFAULT_SETTINGS["radius"],
                "blendOperator": utils.DEFAULT_SETTINGS["blendOperator"],
                "smoothingIterations": utils.DEFAULT_SETTINGS["smoothingIterations"],
                "createWeightShader": True,
            }
        )

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        result = None

        try:
            result = utils.createBySelection("", True, kwargs["createWeightShader"])
        except Exception as e:
            raise (e)

        deformerNode = result
        settableAttrs = [
            "radius",
            "blendOperator",
            "smoothingIterations",
        ]
        cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)
        returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addOptionDialogWidgets(self):
        widgetDict = {}  # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            # radius
            widget = ui_utils.floatSliderGrp(
                "Radius", 0.0, 100.0, True, True, value=utils.DEFAULT_SETTINGS["radius"]
            )
            widgetDict["radius"] = (maya.cmds.floatSliderGrp, widget)

            # blendOperator
            opts = [
                ("Closest Point", 0),
                ("Add", 1),
                ("Max", 2),
            ]
            widget, lookup = ui_utils.createOptionMenu("Blend operator", options=opts)
            self.optionMenuGrp_labelToEnum["blendOperator"] = lookup
            widgetDict["blendOperator"] = (maya.cmds.optionMenuGrp, widget)

            # smoothingIterations
            widget = ui_utils.intSliderGrp(
                "Smoothing iterations",
                0,
                20,
                True,
                True,
                value=utils.DEFAULT_SETTINGS["smoothingIterations"],
            )
            widgetDict["smoothingIterations"] = (maya.cmds.intSliderGrp, widget)

            # createWeightShader
            widget = ui_utils.checkBoxGrp("Create Weight Shader")
            widgetDict["createWeightShader"] = (maya.cmds.checkBoxGrp, widget)

        return widgetDict

    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval("getOptionBoxHelpItem()")
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
