"""

This module will run maya test through maya build-in python interpreter

"""
import argparse
import os
import platform
import subprocess

CMT_ROOT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))


def get_maya_location(maya_version=2019):
    """
    Get the path where maya is installed
    Args:
        maya_version(int): The Maya version

    Returns:
        str: The maya disk path

    """
    if 'MAYA_LOCATION' in os.environ.keys():
        return os.environ['MAYA_LOCATION']
    if platform.system() == 'Windows':
        return 'C:/Program Files/Autodesk/Maya{0}'.format(maya_version)
    elif platform.system() == 'Darwin':
        return '/Applications/Autodesk/maya{0}/Maya.app/Contents'.format(maya_version)
    else:
        location = '/usr/autodesk/maya{0}'.format(maya_version)
        if maya_version < 2016:
            # Starting Maya 2016, the default install directory name changed.
            location += '-x64'
        return location


def get_mayapy_path(maya_version):
    """
    Get the maya executable file
    Args:
        maya_version(int): The Maya version

    Returns:
        str: The mayapy.exe disk path
    """
    python_exe = '{0}/bin/mayapy'.format(get_maya_location(maya_version))
    if platform.system() == 'Windows':
        python_exe += '.exe'
    return python_exe


def main():
    parser = argparse.ArgumentParser(description='Runs unit tests in mayapy')
    parser.add_argument('-p', '--path', help='A path to search test cases from', type=str, default="")

    pargs = parser.parse_args()

    maya_py_runner = os.path.join(os.path.dirname(__file__),
                                  'maya_py_runner.py')
    override_path = pargs.path
    cmd = ["mayapy", maya_py_runner]
    if override_path:
        cmd = cmd + ['-p', override_path]

    try:
        subprocess.check_call(cmd)
    except subprocess.CalledProcessError:
        pass


if __name__ == '__main__':
    main()
