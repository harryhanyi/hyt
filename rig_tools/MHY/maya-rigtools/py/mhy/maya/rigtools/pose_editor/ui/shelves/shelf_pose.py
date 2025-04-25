# -*- coding: utf-8 -*-

import mhy.python.core.compatible as compat

import mhy.maya.rig.face.shelves.shelfBase as shelfBase
compat.reload(shelfBase)

def shelf_show():
    shelf_Pose()


class shelf_Pose(shelfBase.shelfBase):
    '''
    init shelf buttons
    '''
    def __init__(self):
        super(shelf_Pose, self).__init__("MHY")
        self.labelBackground = (0.1322, 0.3344, 0.0393, 1)
        self.build()

    @staticmethod
    def pose_editor():
        '''
        show pose editor
        '''
        import mhy.maya.rigtools.pose_editor.ui.widget.main_window as mw
        ui = mw.Window.get_singleton()
        ui.show(dockable=True, floating=True)
        ui.raise_()

    def build(self):
        '''
        setup buttons
        '''
        self.addButon(
            "Editor",
            "editor.png",
            command=self.pose_editor,
            annotation_str=u'open pose editor')
