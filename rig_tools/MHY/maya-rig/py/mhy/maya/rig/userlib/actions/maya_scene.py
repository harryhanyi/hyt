"""
Maya scene utility actions
"""
import maya.cmds as cmds

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.rig.base_actions import BaseSceneAction


class NewMayaScene(BaseSceneAction):
    """
    Creates a new Maya scene.
    """

    def run(self):
        """Executes this action."""
        cmds.file(newFile=True, force=True)


class SaveMayaScene(BaseSceneAction):
    """
    Saves the current Maya scene.
    """

    @pa.file_param(ext=('ma', 'mb'))
    def file_path(self):
        """The file path to save the current scene to."""

    def run(self):
        """Executes this action."""
        path = self.file_path.value
        if not path:
            raise exp.ActionError('File path is empty.')
        typ = 'mayaAscii' if path.endswith('ma') else 'mayaBinary'
        cmds.file(rename=path)
        cmds.file(save=True, defaultExtensions=False, type=typ, force=True)
        self.info('saved scene to {}'.format(path))
