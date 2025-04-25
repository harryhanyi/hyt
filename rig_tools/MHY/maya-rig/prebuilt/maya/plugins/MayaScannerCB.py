########################################################################
# DESCRIPTION:
#
# Produces the command "MayaScannerCB". 
#
# To use, make sure that MayaScannerCB.py is in your MAYA_PLUG_IN_PATH,
# then do the following:
#
#    import maya
#    maya.cmds.loadPlugin("MayaScannerCB.py")
#    maya.cmds.MayaScannerCB()
#
########################################################################

import sys
import maya.cmds as cmds
import maya.mel as mel
import maya.api.OpenMaya as om

from MayaScannerCleaner import clean_malware, userConfirmFix



def maya_useNewAPI():
    """
    The presence of this function tells Maya that the plugin produces, and
    expects to be passed, objects created using the Maya Python API 2.0.
    """
    pass


MayaScannerCB_cbIds = []
MayaScannerCB_result = 0

# command
class MayaScannerCBcmd(om.MPxCommand):
    kPluginCmdName = "MayaScannerCB"

    def __init__(self):
        om.MPxCommand.__init__(self)

    @staticmethod
    def creator():
        return MayaScannerCBcmd()

    def doIt(self, args):
        if MayaScannerCB_result != 0:
           cmds.error("Autodesk.MayaScannerCB  : FileCallack : issues have been detected")
        return MayaScannerCB_result

    @staticmethod
    def MayaScanAfterCB(clientData):

        kSaveAndQuit = 'Save and Quit'
        kQuitWithoutSave = 'Quit without Saving'
        retStatus = 0        # no issues found

        userConfirmFix('reset',1)
        corrupt_found,corrupt_fixed, malType = clean_malware('FileOpenCB')

        if corrupt_found != 0:
            retStatus = 19        # issues found
            referenceLoad = False
            saveRequest = ""
 
            if clientData == 'afterLoadReference' or clientData == 'afterImportReference':
                cmds.warning("Autodesk.MayaScannerCB  : ReferenceCallback : detected corrupted scene. Please check scene file")
                referenceLoad = True
            elif clientData == 'afterImport' and cmds.file(q=True,sn=True) == "":
                cmds.warning("Autodesk.MayaScannerCB  : Import No Scene Name : detected corrupted scene. Please check scene file")
            else:
                cmds.warning("Autodesk.MayaScannerCB  : FileCallback : detected corrupted scene. Please check scene file")

            if malType == 1:
                typeExtension = 'mel'
            else:
                typeExtension = 'py'

            # check to see if we have current scene name to save
            if cmds.file(q=True, sn=True) == "":
                saveRequest = cmds.confirmDialog( title='Found corrupted scene, No scene name, cannot save', message='Recommend: <b>Quit</b> Maya. Load scene separately or fix offline',
                    messageAlign='center',
                    button=[kQuitWithoutSave], defaultButton=kQuitWithoutSave, cancelButton=kQuitWithoutSave, dismissString=kQuitWithoutSave )
            elif referenceLoad:
                # see if from reference
                saveRequest = cmds.confirmDialog( title='Found corrupted scene, during reference load, will not save', message='Recommend: <b>Quit</b> Maya. Load scene separately or fix offline',
                    messageAlign='center',
                    button=[kQuitWithoutSave], defaultButton=kQuitWithoutSave, cancelButton=kQuitWithoutSave, dismissString=kQuitWithoutSave )
            else:
                # should be able to save cases
                if corrupt_fixed < corrupt_found:
                    if cmds.file(q=True, sn=True):
                        saveRequest = cmds.confirmDialog( title='Found corrupted scene, not fully fixed', message='Recommend: <b>Quit</b> Maya.  Check userSetup.%s and scene file scriptNodes.  Start new Maya session' % typeExtension,
                        messageAlign='center',
                        button=[kSaveAndQuit, kQuitWithoutSave], defaultButton=kQuitWithoutSave, cancelButton=kQuitWithoutSave, dismissString=kQuitWithoutSave )
                    else:
                        saveRequest = cmds.confirmDialog( title='Found corrupted scene, not fully fixed', message='Recommend: <b>Quit</b> Maya.  Check userSetup.%s and scene file scriptNodes.  Start new Maya session' % typeExtension,
                            messageAlign='center',
                            button=[kSaveAndQuit, kQuitWithoutSave], defaultButton=kQuitWithoutSave, cancelButton=kQuitWithoutSave, dismissString=kQuitWithoutSave )
                else:
                    saveRequest = cmds.confirmDialog( title='Found corrupted scene, attempted to fix', message='Recommend: <b>Save</b> current scene.  Quit Maya.  Check userSetup.%s and scene file scriptNodes.  Start new Maya session' % typeExtension,
                    messageAlign='center',
                    button=[kSaveAndQuit, kQuitWithoutSave], defaultButton=kSaveAndQuit, cancelButton=kQuitWithoutSave, dismissString=kQuitWithoutSave )

            # check to see if user wants to save current scene
            if cmds.about(batch=True) or saveRequest == kSaveAndQuit:
                cmds.file(save=True, force=True)
                retStatus = 20          # errors found and saved

            # check for batch mode where we don't have UI we automatically save the file.
            if cmds.about(batch=True):
                cmds.warning("Autodesk.MayaScannerCB  : Batch mode : Found corrupted scene, attempted to fixed. Please check userSetup.%s and scene scriptNodes"  % typeExtension)

            # in all cases if errors time to exit Maya
            cmds.quit(force=True, exitCode=retStatus, abort=True)

    @staticmethod
    def clearCB():
        if len(MayaScannerCb_cbIds) > 0:
            for id in MayaScannerCB_cbIds:
                om.MMessage.removeCallback(id)


