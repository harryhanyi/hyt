import maya.cmds as cmds

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.nodezoo.node import Node

from mhy.maya.rig.base_actions import BaseRigUtilAction
import mhy.maya.rig.constants as const
import mhy.maya.rig.rig_global as rg


ANIM_CURVE_TYPES = ('animCurveTL', 'animCurveTU', 'animCurveTA')
DANGLING_NODE_TYPE_BLACKLIST = ('dagNode', 'objectSet', 'materialInfo')


class RigCleanUp(BaseRigUtilAction):
    """
    Runs various operations to clean up the rig in the scene.

    Clean-up operations (in execution order):

        + Remove existing marker system.
            + Marker system is not needed after rig build.
        + Remove useless nodes.
            + e.g. tweak nodes, unknown nodes, dangling nodes.
        + Clean up skin clusters.
            + Prune tiny weights and unused influences.
        + Lock transform nodes.
            + Prevent transforms from being moved or keyed by accident.
        + Hide channelbox history display.
            + So that channelbox only contains keyable attributes.
        + Embed mirror axis on each ctrl.
            + Required for rig mirroring functions.
    """

    _UI_ICON = 'clean'

    # --- input parameters

    @pa.bool_param(default=True)
    def clean_marker(self):
        """If True, removes marker systems in the scene."""

    @pa.bool_param(default=True)
    def lock_transforms(self):
        """If True, locks all non-ctrl transforms."""

    @pa.bool_param(default=True)
    def clean_channelbox_history(self):
        """If True, hides all ctrl channelbox history."""

    @pa.bool_param(default=True)
    def embed_ctrl_mirror_axis(self):
        """If True, embeds ctrl mirror axis data.
        This is required for rig pose mirroring.
        """

    # --- end of parameter definition

    def run(self):
        """Executes this action.

        Raises:
            ActionError: If no rig exists in the scene.
        """
        if not cmds.objExists(const.RIG_ROOT):
            raise exp.ActionError('Rig not found.')

        if self.clean_marker.value:
            if cmds.objExists(const.MARKER_ROOT):
                cmds.delete(const.MARKER_ROOT)

        self._clean_useless_nodes()
        self._clean_skin_cluster()
        self._clean_attributes()
        if self.lock_transforms.value:
            self._lock_transforms()
        if self.clean_channelbox_history.value:
            self._clean_channelbox_history()
        if self.embed_ctrl_mirror_axis.value:
            self._embed_ctrl_mirror_axis()

    def _clean_useless_nodes(self):
        """Deletes useless nodes in the rig."""
        # tweak nodes and unknown nodes
        nodes = set(cmds.ls(exactType='tweak') or [])
        nodes = nodes | set(cmds.ls(type='unknown') or [])

        # animation curves
        for c in cmds.ls(exactType=ANIM_CURVE_TYPES) or []:
            down_stream = cmds.listConnections(c, s=False, d=True, p=False)
            if not down_stream or cmds.nodeType(down_stream[0]) != 'pairBlend':
                nodes.add(c)

        # do delete
        for node in nodes:
            try:
                cmds.lockNode(node, lock=False)
                cmds.delete(node)
            except BaseException:
                cmds.warning('Can\'t delete node: ' + node)

        self._clean_dangling_nodes()

    def _clean_dangling_nodes(self, _node=None):
        """Removes all the dangling dg nodes in the scene."""
        # Get nodes to operate on
        if _node is None:
            nodes = set(cmds.ls(dependencyNodes=True) or [])
            nodes = nodes - set(cmds.ls(dagObjects=True) or [])
            nodes = nodes - set(cmds.ls(undeletable=True) or [])
            if not nodes:
                return []
        else:
            nodes = [_node]

        deleted = []
        for node in nodes:
            if not cmds.objExists(node):
                continue
            fnset = Node(node).fn_node

            if fnset.isDefaultNode() or fnset.isLocked() or\
                    fnset.isFromReferencedFile() or\
                    cmds.objectType(node, isAType='objectSet') or\
                    cmds.objectType(node, isAType='materialInfo'):
                continue

            blackListed = False
            for each in DANGLING_NODE_TYPE_BLACKLIST:
                if cmds.objectType(node, isAType=each):
                    blackListed = True
            if blackListed:
                continue

            # Check for downstream connections
            doDelete = True
            for each in cmds.listConnections(
                    node, source=False, destination=True,
                    plugs=False, skipConversionNodes=True) or []:
                fnset = Node(each).fn_node
                if not fnset.isDefaultNode() and each != node:
                    doDelete = False
                    break
            if not doDelete:
                continue

            # delete this node and check it's upstream nodes
            inputs = cmds.listConnections(
                node, source=True, destination=False,
                plugs=False, skipConversionNodes=True) or []
            try:
                cmds.lockNode(node, lock=False)
                cmds.delete(node)
                deleted.append(node)
                for each in inputs:
                    deleted.extend(self._clean_dangling_nodes(_node=each))
            except BaseException:
                cmds.warning('Can\'t delete node: ' + node)

        return deleted

    def _clean_skin_cluster(self):
        """Prunes small skin weights and removes unused influences."""
        for skc in cmds.ls(exactType='skinCluster') or []:
            skc = Node(skc)
            # unlock infs
            for inf in cmds.skinCluster(skc, query=True, influence=True) or []:
                cmds.setAttr(inf + '.liw', False)
            skc.clean_up()

    def _lock_transforms(self):
        """Locks trsv for all transform nodes that are not ctrls or ik joints.
            + locking ik joints will break the ik solvers.
        """
        root = Node(const.RIG_ROOT)
        root.v.channelBox = True
        root.lock('trs')

        for each in cmds.listRelatives(
                root, fullPath=True, allDescendents=True,
                type='transform') or []:
            each = Node(each)
            if each.custom_type_name == 'MHYCtrl':
                lockattr = 'v'
                for ch in 'trs':
                    for ax in 'xyz':
                        if not each.attr(ch + ax).is_free_to_change:
                            lockattr += ch + ax

            elif each.type_name == 'joint':
                # if joint belongs to an ik chain, hide tr channels
                if cmds.listRelatives(
                        each, allDescendents=True, type='ikEffector') or\
                    cmds.listConnections(
                        '{}.tx'.format(each), type='ikEffector'):
                    attrs = 's'
                else:
                    attrs = 'trs'

                # Get unconnected channels
                lockattr = 'v'
                for attr in attrs:
                    for ax in 'xyz':
                        if not cmds.listConnections(
                                '{}.{}'.format(each, attr + ax),
                                source=True, destination=False):
                            lockattr += attr + ax
            else:
                lockattr = 'all'

            if lockattr:
                each.lock(lockattr)

    def _clean_attributes(self):
        rig = rg.RigGlobal(const.RIG_ROOT)
        limb_shapes = [x.get_shapes()[0] for x in rig.get_limbs()]
        for ctrl in rig.get_ctrls() + limb_shapes:
            for attr in ctrl.list_attr(keyable=True):
                if not attr.is_free_to_change:
                    attr.keyable = False
                    attr.locked = True
                    attr.channelBox = False

    def _clean_channelbox_history(self):
        """Hides input/output histories so that the ctrl channelbox is clean."""
        nodes = set(cmds.ls(
            '*.isHistoricallyInteresting', objectsOnly=True) or [])
        nodes = nodes - set(cmds.ls(sets=True) or [])
        nodes = nodes - set(cmds.ls(lockedNodes=True) or [])
        nodes = nodes - set(cmds.ls(defaultNodes=True) or [])
        nodes = nodes - set(cmds.ls(
            exactType=('unitConversion', 'groupParts', 'groupId')) or [])

        for each in nodes:
            each = Node(each)
            if each.type_name == 'locator' and \
               each.get_parent().custom_type_name == 'MHYLimbRoot' and \
               cmds.listAttr(each, userDefined=True, keyable=True):
                continue
            each.isHistoricallyInteresting.value = False

    def _embed_ctrl_mirror_axis(self):
        """Embed ctrl mirror axis data."""
        rg.RigGlobal(const.RIG_ROOT).embed_ctrl_mirror_axis()
