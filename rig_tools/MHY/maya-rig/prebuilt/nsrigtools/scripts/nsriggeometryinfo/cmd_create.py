import webbrowser

import maya.cmds
import maya.internal.common.cmd.base as cmdbase
import maya.internal.common.utils.ui as ui_utils
import maya.mel

import nsrigGeometryInfoUtils as utils

HELP_DOC_URL = "https://km.mihoyo.com/articleBase/767/152579"


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
                "createReferenceGeometry": True,
                "measure": utils.DEFAULT_SETTINGS["measure"],
                "deltaComponent": utils.DEFAULT_SETTINGS["deltaComponent"],
                "displayMetricInfo": utils.DEFAULT_SETTINGS["displayMetricInfo"],
                "displayDeltaFlow": utils.DEFAULT_SETTINGS["displayDeltaFlow"],
                "createWeightShader": True,
                "geometryWeightIndex": 0,
            }
        )

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        result = None

        try:
            result = utils.createBySelection(
                "",
                False,
                kwargs["createReferenceGeometry"],
                kwargs["createWeightShader"],
                utils.WEIGHT_ATTRS[kwargs["geometryWeightIndex"]],
                skipSelect=True,
            )
        except Exception as e:
            raise (e)

        deformerNode = result
        settableAttrs = [
            "measure",
            "deltaComponent",
            "displayMetricInfo",
            "displayDeltaFlow",
        ]

        cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)
        returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addOptionDialogWidgets(self):
        widgetDict = {}  # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            # create reference geometry
            widget = ui_utils.checkBoxGrp("Create reference geometry")
            widgetDict["createReferenceGeometry"] = (maya.cmds.checkBoxGrp, widget)

            # measure
            opts = [
                ("Area", 0),
                ("Volume", 1),
                ("Length", 2),
            ]
            widget, lookup = ui_utils.createOptionMenu("Measure", options=opts)
            self.optionMenuGrp_labelToEnum["measure"] = lookup
            widgetDict["measure"] = (maya.cmds.optionMenuGrp, widget)

            # delta component
            opts = [
                ("XYZ", 0),
                ("X", 1),
                ("Y", 2),
                ("Z", 3),
            ]
            widget, lookup = ui_utils.createOptionMenu("Delta component", options=opts)
            self.optionMenuGrp_labelToEnum["deltaComponent"] = lookup
            widgetDict["deltaComponent"] = (maya.cmds.optionMenuGrp, widget)

            # display metric info
            widget = ui_utils.checkBoxGrp("Display metric info")
            widgetDict["displayMetricInfo"] = (maya.cmds.checkBoxGrp, widget)

            # display delta flow
            widget = ui_utils.checkBoxGrp("Display delta flow")
            widgetDict["displayDeltaFlow"] = (maya.cmds.checkBoxGrp, widget)

            # create weight shader
            widget = ui_utils.checkBoxGrp("Create Weight Shader")
            widgetDict["createWeightShader"] = (maya.cmds.checkBoxGrp, widget)

            # weight attr list
            opts = [(attr, i) for i, attr in enumerate(utils.WEIGHT_ATTRS)]
            widget, lookup = ui_utils.createOptionMenu("Geometry weights", options=opts)
            self.optionMenuGrp_labelToEnum["geometryWeightIndex"] = lookup
            widgetDict["geometryWeightIndex"] = (maya.cmds.optionMenuGrp, widget)

        return widgetDict

    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval("getOptionBoxHelpItem()")
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
