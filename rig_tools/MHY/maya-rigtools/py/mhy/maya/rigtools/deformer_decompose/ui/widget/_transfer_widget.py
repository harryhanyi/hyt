from mhy.qt.core import QtWidgets
import mhy.maya.nodezoo.node as nodeApi
import mhy.maya.rigtools.deformer_decompose.api.share as share
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds


class NodeType(object):
    kSkinCluster = "skinCluster"
    kBlendShape = "blendShape"
    kCluster = "cluster"


class TransferWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(TransferWidget, self).__init__(parent)
        self.currentNodeType = None
        main_layout = QtWidgets.QVBoxLayout()
        content_layout = QtWidgets.QVBoxLayout(self)
        box = QtWidgets.QGroupBox("Transfer")
        box.setLayout(content_layout)
        self.setLayout(main_layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        transfer_method_layout = QtWidgets.QHBoxLayout()
        transfer_method_label = QtWidgets.QLabel("Surface Associations:")
        self.transfer_method_combo = QtWidgets.QComboBox(self)
        transfer_method_layout.addWidget(transfer_method_label)
        self.transfer_method_combo.addItems(['closestPoint', 'rayCast', 'closestComponent', 'UvSpace'])
        transfer_method_layout.addWidget(self.transfer_method_combo)
        self.weight_only_check = QtWidgets.QCheckBox("Weight Only")
        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        # self.create_new_def_cb = QtWidgets.QCheckBox("Creat New Deformer")
        # self.create_new_def_cb.setToolTip("If created a new deformer for target objects"
        #                                   " instead of adding them to the deformed set of source node")
        self.ia_widget = QtWidgets.QWidget(self)
        ia_layout = QtWidgets.QGridLayout()
        ia_layout.setContentsMargins(0, 0, 0, 0)
        self.ia_widget.setLayout(ia_layout)
        ia_methods = ['None', "closestJoint", "oneToOne", "label", "name"]
        inf_association_one_label = QtWidgets.QLabel("Influence Association 1:")
        self.inf_association_one_combo = QtWidgets.QComboBox()
        self.inf_association_one_combo.addItems(ia_methods)
        self.inf_association_one_combo.setCurrentText('Closest joint')
        inf_association_two_label = QtWidgets.QLabel("Influence Association 2:")
        self.inf_association_two_combo = QtWidgets.QComboBox()
        self.inf_association_two_combo.addItems(ia_methods)
        inf_association_three_label = QtWidgets.QLabel("Influence Association 3:")
        self.inf_association_three_combo = QtWidgets.QComboBox()
        self.inf_association_three_combo.addItems(ia_methods)
        ia_layout.addWidget(inf_association_one_label, 0, 0)
        ia_layout.addWidget(self.inf_association_one_combo, 0, 1)
        ia_layout.addWidget(inf_association_two_label, 1, 0)
        ia_layout.addWidget(self.inf_association_two_combo, 1, 1)
        ia_layout.addWidget(inf_association_three_label, 2, 0)
        ia_layout.addWidget(self.inf_association_three_combo, 2, 1)

        self.normalize_check = QtWidgets.QCheckBox('Normalize', self)
        transfer_pb = QtWidgets.QPushButton("&Transfer selected object", self)
        transfer_pb.setToolTip("This button will transfer weights from First selected objects to others."
                               "(ignoring the items selected in the list view on the left panel")
        content_layout.addLayout(transfer_method_layout)
        content_layout.addWidget(self.weight_only_check)
        content_layout.addWidget(line)
        content_layout.addWidget(self.ia_widget)
        content_layout.addWidget(self.normalize_check)
        content_layout.addWidget(transfer_pb)
        main_layout.addWidget(box)
        transfer_pb.clicked.connect(self.do_transfer)

    def do_transfer(self):
        """
        Call specific transfer function based on selected node type
        Returns:

        """
        if self.currentNodeType == NodeType.kSkinCluster:
            self.transfer_skin_cluster()
        elif self.currentNodeType == NodeType.kBlendShape:
            self.transfer_blend_shape()
        elif self.currentNodeType == NodeType.kCluster:
            self.transfer_cluster()

    def transfer_blend_shape(self):
        sel = cmds.ls(sl=True)
        assert len(sel) > 1, "Please select a blend shape and the objects to transfer to"
        assert '[' not in sel[0], "Please select blend shape object as transfer source"

        # Get cluster node from the first selected object if it's cluster handler
        source_node = nodeApi.Node(sel[0])
        assert isinstance(source_node, nodeApi.BlendShape), "{} is not a blend shape node".format(sel[0])

        geometries, blend_shapes = share.filter_targets_for_blend_shape(sel[1:])
        creation_data = source_node.export_creation_data()
        if geometries and not creation_data:
            OpenMaya.MGlobal.displayError("The data to import has no creation data. Failed to transfer cluster"
                                          "to a new geometry")
            return

        for geo in geometries:
            bs = nodeApi.BlendShape.create_on_geometry(creation_data,
                                                       geometry=geo.name,
                                                       rename=geo.name.lower() + '_CL')
            blend_shapes.append(bs)

        surface_association = self.transfer_method_combo.currentText()
        data = source_node.export(weight_only=self.weight_only_check.isChecked())

        if surface_association == "vertexId":
            for bs in blend_shapes:
                bs.load(data)
            return

        else:
            share.copy_data_to_blend_shape(data=data, source_deformer=source_node,
                                           destination_shapes=blend_shapes)

    def transfer_cluster(self):
        sel = cmds.ls(sl=True)
        assert len(sel) > 1, "Please select a cluster and the objects to transfer to"
        assert '[' not in sel[0], "Please select cluster object as transfer source"

        # Get cluster node from the first selected object if it's cluster handler
        source_node = nodeApi.Node(sel[0])
        dests = []
        if isinstance(source_node, nodeApi.Transform):
            dests = source_node.worldMatrix[0].destinations

        elif source_node.type_name == "clusterHandle":
            dests = source_node.clusterTransforms[0].destinations
        for d in dests:
            node = d.node
            if isinstance(node, nodeApi.Cluster):
                source_node = node
                break
        assert isinstance(source_node, nodeApi.Cluster), "{} is not a cluster node".format(sel[0])

        geometries, clusters = share.filter_targets_for_cluster(sel[1:])
        creation_data = source_node.export_creation_data()
        if geometries and not creation_data:
            OpenMaya.MGlobal.displayError("The data to import has no creation data. Failed to transfer cluster"
                                          "to a new geometry")
            return

        for geo in geometries:
            cluster = nodeApi.Cluster.create_on_geometry(creation_data,
                                                         geometry=geo.name,
                                                         rename=geo.name.lower() + '_CL')
            clusters.append(cluster)

        surface_association = self.transfer_method_combo.currentText()

        if surface_association == 'vertexId':
            data = source_node.export()
            for cluster in clusters:
                cluster.load(data)
            return

        addition_data = source_node.export_additional_data()
        handle_data = addition_data.get('handleInfo')
        out_objects = source_node.output_objects
        if not out_objects:
            OpenMaya.MGlobal.displayError("The source cluster {} has"
                                          " no output geometry".format(source_node.name))
            return
        for cluster in clusters:
            share.copy_weights_to_deformer(source_deformer=source_node,
                                           source_shape=out_objects[0],
                                           destination_deformer=cluster,
                                           surface_association=surface_association)
            handle = cluster.get_handle()
            if handle and handle_data:
                handle.origin.load(handle_data)

    def transfer_skin_cluster(self):
        """

        Returns:

        """
        sel = cmds.ls(sl=True)
        assert len(sel) > 1, "Please select more than one object to transfer"
        # Get skin cluster node from the first selected object
        source_node = nodeApi.Node(sel[0])
        if isinstance(source_node, nodeApi.Transform):
            for child in source_node.get_children():
                if child.is_deformable and not child.is_intermediate:
                    source_node = child
                    break

        if source_node.is_deformable:
            source_node = nodeApi.SkinCluster.find_skin_cluster(source_node)

        assert source_node.type_name == 'skinCluster', "Failed to find skinCluster on {}".format(source_node.name)

        outputs = source_node.output_objects
        assert outputs, "{} has no deformed objects".format(source_node.name)
        # Fetch arguments from the ui
        influence_association = [
            self.inf_association_one_combo.currentText(),
            self.inf_association_two_combo.currentText(),
            self.inf_association_three_combo.currentText()
        ]

        influence_association = [i for i in influence_association if i != "None"]
        surface_association = self.transfer_method_combo.currentText()
        normalize = self.normalize_check.isChecked()

        geometries, skins, blend_shapes = share.filter_targets_for_skin(sel[1:])
        # Remove duplicated objects in selection

        geometries = list(set(geometries))
        creation_data = source_node.export_creation_data()
        if geometries and not creation_data:
            OpenMaya.MGlobal.displayError("The data to import has no creation data. Failed to transfer skin"
                                          "to a new geometry")
            return

        skins = list(set(skins))
        influences = source_node.influences
        influences_names = [i for i in influences]
        influence_index = source_node.influence_indexes()
        for skin in skins:
            skin.sync_influences_and_order(influences_names, influence_index)

        if surface_association == 'vertexId' or blend_shapes:
            source_data = source_node.export()
            for bs in blend_shapes:
                # We firstly convert weights to blend shapes
                bs.import_target_weight_from_skin(source_data)
                OpenMaya.MGlobal.displayInfo("Copied joint weights to blend shapes"
                                              "target weight from {} to {}".format(source_node.name, bs.name))

            for skin in skins:
                skin.load(source_data)
            return

        for geo in geometries:
            skin = nodeApi.SkinCluster.create_on_geometry(creation_data,
                                                          geometry=geo.name,
                                                          rename="{}_SC".format(geo.name.lower()))
            skins.append(skin)

        for skin in skins:
            share.copy_weights_to_skin(source_deformer=source_node,
                                       destination_deformer=skin,
                                       surface_association=surface_association,
                                       normalize=normalize,
                                       influence_association=influence_association)

    def update_node_type(self, nodeType):
        """
        Args:
            nodeType(str): The selected node type to refresh ui layout

        """
        self.currentNodeType = nodeType
        if nodeType == "skinCluster":
            self.ia_widget.show()
            self.normalize_check.show()
        else:
            self.ia_widget.hide()
            self.normalize_check.hide()


def get_mesh_uv_set(mesh):
    """
    Get current uv set name on given mesh object
    Args:
        mesh:

    Returns:
        str: name of uv

    """
    if isinstance(mesh, nodeApi.Mesh):
        return mesh.get_current_uv_set()
