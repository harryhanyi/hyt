import os
import pathlib
import shutil

cwd = str(pathlib.Path(__file__).parent.absolute()) + "/"
pwd = str(pathlib.Path(__file__).parent.parent.absolute()) + "/"

if __name__ == "__main__":
    if os.path.exists(os.path.join(cwd, "install")):
        print("remove existing install folder")
        shutil.rmtree(os.path.join(cwd, "install"))

    # create environment varibles config files
    shutil.copytree(os.path.join(cwd, "env"), os.path.join(cwd, "install/env"))

    # copy whole package into install folder
    shutil.copytree(pwd + "py", cwd + "install/py")
