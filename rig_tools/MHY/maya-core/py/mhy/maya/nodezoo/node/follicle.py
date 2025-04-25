import re

from maya import cmds

from mhy.maya.nodezoo.node import Node, DagNode


class Follicle(DagNode):
    """
    Follicle shape node class.
    """

    __NODETYPE__ = 'follicle'

    @classmethod
    def create(cls, *args, **kwargs):
        """Wrapper create function."""
        if len(args) == 1:
            if not isinstance(args[0], (list, tuple)) and \
               cmds.objExists(str(args[0])):
                return cls._create_from_geom(*args, **kwargs)
            else:
                return cls._create_from_faces(*args, **kwargs)
        elif len(args) == 2:
            return cls._create_from_edges(*args, **kwargs)
        else:
            raise ValueError(
                'Invalid follicle creation arguments: {}, {}'.format(
                    args, kwargs))

    @classmethod
    def _create_from_geom(cls, geom, name='follicle'):
        """Creates a follicle and attach it to a mesh or surface.

        Args:
            geom (str or Node): A surface or mesh to attach the follicle to.
            name (str): Name of follicle transform node.

        Returns:
            Follicle: The follicle shape node.
        """
        # get geom shape node
        geom_shape = Node(geom)
        geom_shape = geom_shape.get_shapes(type_=('nurbsSurface', 'mesh'))
        if geom_shape:
            geom_shape = geom_shape[0]
        else:
            raise ValueError('Invalid geeometry: {}'.formrat(geom))

        # create the follicle node
        fol = Node(cmds.createNode('follicle'))
        xform = fol.get_parent()
        xform.name = name

        # connect attrs
        geom_shape.worldMatrix >> fol.inputWorldMatrix
        if geom_shape.type_name == 'nurbsSurface':
            geom_shape.local >> fol.inputSurface
        else:
            geom_shape.outMesh >> fol.inputMesh

        for ch in ('translate', 'rotate'):
            for ax in 'XYZ':
                fol.attr('out' + ch.capitalize() + ax) >> xform.attr(ch + ax)

        # set flc and relative nodes state to HasNoEffect
        for node in (xform, fol):
            node.set_attr('nodeState', 1)

        return fol

    @classmethod
    def _create_from_edges(cls, edgeA, edgeB, name='follicle', parent=None):
        """Creates a follicle setup from 2 mesh edges and
        attach a locator to it.

        Args:
            edgeA (str): The first edge.
            edgeB (str): The second edge.
            name (str): Name of the follicle transform node.
            parent (str or Node): A node to parent the setup group to.

        Returns:
            Transform: The locator transform node.
        """
        # create a surface from the 2 edges
        surface = Node.create(
            'nurbsSurface', edgeA, edgeB, name=name + '_patch')
        surface_xform = surface.get_parent()
        surface_xform.v.value = False

        # create the follicle
        fol = cls._create_from_geom(surface, name=name)
        fol.parameterU.value = .5
        fol.parameterV.value = .5
        fol_xform = fol.get_parent()

        # attach a locator
        locator = cmds.spaceLocator(name=name + '_loc')[0]
        locator = Node(locator)
        locator.get_shapes()[0].localScale.value = (.3, .3, .3)
        locator.align(fol_xform, constraint=True)

        # create the group node
        group = Node.create('transform', name=name + '_setup')
        if parent:
            group.set_parent(parent)
        for each in (surface_xform, fol_xform, locator):
            each.set_parent(group)

        return locator

    @classmethod
    def _create_from_faces(cls, face_list, parent=None):
        """Creates a follicle setup for each poly face in a given list.

        Args:
            face_list (str or list): One or more faces to work with.

        Returns:
            list: A list of locators attached to each face.
        """
        if not isinstance(face_list, (list, tuple)):
            face_list = [face_list]

        locators = []
        for each in face_list:
            each = str(each)
            edges = cmds.polyInfo(each, faceToEdge=True)
            digis = re.findall(r'\d+', str(edges[0]))
            edges = digis[1:]
            edge_count = len(edges)
            geom = each.split('|')[-1].split('.')[0]
            i = int(each.split('[')[1][:-1])
            locator = cls._create_from_edges(
                '{}.e[{}]'.format(geom, edges[0]),
                '{}.e[{}]'.format(geom, edges[int(round(edge_count / 2))]),
                name='{}_f{}_fol'.format(geom, i), parent=parent)
            locators.append(locator)

        return locators

    @property
    def parameter(self):
        """Returns the current parameter."""
        return self.get_attr('parameterU'), self.get_attr('parameterV')
