# MHY Viewport Picker

## What is it?
 Animation picker is an interface that make it easier for animators to select object from the maya scene.
 
 MHY viewport picker is a animation picker system consisted of maya locator shape and a Qt gui with a
 graphic view that manage how the viewport picker is placed in the camera view.
 
## Key Features:
 +  Pickers can be created easily from existing controllers. Users can cast controllers to camera
 space and create picker.
 + A ui supporting add/remove individual pickers manually. 
 + Independent visibility control for picker shapes in viewport
 + Viewport picker supports all maya viewport manipulations including display/selection mask, display layer, 
 isolate selection and so on.
 + Customized look of color, selection color and transparency for each picker item.
 + Pickers can be grouped into containers. Each containers support a image background with alpha channel.
 + Light weight I/O as disk file.
 + Pickers is naturally saved with maya rig scene. No additional data file need to be maintained.
 + Gui picker panel support selection undo. Qt item Selection sync with selection in maya scene.   
 
(TODO)
+ Convenient functions hooked up with hotkey to move/scale/frame pickers in the viewport.
  
 