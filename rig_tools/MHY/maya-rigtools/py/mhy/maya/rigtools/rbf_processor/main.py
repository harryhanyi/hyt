import os
import maya.cmds as cmds
import mhy.maya.rigtools.epic_pose_wrangler.v2.main as main
from mhy.maya.rigtools.rbf_processor.json_reader import JSONReader

class RBFProcessor:
    RBFSUFFIX = "_UERBFSolver"
    TRANSSUFFIX = "_trans"

    def __init__(self):
        current_dir = os.path.dirname(__file__)
        json_path = os.path.join(current_dir, 'rbf_config.json')
        self.config = JSONReader(json_path)
        self.solver_list = self.config.get_solvers()
        self.drivenTrans_list = None

    def create_solvers(self):
        for solver in self.solver_list:
            self.create_solver_based_json(solver)

    def create_solver_based_json(self, solver):
        if not self.sanity_check(solver):
            return

        # Create solver node
        self.reset_drivers(solver["drivers"])
        rbf_api = main.UERBFAPI(view=False)
        rbf_name = solver["name"] + RBFProcessor.RBFSUFFIX
        rbf_node = rbf_api.create_rbf_solver(solver_name=rbf_name,drivers=solver["drivers"])
        self.add_drivens(solver["drivens"],solver=rbf_node)
        cmds.setAttr(f"{rbf_name}.inputMode",0)

        # Create poses
        for pose in solver["poses"]: 
            self.move_drivers(pose["driver_trans"])
            self.set_drivens(pose["driven_values"])
            rbf_api.create_pose(pose["name"],solver=rbf_node)

    def add_drivens(self, drivens, solver):
        for driven in drivens:
            # Create a transform node
            trans = cmds.group(em=True, name=driven["target"]+TRANSSUFFIX)
            self.drivenTrans_list.append(trans)

            # Connect the driven to this transform node
            target_index = self.find_target_index(driven["blendshape"], driven["target"])
            cmds.connectAttr(trans + '.translateX', "{}.w[{}]".format(driven["blendshape"], target_index))
        solver.add_driven_transforms(self.drivenTrans_list, edit=False)

    def set_drivens(self, driven_values):
        for driven_value in driven_values:
            # blendshape = driven_value["blendshape"]
            trans = driven_value["target"] + TRANSSUFFIX
            transX = driven_value["weight"]
            # target_index = self.find_target_index(blendshape, target)
            # cmds.setAttr("{}.w[{}]".format(blendshape, target_index), weight)
            cmds.setAttr(trans + ".translateX", transX)

    def find_target_index(self, blendshape, target):
        allTargetNames = cmds.aliasAttr(blendshape, query=True)[::2] # Skip every second item to get names only
        return allTargetNames.index(target)

    def move_drivers(self, driver_trans):
        for driver in driver_trans:
            name = driver["name"]
            cmds.setAttr(f"{name}.translateX", driver["trans_x"])
            cmds.setAttr(f"{name}.translateY", driver["trans_y"])

    def reset_drivers(self, drivers):
        for driver in drivers:
            if not cmds.getAttr(f"{driver}.translateX", lock=True):
                cmds.setAttr(f"{driver}.translateX", 0)
            if not cmds.getAttr(f"{driver}.translateY", lock=True):
                cmds.setAttr(f"{driver}.translateY", 0)

    def sanity_check(self, solver):
        # Check json info
        if not self.check_name_in_json(solver):
            print("One RBF solver doesn't have valid name in rbf_config.json")
            return False
        if not self.check_drivers_in_json(solver):
            print("One RBF solver doesn't have valid driver info in rbf_config.json")
            return False
        if not self.check_poses_in_json(solver):
            print("One RBF solver doesn't have valid pose info in rbf_config.json")
            return False
        if not self.check_blendshapes_in_json(solver):
            print("One RBF solver doesn't have valid blendshape info in rbf_config.json")
            return False

        # Check drivers and drivens if exist in Maya scene
        if not self.check_drivers_in_scene(solver):
            print(f"One or more drivers do not exist in current Maya scene.")
            return False
        if not self.check_drivens_in_scene(solver):
            print(f"One or more blendshapes or targets do not exist in current Maya scene.")
            return False

        return True

    def check_drivers_in_scene(self, solver):
        drivers = solver.get("drivers", [])
        for driver in drivers:
            if not cmds.objExists(driver):
                return False
        return True

    def check_drivens_in_scene(self, solver):
        drivens = solver.get("drivens", [])
        for driven in drivens:
            # if no blendshape or target exists
                return False
        return True

    def check_blendshapes_in_scene(self, solver):
        blendshapes = solver.get("blendshapes", [])
        for blendshape in blendshapes:
            if not cmds.objExists(blendshape.get("target")) or not cmds.objExists(blendshape.get("base")):
                return False
        return True

    def check_name_in_json(self, solver):
        return bool(solver.get("name"))

    def check_drivers_in_json(self, solver):
        drivers = solver.get("drivers", [])
        if not drivers:
            return False
        for driver in drivers:
            if driver == "" or driver.isspace():
                return False
        return True

    def check_poses_in_json(self, solver):
        poses = solver.get("poses", [])
        if not poses:
            return False
        for pose in poses:
            if not pose.get("name"):
                return False
            driver_trans = pose.get("driver_trans", [])
            if not driver_trans:
                return False
            for dt in driver_trans:
                if not dt.get("name") or dt.get("trans_x") in [None, ""] or dt.get("trans_y") in [None, ""]:
                    return False
        return True

    def check_blendshapes_in_json(self, solver):
        blendshapes = solver.get("blendshapes", [])
        if not blendshapes:
            return False
        for blendshape in blendshapes:
            if not blendshape.get("pose") or not blendshape.get("target") or not blendshape.get("base"):
                return False
        return True
