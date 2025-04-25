import maya.cmds as cmds

from mhy.maya.nodezoo.node import Node, Transform
import mhy.maya.standard.name as nlib


ATTR_LIMB_NAME = 'limb_name'
ATTR_LIMB_TYPE = 'limb_type'
ATTR_CTRLS = 'ctrls'
ATTR_PARENT_LIMB = 'parent_limb_root'


class MHYLimbRoot(Transform):
    """
    A class interfacing the limb root node used in the MHY rigging system.
    """

    __CUSTOMTYPE__ = 'MHYLimbRoot'

    @classmethod
    def create(cls, name='part_ROOT_00_M_LIMB', limb_type=''):
        """Builds a MHY limb shape node.

        Args:
            name (str): Name of the limb node.

        Returns:
            LSLimbShape: The MHY limb shape node.
        """
        name = nlib.NodeName(name)
        name = name.replace_ext('LIMB')
        shape = cmds.createNode('locator')
        for attr in ('localPosition', 'localScale'):
            cmds.setAttr('{}.{}'.format(shape, attr), channelBox=False)
            for ax in 'XYZ':
                cmds.setAttr('{}.{}'.format(shape, attr + ax), channelBox=False)
        cmds.hide(shape)
        node = cls.make_custom_node(cmds.listRelatives(shape, parent=True)[0])
        node.name = name
        node.sync_shape_name()
        attr = node.add_attr('string', name=ATTR_LIMB_NAME)
        attr.value = '{}_{}'.format(name.part, name.side)
        attr = node.add_attr('string', name=ATTR_LIMB_TYPE)
        attr.value = limb_type
        node.add_attr('message', name=ATTR_PARENT_LIMB)
        return node

    @property
    def limb_name(self):
        """Returns the nice limb name."""
        return self.attr(ATTR_LIMB_NAME).value

    @property
    def limb_type(self):
        """Returns the limb type."""
        return self.attr(ATTR_LIMB_TYPE).value

    @property
    def shape(self):
        """Returns the limb shape node."""
        shapes = self.get_shapes(type_=['locator', 'limbNode'])
        if not shapes:
            raise RuntimeError(
                'Broken MHYLimbRoot: {}. No limb node shape found.'.format(self))
        return shapes[0]

    def connect_parent_limb(self, parent_limb_root):
        """Connects this limb to a given parent limb."""
        Node(parent_limb_root).message.connect(
            self.attr(ATTR_PARENT_LIMB), force=True)

    def get_parent_limbs(self, recursive=False):
        """Returns the parent limb root nodes.

        Args:
            recursive (bool): If True, returns all parent limbs.
                Otherwise only returns the immediate parent limb.

        Returns:
            [MHYLimbRoot]: The parent limb root nodes.
        """
        parents = []
        node = self
        while node:
            node = cmds.listConnections(
                '{}.{}'.format(node, ATTR_PARENT_LIMB),
                source=True, destination=False, plugs=False)
            if node:
                node = Node(node[0])
                parents.append(node)
            if not recursive:
                break
        return reversed(parents)

    def get_child_limbs(self, recursive=False):
        """Returns the child limbs of this node.

        Args:
            recursive (bool): If True, returns all children limbs.
                Otherwise only returns the immediate children limbs.

        Returns:
            [MHYLimbRoot]: The child limb root nodes.
        """
        children = []
        for node in cmds.listConnections(
                '{}.message'.format(self),
                source=False, destination=True, plugs=True) or []:
            node, attr = node.split('.', 1)
            if attr == ATTR_PARENT_LIMB:
                node = Node(node)
                children.append(node)
                if recursive:
                    children.extend(node.get_child_limbs(recursive=True))
        return children

    # @property
    # def rig_root(self):
    #     """Returns the rig root."""
    #     for node in cmds.listConnections(
    #             '{}.message'.format(self),
    #             source=False, destination=True, plugs=False) or []:
    #         node = Node(node)
    #         if node.name == const.RIG_ROOT:
    #             return node

    def get_ctrls(self):
        """Returns a list of ctrls connected to this limb root."""
        ctrls = []
        if self.has_attr(ATTR_CTRLS):
            for each in cmds.listConnections(
                    '{}.{}'.format(self, ATTR_CTRLS),
                    source=True, destination=False, plugs=False) or []:
                ctrls.append(Node(each))
        return ctrls

    def add_ctrl(self, ctrl, force=False):
        """Adds a ctrl to this limb root.

        Args:
            ctrl (MHYCtrl): A ctrl node to to add.
            force (bool): If True and the ctrl is already linked to a
                limb, unlink it first.

        Returns:
            None

        Raises:
            ValueError: If the given ctrl is not valid.
            RuntimeError: If the ctrl is already connected to a limb root
                and force is False.
        """
        ctrl = Node(ctrl)
        if ctrl.custom_type_name != 'MHYCtrl':
            raise ValueError('{} is not a ctrl node!'.format(ctrl))

        cur = ctrl.limb_root
        if cur:
            if cur == self:
                return

            if not force:
                raise RuntimeError(
                    '{} is already connected to a limb root'.format(ctrl))

            ctrl.disconnect_limb()

        if not self.has_attr(ATTR_CTRLS):
            attr = self.add_attr('message', name=ATTR_CTRLS, multi=True)
        else:
            attr = self.attr(ATTR_CTRLS)

        i = attr.num_elements
        cmds.connectAttr(
            '{}.message'.format(ctrl),
            '{}.{}[{}]'.format(self, ATTR_CTRLS, i))

        self.add_instance(ctrl)

    def add_instance(self, node):
        """Creates an instance of this shape under a given node.

        Args:
            node (str or Node): A node to add instances to.

        Returns: None
        """
        shape = self.shape
        cmds.parent(shape.long_name, node, add=True, shape=True)
        cmds.select(clear=True)
