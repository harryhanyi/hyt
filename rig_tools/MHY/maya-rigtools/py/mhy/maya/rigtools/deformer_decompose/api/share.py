import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMaya as OpenMaya
import mhy.maya.nodezoo.node as node_api


def created_dummy_deformer(class_object, node_data):
    # Need to create the a dummy mesh of orig mesh from the data
    additional_data = node_data.get('additional')
    if not additional_data:
        return None, None
    out_object_info = additional_data['out_object_info']
    mesh_data = None
    if out_object_info:
        mesh_data = out_object_info.values()[0]
    if not mesh_data:
        return None, None
    mesh_creation_data = mesh_data.get('creation')
    dummy_mesh = node_api.Mesh.create(**mesh_creation_data)
    dummy_mesh.load(mesh_data)
    node_creation_data = node_data.get('creation')
    dummy_deformer = class_object.create_on_geometry(node_creation_data,
                                                     geometry=dummy_mesh.name)
    dummy_deformer.load(node_data)
    return dummy_mesh, dummy_deformer


def filter_targets_for_cluster(targets):
    """
    With some object names passed in, this function will analyze and classify them, return
    none repeated lists of clusters and geometries. They are useful for applying data.
    Args:
        targets(list): A list of names

    Returns:
        (list, list): A list of deformable Nodes and a list of cluster Nodes

    """
    def get_cluster_from_handle(handle_instance):
        dests = handle_instance.clusterTransforms[0].destinations
        for d in dests:
            node = d.node
            if isinstance(node, node_api.Cluster):
                return node
    assert isinstance(targets, list), "Argument is not valid list type"
    clusters = []
    geometries = []

    for obj in targets:
        if '[' in obj:
            OpenMaya.MGlobal.displayWarning("Component targets are not currently supported")
            continue
        target = node_api.Node(obj)
        if isinstance(target, node_api.Cluster):
            clusters.append(target)
            continue
        elif target.type_name == "clusterHandle":
            cluster = get_cluster_from_handle(target)
            if cluster:
                clusters.append(cluster)
                continue
        elif target.is_deformable:
            geometries.append(target)
        elif isinstance(target, node_api.Transform):
            for child in target.get_children():
                if child.type_name == "clusterHandle":
                    cluster = get_cluster_from_handle(child)
                    if cluster:
                        clusters.append(cluster)
                        continue

                elif child.is_deformable and not child.is_intermediate:
                    target = child
                    geometries.append(target)
                    break
    # Remove duplicated objects in selection
    geometries = list(set(geometries))
    clusters = list(set(clusters))
    return geometries, clusters


def filter_targets_for_skin(targets):
    """
    With some object names passed in, this function will analyze and classify them, return
    none repeated lists of skin geometries, clusters and blend shapes. They are useful for applying data.
    Args:
        targets(list): A list of names

    Returns:
        (list, list, list): A list of deformable Nodes, a list of skin cluster Nodes and
        a list of blend shape Nodes

    """
    assert isinstance(targets, list), "Argument is not valid list type"
    geometries = []
    skins = []
    blend_shapes = []

    for obj in targets:
        if '[' in obj:
            OpenMaya.MGlobal.displayWarning("Component targets are not currently supported")
            continue
        target = node_api.Node(obj)
        if isinstance(target, node_api.BlendShape):
            blend_shapes.append(target)
            continue
        elif isinstance(target, node_api.Transform):
            for child in target.get_children():
                if child.is_deformable and not child.is_intermediate:
                    target = child
                    break
        if not target.is_deformable:
            OpenMaya.MGlobal.displayWarning("{} is not deformable, skip".format(target.name))
            continue
        skin = node_api.SkinCluster.find_skin_cluster(target)
        if skin:
            skins.append(skin)
        else:
            geometries.append(target)
    return geometries, skins, blend_shapes


def filter_targets_for_blend_shape(targets):
    """

    With some object names passed in, this function will analyze and classify them, return
    none repeated lists of blend shapes and geometries. They are useful for applying data.
    Args:
        targets(list): A list of names

    Returns:
        (list, list): A list of deformable Nodes and a list of cluster Nodes

    """
    assert isinstance(targets, list), "Argument is not valid list type"
    blend_shapes = []
    geometries = []

    for obj in targets:
        if '[' in obj:
            OpenMaya.MGlobal.displayWarning("Component targets are not currently supported")
            continue
        target = node_api.Node(obj)
        if isinstance(target, node_api.BlendShape):
            blend_shapes.append(target)
            continue
        elif target.is_deformable:
            geometries.append(target)
        elif isinstance(target, node_api.Transform):
            for child in target.get_children():
                if child.is_deformable and not child.is_intermediate:
                    target = child
                    break
            if not target.is_deformable:
                OpenMaya.MGlobal.displayWarning("{} is not deformable, skip".format(target.name))
                continue
            geometries.append(target)
    # Remove duplicated objects in selection
    geometries = list(set(geometries))
    blend_shapes = list(set(blend_shapes))
    return geometries, blend_shapes


