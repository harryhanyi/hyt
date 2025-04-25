from imp import reload
import webbrowser

import maya.cmds
import maya.mel

import maya.internal.common.cmd.base as cmdbase
import maya.internal.common.utils.ui as ui_utils

import nsrigMultiIntersectorUtils as utils

reload(utils)

HELP_DOC_URL = 'https://km.mihoyo.com/articleBase/767/272908'


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
        # self.commandDescription = 'Blablabla...'
        self.commandTitle = '%s Options' % utils.NODE_TYPE_NAME
        self.optionVarPrefix = utils.NODE_TYPE_NAME

        self.optionVarDefaults.update(
            {
                'worldSpace': True,
                'intersectionTransparency': utils.DEFAULT_SETTINGS[
                    'intersectionTransparency'
                ],
                'randomizeColors': utils.DEFAULT_SETTINGS['randomizeColors'],
                'backfaceCulling': utils.DEFAULT_SETTINGS['backfaceCulling'],
            }
        )

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        result = None

        try:
            result = utils.createBySelection('', kwargs['worldSpace'])
        except Exception as e:
            raise (e)

        deformerNode = result
        settableAttrs = [
            'intersectionTransparency',
            'randomizeColors',
            'backfaceCulling',
        ]
        cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)
        returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addOptionDialogWidgets(self):
        widgetDict = {}  # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            widget = ui_utils.checkBoxGrp('Create under world space')
            widgetDict['worldSpace'] = (maya.cmds.checkBoxGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Intersection transparency',
                0.0,
                1.0,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['intersectionTransparency'],
            )
            widgetDict['intersectionTransparency'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.checkBoxGrp('Randomize colors')
            widgetDict['randomizeColors'] = (maya.cmds.checkBoxGrp, widget)

            widget = ui_utils.checkBoxGrp('Backface culling')
            widgetDict['backfaceCulling'] = (maya.cmds.checkBoxGrp, widget)

        return widgetDict

    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval('getOptionBoxHelpItem()')
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
