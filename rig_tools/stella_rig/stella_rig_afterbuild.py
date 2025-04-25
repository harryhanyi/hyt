import importlib
import stella_rig.connect_proxy_skeleton as cpk
importlib.reload(cpk)
import maya.cmds as cmds


def connect_proxy_skeleton():
    cpk.connect_deform_skeleton()

# Reconnect Ctrl structure
_CTRL_DICT = {'breast_L_FKPLC': 'spine_02_M_JNT', 'breast_R_FKPLC': 'spine_02_M_JNT'}
def connect_controls(ctrl_dict = _CTRL_DICT):
    for ctrl_root in ctrl_dict:
        cmds.parentConstraint(ctrl_dict[ctrl_root], ctrl_root, maintainOffset=True)



# Import PSD
def import_PSD(psd_path, shape=1):
    poseInterpolatorImportPoses(psd_path, shape)

