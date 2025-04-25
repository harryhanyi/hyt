import maya.OpenMaya as OpenMaya

from mhy.maya.nodezoo.attribute.attribute_ import Attribute


class CompoundAttribute(Attribute):
    def __getattr__(self, attrName):
        return Attribute(self, attrName)

    def __iter__(self):
        for i in range(self.num_children):
            child = self.__plug__.child(i)
            child_attr = Attribute(child)
            yield child_attr

    @property
    def num_children(self):
        return self.__plug__.numChildren()

    def find_child(self, name):
        for i in range(self.num_children):
            child = self.__plug__.child(i)
            attr_obj = child.attribute()
            attr_fn = OpenMaya.MFnAttribute(attr_obj)
            attr_name = attr_fn.name()
            attr_short_name = attr_fn.shortName()

            if name == attr_name or name == attr_short_name:
                return Attribute(child)

    def export(self, withConnection=True, isNested=False, ignore=None, filter=None):
        """
        Export data for compound attribute will create a key called 'children' mapped to list
        of children attribute data
        Args:
            withConnection(bool):
            isNested(bool):
            ignore(list): The attribute name to be ignored
            filter(list): Only export attributes in the filter list

        Returns:
            dict: The exported data

        """
        data = {}
        children = []
        for i in self:
            if filter and any(f in i.name for f in filter):
                continue

            if ignore and not all(iga not in i.name for iga in ignore):
                continue
            child_data = i.export(withConnection=withConnection, isNested=True,
                                  ignore=ignore, filter=None)
            if child_data:
                children.append(child_data)
        if children:
            data['children'] = children
        if data:
            if self.is_element:
                data['index'] = self.index
            elif isNested:
                data['name'] = self.name.split('.')[-1]
            else:
                data['name'] = self.name
        return data

    def load(self, data, makeConnections=True):
        children = data.get('children')
        for childData in children:
            child_name = childData.get('name')
            if child_name:
                child_plug_name = child_name.split('.')[-1]
                child_attr = self.find_child(child_plug_name)
                if child_attr:
                    child_attr.load(childData, makeConnections=makeConnections)
                else:
                    OpenMaya.MGlobal.displayWarning(
                        ('Failed to find child attribute of {}'
                         ' called {}.').format(
                             self.short_name, child_plug_name))
