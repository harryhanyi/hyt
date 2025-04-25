from packages.project import Project


def get_project(flavor):
    project = Project(name='maya-test-resource', flavor=flavor)
    project.install(src='resource', dst='resource')
    project.install(src='publish/env', dst='env')
    project.install(src='workarea/rigs/biped/assets', dst='workarea/rigs/biped/assets')
    project.install(src='workarea/rigs/biped/sourceimages', dst='workarea/rigs/biped/sourceimages')
    project.install(src='workarea/rigs/game_face/assets', dst='workarea/rigs/game_face/assets')
    project.install(src='workarea/rigs/hi_face/assets', dst='workarea/rigs/hi_face/assets')
    return project
