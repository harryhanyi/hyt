import argparse
import os
import json
import re

cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
parser = argparse.ArgumentParser(description='Loading a pipeline file')
parser.add_argument('-p', '--pipeline', help='pipeline path', type=str, default="")
parser.add_argument('-ws', '--workspace', help='workspace path', type=str, default="")

write_env_json = False


def replace_var(matchobj):
    """
    This function replace pattern string with environment
    Args:
        matchobj:

    Returns:

    """
    txt = matchobj.group(0)
    txt = txt[txt.find("<")+1:txt.find(">")]
    if not txt:
        return ""
    split_txt = txt.split('?')
    key = split_txt[0]
    default = ""
    if len(split_txt) == 2:
        default = split_txt[1]
    txt = os.environ.get(key, default)
    return txt


def get_environment_file(package_root):
    is_publish_env = True
    dev_env_json = os.path.join(package_root, 'publish', 'env', 'env.json')
    built_env_json = os.path.join(package_root, 'env', 'env.json')
    environment_file = None
    if os.path.isfile(dev_env_json):
        environment_file = dev_env_json
    elif os.path.isfile(built_env_json):
        is_publish_env = False
        environment_file = built_env_json
    else:
        return environment_file, True
    return environment_file, is_publish_env


def promote_environment_data_to_dict(env_data, cached_env):
    for key, paths in env_data.items():
        if not isinstance(paths, list):
            paths = [paths]
        for path in paths:
            path = re.sub(r'\<(.+?)\>', replace_var, path)
            if not os.path.isabs(path):
                # This is temporary because we have one additional publish
                # hierarchy in source code
                path = os.path.abspath(
                    os.path.join(os.path.dirname(parent_path), path))
            current = cached_env.get(key, "")
            if current:
                path = current + os.pathsep + path
            else:
                path = path

            path = path.replace('\\', '/')
            cached_env[key] = path

args = parser.parse_args()
pipe_line_file = args.pipeline
workspace_file = args.workspace


if not os.path.isfile(pipe_line_file):
    raise OSError("{} is not a valid file path, "
                  "skip setting environment".format(pipe_line_file))

with open(pipe_line_file) as f_data:
    pipe_line_data = json.load(f_data)

env_got_set = {'PATH': ""}

dir_path = os.path.dirname(os.path.abspath(pipe_line_file))

executable_roots = pipe_line_data.get('executable', [])

for path in executable_roots:
    path = re.sub(r'\<(.+?)\>', replace_var, path)
    if not os.path.isabs(path):
        path = os.path.abspath(os.path.join(dir_path, path))
    path = path.replace('\\', '/')
    current = env_got_set.get('PATH', "")
    if current:
        env_got_set['PATH'] = current + os.pathsep + path
    else:
        env_got_set['PATH'] = path

package_roots = pipe_line_data.get('package', [])
env_cache = {}
for root in package_roots:
    package_name = os.path.basename(root)
    if not os.path.isabs(root):
        root = os.path.abspath(os.path.join(dir_path, root))

    env_file, publish_env = get_environment_file(root)
    if not env_file:
        continue

    with open(env_file) as f:
        env_data = json.load(f)
    if not env_data:
        continue

    if publish_env:
        parent_path = os.path.dirname(os.path.dirname(os.path.abspath(env_file)))
    else:
        parent_path = os.path.dirname(os.path.abspath(env_file))
    promote_environment_data_to_dict(env_data, env_got_set)
    if write_env_json:
        env_cache[package_name] = {}
        promote_environment_data_to_dict(env_data, env_cache[package_name])

if env_cache:
    env_json = json.dumps(env_cache, indent=4)
    f = open("./env.json", "w")
    f.write(env_json)
    f.close()

tmp_data = ""
for k, v in env_got_set.items():
    previous_value = os.environ.get(k)
    if previous_value:
        path_for_env = v + os.pathsep + previous_value
    else:
        path_for_env = v
    tmp_data = tmp_data + str(k) + "?" + path_for_env + "\n"

f = open("./.env_temp", "w")
f.write(tmp_data)
f.close()


