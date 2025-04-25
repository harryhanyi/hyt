from imp import reload
import webbrowser

import maya.cmds
import maya.mel

import maya.internal.common.cmd.deformer as cmddeformer
import maya.internal.common.utils.ui as ui_utils

import nsrigWrapUtils as utils

reload(utils)

HELP_DOC_URL = 'https://km.mihoyo.com/articleBase/767/433661'


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
                'bindMode': utils.DEFAULT_SETTINGS['bindMode'],
                'bindSpace': utils.DEFAULT_SETTINGS['bindSpace'],
                'wrapMode': utils.DEFAULT_SETTINGS['wrapMode'],
                'bindDistance': utils.DEFAULT_SETTINGS['bindDistance'],
                'setWorldPoints': utils.DEFAULT_SETTINGS['setWorldPoints'],
                'lastSelectedIsDriver': True,
                'createBindGeoms': False,
            }
        )

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        kw = cmddeformer.Command.getDeformerCommandArgs(**kwargs)
        result = None

        try:
            isLastSelectedDriver = kwargs['lastSelectedIsDriver']
            if isLastSelectedDriver:
                result = utils.wrapToLastSelectedMesh(
                    '', kwargs['createBindGeoms'], **kw
                )
            else:
                result = utils.wrapFirstSelectedGeomToDrivers(
                    '', kwargs['createBindGeoms'], **kw
                )
        except Exception as e:
            raise (e)

        deformerNode = result
        settableAttrs = [
            'bindMode',
            'bindSpace',
            'wrapMode',
            'bindDistance',
            'setWorldPoints',
        ]
        cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)
        maya.cmds.setAttr('%s.bindState' % deformerNode, 1)

        returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addBasicDeformerDialogWidgets(self):
        widgetDict = {}  # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            opts = [('Cached', 0), ('Live', 1)]
            widget, lookup = ui_utils.createOptionMenu('Bind mode', opts)
            self.optionMenuGrp_labelToEnum['bindMode'] = lookup
            widgetDict['bindMode'] = (maya.cmds.optionMenuGrp, widget)

            opts = [('World', 0), ('UV', 1)]
            widget, lookup = ui_utils.createOptionMenu('Bind space', opts)
            self.optionMenuGrp_labelToEnum['bindSpace'] = lookup
            widgetDict['bindSpace'] = (maya.cmds.optionMenuGrp, widget)

            opts = [('Surface', 0), ('Snap', 1)]
            widget, lookup = ui_utils.createOptionMenu('Wrap mode', opts)
            self.optionMenuGrp_labelToEnum['wrapMode'] = lookup
            widgetDict['wrapMode'] = (maya.cmds.optionMenuGrp, widget)

            widget = ui_utils.floatSliderGrp(
                'Bind distance',
                -1.0,
                10.0,
                True,
                False,
                value=utils.DEFAULT_SETTINGS['bindDistance'],
            )
            widgetDict['bindDistance'] = (maya.cmds.floatSliderGrp, widget)

            widget = ui_utils.checkBoxGrp('Set world points')
            widgetDict['setWorldPoints'] = (maya.cmds.checkBoxGrp, widget)

            widget = ui_utils.checkBoxGrp('Last selected is driver')
            widgetDict['lastSelectedIsDriver'] = (maya.cmds.checkBoxGrp, widget)

            widget = ui_utils.checkBoxGrp('Create bind geometries')
            widgetDict['createBindGeoms'] = (maya.cmds.checkBoxGrp, widget)

        return widgetDict

    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval('getOptionBoxHelpItem()')
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
