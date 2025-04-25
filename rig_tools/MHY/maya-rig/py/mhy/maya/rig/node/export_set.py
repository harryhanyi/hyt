import re

from maya import cmds

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node, Set

import mhy.maya.utils as util
import mhy.maya.rig.constants as const


ATTR_EXPORT_PARENT = 'export_parent'
EXPORT_NODE_TYPES = ('joint', 'mesh')
EXPORT_NODE_ROOTS = {
    'mesh': [const.RIGMESH_ROOT],
    'joint': [const.BIND_SKEL_ROOT]
}


# --- query node info

def _node_type(node):
    """Returns the node type wth shape type taken into account."""
    shape = cmds.listRelatives(
        node, children=True, shapes=True, fullPath=True, noIntermediate=True)
    if shape:
        return cmds.nodeType(shape[0])
    else:
        return cmds.nodeType(node)


def is_export_ready(node):
    """Checks if a node is export ready.
    Only export-ready nodes can be added to export sets.

    export ready nodes must:

        + match type in EXPORT_NODE_TYPES.
        + under root groups defined in EXPORT_NODE_ROOTS, if any.

    Returns:
       bool
    """
    # filter out components
    if '.' in str(node):
        return False

    typ = _node_type(node)
    if isinstance(node, Node):
        node = node.long_name
    else:
        node = Node(node).long_name

    if typ not in EXPORT_NODE_TYPES:
        return False

    namespace = NodeName.namespace(node)
    roots = EXPORT_NODE_ROOTS.get(typ)
    if not roots:
        return True
    for root in roots:
        if namespace:
            root = '{}:{}'.format(namespace, root)
        if cmds.objExists(root) and \
           re.match('.*{}*'.format(root), node):
            return True

    return False


def get_export_ready_node_dict(namespace=None):
    """Returns all export ready node as a dict as
    {node_type: [node]} pairs.

    Args:
        namespace (str or None): The namespace to work within.

    Returns:
        dict: Export ready node dict.
    """
    data = {}
    node_set = set()

    search_strings = ['*', '*:*']
    if namespace:
        search_strings = ['{}:*'.format(namespace)]

    for typ in EXPORT_NODE_TYPES:
        for search_str in search_strings:
            for node in sorted(cmds.ls(search_str, type=typ, long=True) or []):
                if typ == 'mesh':
                    node = Node(node).get_parent()
                else:
                    node = Node(node)
                if node not in node_set and is_export_ready(node):
                    data.setdefault(typ, [])
                    data[typ].append(node)
                    node_set.add(node)
    return data


def get_parent_override(node):
    """Returns the parent override node of a given node.

    Args:
        node (DagNode or str): A node to work with.

    Returns:
        Transform or None: The parent override node.
    """
    node = Node(node)
    if node.has_attr(ATTR_EXPORT_PARENT):
        return node.get_tag(ATTR_EXPORT_PARENT)


def set_parent_override(node, parent):
    """Explicitly sets the exportable parent for a given node.

    Args:
        node (Transform or str): A node to operate on.
        parent (Transform or str): Parent the node to this
            on export.

    Returns:
        None
    """
    if _node_type(node) == 'joint' and _node_type(parent) != 'joint':
        cmds.warning('Joint must be parented to another joint.')
        return
    Node(node).add_tag(ATTR_EXPORT_PARENT, parent, force=True)


def remove_parent_override(node):
    """Removes the parent override of a given node.

    Args:
        node (Transform or str): A node to operate on.

    Returns:
        None
    """
    node = Node(node)
    if node.has_attr(ATTR_EXPORT_PARENT):
        node.delete_attr(ATTR_EXPORT_PARENT)


def nodes_with_parent_override():
    """Returns a list of nodes with parent override.

    Returns:
        list: A list of Transform objects.
    """
    return [Node(x) for x in
            cmds.ls('*.{}'.format(ATTR_EXPORT_PARENT), objectsOnly=True)]


def clear_scene():
    """Removes all export sets and parent overrides in the scene.

    Returns:
        None
    """
    for each in ExportSet.get_export_sets():
        cmds.delete(each)
    for node in nodes_with_parent_override():
        remove_parent_override(node)


# --- Export Set class


