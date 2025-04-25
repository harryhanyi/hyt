from imp import reload
import webbrowser

import maya.cmds
import maya.mel

import maya.internal.common.cmd.deformer as cmddeformer
import maya.internal.common.utils.ui as ui_utils

import nsrigMultiCollideUtils as utils

reload(utils)

HELP_DOC_URL = 'https://km.mihoyo.com/articleBase/767/298527'


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
                'iterations': utils.DEFAULT_SETTINGS['iterations'],
                'smoothing': utils.DEFAULT_SETTINGS['smoothing'],
                'surfaceSmoothing': utils.DEFAULT_SETTINGS['surfaceSmoothing'],
                'bendingResistance': utils.DEFAULT_SETTINGS['bendingResistance'],
                'volumePreservation': utils.DEFAULT_SETTINGS['volumePreservation'],
                'bulge': utils.DEFAULT_SETTINGS['bulge'],
                'bulgeDistance': utils.DEFAULT_SETTINGS['bulgeDistance'],
                'separationDistance': utils.DEFAULT_SETTINGS['separationDistance'],
                'maxPenetrationDepth': utils.DEFAULT_SETTINGS['maxPenetrationDepth'],
            }
        )

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        kw = cmddeformer.Command.getDeformerCommandArgs(**kwargs)
        result = None

        try:
            result = utils.createBySelection('', **kw)
        except Exception as e:
            raise (e)

        deformerNode = result
        settableAttrs = [
            'iterations',
            'smoothing',
            'surfaceSmoothing',
            'bendingResistance',
            'volumePreservation',
            'bulge',
            'bulgeDistance',
            'separationDistance',
            'maxPenetrationDepth',
        ]
        cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)
        returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addBasicDeformerDialogWidgets(self):
        widgetDict = {}  # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            widget = ui_utils.intSliderGrp(
                'Iterations',
                0,
                100,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['iterations'],
            )
            widgetDict['iterations'] = (maya.cmds.intSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Smoothing',
                0.0,
                1.0,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['smoothing'],
            )
            widgetDict['smoothing'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Surface smoothing',
                0.0,
                1.0,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['surfaceSmoothing'],
            )
            widgetDict['surfaceSmoothing'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Bending resistance',
                0.0,
                1.0,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['bendingResistance'],
            )
            widgetDict['bendingResistance'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Volume preservation',
                0.0,
                1.0,
                True,
                True,
                value=utils.DEFAULT_SETTINGS['volumePreservation'],
            )
            widgetDict['volumePreservation'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Bulge', 0.0, 1.0, True, True, value=utils.DEFAULT_SETTINGS['bulge']
            )
            widgetDict['bulge'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Bulge distance',
                0.0,
                2.0,
                True,
                False,
                value=utils.DEFAULT_SETTINGS['bulgeDistance'],
            )
            widgetDict['bulgeDistance'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Separation distance',
                0.0,
                1.0,
                True,
                False,
                value=utils.DEFAULT_SETTINGS['separationDistance'],
            )
            widgetDict['separationDistance'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Max penetrationDepth',
                0.0,
                1.0,
                True,
                False,
                value=utils.DEFAULT_SETTINGS['maxPenetrationDepth'],
            )
            widgetDict['maxPenetrationDepth'] = (maya.cmds.floatSliderGrp, widget)

        return widgetDict

    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval('getOptionBoxHelpItem()')
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
