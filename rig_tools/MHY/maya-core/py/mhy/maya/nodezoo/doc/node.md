# Nodezoo Nodes library

 All the examples should be executed after import Node factory class
  
 ```angular2
from mhy.maya.nodezoo.node import Node
```
## The Basics
Creating a Node object from factory is simple. Just call Node class with an argument of string or OpenMaya instance type.  
 
 ```angular2
import maya.cmds as cmds

cube_transform, cube_shape = cmds.polyCube()

transform = Node(cube_transform) # <Nodezoo.Node Transform: 'pCube3' at <0x24bee519940L>>
mesh = Node(cube_shape) # <Nodezoo.Node DependencyNode: 'polyCube3' at <0x24bee519978L>>
``` 
Based on the object passed in, a Node instance of closest api type will be  returned. 

There are two ways to access attribute from a node. One is using dot sign as python get attribute syntax.
 ```angular2
transform.tx # <Nodezoo.Attribute:UnitAttribute: 'pCube3.translateX' at <0x24bee519a20L>>
``` 
 The other way is using .attr method.
  ```angular2
transform.attr('tx') # <Nodezoo.Attribute:UnitAttribute: 'pCube3.translateX' at <0x24bee519a20L>>
``` 
**If using .attrName to get node attribute, instance will search for class method first then node attribute.**

More detailed usage of [Attribute](attribute.md) 



## Register studio override
If  user wants to extend an existing maya node type with some studio 
overrides, please follow the steps below to register it.

+ Subclass the closest node type class

 ```angular2
from mhy.maya.nodezoo.node._joint import Joint
class LsJoint(Joint):
    pass
``` 
 + Create a class attribute as the tag attribute
 ```augular2
    __CUSTOMTYPE__ = 'LSJoint'
    
```
 
 + Be sure a string typed attribute named with nodezoo_type will be added to target object with the same value as
 returned from the nodezoo_type property.
 
 + added class import to the top init file: <br />
 **maya-core/py/mhy/maya/nodezoo/node/\__init\__.py**<br />
  so the factory will register it.
 ```angular2
 from _ls_joint import LsJoint
 ```
