"""
Name API used to interact with MHY naming convention.
See class NodeName for details.
"""

import re

import mhy.python.core.logger as logger
import mhy.python.core.compatible as comp


__all__ = ['NodeName']


MAIN_DESC = 'main'

SEP_HIER = '|'
SEP_NAMESPACE = ':'
SEP_NAME = '_'


def _sanitize_token(token):
    """Sanitizes a generic name token by removing all
    non-alphanumeric characters (everything except letters, numbers, and {}).

    Returns:
        str: The sanitized token.

    Raises:
        ValueError: If the sanitized token is empty.
    """
    ctoken = re.sub(r'[^a-zA-Z0-9\{\}]', '', str(token))
    if not ctoken:
        raise ValueError(
            'Sanitized token is empty: {} -> {}'.format(token, ctoken))
    return ctoken


def _sanitize_desc_token(token):
    """Sanitizes a descriptor token.

    If the descriptor is MAIN_DESC, treat it as None.

    Returns:
        str: The sanitized descriptor token.
        None: if the descriptor is MAIN_DESC or empty.
    """
    if token:
        token = _sanitize_token(token)
        if not token or token.lower() == MAIN_DESC:
            return None
        return token


def _sanitize_num_token(token):
    """Sanitizes an number/index token.

    Ensures the input token is a valid integer or integer string.

    Returns:
        int: The sanitized index token.
        None: If token is empty.

    Raises:
        ValueError: If the index token is not an int or int string.
    """
    if token is not None:
        if isinstance(token, int):
            return token
        try:
            return int(_sanitize_token(token))
        except BaseException:
            raise ValueError('Invalid index token: {}'.format(token))


def _sanitize_side_token(token):
    """Sanitizes a side token.

    Ensures the token is a valid side in VALID_SIDES.

    Returns:
        str: The sanitized side token.
        None: If token is empty.

    Raises:
        ValueError: If the side token is not in VALID_SIDES.
    """
    if token:
        token = _sanitize_token(token)
    if token:
        for t in NodeName.VALID_SIDES:
            if token.lower() == t.lower():
                return t
        raise ValueError('Invalid side token: {}'.format(token))


def _process_tokens(*args, **kwargs):
    """Returns 5 name tokens from the following args and kwargs.

    Args:
        name (str or None): A name to extract base tokens from.
            If None, use default tokens.
    Kwargs:
        part (str or None): If not None, override the base part token.
        desc (str or None): If not None, override the base desc token.
        num (str or int None): If not None, override the base num token.
        side (str or None): If not None, override the base side token.
        ext (str or None): If not None, override the base ext token.

    Raises:
        ValueError: If the specified base name has invalid token number.
    """
    # validate args and kwargs
    if args and len(args) > 1:
        raise ValueError('More than one argument provided.')
    keys = set(kwargs.keys()) - set(('part', 'desc', 'num', 'side', 'ext'))
    if keys:
        raise ValueError('Invalid kwargs: {}'.format(list(keys)))

    # private token vars
    part = 'part'
    desc = None
    num = None
    side = None
    ext = 'EXT'

    # get tokens from the base name, if specified
    if args:
        cname = NodeName.clean_name(args[0])
        tokens = list(cname.split(SEP_NAME))
        count = len(tokens)

        # fill missing tokens
        if count == 2:
            part, ext = tokens
        elif count == 3:
            if tokens[1].isdigit():
                part, num, ext = tokens
            elif tokens[1].upper() in NodeName.VALID_SIDES:
                part, side, ext = tokens
            else:
                part, desc, ext = tokens
        elif count == 4:
            if tokens[1].isdigit():
                part, num, side, ext = tokens
            elif tokens[2].upper() in NodeName.VALID_SIDES:
                part, desc, side, ext = tokens
            else:
                part, desc, num, ext = tokens
        elif count == 5:
            part, desc, num, side, ext = tokens
        else:
            raise ValueError(
                ('Invalid name {}. '
                    'Number of tokens must be >=2 and <=5.').format(args[0]))

    # override tokens, if specified
    part = kwargs.get('part', part)
    desc = kwargs.get('desc', desc)
    num = kwargs.get('num', num)
    side = kwargs.get('side', side)
    ext = kwargs.get('ext', ext)

    # sanitize tokens
    part = _sanitize_token(part)
    desc = _sanitize_desc_token(desc)
    num = _sanitize_num_token(num)
    side = _sanitize_side_token(side)
    ext = _sanitize_token(ext)

    return part, desc, num, side, ext


