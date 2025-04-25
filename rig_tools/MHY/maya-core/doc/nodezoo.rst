=======
Nodezoo
=======

Nodezoo is an inhouse maya node api library. It provides interface for
all maya nodes and also some plugin nodes studio maintains internally.

What is it for?
===============

1. Nodezoo is an object-oriented high level factory interface based on
   maya built-in python api and cmds. It is more intuitive to learn
   because the functionality of an object is directly associated with
   the object itself.

2. Nodezoo is a api center that all the node related functions can be
   registered here and shared with other front end tools. It will try to
   provide enough api functions so that user can avoid duplicated
   implementations.

3. Nodezoo provide a easy way to query, edit, export or import nested
   attributes which is cumbersome using native maya api.


Limitation
==========

Since nodezoo created another layer of logic on top of the maya native
api, so user may comes to a bottleneck if they need to push the
performace to some level. So it might not be suitable for applications
involving large number of nodes or attributes editing and with very
high-performace requirements.


Node
======================

All the examples should be executed after import Node factory class

.. code-block:: python

    from mhy.maya.nodezoo.node import Node


The Basics
----------

Creating a Node object from factory is simple. Just call Node class with
an argument of string or OpenMaya instance type.

.. code-block:: python

    import maya.cmds as cmds
    cube_transform, cube_shape = cmds.polyCube()
    transform = Node(cube_transform)
    # >> mesh = Node(cube\_shape)


Based on the object passed in, a Node instance of closest api type will be  returned.

There are two ways to access attribute from a node. One is using dot sign as python get attribute syntax.

.. code-block:: python

    transform.tx
    # >> <Nodezoo.Attribute:UnitAttribute: 'pCube3.translateX' at <0x24bee519a20L>>

The other way is using .attr method.

.. code-block:: python

    transform.attr('tx')
    # >> <Nodezoo.Attribute:UnitAttribute: 'pCube3.translateX' at <0x24bee519a20L>>

**If using .attrName to get node attribute, instance will search for
class method first then node attribute.**


Register studio override
------------------------

If user wants to extend an existing maya node type with some studio
overrides, please follow the steps below to register it.

-  Subclass the closest node type class

.. code-block:: python

    from mhy.maya.nodezoo.node.joint import Joint
    class LsJoint(Joint):
         pass

+ Create a class attribute as the tag attribute

.. code-block:: python

    __CUSTOMTYPE__ = 'LSJoint'

-  Be sure a string typed attribute named with nodezoo\_type will be
   added to target object with the same value as returned from the
   **nodezoo\_type** property.

-  added class import to the top init file:
   **maya-core/py/mhy/maya/nodezoo/node/\_\ *init\_*.py**\  so the
   factory will register it.

.. code-block:: python

    from _ls_joint import LsJoint


Attribute
======================
The Attribute classes is constructed according to maya MFnAttribute

The Basics
---------------

Attributes can be initialized with Attribute class itself.

.. code-block:: python

    from mhy.maya.nodezoo.attribute import Attribute
    Attribute('perspShape.preScale')
    # >> <Nodezoo.Attribute:NumericAttribute: 'perspShape.preScale' at <0x24bee596588L>>

Also, user can query attribute from a Node object.

.. code-block:: python

    from mhy.maya.nodezoo.node import Node
    camera = Node('persp')
    camera.rx
    # >> <Nodezoo.Attribute:UnitAttribute: 'persp.rotateX' at <0x24bee5197b8L>>
    camera.attr('tx')
    # >> <Nodezoo.Attribute:UnitAttribute: 'persp.translateX' at <0x24bd1c40630L>>

Getting and setting value are simple:
.. code-block:: python

    print(camera.rx.value)
    camera.rx.value = 20

The interface is the same for different type of attribute. You don't
need to search for the date type of the attribute because the Attribute
knows the type of itself!

.. code-block:: python

    script = Node.create('script')
    script.sourceType.value = 1
    script.before.value = "print('YES')"

When it comes to more complex attribute type like ArrayAttribute and
CompoundAttribute, value property is not valid. But nodezoo introduced
export and load methods to convert their data into dictionary format
data and set it back.

.. code-block:: python

    ramp = Node.create('ramp')
    data = ramp.uvCoord.export()
    ramp.uvCoord.load(data)


API Reference
=============

Node Class List
---------------

.. autosummary::
   :toctree: node_api

    mhy.maya.nodezoo.node.node_.Node
    mhy.maya.nodezoo.node.anim_curve.AnimCurve
    mhy.maya.nodezoo.node.blend_shape.BlendShape
    mhy.maya.nodezoo.node.cluster.Cluster
    mhy.maya.nodezoo.node.dag_node.DagNode
    mhy.maya.nodezoo.node.dependency_node.DependencyNode
    mhy.maya.nodezoo.node.follicle.Follicle
    mhy.maya.nodezoo.node.geometry_filter.GeometryFilter
    mhy.maya.nodezoo.node.joint.Joint
    mhy.maya.nodezoo.node.lattice.Lattice
    mhy.maya.nodezoo.node.mesh.Mesh
    mhy.maya.nodezoo.node.nurbs_curve.NurbsCurve
    mhy.maya.nodezoo.node.nurbs_surface.NurbsSurface
    mhy.maya.nodezoo.node.rbf_solver.RbfSolver
    mhy.maya.nodezoo.node.set_.Set
    mhy.maya.nodezoo.node.skin_cluster.SkinCluster
    mhy.maya.nodezoo.node.transform.Transform
    mhy.maya.nodezoo.node.viewport_picker.ViewportPicker

Attribute Class List
--------------------

.. autosummary::
   :toctree: attribute_api

    mhy.maya.nodezoo.attribute.attribute_.Attribute
    mhy.maya.nodezoo.attribute.array_attribute.ArrayAttribute
    mhy.maya.nodezoo.attribute.compound_attribute.CompoundAttribute
    mhy.maya.nodezoo.attribute.enum_attribute.EnumAttribute
    mhy.maya.nodezoo.attribute.generic_attribute.GenericAttribute
    mhy.maya.nodezoo.attribute.light_data_attribute.LightDataAttribute
    mhy.maya.nodezoo.attribute.matrix_attribute.MatrixAttribute
    mhy.maya.nodezoo.attribute.message_attribute.MessageAttribute
    mhy.maya.nodezoo.attribute.multi_numeric_attribute.MultiNumericAttribute
    mhy.maya.nodezoo.attribute.typed_attribute.TypedAttribute
    mhy.maya.nodezoo.attribute.unit_attribute.UnitAttribute

Utility Function List
---------------------

.. autosummary::
   :toctree: utils_api

    mhy.maya.nodezoo.utils
