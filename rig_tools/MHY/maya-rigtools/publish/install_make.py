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

    # copy run.bat
    os.makedirs(os.path.join(cwd, "install/env"))
    shutil.copy(os.path.join(cwd, "env_init.rawpy"),
                os.path.join(cwd, "install/env/env_init.py"))

    # create environment varibles config files
    env_variables = {
        "PYTHONPATH": "./py"
    }
    with open(os.path.join(cwd, "install/env/env.json"), 'w') as env_config:
        env_config.write(json.dumps(env_variables, indent=4))

    if os.path.exists(os.path.join(cwd, "run.rawbat")):
        shutil.copy(os.path.join(cwd, "run.rawbat"),
                    os.path.join(cwd, "install/env/run.bat"))

    # copy whole package into install folder
    shutil.copytree(pwd + "py", cwd + "install/py")
