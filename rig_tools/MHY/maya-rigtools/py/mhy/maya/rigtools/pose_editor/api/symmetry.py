"""
the symmetry class to flag the pose or influence symmetry information.
"""


class Symmetry(object):
    """
    the enum is used to define the symmetry of pose.
    """
    CENTER = 0
    LEFT = 1
    RIGHT = 2

    to_str_table = {CENTER: 'M', LEFT: 'L', RIGHT: 'R'}
    from_str_table = {'M': CENTER, 'L': LEFT, 'R': RIGHT}
    suffix = ['M', 'L', 'R']

    def __init__(self, name, is_limb=False):
        # init symmetry_name
        split_names = name.split('_')
        self.main_name = name
        self.symmetry = Symmetry.CENTER
        if is_limb:
            return
        if len(split_names) > 1:
            symmetry_str = split_names[-1]
            if symmetry_str not in Symmetry.from_str_table:
                return
            self.main_name = name[:-1 - len(symmetry_str)]
            self.symmetry = Symmetry.from_str_table[symmetry_str]

    def get_name(self):
        return '{}_{}'.format(self.main_name, Symmetry.to_str_table[self.symmetry])

    def rename(self, new_name):
        split_names = new_name.split('_')
        self.main_name = new_name
        if len(split_names) > 1:
            symmetry_str = split_names[-1]
            self.symmetry = self.from_str_table.get(symmetry_str, self.CENTER)
            self.main_name = new_name[:-1 - len(symmetry_str)]

    @property
    def name(self):
        return self.get_name()

    @name.setter
    def name(self, new_name):
        self.rename(new_name)

    def get_mirror_name(self):
        """
        Get the mirror name.
        """
        if self.symmetry == Symmetry.RIGHT:
            return '{}_{}'.format(self.main_name, Symmetry.to_str_table[Symmetry.LEFT])
        if self.symmetry == Symmetry.LEFT:
            return '{}_{}'.format(self.main_name, Symmetry.to_str_table[Symmetry.RIGHT])
        return self.name

    def is_symmetry(self):
        """
        Return true if the pose is a symmetry pose.
        """
        return self.symmetry == Symmetry.CENTER
