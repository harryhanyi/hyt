from mhy.maya.nodezoo.node import DependencyNode


class Rbf(DependencyNode):
    __NODETYPE__ = 'rbf'

    @property
    def attributes_to_export(self):
        attrs = super(Rbf, self).attributes_to_export
        attrs.extend(['inputValue',
                      'inputValueCount',
                      'inputQuat',
                      'inputRestQuat',
                      'inputQuatCount',
                      'inputValueCount',
                      'radius',
                      'rbf',
                      'regularization',
                      'outputValueCount',
                      'outputQuatCount',
                      'sampleMode',
                      'sample'])
        return attrs
