@echo off
pushd %~dp0

python ..\py\mhy\maya\mayapy_test\main.py %*

popd