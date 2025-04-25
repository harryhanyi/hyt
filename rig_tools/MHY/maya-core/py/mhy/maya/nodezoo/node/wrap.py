import maya.cmds as cmds
import maya.internal.nodes.proximitywrap.node_interface as node_interface

from mhy.maya.nodezoo.node import GeometryFilter, Node


class ProximityWrap(GeometryFilter):
    """
        ProximityWrap node class.
        Maya doesn't have a specific command to create proxcimity wrap.
    """

    __NODETYPE__ = 'proximityWrap'

    deformer=None

    @classmethod
    def create(cls, *args, **kwargs):
        """
            Create a proximityWrap node.
        """
        driven = kwargs.get('driven')
        driver = kwargs.get('driver')
        deformer_name = kwargs.get('name')

        if driven and driver:
            """ using kwargs """
            if isinstance(driver, str):
                driver = [driver]
                
            cls.deformer = ProximityWrap.__create_with_input(driven, driver, deformer_name)
            ProximityWrap.__config_settings(**kwargs)
        
        else:
            """ using args or scene selection """
            if not args:
                args = cmds.ls(sl=True) or []

            for i in args:
                if not cmds.objExists(i):
                    raise RuntimeError('{} does not exists'.format(i))
            
            driven = args[0]
            drivers = args[1:]
            cls.deformer = ProximityWrap.__create_with_input(driven, drivers, deformer_name)
            ProximityWrap.__config_settings(**kwargs)

        return cls.deformer

    @classmethod
    def __create_with_input(cls, driven, driver, deformer_name):
        """
        """
        if driven and driver:
            deformer = cmds.deformer(driven, type='proximityWrap', name=deformer_name)[0]
            for drvr in driver:
                proximity_interface = node_interface.NodeInterface(deformer)
                proximity_interface.addDriver(Node(drvr).get_shapes()[-1])
                
        return Node(deformer)
    
    @classmethod
    def __replace_driver_bind_geo(cls, mesh):
        shape = Node(mesh).get_shapes()[-1]
        src_plug = shape.attr('outMesh')
        des_plug = cls.deformer.attr('drivers[0].driverBindGeometry')
        src_plug.connect(des_plug, force=True)
        print('{} >> {}'.format(src_plug, des_plug))    #


    @classmethod
    def __config_settings(cls, **kwargs):
        """ post config proximity wrap settings """

        wrapMode = kwargs.get('wrapMode')
        maxDrivers = kwargs.get('maxDrivers')
        falloffScale = kwargs.get('falloffScale')
        smoothInfluences = kwargs.get('smoothInfluences')
        smoothNormals = kwargs.get('smoothNormals')
        driverBindGeo = kwargs.get('driverBindGeo')

        modes = ['offset', 'surface', 'snap', 'rigid', 'cluster']
        
        if wrapMode:
            value = float(modes.index(wrapMode))
            cls.deformer.set_attr('wrapMode', value)
        if maxDrivers:
            cls.deformer.set_attr('maxDrivers', maxDrivers)
        if falloffScale:
            cls.deformer.set_attr('falloffScale', falloffScale)
        if smoothInfluences:
            cls.deformer.set_attr('smoothInfluences', smoothInfluences)
        if smoothNormals:
            cls.deformer.set_attr('smoothNormals', smoothNormals)
            
        if driverBindGeo:
            cls.__replace_driver_bind_geo(driverBindGeo)

                
                



