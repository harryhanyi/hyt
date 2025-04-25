from maya import cmds

from mhy.maya.nodezoo.attribute import Attribute
from mhy.maya.nodezoo.node import Node, Set


class AnimLayer(Set):
    """
    AnimLayer node class.
    """

    __NODETYPE__ = 'animLayer'

    @classmethod
    def create(cls, name='animLayer'):
        layer = cmds.animLayer(name)
        return cls(layer)

    @classmethod
    def get_base_layer(cls):
        """Returns the base anim layer, if exists.

        Returns:
            AnimLayer
        """
        for each in cmds.ls(type='animLayer'):
            parent = cmds.animLayer(each, query=True, parent=True)
            if not parent:
                return AnimLayer(each)

    @classmethod
    def get_anim_layers(cls, include_base=False):
        """Returns a list of anim layers in the scene with
        hierarchical order.

        Args:
            include_base (bool): Include the base layer?

        Returns:
            list
        """
        base = cls.get_base_layer()
        if not base:
            return []
        layers = base.get_children(recursive=True)

        if include_base:
            return [base] + layers
        return layers

    @property
    def is_base_layer(self):
        """Checks if this anim layer is the base layer."""
        return self == self.get_base_layer()

    def get_attributes(self):
        """Returns a list of attributes in this layer."""
        return [Attribute(x) for x in
                cmds.animLayer(self, query=True, attribute=True) or []]

    @property
    def members(self):
        """Returns a list of nodes in this layer."""
        node_set = set()
        nodes = []
        for each in self.get_attributes():
            n = each.node
            if n not in node_set:
                nodes.append(n)
                node_set.add(n)
        return nodes

    def add_member(self, nodes):
        """Adds one or more nodes into this anim layer."""
        cmds.select(nodes, replace=True)
        cmds.animLayer(self, edit=True, addSelectedObjects=True)

    def remove_member(self, nodes):
        """Removes one or more nodes from this anim layer."""
        if not isinstance(nodes, (list, tuple)):
            nodes = [nodes]
        nodes = [Node(x) for x in nodes]

        for attr in self.get_attributes():
            if attr.node in nodes:
                cmds.animLayer(self, edit=True, ra=attr)

    def get_children(self, recursive=True):
        """Returns a list of children layers.

        Args:
            recursive (bool): If True, return all children recursively.

        Returns:
            list: A list of anim layer objects.
        """
        layers = []
        for each in cmds.listConnections(
                '{}.childrenLayers'.format(self),
                source=True, destination=True, plugs=False) or []:
            each = AnimLayer(each)
            layers.append(each)
            if recursive:
                layers.extend(each.get_children(recursive=recursive))
        return layers

    def get_parent(self):
        """Returns the parent anim layer."""
        parent = cmds.animLayer(self, query=True, parent=True)
        if parent:
            return AnimLayer(parent)

    def isolate(self):
        """Solos this anim layer by enabling and selecting it,
        then disabling all other layers."""
        for each in self.get_anim_layers(include_base=True):
            if not each.is_base_layer:
                cmds.animLayer(each, edit=True, mute=(each != self))
                cmds.animLayer(each, edit=True, solo=False)
            if each == self:
                cmds.animLayer(each, edit=True, selected=True)
                cmds.animLayer(each, edit=True, preferred=True)
                cmds.animLayer(each, edit=True, lock=False)
            else:
                cmds.animLayer(each, edit=True, selected=False)
                cmds.animLayer(each, edit=True, preferred=False)