def copy_weights_to_deformer(source_deformer,
                             source_shape,
                             destination_deformer,
                             destination_shape=None,
                             surface_association="closestPoint"):
    """
    This function will do some pre-actions on Node instances and pass supported data for maya's
    copySkinWeights which is register as an Api method in GeometryFilter class.

    Args:
        source_deformer(Node): An instance inherited from GeometryFilter that data will be copied from
        source_shape(Node): A deformable object Node
        destination_deformer(Node): An instance inherited from GeometryFilter that data will be copied to
        destination_shape(Node): A deformable object Node
        surface_association(str): The surface association method. Supported options are:
        'closestPoint', 'rayCast', 'closestComponent', 'UvSpace'

    Returns:
        (GeometryFilter): The target geometry instance that data is applied to
    """
    kwargs = {'source_shape': source_shape.name}
    if not destination_shape:
        target_geos = destination_deformer.output_objects
        if not target_geos:
            OpenMaya.MGlobal.displayWarning("{} has no output object, "
                                            "skipped".format(destination_deformer.name))
            return
        destination_shape = target_geos[0]
    kwargs["destination_shape"] = destination_shape.name
    kwargs["destination_deformer"] = destination_deformer.name

    if surface_association == "UvSpace":
        if not isinstance(destination_shape, node_api.Mesh):
            OpenMaya.MGlobal.displayWarning("Target object '{}' has no uv sets."
                                            " Roll back to use distance instead".format(destination_shape.name))

        else:
            source_uvs = source_shape.get_current_uv_set()
            target_uvs = destination_shape.get_current_uv_set()
            if not source_uvs or not target_uvs:
                OpenMaya.MGlobal.displayWarning("Target object '{}' or '{}' has no uv sets."
                                                " Roll back to use distance "
                                                "instead".format(source_shape.name,
                                                                 destination_shape.name))
            else:
                kwargs['uv_space'] = (source_uvs, target_uvs)
        kwargs['surface_association'] = 'closestPoint'
    else:
        kwargs['surface_association'] = surface_association
    source_deformer.copy_weight_to(**kwargs)
    return destination_deformer


def copy_weights_to_skin(source_deformer,  destination_deformer,
                         surface_association="closestPoint", normalize=False,
                         influence_association=None):
    kwargs = {"normalize": normalize,
              "noMirror": True,
              "destination_skin": destination_deformer.name}

    if influence_association:
        kwargs['influenceAssociation'] = influence_association

    source_out_geos = source_deformer.output_objects
    if not source_out_geos:
        OpenMaya.MGlobal.displayWarning("Skin cluster {} has no output object. "
                                        "Skipped".format(source_deformer.name))
        return

    source_shape = source_out_geos[0]
    target_out_geos = destination_deformer.output_objects
    if not target_out_geos:
        OpenMaya.MGlobal.displayWarning("Skin cluster {} has no output object. "
                                        "Skipped".format(destination_deformer.name))
        return

    destination_shape = target_out_geos[0]
    if surface_association == "UvSpace":
        if not isinstance(destination_shape, node_api.Mesh):
            OpenMaya.MGlobal.displayWarning("Target object '{}' has no uv sets."
                                            " Roll back to use distance instead".format(destination_shape.name))

        else:
            source_uvs = source_shape.get_current_uv_set()
            target_uvs = destination_shape.get_current_uv_set()
            if not source_uvs or not target_uvs:
                OpenMaya.MGlobal.displayWarning("Target object '{}' or '{}' has no uv sets."
                                                " Roll back to use distance "
                                                "instead".format(source_shape.name, destination_shape.name))
            else:
                kwargs['uvSpace'] = (source_uvs, target_uvs)

        kwargs['surfaceAssociation'] = 'closestPoint'
    else:
        kwargs['surfaceAssociation'] = surface_association
    source_deformer.copy_weight_to(**kwargs)


