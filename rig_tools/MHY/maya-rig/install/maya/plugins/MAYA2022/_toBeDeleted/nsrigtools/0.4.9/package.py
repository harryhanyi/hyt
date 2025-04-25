name = "nsrigtools"

# version = '0.0.1'

authors = ["Rigging"]

description = """
    Load specified rigging plugins in one go.
    """

requires = ["maya", "embree", "bodypusher"]

build_requires = [
    "nsrigGeometryInfo",
    "nsrigPoseInterpolator",
    "nsrigWeightShader",
    "nsrigSmooth",
    "nsrigTransferTools",
    "nsrigProximityMap",
    "nsrigBodyPusher",
    "nsrigCollisionTools",
]

variants = [
    ["platform-windows", "maya-2022.3"],
    ["platform-windows", "maya-2022.1"],
    ["platform-windows", "maya-2020.4"],
]

build_command = 'rez env python-3.7.7 -c "python {root}/rezbuild.py {install}"'


def pre_build_commands():
    import os
    import errno

    if "maya" in resolve:
        maya_major_ver = resolve.maya.version.major

    maya_plugin_path = os.path.join(build.build_path, "plug-ins")
    maya_script_path = os.path.join(build.build_path, "scripts")
    # print(maya_plugin_path)
    # print(maya_script_path)

    def _force_symlink(src, dst):
        try:
            os.symlink(src, dst)
        except OSError as e:
            if e.errno == errno.EEXIST:
                os.remove(dst)
                os.symlink(src, dst)
            else:
                raise e

    def _make_symlink(name, src_dir, dst_dir):
        src = os.path.join(src_dir, name)
        dst = os.path.join(dst_dir, name)

        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)

        _force_symlink(src, dst)

    for pkg in this.build_requires:
        n = str(pkg)

        if n in resolve:
            pkg_root_path = resolve[n].root

            env.NSRIG_RESOLVED_TOOLS.append(str(resolve[n]))

            for d in os.listdir(pkg_root_path):
                # print('  *%s' % d)
                pkg_sub_path = os.path.join(pkg_root_path, d)
                if d == "scripts":
                    for f in os.listdir(pkg_sub_path):
                        # print('    -%s' % f)
                        _make_symlink(f, pkg_sub_path, maya_script_path)
                elif d == "plug-ins":
                    for f in os.listdir(pkg_sub_path):
                        # print('    -%s' % f)
                        _make_symlink(f, pkg_sub_path, maya_plugin_path)


def commands():
    print("Tools installed: %s" % str(this.installed_tools))

    env.MAYA_PLUG_IN_PATH.append("{root}/plug-ins")
    env.MAYA_SCRIPT_PATH.append("{root}/scripts")
    env.PYTHONPATH.append("{root}/scripts")


installed_tools = [
    "nsrigGeometryInfo-0.1.3",
    "nsrigPoseInterpolator-1.0.5",
    "nsrigWeightShader-1.0.6",
    "nsrigSmooth-0.2.1",
    "nsrigTransferTools-0.1.0",
    "nsrigProximityMap-0.1.1",
    "nsrigBodyPusher-0.0.7",
    "nsrigCollisionTools-0.1.0",
]
