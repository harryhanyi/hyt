from packages.project import Project


def get_project(flavor):
    project = Project(name='launcher', flavor=flavor)
    project.install('maya_unittest.bat', 'maya_unittest.bat', local_edit=True)
    project.install('mhy.bat', 'mhy.bat', local_edit=True)
    project.install(src='py', dst='py', local_edit=True)
    project.install('maya_launcher.bat', 'maya_launcher.bat', local_edit=True)
    project.install('mhy_doc.html', 'mhy_doc.html', local_edit=True)
    project.install('hou_launcher.bat', 'hou_launcher.bat', local_edit=True)
    project.install('default.pipeline', 'default.pipeline', local_edit=True)
    return project