def load_cluster_to_objects(data, objects, surface_association='closestPoint', ui=False):
    geometries, clusters = filter_targets_for_cluster(objects)
    creation_data = data.get('creation')
    if geometries and not creation_data:
        OpenMaya.MGlobal.displayError("The data to import has no creation data. Failed to transfer cluster"
                                      "to a new geometry")
        return

    for geo in geometries:
        cluster = node_api.Cluster.create_on_geometry(creation_data, geometry=geo.name)
        clusters.append(cluster)

    g_main_progress_bar = None
    num_nodes = len(clusters)

    if ui:
        g_main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(g_main_progress_bar, e=True, beginProgress=True, isInterruptable=False,
                         status="Importing nodes ...", maxValue=num_nodes + 1)

    if surface_association == 'vertexId':
        try:
            for cluster in clusters:
                if g_main_progress_bar:
                    cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                     status="Loading data to `{}`...".format(cluster.name))
                cluster.load(data)
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            if g_main_progress_bar:
                cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
        return

    # Need to create the a dummy mesh of orig mesh from the data
    if g_main_progress_bar:
        cmds.progressBar(g_main_progress_bar, e=True, step=1,
                         status="Creating dummy objects")
    dummy_mesh, dummy_deformer = node_api.Cluster.create_dummy_deformer(data)
    OpenMaya.MGlobal.displayInfo("Created dummy objects to copy data from")

    if not dummy_mesh or not dummy_deformer:
        OpenMaya.MGlobal.displayWarning("Failed to find source geometry info. "
                                        "Roll back to using vertex association")
        for cluster in clusters:
            cluster.load(data)
            OpenMaya.MGlobal.displayInfo("Imported data to {}".format(cluster.name))
        return

    handle_data = None
    if 'additional' in data:
        handle_data = data['additional'].get('handleInfo')
    try:
        for cluster in clusters:
            if g_main_progress_bar:
                cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                 status="Loading data to `{}`...".format(cluster.name))
            copy_weights_to_deformer(source_deformer=dummy_deformer,
                                     source_shape=dummy_mesh,
                                     destination_deformer=cluster,
                                     surface_association=surface_association)
            handle = cluster.get_handle()
            if handle and handle_data:
                handle.origin.load(handle_data)
            OpenMaya.MGlobal.displayInfo("Imported data to {}".format(cluster.name))

    except Exception as e:
        raise Exception(str(e))
    finally:
        if g_main_progress_bar:
            cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
        cmds.delete(dummy_deformer.name)
        dummy_mesh.destruct()


def load_skin_to_objects(data, objects, surface_association='closestPoint',
                         influence_association=None, normalize=True,
                         ui=False):
    geometries, skins, blendshapes = filter_targets_for_skin(objects)

    for bs in blendshapes:
        # We firstly convert weights to blend shapes
        bs.import_target_weight_from_skin(data)

    # Remove duplicated objects in selection
    geometries = list(set(geometries))
    creation_data = data.get('creation')
    if geometries and not creation_data:
        OpenMaya.MGlobal.displayError("The data to import has no creation data. Failed to transfer skin"
                                      "to a new geometry")
        return
    skins = list(set(skins))
    influences = data.get('influences')
    influence_names, influence_index = None, None
    if influences:
        influence_names, influence_index = influences

    for skin in skins:
        if influence_names and influence_index:
            index_map = skin.sync_influences_and_order(influence_names, influence_index)
            node_api.SkinCluster.update_data_with_index_map(data, index_map)

    for geo in geometries:
        skin = node_api.SkinCluster.create_on_geometry(creation_data, geometry=geo.name)
        skins.append(skin)

    g_main_progress_bar = None
    num_nodes = len(skins)
    if ui:
        g_main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(g_main_progress_bar, e=True, beginProgress=True, isInterruptable=False,
                         status="Importing nodes ...", maxValue=num_nodes + 1)

    if surface_association == 'vertexId':
        for skin in skins:
            skin.load(data)
        return

    # Need to create the a dummy mesh of orig mesh from the data
    if g_main_progress_bar:
        cmds.progressBar(g_main_progress_bar, e=True, step=1,
                         status="Creating dummy objects")
    try:
        dummy_mesh, dummy_deformer = node_api.SkinCluster.create_dummy_deformer(data)
        OpenMaya.MGlobal.displayInfo("Created dummy objects to copy data from")

    except RuntimeError as e:
        if g_main_progress_bar:
            cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
        raise RuntimeError(str(e))

    if not dummy_mesh or not dummy_deformer:
        OpenMaya.MGlobal.displayWarning("Failed to find source geometry info. "
                                        "Roll back to using vertex association")
        for skin in skins:
            skin.load(data)
            OpenMaya.MGlobal.displayInfo("Imported data to {}".format(skin.name))

        return

    try:
        for skin in skins:
            if g_main_progress_bar:
                cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                 status="Loading data to `{}`...".format(skin.name))
            copy_weights_to_skin(source_deformer=dummy_deformer,
                                 destination_deformer=skin,
                                 surface_association=surface_association,
                                 normalize=normalize,
                                 influence_association=influence_association)
            OpenMaya.MGlobal.displayInfo("Imported data to {}".format(skin.name))
    except Exception as e:
        raise Exception(str(e))
    finally:
        if g_main_progress_bar:
            cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
        cmds.delete(dummy_deformer.name)
        dummy_mesh.destruct()