def _format_name(part, desc, num, side, ext):
    """Returns a final name string by formalizing 5 tokens."""
    name = part + '_'
    if desc:
        name += desc + '_'
    if num is not None:
        name += '{:02d}_'.format(num)
    if side:
        name += side + '_'
    name += ext
    return name


class NodeName(str):
    """
    Node name class for enforcing MHY naming convention:

        **Part_Dsecriptor_Number_Side_Extension**

    The NodeName class can be used as a substitute of string types.
    This is because all string methods are wrapped within this class
    (see methods marked by **Wrapped String Method**). Each of these
    methods returns NodeName object if the result is a string and it
    still follows MHY naming convention, otherwise return the original
    result.

    Name Tokens:

        + part:
            The rig part/component this node belongs to.
        + descriptior [Optional]:
            An additional description for this node.
            Ignored if it matches the default desc "main".
        + number [Optional]:
            An number/index token.
        + side [Optional]:
            The side this node blongs to.
        + extension:
            An token indicating the node type.

    Name Examples:

        + arm_upper_L_JNT
        + arm_lower_L_JNT
        + arm_wrist_L_JNT

        + spine_00_M_FKCTRL
        + spine_01_M_FKCTRL
        + spine_02_M_FKCTRL
    """

    SIDE_L = 'L'
    SIDE_R = 'R'
    SIDE_M = 'M'
    VALID_SIDES = ('L', 'R', 'M')

    def __new__(cls, *args, **kwargs):
        """Class constructor.

        Extracts tokens from given args and kwargs, formats the final
        name, then pass it into the str constructor.

        See _process_tokens() of valid args and kwargs.
        """
        part, desc, num, side, ext = _process_tokens(*args, **kwargs)
        return str.__new__(cls, _format_name(part, desc, num, side, ext))

    def __init__(self, *args, **kwargs):
        """Instance initializer.

        Extracts tokens from given args and kwargs, formats the final
        name, then pass it into the str initializer.

        See _process_tokens() of valid args and kwargs.
        """
        tokens = _process_tokens(*args, **kwargs)
        self.__part, self.__desc, self.__num, self.__side, self.__ext = tokens
        str.__init__(self.__repr__())

    @classmethod
    def short_name(cls, name):
        """Returns the short name of a given name.
        Short name does NOT have hierarchy separators.
        """
        return re.search('[^{}]*$'.format(SEP_HIER), str(name)).group()

    @classmethod
    def clean_name(cls, name):
        """Returns the clean name of a given name.
        Clean name does NOT have hierarchy separators or namespace separators.
        """
        return cls.short_name(name).split(SEP_NAMESPACE)[-1]

    @classmethod
    def namespace(cls, name):
        """Returns the namespace of a given name, or '' if not found."""
        name = NodeName.short_name(name)
        if ':' in name:
            return name.split(':', 1)[0]
        return ''

    @classmethod
    def is_valid(cls, name):
        """Checks if a name follows the naming convention defined in
        this class.

        Returns:
            bool
        """
        try:
            _process_tokens(cls.clean_name(name))
            return True
        except BaseException:
            return False

    @classmethod
    def flip_node_name(cls, node):
        """Flips a node name between left and right side.
        Returns the input node name directly if it has no side token.

        This functions works on all generic naming convensions,
        not just the MHY convention.

        Args:
            node (str or Node): A node or a node name to flip.

        Returns:
            str: The flipped node name.
        """
        name = NodeName.clean_name(node)
        fname = name
        flipped = False
        for s, d in (
                ('l_', 'r_'),
                ('r_', 'l_'),
                ('L_', 'R_'),
                ('R_', 'L_')):
            if flipped:
                break
            if name.startswith(s):
                fname = d + name[2:]
                flipped = True

        for s, d in (
                ('_l', '_r'),
                ('_r', '_l'),
                ('_L', '_R'),
                ('_R', '_L')):
            if flipped:
                break
            if name.endswith(s):
                fname = name[:-2] + d
                flipped = True

        for s, d in (
                ('_l_', '_r_'),
                ('_r_', '_l_'),
                ('_L_', '_R_'),
                ('_R_', '_L_'),
                ('left', 'right'),
                ('right', 'left'),
                ('Left', 'Right'),
                ('Right', 'Left'),
                ('LEFT', 'RIGHT'),
                ('RIGHT', 'LEFT')):
            if flipped:
                break
            if s in name:
                fname = name.replace(s, d)
                flipped = True

        return fname

    # --- basic properties

    @property
    def part(self):
        """The part token."""
        return self.__part

    def replace_part(self, token):
        """Replace the part token and return a new NodeName object."""
        return NodeName(self, part=token)

    @property
    def desc(self):
        """The desc token, or None if not specified."""
        return self.__desc

    def replace_desc(self, token):
        """Replace the desc token and return a new NodeName object."""
        return NodeName(self, desc=token)

    @property
    def num(self):
        """The number/index token as an integer,
        or None if not specified.
        """
        return self.__num

    def replace_num(self, token):
        """Replace the num token and return a new NodeName object."""
        return NodeName(self, num=token)

    @property
    def side(self):
        """The side token, or None if not specified."""
        return self.__side

    def replace_side(self, token):
        """Replace the side token and return a new NodeName object."""
        return NodeName(self, side=token)

    @property
    def is_left(self):
        """Checks if this name has a side token of "L"."""
        return self.side == self.SIDE_L

    @property
    def is_right(self):
        """Checks if this name has a side token of "R"."""
        return self.side == self.SIDE_R

    @property
    def is_middle(self):
        """Checks if this name has a side token of "M"."""
        return self.side == self.SIDE_M

    @property
    def ext(self):
        """The extension token."""
        return self.__ext

    def replace_ext(self, token):
        """Replace the ext token and return a new NodeName object."""
        return NodeName(self, ext=token)

    # --- utility methods

    def flip(self):
        """
        Returns a copy of this object with the side token flipped.

        Returns:
            NodeName: the flipped name object.
        """
        side = self.side
        if side:
            if side == self.SIDE_L:
                return NodeName(self, side=self.SIDE_R)
            elif side == self.SIDE_R:
                return NodeName(self, side=self.SIDE_L)
        return NodeName(self)


