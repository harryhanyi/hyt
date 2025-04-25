<div align="center">

# mhy launcher

</div>

# Introduction
mhy launcher provides a command line tool that initialize environment variables based
on the arbitrary package structure

# Basic Usage
mhy.bat is the main entry point of this launcher system. It does nothing but update environment variables
for the current session. So user can basically call any command with mhy before it to execute under our
environment.
 
 E.g. **mhy python my_script.py**

Without arguments, mhy will assume all the packages are under the same directory as the root of launcher package.
Otherwise, user can use -p argument to pass an arbitrary pipeline file:

E.g. **mhy -p=test.pipeline maya**

It is recommended to add directory of mhy.bat to environment PATH so command can directly recognize it
as executable

# Developer Guide
mhy.bat is fetching environment data merely from a json format pipeline file.
One example of pipeline file is this: 
 ```angular2
{
    "executable": [
        "C:/Program Files/Autodesk/<MAYA_VERSION?2020>/bin"
    ],
    "package": [
        "../maya-core",
        "../maya-rig",
        "../maya-rigtools",
        "../maya-test-resource",
        "../protostar",
        "../python-core"
    ]
}
```
or

 ```angular2
{
    "executable": [
        "C:/Program Files/Autodesk/Maya<MAYA_VERSION?2020>/bin"
    ],
    "package": [
        "C:/Users/admin/Documents/MHY/maya-core",
        "C:/Users/admin/Documents/MHY/maya-rig",
        "C:/Users/admin/Documents/MHY/maya-rigtools",
        "C:/Users/admin/Documents/MHY/maya-test-resource",
        "C:/Users/admin/Documents/MHY/protostar",
        "C:/Users/admin/Documents/MHY/python-core"
    ]
}
```

The launcher recognize special syntax as variable format: **<VARIABLE_KEY?DEFAULT_VALUE>**
When it is generating absolute path from the json file and find this syntax, launcher will replace **VARIABLE_KEY**
string with environment variable with the same name. If no environment found for given key, the **DEFAULT_VALUE** will
be used instead. The **DEFAULT_VALUE** is optional

All the paths in the dictionary support absolute path or relative path from the **pipeline file's location**.

+ The packages list will be analyzed to get environment configurations and executable from each package. The package
 order matters.
+ executable folder under the root of each package will be added to PATH.
+ env.json file under /publish/env is used for registering environments. Values for the same environment key will 
be extended rather than replaced.

# DCC(MAYA) Launcher
maya_launcher.bat is a convenient launcher to open specific maya.exe version. It takes the first argument as maya 
version. 

    E.g. **maya_launcher 2019**
     
# Prerequisites
+ Python
+ Windows OS
