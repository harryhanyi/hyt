from imp import reload
import webbrowser

import maya.cmds
import maya.mel

import maya.internal.common.cmd.deformer as cmddeformer
import maya.internal.common.utils.ui as ui_utils

import nsrigStickyUtils as utils

reload(utils)

HELP_DOC_URL = 'https://km.mihoyo.com/articleBase/767/490321'


def open_help_doc(*args):
    webbrowser.open_new(HELP_DOC_URL)


# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------
class Command(cmddeformer.Command):
    def __init__(self):
        super(Command, self).__init__()

        self.commandName = utils.NODE_TYPE_NAME
        self.commandHelpTag = utils.NODE_TYPE_NAME
        # self.commandDescription = 'Blablabla...'
        self.commandTitle = '%s Options' % utils.NODE_TYPE_NAME
        self.optionVarPrefix = utils.NODE_TYPE_NAME

        self.optionVarDefaults.update(
            {
                'mode': utils.DEFAULT_SETTINGS['mode'],
                'attach': utils.DEFAULT_SETTINGS['attach'],
                'smoothingIterations': utils.DEFAULT_SETTINGS['smoothingIterations'],
                'resetFrame': utils.DEFAULT_SETTINGS['resetFrame'],
                'detachFrames': utils.DEFAULT_SETTINGS['detachFrames'],
                'createRefGeom': True,
            }
        )

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        kw = cmddeformer.Command.getDeformerCommandArgs(**kwargs)
        result = None

        try:
            result = utils.createBySelection('', kwargs['createRefGeom'], **kw)
        except Exception as e:
            raise (e)

        deformerNode = result
        settableAttrs = [
            'mode',
            'attach',
            'smoothingIterations',
            'resetFrame',
            'detachFrames',
        ]
        cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)

        returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addBasicDeformerDialogWidgets(self):
        widgetDict = {}  # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            opts = [('Static', 0), ('Dynamic', 1)]
            widget, lookup = ui_utils.createOptionMenu('Mode', opts)
            self.optionMenuGrp_labelToEnum['mode'] = lookup
            widgetDict['mode'] = (maya.cmds.optionMenuGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Attach',
                0.0,
                1.0,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['attach'],
            )
            widgetDict['attach'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.intSliderGrp(
                'Smoothing iterations',
                0,
                50,
                True,
                False,
                value=utils.DEFAULT_SETTINGS['smoothingIterations'],
            )
            widgetDict['smoothingIterations'] = (maya.cmds.intSliderGrp, widget)

            widget = ui_utils.intSliderGrp(
                'Reset frame',
                -1000,
                1000,
                False,
                False,
                value=utils.DEFAULT_SETTINGS['resetFrame'],
            )
            widgetDict['resetFrame'] = (maya.cmds.intSliderGrp, widget)

            widget = ui_utils.intSliderGrp(
                'Detach frames',
                1,
                50,
                True,
                False,
                value=utils.DEFAULT_SETTINGS['detachFrames'],
            )
            widgetDict['detachFrames'] = (maya.cmds.intSliderGrp, widget)

            widget = ui_utils.checkBoxGrp('Create reference geometry')
            widgetDict['createRefGeom'] = (maya.cmds.checkBoxGrp, widget)

        return widgetDict

    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval('getOptionBoxHelpItem()')
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
