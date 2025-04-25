import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.node import DependencyNode


class Set(DependencyNode):

    __NODETYPE__ = 'objectSet'
    __FNCLS__ = OpenMaya.MFnSet

    @classmethod
    def create(cls, *args, **kwargs):
        if not args:
            args = cmds.ls(sl=True) or []

        for i in args:
            if not cmds.objExists(i):
                raise RuntimeError('{} does not exists'.format(i))
        node_name = cmds.sets(*args, **kwargs)
        node = Node(node_name)
        return node

    @property
    def members(self):
        # TODO support components
        return [n for n in cmds.sets(self.name, query=True) or []]

    def is_member(self, node):
        """
        Check if given node is the member of this object set
        Args:
            node:

        Returns:
            bool:
        """
        return cmds.sets(node, isMember=self.name)

    def add_member(self, node):
        """
        Add a node to this set
        Args:
            node(Node): Object to add

        """
        cmds.sets(node, addElement=self.name)

    def remove_member(self, node):
        """
        Remove a node from this set
        Args:
            node:

        Returns:

        """
        if not self.is_member(node):
            return
        cmds.sets(node, remove=self.name)

    def select(self):
        members = self.members
        cmds.select([m for m in members])

    def export(self, *args, **kwargs):
        data = dict()
        data['name'] = self.name
        data['members'] = list()
        for member in self.members:
            data['members'].append(member)
        return data

    def load(self, data, *args, **kwargs):
        members = data.get('members')
        if not members:
            return

        for m in members:
            print('m', m)
            if Node.object_exist(m):
                print('add memeber', m)
                self.add_member(m)
