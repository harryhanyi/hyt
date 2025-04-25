import maya.cmds as cmds


def gptc_scene_config():
    # set playback speed
    cmds.currentUnit( time='ntsc' )
    
    # set camera pref.
    if cmds.objExists('perspShape'):
        cmds.setAttr('perspShape.focalLength', lock=False)
        cmds.setAttr('perspShape.focalLength', 80)
        cmds.setAttr('perspShape.focalLength', lock=True)
        #cmds.setAttr('perspShape.nearClipPlane', 10)
        
    # set time slider pref.
    start = 990
    end = 1515
    #cmds.playbackOptions(animationStartTime=start,animationEndTime=end,minTime=start,maxTime=end )

        

cmd = """
# register rig nodes on maya startup
try:
    import mhy.maya.rig.node
except Exception as e:
    cmds.warning(str(e))
    

# load plugins
for plugin in (
        'fbxmaya', 'gameFbxExporter', 'objExport',
        'matrixNodes', 'lookdevKit',
        'rbfSolver', 'limbNode', 'mhy', 'cmt'):
    if not cmds.pluginInfo(plugin, query=True, loaded=True):
        try:
            cmds.loadPlugin(plugin, quiet=True)
        except BaseException:
            cmds.warning('Failed loading plugin {}'.format(plugin))
            

# Set project pref
cmds.scriptJob(event=["NewSceneOpened", "gptc_scene_config()"])
cmds.scriptJob(event=["SceneOpened", "gptc_scene_config()"])

gptc_scene_config()

"""

cmds.evalDeferred(cmd)

