import unittest

from maya import cmds

import mhy.maya.animtools.picker_manager.node.viewport_picker as vp

from mhy.maya.nodezoo.node import Node


class TestViewportPicker(unittest.TestCase):
    """
    Test DG, DAG, and transfrom
    """

    def setup(self):
        cmds.file(newFile=True, force=True)

        self.transform = Node.create('transform', name='transform')
        self.node = vp.ViewportPicker.create(name='pickerShape', parent=self.transform)

        self.container = vp.ViewportPicker.create_container('picker_container')
        self.node.radius.value = 20
        self.transform.set_translation([3, 4, 7], 'world')
        if not cmds.about(batch=True):
            # Can't test this in batch mode
            self.node.init_position_from_current_view()
        self.node.get_picker_color()

        self.node.set_picker_color((0, 1, 0))
        self.node.set_ui_type('image')
        self.node.set_ui_type(2)

        self.node.set_picker_position((1000, 1000))
        self.node.set_width(20)
        self.node.set_height(20)

        self.container.set_picker_position((1300, 1300))
        self.container.set_width(1000)
        self.container.set_height(1000)

        self.node.set_picker_alpha(0.7)
        self.container.add_child_pickers([self.node])

    def test_initialize(self):
        self.setup()
        vp.ViewportPicker.clear_pickers()
        self.assertTrue(not cmds.ls(type='mhyViewportPicker'))

    def test_export(self):
        self.setup()
        container_data = self.container.export()
        picker_data = self.node.export()
        vp.ViewportPicker.clear_pickers()

        self.container = vp.ViewportPicker.create_container('picker_container')
        self.transform = Node.create('transform', name='transform')
        self.node = vp.ViewportPicker.create(name='pickerShape', parent=self.transform)

        self.container.load(container_data)
        self.node.load(picker_data)
        self.assertTrue(self.container.export() == container_data)
        self.assertTrue(self.node.export() == picker_data)


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestViewportPicker))
    unittest.TextTestRunner(failfast=True).run(suite)
