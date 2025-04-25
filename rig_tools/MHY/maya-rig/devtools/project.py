from packages.project import Project, MayaTarget
from packages import locate
from packages import logger
import os
import subprocess
import shutil

class MayaRigProject(Project):
    def __init__(self, name, flavor, maya_vers=[2020]) -> None:
        super().__init__(name=name, flavor=flavor)
        for maya_ver  in maya_vers:
            maya_path = locate.maya(version=maya_ver)
            if maya_path:
                self.add_target(MayaTarget('mhy', 'src/plugins/mhy', maya_ver), libs=['OpenMaya','OpenAnimation'])
            else:
                logger.error("Can't find Maya{}, skip building plugin: {}@{}".format(maya_ver, name, maya_ver))
        self.add_static(libs=['jsoncpp_static'])
        self.add_conda_header_prefix(['json', 'eigen3'])

    def build(self):
        if self.targets:
            for target in self.targets:
                #makde build directory.
                build_folder = self.build_folder(target)
                #generate the files.
                self.generate_headers(target)
                if not os.path.isdir(build_folder):
                    shutil.os.makedirs(build_folder)
                self.generate_cmake(target)
                subprocess.call(['{}/shell/build.bat'.format(Project.dev_root), target.name], env=self.build_env(target))
       
def get_project(flavor):    
    project = MayaRigProject(name='maya-rig', flavor=flavor, maya_vers=[2018, 2020, 2022])
    project.install(src='py', dst='py', local_edit=True)
    project.install(src='resource', dst='resource')
    project.install(src='doc_html', dst='doc_html')
    project.install(src='prebuilt/maya', dst='maya')
    project.install(src='prebuilt/ue_rbf', dst='ue_rbf')
    project.install(src='publish/env', dst='env')
    project.install(src='test', dst='test')
    return project

def build(flavor, maya_ver):
    project = MayaRigProject(name='maya-rig', flavor=flavor, maya_vers=[maya_ver])
    project.build()
