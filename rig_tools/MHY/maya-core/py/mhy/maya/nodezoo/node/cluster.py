from six import string_types

import maya.cmds as cmds

from mhy.maya.nodezoo.node import GeometryFilter, Node, DependencyNode


class Cluster(GeometryFilter):
    """
    Cluster deformer node class.
    """

    __NODETYPE__ = 'cluster'

    @classmethod
    def create(cls, *args, **kwargs):
        if not args:
            args = cmds.ls(sl=True) or []

        for i in args:
            if not cmds.objExists(i):
                raise RuntimeError('{} does not exists'.format(i))

        cluster_result = cmds.cluster(*args, **kwargs)

        if cluster_result:
            cluster, handle = cluster_result
            if not cmds.objExists(cluster):
                # Maya auto rename cluster node based on handle,
                # Sometimes returned cluster name doesn't exits.
                # Need to query cluster node from handle
                cluster_handle = Node(cluster[1])
                destinations = cluster_handle.worldMatrix[0].destinations
                if destinations:
                    cluster = destinations[0].node
                    return cluster, cluster_handle
            else:
                return Node(cluster), Node(handle)

    @classmethod
    def import_create(cls, *args, **kwargs):
        """
        Override import create to return the cluster node instead of tuple
        Args:
            *args:
            **kwargs:

        Returns:

        """
        args, kwargs = cls._pre_creation_callback(*args, **kwargs)
        result = cls.create(*args, **kwargs)
        cls._post_creation_callback(*args, **kwargs)
        return result[0]

    @property
    def attributes_to_export(self):
        attrs = super(Cluster, self).attributes_to_export
        attrs = attrs + ['usePartialResolution', 'relative',
                         'percentResolution', 'angleInterpolation']
        return attrs

    def add_geometry(self, obj):
        """
        Add a geometry to deform set of this cluster
        Args:
            obj(Node or str): A node or name representing the cluster node
        """
        if isinstance(obj, DependencyNode):
            obj = obj.name
        assert isinstance(obj, string_types), "{} is not a string type object".format(obj)
        cmds.cluster(self.name, e=True, geometry=obj)

    def get_handle(self):
        """
        Get the handle
        Returns:

        """
        source = self.clusterXforms.source
        if source:
            return source.node

    def export_additional_data(self):
        """
        Override export_additional_data to export handle information additionally
        Returns:
            dict:
        """
        data = super(Cluster, self).export_additional_data()
        handle = self.get_handle()
        if handle:
            data['handleInfo'] = handle.origin.export()
        return data

    def load(self, data, make_connections=True, rename=False, **kwargs):
        """
        Override load method to additionally set cluster handle ot it was stored in the data
        Args:
            data:
            make_connections:
            rename:

        """
        super(Cluster, self).load(data, make_connections, rename, **kwargs)
        additional_data = data.get('additional')
        if not additional_data:
            return
        handle_data = additional_data.get('handleInfo')
        if not handle_data:
            return
        handle = self.get_handle()
        handle.origin.load(handle_data)

    def clean_up(self):
        """Cleans up cluster weighting on each poly face

        Only works on meshes with non-connected faces,
        such as deformableTransform mesh.
        """
        geom = cmds.cluster(self, query=True, geometry=True)[0]
        shape = Node(geom).get_shapes(type_='mesh')
        if shape:
            shape = shape[0]
        else:
            raise ValueError(
                'Cluster {} is not attached to a mesh.'.format(self))

        for i, vert_ids, in enumerate(shape.polygon_vertices):
            weights = []
            for i in vert_ids:
                vert = '{}.vtx[{}]'.format(shape, i)
                weights.append(
                    cmds.percent(self, vert, query=True, value=True)[0])

            max_weight = max(weights)
            for i in vert_ids:
                vert = '{}.vtx[{}]'.format(shape, i)
                cmds.percent(self, vert, value=max_weight)
                
                
    def mirror_weight(self, mesh):
        '''
        mirror cluster weight from L to R
        '''
        cluster = self.name
        shape = Node(mesh).get_shapes()[0]
        points = shape.get_points()
        lf_pnt_index_dict={}
        for pos in points:
            if pos[0]>0:
                lf_pnt_index_dict[points.index(pos)] = pos
            else:
                continue

        cpom = cmds.createNode('closestPointOnMesh')
        cmds.connectAttr('{}.worldMesh'.format(shape.name), '{}.inMesh'.format(cpom))
        for index, pos in lf_pnt_index_dict.items():
            pnt = '{}.vtx[{}]'.format(shape.name, index)
            wt = cmds.percent(cluster, pnt, q=True, v=True)
            if wt:
                weight = wt[0]
                cmds.setAttr(cpom+'.inPositionX', -pos[0])
                cmds.setAttr(cpom+'.inPositionY', pos[1])
                cmds.setAttr(cpom+'.inPositionZ', pos[2])
                rt_closest_index = cmds.getAttr(cpom+'.closestVertexIndex')
                rt_pnt = '{}.vtx[{}]'.format(shape.name, rt_closest_index)
                cmds.percent(cluster, rt_pnt, value=weight)
            else:
                continue
                    
        cmds.delete(cpom)
