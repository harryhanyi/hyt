from imp import reload
import webbrowser

import maya.cmds
import maya.mel

import maya.internal.common.cmd.deformer as cmddeformer
import maya.internal.common.utils.ui as ui_utils

import nsrigSmoothUtils as utils
reload(utils)

HELP_DOC_URL = 'https://km.mihoyo.com/articleBase/767/194700'

def open_help_doc(*args):
    webbrowser.open_new(HELP_DOC_URL)

# ------------------------------------------------------------------------------
# Command
# ------------------------------------------------------------------------------
class Command(cmddeformer.Command):

    def __init__(self):
        super(Command, self).__init__()

        self.commandName = utils.NODE_TYPE_NAME
        self.commandHelpTag	= utils.NODE_TYPE_NAME
        # self.commandDescription = 'Blablabla...'
        self.commandTitle = '%s Options' % utils.NODE_TYPE_NAME
        self.optionVarPrefix = utils.NODE_TYPE_NAME

        self.optionVarDefaults.update({'weightingScheme': utils.DEFAULT_SETTINGS['weightingScheme'],
                                       'smoothingIterations': utils.DEFAULT_SETTINGS['smoothingIterations'],
                                       'smoothingDirection': utils.DEFAULT_SETTINGS['smoothingDirection'],
                                       'uvSet': utils.DEFAULT_SETTINGS['uvSet'],
                                       'createRefMesh': True})

    @classmethod
    def command(cls, **kwargs):
        returnedNodes = list()

        kw = cmddeformer.Command.getDeformerCommandArgs(**kwargs)
        result = None

        try:
            result = utils.createBySelection(kwargs['createRefMesh'], '', False, **kw)
        except Exception as e:
            raise(e)
    
        for deformerNode in result:
            settableAttrs = ['weightingScheme', 'smoothingIterations', 'smoothingDirection', 'uvSet']
            cls.setNodeAttributes(deformerNode, kwargs, settableAttrs)
            returnedNodes.append(deformerNode)

        return cls.finalizeCommand(returnedNodes)

    def addBasicDeformerDialogWidgets(self):
        widgetDict = {} # {optionVarDictKey, (widgetClass, widget)}

        with ui_utils.AttributeLayoutManager():
            widget = ui_utils.checkBoxGrp('Create reference geometry')
            widgetDict['createRefMesh'] = (maya.cmds.checkBoxGrp, widget)

            opts = [('Uniform', 0), ('Cotangent', 1), ('Span-Aware', 2)]
            widget, lookup = ui_utils.createOptionMenu('Weighting scheme', opts)
            self.optionMenuGrp_labelToEnum['weightingScheme'] = lookup
            widgetDict['weightingScheme'] = (maya.cmds.optionMenuGrp, widget)

            widget = ui_utils.intSliderGrp('Smoothing iterations', 0, 100, True, True,
                                           value=utils.DEFAULT_SETTINGS['smoothingIterations'])
            widgetDict['smoothingIterations'] = (maya.cmds.intSliderGrp, widget)

            opts = [('Surrounding', 0), ('UV', 1)]
            widget, lookup = ui_utils.createOptionMenu('Smoothing direction', opts)
            self.optionMenuGrp_labelToEnum['smoothingDirection'] = lookup
            widgetDict['smoothingDirection'] = (maya.cmds.optionMenuGrp, widget)

            widget = ui_utils.textFieldGrp('UV Set', text=utils.DEFAULT_SETTINGS['uvSet'])
            widgetDict['uvSet'] = (maya.cmds.textFieldGrp, widget)

        return widgetDict
    
    def createDialog(self, optionVarOverrideDict=None, saveOptionVars=True):
        super(Command, self).createDialog(optionVarOverrideDict, saveOptionVars)

        # Override help item command
        helpItem = maya.mel.eval('getOptionBoxHelpItem()')
        maya.cmds.menuItem(helpItem, e=1, c=open_help_doc)
