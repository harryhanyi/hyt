import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.attribute.attribute_ import Attribute


class ArrayAttribute(Attribute):
    def __getitem__(self, index):
        """
        Get child element by logical index
        Args:
            index(int): Index used to find child element

        Returns:
            Attribute: Found attribute

        """
        element = self.__plug__.elementByLogicalIndex(index)
        return Attribute(element)

    def __iter__(self):
        """
        Generator go through all the existing child element attributes
        Yields:
            Attribute: Element attribute
        """
        for i in self.indices:
            yield self[i]

    @property
    def indices(self):
        """
        Get all the existing indices in a tuple
        Returns:
            tuple:

        """
        self.__plug__.evaluateNumElements()
        int_array = OpenMaya.MIntArray()
        self.__plug__.getExistingArrayAttributeIndices(int_array)
        return tuple(int_array)

    def minimum_available_index(self):
        """
        Get the child element minimum index that not been used
        Returns:
            int: The child element index
        """
        existing_indices = self.indices
        start = 0
        while start in existing_indices:
            start = start + 1
        return start

    def clear(self, force=False):
        """

        Args:
            force(bool): If force clear if the attribute has input connection

        Returns:

        """
        for i in self:
            if not force and i.sourceWithConversion:
                continue
            cmds.removeMultiInstance(i.long_name, b=True)

    def export(self, withConnection=True, isNested=False, ignore=None, filter=None):
        data = {}
        attr_array = []
        indices = self.indices
        for i in indices:
            ele_data = self[i].export(withConnection=withConnection,
                                      isNested=True, ignore=ignore,
                                      filter=filter)

            if ele_data:
                attr_array.append(ele_data)
        if attr_array:
            data['array'] = attr_array
        if data:
            if self.is_element:
                data['index'] = self.index
            elif isNested:
                data['name'] = self.name.split('.')[-1]
            else:
                data['name'] = self.name
        return data

    def load(self, data, makeConnections=True):
        elements = data.get('array')
        self.clear()
        for elementData in elements:
            index = elementData.get('index')
            if index is not None:
                ele = self[index]
                if ele:
                    ele.load(elementData, makeConnections=makeConnections)


