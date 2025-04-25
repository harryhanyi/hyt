import os

from maya import cmds, OpenMaya

from mhy.maya.scene import safe_open
from mhy.maya.nodezoo.node import DependencyNode


class Reference(DependencyNode):
    """
    Reference node class.
    """

    __NODETYPE__ = 'reference'
    __FNCLS__ = OpenMaya.MFnReference

    @classmethod
    def create(cls, file_path, namespace=None):
        # get file type
        head, ext = os.path.splitext(file_path)
        if ext == '.ma':
            typ = 'mayaAscii'
        elif ext == '.mb':
            typ = 'mayaBinary'
        else:
            raise ValueError('Not a maya file: {}'.format(file_path))

        # get default namespace
        if not namespace:
            namespace = os.path.split(head)[-1]

        # create reference
        refs = set(cmds.ls(type='reference'))
        safe_open(
            file_path, reference=True, namespace=namespace,
            type=typ, ignoreVersion=True, groupLocator=True,
            mergeNamespacesOnClash=False, options='v=0;')
        refs = set(cmds.ls(type='reference')) - refs

        for ref in refs:
            if not cmds.referenceQuery(ref, isNodeReferenced=True):
                return cls(ref)

    @classmethod
    def get_reference_nodes(cls, file_path=None):
        """Returns reference nodes in the scene.

        Args:
            file_path (str or None): If not None, return
                reference nodes associated with this file.
                Otherwise return all reference nodes.

        Returns:
            list: A list of reference node objects.
        """
        if file_path:
            file_path = file_path.replace('\\', '/')
        references = []

        for ref_node in cmds.ls(type='reference', objectsOnly=True):
            if ':' not in ref_node and 'sharedReferenceNode' not in ref_node:
                try:
                    cmds.referenceQuery(ref_node, filename=True)
                    references.append(Reference(ref_node))
                except BaseException:
                    pass

        return references

    @property
    def file_path(self):
        """The referenced file path.

        :type: str
        """
        return cmds.referenceQuery(
            self, filename=True, withoutCopyNumber=True).replace('\\', '/')

    @property
    def full_file_path(self):
        """The referenced file path with copy number.

        :type: str
        """
        return cmds.referenceQuery(
            self, filename=True, withoutCopyNumber=False).replace('\\', '/')

    @property
    def namespace(self):
        """The namespace of this reference.

        :type: str
        :setter: sets the namespace.
        """
        return self.fn_node.associatedNamespace(True)

    @namespace.setter
    def namespace(self, namespace):
        if self.namespace != namespace:
            cmds.file(self.full_file_path, edit=True, namespace=namespace)

    @property
    def is_loaded(self):
        """The loaded state.

        :type: bool
        """
        return self.fn_node.isLoaded()

    def load(self):
        """Loads this reference.

        Returns:
            None
        """
        if not self.is_loaded:
            cmds.file(loadReference=self)

    def unload(self):
        """Unloads this reference.

        Returns:
            None
        """
        if self.is_loaded:
            cmds.file(unloadReference=self)

    def delete(self):
        """Removes this reference.

        Returns:
            None
        """
        cmds.file(self.full_file_path, removeReference=True, force=True)