STR_METHOD_BLACKLIST = set((
    '__class__',
    '__init_subclass__',
    '__doc__',
    '__delattr__',
    '__getattribute__',
    '__getnewargs__',
    '__getslice__',
    '__hash__',
    '__init__',
    '__new__',
    '__reduce__',
    '__reduce_ex__',
    '__repr__',
    '__setattr__',
    '__str__',
    '__subclasshook__',
))


def _str_method_wrapper(self, *args, **kwargs):
    """A generic wrapper that executes a regular string method
    and tries to cast it back into NodeName.

    Returns:
        NodeName or var: Returns a NodeName object If the result is
        a string and still follows MHY naming convention, otherwise
        directly return the original result.
    """
    string = str(self)
    method_name = kwargs.pop('method_name')
    method = getattr(string, method_name)
    result = method(*args, **kwargs)
    # print(self, method_name, args, kwargs, result)

    if isinstance(result, str):
        try:
            return NodeName(result)
        except BaseException:
            logger.warn(
                ('New string "{}" does not fit MHY naming '
                 'convention after {} operaton.').format(result, str(method)))
    return result


# insert string method wrappers into NodeName dynamically
# this allows us to use NodeName as a substitute of str type.
for method in dir(str):
    if method in STR_METHOD_BLACKLIST or \
       (len(method) > 1 and method[0] == '_' and method[1] != '_'):
        continue
    wrapped_method = comp.partialmethod(_str_method_wrapper, method_name=method)
    wrapped_method.__doc__ = """
**Wrapped String Method**

{}""".format(getattr(str, method).__doc__)
    setattr(NodeName, method, wrapped_method)
