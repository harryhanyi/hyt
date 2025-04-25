import maya.cmds as cmds
from mhy.maya.nodezoo.node import Node

rest_geo = 'head'

targets = cmds.ls('*_TARGET')

bs = Node(cmds.blendShape(targets, rest_geo)[0])

cmds.currentTime(1)
for i in targets:
    cmds.setKeyframe(bs.attr(i).long_name, value=0)

for idx, i in enumerate(targets):
    cmds.currentTime(idx + 2)
    for j in targets:
        if j == i:
            cmds.setKeyframe(bs.attr(j).long_name, value=1)
        else:
            cmds.setKeyframe(bs.attr(j).long_name, value=0)
