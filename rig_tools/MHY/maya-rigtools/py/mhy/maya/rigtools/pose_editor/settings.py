
class Settings(object):
    maximum_weight = 10.0
    epsilon = 0.01
    pose_decimal = 2
    batch_mode = False
    live_update_corrective_weight = True
    channels = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
    mid_poses_group = ['M', 'WHOLE']
    anim_curve_types = ['animCurveUU', 'animCurveUL', 'animCurveUA']
    # affected_node_types = ['unitConversion', 'animCurveUU',
    #                 'animCurveUL', 'animCurveUA', 'blendWeighted']
    affected_node_types = ['unitConversion', 'animCurveUU',
                           'animCurveUL', 'animCurveUA']
    controller_node_name = 'poseDriver_root_00_M_PoseWeightAttributes'
