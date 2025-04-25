import mhy.maya.startup.action as action_api
import mhy.maya.startup.menu as menu_api
import mhy.maya.startup.marking_menu as mm_api
import mhy.maya.startup.shelf as shelf_api
import mhy.maya.startup.hot_key as hot_key_api
import os
import maya.OpenMaya as OpenMaya
from maya import cmds


def remove_malware(*args, **kwargs):
    """
    remove the infamous vaccine/malware.
    """
    found_malware = False
    # remove the script node.
    script_nodes = cmds.ls("vaccine_gene", type="script")
    if script_nodes:
        found_malware = True
        cmds.delete(script_nodes)
    # stop jobscripts.
    jobs = cmds.scriptJob(lj=True)
    for job in jobs:
        if "leukocyte.antivirus()" in job:
            found_malware = True
            job_id = job.split(":")[0]
            if job_id.isdigit():
                cmds.scriptJob(k=int(job_id), f=True)

    if found_malware:
        remove = cmds.confirmDialog(title='Confirm', message='Found a malware, Do you want to remove it?', button=[
                                    'Yes', 'No'], defaultButton='Yes', cancelButton='No', dismissString='No')
        if remove == 'No':
            return

    script_dir = cmds.internalVar(userAppDir=True)+'/scripts'
    # remove vaccine and pyc files.
    malware_file_list = ['vaccine.py', 'vaccine.pyc', 'userSetup.pyc']
    for malware_file_name in malware_file_list:
        malware_file_path = '{}/{}'.format(script_dir, malware_file_name)
        if os.path.exists(malware_file_path):
            os.remove(malware_file_path)

    # remove/modify userSetup.py
    usersetup_file_path = '{}/{}'.format(script_dir, 'userSetup.py')
    if os.path.exists(usersetup_file_path):
        usersetup_file = open(usersetup_file_path, 'r')
        file_content = usersetup_file.read()
        usersetup_file.close()
        file_content.replace('\r', '')
        usersetup_py_content = "import sys\n\nimport maya.cmds as cmds\n\nmaya_path = cmds.internalVar(userAppDir=True) + '/scripts'\n\nif maya_path not in sys.path:\n\n    sys.path.append(maya_path)\n\nimport vaccine\n\ncmds.evalDeferred('leukocyte = vaccine.phage()')\n\ncmds.evalDeferred('leukocyte.occupation()')"
        if usersetup_py_content == file_content:
            os.remove(usersetup_file_path)
        else:
            usersetup_file = open(usersetup_file_path, 'w')
            file_content = file_content.replace(usersetup_py_content, '')
            usersetup_file.write(file_content)
            usersetup_file.close()


def initialize():
    from maya import cmds, mel
    mel.eval('source "auto_source.mel"')
    if not cmds.about(batch=True):
        action_api.load_actions()
        menu_api.init_menus()
        mm_api.init()
        shelf_api.init_shelf()
        hot_key_api.init_hot_key()
        # TODO:remove save callback once we get rid of malware completely.
        OpenMaya.MSceneMessage.addCallback(
            OpenMaya.MSceneMessage.kBeforeSave, remove_malware)
