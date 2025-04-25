"""
A parser class for extracting and modifying data in a
Maya ASCII file without opening it.
"""

import os
import re

import mhy.python.core.logger as logger

TEXTURE_EXTS = set(('tga', 'jpg', 'png'))
MAYA_EXTS = set(('ma', 'mb'))


class MAParser(object):
    """
    A parser for extracting/modifying data in a Maya ASCII file.
    """

    def __init__(self, file_path, file_contents=None):
        self.file_contents = []
        if file_contents:
            self.file_contents = file_contents.split('\n')
        elif not file_path.endswith('.ma'):
            raise ValueError('This is not a Maya ASCII file: ' + file_path)
        self.__path = file_path

    def __get_copy_path(self):
        head, ext = os.path.splitext(self.__path)
        return head + '_copy' + ext

    def __get_lines(self):
        if self.file_contents:
            return self.file_contents

        if not os.path.isfile(self.__path):
            raise ValueError('File not found: ' + self.__path)

        with open(self.__path) as f:
            lines = f.readlines()
            self.file_contents = lines

        return lines

    def get_units(self):
        """Returns all the units used in this file.

        Returns:
            dict: Keys are "angle", "linear", "time".
        """
        units = {
            'angle': None,
            'linear': None,
            'time': None}

        lines = self.__get_lines()
        for line in lines:
            if line.startswith('currentUnit'):
                tokens = line[:-2].split()
                for i, t in enumerate(tokens):
                    if t in ('-l', '-linear'):
                        units['linear'] = tokens[i + 1]
                    elif t in ('-a', '-angle'):
                        units['angle'] = tokens[i + 1]
                    elif t in ('-t', '-time'):
                        units['time'] = tokens[i + 1]
            if line.startswith('createNode'):
                break

        return units

    def get_nodes(self, pattern, type_='(.*)'):
        """Returns a list of node names that matches a given regex pattern.

        Args:
            pattern (string): A regex pattern used to search for nodes.
            type_ (string): Specify a type of node to search for.

        Returns:
            list: A list of node names found.
        """
        lines = self.__get_lines()
        nodes = []
        matcher = 'createNode {} (-n|-name) "([a-zA-Z0-9_]*{}[a-zA-Z0-9_]*)"'
        matcher = matcher.format(type_, pattern)
        for line in lines:
            test = re.match(matcher, line)
            if test:
                nodes.append(test.groups()[-1])
        return nodes

    def replace_node_names(self, text_dict, as_copy=True):
        """Replaces node names in a MA file based on a dictionary.

        Args:
            text_dict (dict): A dict containing {old_text: new_text} pairs.
            as_copy (bool): If true, save the processed file as a separate copy.

        Returns:
            None
        """
        if not os.path.isfile(self.__path):
            raise ValueError('File not found: ' + self.__path)

        new_lines = []
        nodes = {}
        changed = False

        with open(self.__path, 'r') as f:
            for line in f.readlines():

                if line.startswith('createNode'):
                    name = None
                    new_name = None
                    tokens = line.split()
                    for i, t in enumerate(tokens):
                        if t == '-n' or t == '-name':
                            name = tokens[i + 1].split('"')[1]
                            break
                    if name:
                        new_name = name
                        for old, new in text_dict.iteritems():
                            new_name = new_name.replace(old, new)
                        if name != new_name:
                            nodes[name] = new_name
                            changed = True

                if len(nodes) > 0:
                    new_line = line
                    for old, new in nodes.iteritems():
                        new_line = new_line.replace(old, new)
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)

        if changed:
            path = self.__get_copy_path() if as_copy else self.__path
            with open(path, 'w+') as f:
                f.writelines(new_lines)
            logger.info('Saved file: ' + path)
        else:
            logger.info('No changes were made: ' + self.__path)

    def get_textures(self):
        """
        Returns a list of texture file paths referenced.

        Returns:
            list: A list of texture file paths.
        """
        lines = self.__get_lines()
        length = len(lines)

        textures = set()
        i = 0
        while i != length - 1:
            line = lines[i]

            # No more createNode commands after
            if line.startswith('connectAttr') or line.startswith('setAttr'):
                break

            # Only look for createNode commands
            if not line.startswith('createNode'):
                i += 1
                continue
            # Only look for file nodes
            elif line.split()[1] != 'file':
                i += 1
                continue

            i += 1
            line = lines[i]
            maxIter = 100
            it = 0
            while it < maxIter and re.match(r'\s', line):
                tokens = line.split('"')
                found = False
                if len(tokens) > 2:
                    path = tokens[-2]
                    ext = path.split('.')[-1]
                    if ext.lower() in TEXTURE_EXTS:
                        textures.add(path)
                        found = True
                if found:
                    break
                i += 1
                line = lines[i]
                it += 1

            i += 1

        return sorted(list(textures))

    def get_references(self):
        """Returns a list of reference path.

        Returns:
            list: A list of reference paths
        """
        lines = self.__get_lines()
        length = len(lines)

        references = set()
        i = 0
        while i != length - 1:
            line = lines[i]

            # No more file commands after requires
            if line.startswith('requires') or line.startswith('createNode'):
                break

            # Only look for file commands
            if not line.startswith('file'):
                i += 1
                continue

            tokens = line.split('"')
            if len(tokens) > 2:
                path = tokens[-2]
                ext = path.split('.')[-1]
                if ext.lower() in MAYA_EXTS:
                    references.add(path)

            i += 1

        return sorted(list(references))

    def get_playback_options(self):
        """Returns a dict containing playback options.

        Returns:
            dict: keys are "minTime", "maxTime",
                "animationStartTime", "animationEndTime"
        """
        lines = self.__get_lines()

        data = {
            'minTime': 0,
            'maxTime': 0,
            'animationStartTime': 0,
            'animationEndTime': 0
        }

        for i, line in enumerate(lines):
            if re.search(r'.*"sceneConfigurationScriptNode".*', line):
                line = lines[i + 2]
                tokens = line.split()

                for j, token in enumerate(tokens):
                    if token == '-min':
                        data['minTime'] = float(tokens[j + 1])
                    elif token == '-max':
                        data['maxTime'] = float(tokens[j + 1])
                    elif token == '-ast':
                        data['animationStartTime'] = float(tokens[j + 1])
                    elif token == '-aet':
                        data['animationEndTime'] = float(tokens[j + 1])
                break

        return data
