# Nodezoo Attributes

The Attribute classes is constructed according to maya MFnAttribute

## Usage examples:

Attributes can be initialized with Attribute class
itself.
 
 ```angular2
from mhy.maya.nodezoo.attribute import Attribute
Attribute('perspShape.preScale') # <Nodezoo.Attribute:NumericAttribute: 'perspShape.preScale' at <0x24bee596588L>>
```
Also, user can query attribute from a Node object.
 ```angular2
from mhy.maya.nodezoo.node import Node
camera = Node('persp')
camera.rx # <Nodezoo.Attribute:UnitAttribute: 'persp.rotateX' at <0x24bee5197b8L>>
camera.attr('tx') # <Nodezoo.Attribute:UnitAttribute: 'persp.translateX' at <0x24bd1c40630L>>
```

Getting and setting value are simple:
 ```angular2
print(camera.rx.value)
camera.rx.value = 20
```
 
The interface is the same for different type of attribute. You don't need to search
for the date type of the attribute because the Attribute knows the type of itself! :wink:
 ```angular2
script = Node.create('script')
script.sourceType.value = 1
script.before.value = "print('YES')"
```
 
When it comes to more complex attribute type like ArrayAttribute and CompoundAttribute,
value property is not valid. But nodezoo introduced export and load methods to convert 
their data into dictionary format data and set it back.
 ```angular2
ramp = Node.create('ramp')
data = ramp.uvCoord.export()
ramp.uvCoord.load(data)
```
