from mhy.maya.nodezoo.node import DependencyNode


class RbfSolver(DependencyNode):
    __NODETYPE__ = 'rbfSolver'

    @property
    def attributes_to_export(self):
        attrs = super(RbfSolver, self).attributes_to_export
        attrs.extend(['NDimension',
                      'MDimension',
                      'scale',
                      'normalize',
                      'blendShapeMode',
                      'nInput',
                      'distanceMode',
                      'poses',
                      'rbfMode',
                      'mOutput'])
        return attrs
