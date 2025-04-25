"""
This modules contains api for DagNode
"""
from six import string_types
import re
from maya import cmds, mel, OpenMaya

from mhy.maya.nodezoo.node import DependencyNode, Node
from mhy.maya.nodezoo.constant import kMDagPathStr


class DagNode(DependencyNode):
    """
    DAG node class.
    """

    __NODETYPE__ = 'dagNode'
    __FNCLS__ = OpenMaya.MFnDagNode

    def api_repr(self):
        dag_path = self.internal_data.get(kMDagPathStr)
        return dag_path if dag_path else self.object()

    # --- basic properties

    @property
    def is_shape(self):
        """Checks if this is a shape DAG node or not."""
        return 'transform' not in cmds.nodeType(self.long_name, inherited=True)

    @property
    def is_instanced(self):
        """Checks if this is an instanced node."""
        return self.fn_node.isInstanced()

    @property
    def name(self):
        """Returns the short name of this node."""
        return self.fn_node.partialPathName()

    @name.setter
    def name(self, new_name):
        """[Passthrough] Sets the short name of this node."""
        DependencyNode.name.fset(self, new_name)

    @property
    def long_name(self):
        """Returns the long name of this node."""
        return self.fn_node.fullPathName()

    @property
    def is_intermediate(self):
        """Checks if this is a intermediate object."""
        return self.fn_node.isIntermediateObject()

    @property
    def dag_path(self):
        """Returns the dag path object."""
        dag_path = OpenMaya.MDagPath()
        self.fn_node.getPath(dag_path)
        return dag_path

    # --- hierarchy

    @property
    def child_count(self):
        """Returns the number of children."""
        return self.fn_node.childCount()

    def get_parent(self, level=1):
        """Returns the parent of this dag node.

        Args:
            level (int): The parent level to query.
                level 1 means the immediate parent.

        Returns:
            DagNode: The parent dag node.
            None: If level is out of range or this node is under world root.
        """
        parent = self
        for _ in range(level):
            p = Node(parent.fn_node.parent(0))
            if p.name and p.name != 'world':
                parent = p
            else:
                return
        if parent == self:
            return
        return parent

    def is_hidden(self):
        """
        Check if this object is hidden from the view. This method will go
        through the hierarchy, any parent node is hidden, return True
        Returns:
            bool: if this node is hidden
        """
        if self.visibility.value:
            parent = self.get_parent()
            if parent:
                return parent.is_hidden()
            else:
                return False
        return True


    def get_root_parent(self):
        """Returns the root parent node."""
        parent = self
        while parent:
            p = Node(parent.fn_node.parent(0))
            if p.name and p.name != 'world':
                parent = p
            else:
                break
        if parent == self:
            return
        return parent

    def set_parent(self, parent=None):
        """Sets the parent of this node.

        Args:
            parent (str or None): The parent node.
                If None or "world", parent this node to world root.

        Returns: None
        """
        cur = self.get_parent()

        # Parent to world
        if (not parent or str(parent).lower() == 'world') and cur:
            cmds.parent(self.long_name, w=True)
            return

        parent = Node(parent)
        if parent != cur:
            # prepare shape kwargs for cmds.parent()
            kwargs = {}
            if self.is_shape:
                kwargs = {'relative': True, 'shape': True}

            cmds.parent(self.long_name, parent.long_name, **kwargs)

            # rename shape
            if self.is_shape:
                self.name = parent.name + 'Shape'

    def get_children(self, type_=None, exact_type=None):
        """Lists the children nodes.

        Args:
            type_ (str or list): One or more types used to filter the children.
            exact_type(str): Filter only children of specific type

        Returns:
            list: A list of children nodes.
        """
        if type_:
            type_ = type_ if isinstance(type_, (list, tuple)) else [type_]
            type_ = set(type_)

        children = []
        for i in range(self.child_count):
            c = Node(self.fn_node.child(i))
            if not type_ and not exact_type:
                children.append(c)
            elif exact_type and cmds.nodeType(c.name) == exact_type:
                children.append(c)
            elif type_:
                types = set(cmds.nodeType(c.name, inherited=True) or [])
                if type_ & types:
                    children.append(c)

        return children

    def is_child_of(self, node):
        """Checks if this node is a child of a given node."""
        if isinstance(
                node, (string_types, OpenMaya.MObjectHandle, OpenMaya.MObject)):
            node = Node(node)
        if not isinstance(node, Node):
            return False
        return self.fn_node.isChildOf(node.object())

    def is_parent_of(self, node):
        """Checks if this node is a parent of a given node."""
        if isinstance(
                node, (string_types, OpenMaya.MObjectHandle, OpenMaya.MObject)):
            node = Node(node)
        if not isinstance(node, Node):
            return False
        return self.fn_node.isParentOf(node.object())

    def sync_shape_name(self):
        """Finds the transform node of from this dag node,
        then syncs all shape node names with the transform.
        """
        # get the transform node
        if self.is_shape:
            xform = self.get_parent()
        else:
            xform = self

        # rename shapes to match transform
        shape_name = '{}Shape'.format(xform.name).split('|')[-1].split(':')[-1]
        shape_name = shape_name.split('->')[-1]
        for shape in cmds.listRelatives(
                xform.long_name, children=True, shapes=True,
                fullPath=True, noIntermediate=True) or []:
            if not shape.split('|')[-1].startswith(shape_name):
                cmds.rename(shape, shape_name)

    def get_xform(self):
        """If this is a shape, returns the parent transform.
        Otherwise return self.
        """
        if self.is_shape:
            return self.get_parent()
        return self

    def get_shapes(self, type_=None, exact_type=None, intermediate=False):
        """If this is a shape, returns a list of shapes under its
        parent transform. Otherwise return a list of shapes under this node.

        Args:
            type_ (str or list): One or more types used to filter the children.
            exact_type(str: Only shape of specific type will be returned
            intermediate (bool): If True, include intermediate shapes.

        Returns:
            list: A list of children nodes.
        """
        if type_:
            type_ = type_ if isinstance(type_, (list, tuple)) else [type_]
            type_ = set(type_)

        xform = self.get_xform()
        shapes = []
        for s in cmds.listRelatives(xform, shapes=True, fullPath=True) or []:
            s = Node(s)
            if intermediate or not s.is_intermediate:
                if not type_ and not exact_type:
                    shapes.append(s)
                elif exact_type and s.type_name == exact_type:
                    shapes.append(s)
                elif type_ and s.type_name in type_:
                    shapes.append(s)

        return shapes

    def get_deformers(self, type_=None):
        """Returns a list of deformers attached to this node.

        Args:
            type_ (list or None): A list of deformer types to check for.
            if None, return all deformers found.

        Returns:
            list: A list of deformers found.
        """
        deformers = []
        if type_:
            if not isinstance(type_, (list, tuple)):
                type_ = [type_]
            type_ = set(type_)

        for shape in self.get_shapes():
            for each in mel.eval(
                    'findRelatedDeformer "{}"'.format(shape)) or []:
                types = set(cmds.nodeType(each, inherited=True) or [])
                if not type_ or type_ & types:
                    deformers.append(Node(each))

        return list(set(deformers))

    def list_relatives(self, *args, **kwargs):
        """Wrapper around cmds.listRelatives(). """
        nodes = []
        if 'f' in kwargs:
            kwargs.pop('f')
        kwargs['fullPath'] = True
        for node in cmds.listRelatives(self.name, *args, **kwargs) or []:
            nodes.append(Node(node))
        return nodes

    # --- data methods

    def export_creation_data(self):
        """
        Override export creation data. The creation data contains
        the parent node and parent matrix so node recreation can be
        placed at the original position
        Returns:
            dict: Creation data

        """
        data = DependencyNode.export_creation_data(self)
        parent = self.get_parent()
        if parent:
            data['parent'] = parent.name
            world_matrix = parent.dag_path.inclusiveMatrix()
            world_matrix_list = []
            for i in range(4):
                for j in range(4):
                    world_matrix_list.append(world_matrix(i, j))
            data['parentMatrix'] = world_matrix_list
        return data

    # --- misc

    def set_color(self, color=4, shape=False):
        """Sets the color override.

        Args:
            color (int): A color id to set.
            shape (bool): If True, operates on the shape node.

        Returns: None
        """
        shapes = self.get_shapes()
        if shape and shapes:
            for s in shapes:
                s.set_attr('overrideEnabled', True)
                s.set_attr('overrideColor', color)
        else:
            self.set_attr('overrideEnabled', True)
            self.set_attr('overrideColor', color)

    def hide(self):
        """Hides this node."""
        self.v.value = False

    def show(self):
        """Unhides this node."""
        self.v.value = True
        self.lodVisibility.value = True

    def search_hierarchy(self, pattern, upstream=True, traversal_type="depth"):
        """Search the dag hierarchy from this node for another node ends with
        a given regex pattern.

        Args:
            pattern (str): A regex pattern used for matching node names.
            upstream (bool): If True, search upstream, otherwise downstream.
            traversal_type (str): determines the direction of the traversal, valid values are: depth, breadth. Only
            valid for downstream search

        Returns:
            DagNode: The node found.
            None: If no node was found.
        """
        if upstream:
            parent = self.get_parent()
            if not parent:
                return
            if re.match(pattern, parent.name):
                return parent
            return parent.search_hierarchy(pattern, True)
        else:
            if traversal_type == 'depth':
                traversal_type = OpenMaya.MItDag.kDepthFirst
            else:
                traversal_type = OpenMaya.MItDag.kBreadthFirst
            it_dag = OpenMaya.MItDag(traversal_type)
            it_dag.reset(self.dag_path)

            while not it_dag.isDone():
                cur_item = it_dag.currentItem()
                cur_item = Node(cur_item)
                if re.match(pattern, cur_item.name):
                    return cur_item
                it_dag.next()
