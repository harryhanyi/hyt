<div align="center">

# MHY Pose Editor

</div>

# Introduction
Pose Editor is a tool for creating and managing complex network of multiple drivers triggering multiple drivens. The
set up under the hood is lots of animation curves and rbf node. 

It's usually used for additional rig setup on top of
basic joint or fk rig. For example face pose rig or body corrective shapes.

# Features
1. **Influence**: One pose triggers multiple attributes. By default, translation and rotation will be connected. User
can also define specific attribute with a tagging attribute called _poseDrivenAttributes_.
 
2. **PSD blendshape targets**: One pose can trigger a blendshape target. In between shapes are supported. User can save 
a sculpted to a target in pose space.
  
3. **Combine Poses**: User can trigger one pose with multiple existing poses at given weights. 

# Prerequisites
+ mhyController
+ rbfSolver