class ExportSet(Set):
    """
    Export set class.
    """

    __CUSTOMTYPE__ = 'MHYExportSet'

    @classmethod
    def create(cls, name='asset'):
        """Creates a new expot set.

        Args:
            name (str): Export set name.

        Returns:
            MHYExportSet: The new export set.
        """
        exp_set = cmds.sets(empty=True, name=name)
        return cls.make_custom_node(exp_set)

    @classmethod
    def get_export_sets(cls):
        """Retruns a list of export sets in the scene.

        Returns:
            list: A list of MHYExportSet objects.
        """
        sets = []
        for node in cmds.ls(type='objectSet'):
            node = Node(node)
            if node.custom_type_name == cls.__CUSTOMTYPE__:
                sets.append(node)
        return sets

    def add_member(self, node):
        """Adds a node to this set, Skip and throw warning if this node
        is not export ready.

        Args:
            node (DagNode or str): The node to add.

        Returns:
            None
        """
        if not is_export_ready(node):
            cmds.warning('{} is not export ready.'.format(node))
        else:
            return super(ExportSet, self).add_member(node)

    def clean_members(self):
        """Remove all non-export ready members."""
        for member in self.members:
            if not is_export_ready(member):
                self.remove_member(member)

    def iter_valid_members(self):
        """Iterates through all export ready members.

        Yields:
            DagNode
        """
        for node in self.members:
            if is_export_ready(node):
                yield node

    def get_member_dict(self):
        """Returns a dict of {node_type: [node]} pairs.

        Returns:
            dict: A dict of source nodes.
        """
        data = {}
        for node in self.iter_valid_members():
            typ = _node_type(node)
            data.setdefault(typ, [])
            data[typ].append(Node(node))
        return data

    def get_closest_exportable_parent(self, node):
        """Given a node, returns it's closest exportable parent.

        Args:
            node (DagNode or str): A node to operate on.

        Returns:
            Transform or None: The closest exportable parent.
        """
        if not self.is_member(node):
            cmds.warning('{} is not in export set {}'.format(node, self))
            return

        node = Node(node)
        parent = node
        exp = True

        while parent:
            parent = parent.get_parent()
            exp = self.is_member(parent)
            if exp:
                return parent

    def get_exportable_parent(self, node):
        """Returns a given node's exportable parent node.

        Args:
            node (DagNode or str): A node to operate on.

        Returns:
            Transform or None: The exportable parent node.

        Raises:
            RuntimeError: If the explicit export parent is not exportable.
        """
        if not self.is_member(node):
            cmds.warning('{} is not in export set {}'.format(node, self.name))
            return

        node = Node(node)

        # look for the explicit parent first
        parent = get_parent_override(node)
        if parent and not self.is_member(parent):
            raise RuntimeError(
                ('{} and its export parent {} are not '
                    'in the same export set!').format(node, parent))
        elif parent:
            return parent
        else:
            # no export parent explicitly set, find the closest
            # exportable parent instead.
            return self.get_closest_exportable_parent(node)

    def __get_child(self, root, child_name):
        """Returns a child node under a root node by checking long names."""
        child_name = NodeName.clean_name(child_name)
        for each in cmds.ls(child_name, long=True) + \
                cmds.ls('*:' + child_name, long=True):
            each = Node(each)
            if each.is_child_of(root):
                return each

    def __create_export_joint(self, src_joint, root, attach=True):
        """Creates an export joint and all of its export parent joints.

        Args:
            src_joint (Joint): A source joint to create the
                export joint from.
            root (Transform or str): A root node to host all export joints.
            attach (bool): If True, attach the export joint to the source joint.

        Returns:
            Joint: The export joint.
        """
        exp_joint = self.__get_child(root, src_joint)
        if exp_joint:
            return exp_joint

        src_parent = self.get_exportable_parent(src_joint)
        exp_parent = None

        # make sure its parent is already created
        if src_parent:
            exp_parent = self.__get_child(root, src_parent)
            if not exp_parent:
                exp_parent = self.__create_export_joint(
                    src_parent, root=root, attach=attach)

        # create the export joint
        exp_joint = Node.create(
            'joint', name=NodeName.clean_name(src_joint), clear_selection=True)
        exp_joint.rotateOrder.value = cmds.getAttr(
            '{}.rotateOrder'.format(src_joint))
        if exp_parent:
            exp_joint.set_parent(exp_parent)
        elif root:
            exp_joint.set_parent(root)

        # align the export joint to the rig joint
        exp_joint.align(src_joint)
        exp_joint.make_identity(
            translate=False, rotate=True, scale=True, apply=True)
        if attach:
            exp_joint.constrain('parent', src_joint, maintainOffset=False)
            exp_joint.constrain('scale', src_joint, maintainOffset=False)

        return exp_joint

    @util.undoable
    def create_export_asset(self, attach=True, skel_only=False, force=False):
        """Creates an independent export asset group from the exportable
        members in this set.

        Args:
            attach (bool): If True, attach the export asset to the rig
                via joint constraints.
            skel_only (bool): If True, only builds the skeleton.
            force (bool): If True, remove existing export asset with
                the same name and rebuild it.

        Returns:
            Transform or None: The export asset root group,
            or None if aborted.
        """
        root = 'export_{}'.format(NodeName.clean_name(self))
        if cmds.objExists(root):
            if not force:
                cmds.warning(
                    'Export asset "{}" already exists.'.format(self.name))
                return
            cmds.delete(root)

        src_joints = set()
        src_geoms = []
        for typ, nodes in self.get_member_dict().items():
            if typ == 'joint':
                src_joints = src_joints | set(nodes)
            elif not skel_only and typ == 'mesh':
                src_geoms.extend(nodes)

        # validation
        status = True
        if not skel_only:
            for src_geom in src_geoms:
                skc = src_geom.get_deformers('skinCluster')
                if skc:
                    infs = [Node(i) for i in skc[0].influences]
                    missing_infs = set(infs) - src_joints
                    if missing_infs:
                        cmds.warning(
                            ('{} conatins non-exportable skinned '
                             'joints: {}').format(src_geom, missing_infs))
                        status = False
            if not status:
                return

        # create root group
        root = Node.create('transform', name=root)

        # create export joints
        for src_joint in src_joints:
            self.__create_export_joint(src_joint, root=root, attach=attach)

        # create export geom
        for src_geom in src_geoms:
            name = NodeName.clean_name(src_geom)
            exp_geom = src_geom.duplicate(name=name, parentOnly=False)[0]
            exp_geom.set_parent(root)
            exp_geom.name = name
            for each in exp_geom.get_children(type_='transform'):
                cmds.delete(each)

            skc = src_geom.get_deformers('skinCluster')
            if skc:
                skc = skc[0]
                exp_infs = []
                for inf in skc.influences:
                    exp_infs.append(
                        self.__get_child(root, NodeName.clean_name(inf)))
                exp_skc = cmds.skinCluster(
                    exp_geom, exp_infs, toSelectedBones=True)[0]
                # weights = skc.get_weights_data()
                # Node(exp_skc).set_weight_data(weights)
                cmds.copySkinWeights(
                    sourceSkin=skc,
                    destinationSkin=exp_skc,
                    noMirror=True,
                    smooth=False,
                    surfaceAssociation='closestComponent',
                    influenceAssociation='oneToOne')