# Initialize the plug-in
def initializePlugin(obj):
    plugin = om.MFnPlugin(obj)
    try:
        plugin.registerCommand(
            MayaScannerCBcmd.kPluginCmdName, MayaScannerCBcmd.creator
        )
    except:
        sys.stderr.write(
            "Failed to register command: %s\n" % MayaScannerCBcmd.kPluginCmdName
        )
        raise


    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, MayaScannerCBcmd.MayaScanAfterCB,'afterOpen'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterImport, MayaScannerCBcmd.MayaScanAfterCB,'afterImport'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterLoadReference, MayaScannerCBcmd.MayaScanAfterCB,'afterLoadReference'))
    MayaScannerCB_cbIds.append(om.MSceneMessage.addCallback(om.MSceneMessage.kAfterImportReference, MayaScannerCBcmd.MayaScanAfterCB,'afterImportReference'))

# Uninitialize the plug-in
def uninitializePlugin(obj):
    plugin = om.MFnPlugin(obj)

    for id in MayaScannerCB_cbIds:
        om.MMessage.removeCallback(id)

    try:
        plugin.deregisterCommand(MayaScannerCBcmd.kPluginCmdName)
    except:
        sys.stderr.write(
            "Failed to unregister command: %s\n" % MayaScannerCBcmd.kPluginCmdName
        )
        raise

#-
# ==========================================================================
# Copyright (C) 2020 Autodesk, Inc. and/or its licensors.  All 
# rights reserved.
#
# The coded instructions, statements, computer programs, and/or related 
# material (collectively the "Data") in these files contain unpublished 
# information proprietary to Autodesk, Inc. ("Autodesk") and/or its 
# licensors, which is protected by U.S. and Canadian federal copyright 
# law and by international treaties.
#
# The Data is provided for use exclusively by You. You have the right 
# to use, modify, and incorporate this Data into other products for 
# purposes authorized by the Autodesk software license agreement, 
# without fee.
#
# The copyright notices in the Software and this entire statement, 
# including the above license grant, this restriction and the 
# following disclaimer, must be included in all copies of the 
# Software, in whole or in part, and all derivative works of 
# the Software, unless such copies or derivative works are solely 
# in the form of machine-executable object code generated by a 
# source language processor.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. 
# AUTODESK DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED 
# WARRANTIES INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF 
# NON-INFRINGEMENT, MERCHANTABILITY OR FITNESS FOR A PARTICULAR 
# PURPOSE, OR ARISING FROM A COURSE OF DEALING, USAGE, OR 
# TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS LICENSORS 
# BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL, 
# DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK 
# AND/OR ITS LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY 
# OR PROBABILITY OF SUCH DAMAGES.
#
# ==========================================================================
#+