def load_blendshape_to_objects(data, objects, surface_association="closestPoint", ui=False):
    geometries, blend_shapes = filter_targets_for_blend_shape(objects)
    creation_data = data.get('creation')
    if geometries and not creation_data:
        OpenMaya.MGlobal.displayError("The data to import has no creation data. Failed to transfer blend shape"
                                      "to a new geometry")
        return
    for geo in geometries:
        bs = node_api.BlendShape.create_on_geometry(creation_data, geometry=geo.name)
        blend_shapes.append(bs)

    g_main_progress_bar = None
    num_nodes = len(blend_shapes)

    if ui:
        g_main_progress_bar = mel.eval('$tmp = $gMainProgressBar')
        cmds.progressBar(g_main_progress_bar, e=True, beginProgress=True, isInterruptable=False,
                         status="Importing nodes ...", maxValue=num_nodes + 1)

    if surface_association == 'vertexId':
        try:
            for bs in blend_shapes:
                if g_main_progress_bar:
                    cmds.progressBar(g_main_progress_bar, e=True, step=1,
                                     status="Loading data to `{}`...".format(bs.name))
                bs.load(data)
        except RuntimeError as e:
            raise RuntimeError(str(e))
        finally:
            if g_main_progress_bar:
                cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
        return

    # Need to create the a dummy mesh of orig mesh from the data
    if g_main_progress_bar:
        cmds.progressBar(g_main_progress_bar, e=True, step=1,
                         status="Creating dummy objects")
    dummy_mesh, dummy_deformer = node_api.BlendShape.create_dummy_deformer(data)
    OpenMaya.MGlobal.displayInfo("Created dummy objects to copy data from")

    if not dummy_mesh or not dummy_deformer:
        OpenMaya.MGlobal.displayWarning("Failed to find source geometry info. "
                                        "Roll back to using vertex association")
        for bs in blend_shapes:
            bs.load(data)
            OpenMaya.MGlobal.displayInfo("Imported data to {}".format(bs.name))
        return

    try:
        copy_data_to_blend_shape(data, source_deformer=dummy_deformer, destination_shapes=blend_shapes)

    except Exception as e:
        raise Exception(str(e))
    finally:
        if g_main_progress_bar:
            cmds.progressBar(g_main_progress_bar, e=True, endProgress=True)
        cmds.delete(dummy_deformer.name)
        dummy_mesh.destruct()


def copy_data_to_blend_shape(data, source_deformer, destination_shapes):
    for attr in data['attributes']:
        if attr['name'] == 'inputTarget':
            target_data = attr
    out_objects = source_deformer.output_objects
    if not out_objects:
        OpenMaya.MGlobal.displayError("The source cluster {} has"
                                      " no output geometry".format(source_deformer.name))
        return

    for bs in destination_shapes:
        target_output_objects = bs.output_objects
        if not target_output_objects:
            continue
        target_shape = target_output_objects[0]
        if not isinstance(target_shape, node_api.Mesh):
            continue

        vertex_association = target_shape.get_vtx_association_with_distance(out_objects[0])
        for attr in data['attributes']:
            if attr['name'] == 'inputTarget':
                target_data = attr
                target_array = target_data['array']
                for target in target_array:
                    children = target['children']
                    for child in children:
                        if child['name'] == 'baseWeights':
                            update_weight_dict(child, vertex_association)
                        elif child['name'] == 'inputTargetGroup':
                            input_target_group = child
                            target_grp_array = input_target_group.get('array')
                            for target_grp in target_grp_array:
                                target_grp_children = target_grp.get('children')
                                if target_grp_children:
                                    for target_grp_child in target_grp_children:
                                        if target_grp_child['name'] == 'targetWeights':
                                            update_weight_dict(target_grp_child, vertex_association)

        bs.load(data, make_connections=False)


def update_weight_dict(weight_dict, vertex_association):
    tmp_weight_dict = {}
    for ele in weight_dict['array']:
        tmp_weight_dict[ele['index']] = ele['value']
    updated_base_weight_list = []
    for vtx, association in vertex_association.items():
        result_weight = 0
        for bc in association:
            idx, w = bc
            current_weight = tmp_weight_dict.get(idx, 1)
            result_weight = result_weight + current_weight * w
        if result_weight != 1:
            element_data = {'index': vtx, 'value': result_weight}
            updated_base_weight_list.append(element_data)
    weight_dict['array'] = updated_base_weight_list
