import os
from mhy.qt.core import QtWidgets, QtGui


def _resolve_path(sub_dir):
    path_root = os.environ.get('MHY_ICON_PATH')
    if not path_root or not sub_dir:
        return None

    paths = path_root.split(os.pathsep)
    for root in paths:
        test_path = root + sub_dir
        if os.path.isfile(test_path):
            return test_path
    return None


def get_icon(sub_dir, color=None):
    """

    Args:
        sub_dir:
        color:

    Returns:

    """

    path = _resolve_path(sub_dir)
    if not path:
        return QtGui.QIcon()

    if color:
        pix_map = QtGui.QPixmap(path)
        mask = pix_map.mask()
        if not isinstance(color, QtGui.QColor):
            if isinstance(color, (list, tuple)):
                color = QtGui.QColor(*color)
            else:
                color = QtGui.QColor(color)
        pix_map.fill(color)
        pix_map.setMask(mask)
        return QtGui.QIcon(pix_map)
    else:
        return QtGui.QIcon(path)


def get_pixmap(sub_dir, color=None):
    path = _resolve_path(sub_dir)
    if not path:
        return QtGui.QPixmap()

    pix_map = QtGui.QPixmap(path)
    if color:
        mask = pix_map.mask()
        if not isinstance(color, QtGui.QColor):
            if isinstance(color, (list, tuple)):
                color = QtGui.QColor(*color)
            else:
                color = QtGui.QColor(color)
        pix_map.fill(color)
        pix_map.setMask(mask)
    return pix_map


def _clean_join(*args):
    return os.path.join(*args).replace('\\', ' /').replace(' ', '')


class Icon(object):
    def __init__(self, name, file_ext, directory, root, parent=None, size=None):
        self.__name = name
        self.__file_ext = file_ext.replace('.', '')
        self.__size = size
        self.__directory = directory
        self.__parent = parent
        self.root = root

        self.tags = self.full_path.split(os.sep)

    def __repr__(self):
        return "<0>.{1}: '{2}'> at <{3}>".format(
            self.__module__,
            self.__class__.__name__,
            self.name,
            hex(id(self))
        )

    @property
    def name(self):
        return self.__name

    @property
    def file_ext(self):
        return self.__file_ext

    @property
    def size(self):
        return self.__size

    @property
    def directory(self):
        return self.__directory

    @property
    def parent(self):
        return self.__parent

    @parent.setter
    def parent(self, p):
        self.__parent = p

    @property
    def full_path(self):
        file_name = '{}.{}'.format(self.name, self.file_ext)
        return _clean_join(self.directory, file_name)

    @property
    def relative_path(self):
        return self.full_path.replace(self.root, '')


class IconContainer(object):
    def __init__(self, name, directory):
        self.__path = directory
        self.__name = name
        self.children = list()

    def __repr__(self):
        return "<{}>:<{}>".format(
            self.path,
            self.name
        )

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_children(self, children):
        for child in children:
            self.add_child(child)

    def find_biggest_png_if_any(self):
        if not self.children:
            return
        biggest = None
        for child in self.children:
            if child.file_ext == '.png':
                if biggest is None:
                    biggest = child
                elif not biggest.size or (child.size and child.size > biggest.size):
                    biggest = child
            elif not biggest:
                biggest = child
        return biggest

    @property
    def name(self):
        return self.__name

    @property
    def path(self):
        return self.__path

    @property
    def num_children(self):
        return len(self.children)

    def find_child(self, format, size=None):
        for child in self.children:
            if not child.file_ext == format:
                continue
            if size is None:
                return child
            elif int(size) == child.size:
                return child


cached_icon_lib = []


def populate_icons(directory, root, img_exts):
    global cached_icon_lib
    container_map = {}
    for p in os.listdir(directory):
        full_path = os.path.join(directory, p)
        if os.path.isdir(full_path):
            if img_exts and p in img_exts:
                icons = populate_icons_format_dir(path=full_path, img_exts=img_exts, root=root)
                for icon in icons:
                    if icon.name not in container_map:
                        container = IconContainer(name=icon.name, directory=directory)
                        container_map[icon.name] = container
                    else:
                        container = container_map.get(icon.name)

                    container.add_child(icon)
            else:
                populate_icons(full_path, root, img_exts=img_exts)
                continue
        elif os.path.isfile(full_path):
            icon = get_icon_from_path(full_path, img_exts=img_exts, root=root)
            if icon:
                container = IconContainer(name=icon.name, directory=directory)
                container.add_child(icon)
                container_map[icon.name] = container

    for k, v in container_map.items():
        if v.num_children:
            cached_icon_lib.append(v)


def get_icon_from_path(path, img_exts, root, size=None):
    base_name = os.path.basename(path)
    split_file = os.path.splitext(base_name)
    if split_file[-1].endswith(img_exts):
        icon = Icon(split_file[0], split_file[-1], os.path.dirname(path), root, None, size=size)
        return icon


def populate_icons_format_dir(path, img_exts, root, size=None):
    children = os.listdir(path)
    icons = []
    for sub_path in children:
        child_path = _clean_join(path, sub_path)
        if os.path.isfile(child_path):
            icon = get_icon_from_path(child_path, img_exts=img_exts, root=root, size=size)
            if icon:
                icons.append(icon)
        elif sub_path.isdigit():
            size_val = int(sub_path)
            icons.extend(populate_icons_format_dir(child_path, img_exts=img_exts, root=root, size=size_val))
    return icons


def start_cache():
    print('Caching icon data...')
    supported_img_formats = ('png', 'svg', 'jpg')
    icon_env = os.environ.get('MHY_ICON_PATH')
    paths = icon_env.split(os.pathsep)
    for path in paths:
        if os.path.isdir(path):
            populate_icons(path, root=path, img_exts=supported_img_formats)
    print('Done caching')
    return cached_icon_lib
