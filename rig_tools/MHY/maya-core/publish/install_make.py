import os
import pathlib
import shutil
import json

cwd = str(pathlib.Path(__file__).parent.absolute()) + "/"
pwd = str(pathlib.Path(__file__).parent.parent.absolute()) + "/"

if __name__ == "__main__":
    if os.path.exists(os.path.join(cwd, "install")):
        print("remove existing install folder")
        shutil.rmtree(os.path.join(cwd, "install"))

    # create environment varibles config files
    os.makedirs(os.path.join(cwd, "install/env"))
    env_variables = {
        "PYTHONPATH": "./py"
    }
    with open(os.path.join(cwd, "install/env/env.json"), 'w') as env_config:
        env_config.write(json.dumps(env_variables, indent=4))

    # copy whole package into install folder
    shutil.copytree(pwd + "py", cwd + "install/py")
