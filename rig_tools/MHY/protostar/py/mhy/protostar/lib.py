"""
A library class used to access registered actions and action graphs.
"""

import os
import sys
import inspect
import traceback
import json

import mhy.python.core.logger as logger
import mhy.python.core.tryimport as tryimp
import mhy.python.core.compatible as compat

import mhy.protostar.core.action as act
import mhy.protostar.core.graph as ag
import mhy.protostar.core.exception as exp
import mhy.protostar.constants as const
import mhy.protostar.utils as util


__all__ = ['ActionLibrary']

LIB_ENV_VAR = 'PROTOSTAR_LIB_PATH'
ICON_ENV_VAR = 'PROTOSTAR_ICON_PATH'
TEAM_CONFIG_FILE = 'team_config.json'


def _get_files(path, ext, out_list):
    """Returns all files in a path with a given ext."""
    if not isinstance(ext, (tuple, list)):
        ext = [ext]
    for each in os.listdir(path):
        p = os.path.join(path, each).replace('\\', '/')
        if os.path.isdir(p):
            _get_files(p, ext, out_list)
        elif os.path.splitext(each)[-1][1:] in ext:
            out_list.append(p)


def _action_filer(cls, app, tag, name_match_str):
    if (not app or cls.app == app) and \
       (not tag or cls.has_tag(tag)) and \
       (not name_match_str or util.match_name(cls.__name__, name_match_str)):
        return True
    return False


def _graph_filer(graph_name, name_match_str):
    if not name_match_str or util.match_name(graph_name, name_match_str):
        return True
    return False


class ActionLibrary(object):
    """Action library class.

    This is the main entry point for the user to access registered
    actions and graphs.
    """

    _ACTION_DICT = {}
    _GRAPH_DICT = {}
    _MODULE_SET = set()
    _TAG_LIST = []
    _ICON_DICT = {}

    @classmethod
    def refresh(cls, verbose=False):
        """Refreshes the action library by going through each userlib path
        registered in environment variable ``PROTOSTAR_LIB_PATH``,
        then reload and cache action classes and action graph paths

        Returns: None
        """
        # clears all action modules to ensure a fresh reload.
        for each in cls._MODULE_SET:
            if each in sys.modules:
                del sys.modules[each]

        cls._MODULE_SET = set()
        cls._TAG_LIST = []
        cls._ACTION_DICT = {}
        cls._GRAPH_DICT = {}
        cls._ICON_DICT = {}

        processed = set()
        val = os.getenv(ICON_ENV_VAR)
        if val:
            for path in set(val.split(os.pathsep)):
                path = path.replace('\\', '/')
                if path not in processed:
                    cls.process_icon_path(path)
                    processed.add(path)

        processed = set()
        val = os.getenv(LIB_ENV_VAR)
        if val:
            for path in set(val.split(os.pathsep)):
                path = path.replace('\\', '/')
                if path not in processed:
                    cls.process_lib_path(path, verbose=verbose)
                    processed.add(path)

    @classmethod
    def process_lib_path(cls, lib_path, verbose=False):
        """Processes content in a given library path and load all
        contained actions and action graphs into the Action Library.

        Args:
            lib_path (string): A library path to register.
            verbose (bool): If True, print details of each action/graph loaded.
                Otherwise only log summary at the end.

        Returns:
            None
        """
        if not os.path.isdir(lib_path):
            logger.warn(
                '[Protostar] User lib path not found: {}'.format(lib_path))
            return

        # try get team config variables
        team_name = const.DEFAULT_TEAM
        config = os.path.join(lib_path, TEAM_CONFIG_FILE)
        if os.path.isfile(config):
            with open(config, 'r') as f:
                data = json.load(f)
                team_name = data.get('team_name', const.DEFAULT_TEAM)

        cls._ACTION_DICT[team_name] = {}
        cls._GRAPH_DICT[team_name] = {}

        # cache icons
        root = os.path.join(lib_path, 'icons')
        cls.process_icon_path(root)

        # cache action classes
        root = os.path.join(lib_path, 'actions')
        action_count = 0
        graph_count = 0
        if os.path.isdir(root):
            paths = []
            _get_files(root, 'py', paths)
            for module_path in paths:
                if module_path.endswith('__init__.py'):
                    continue

                try:
                    with tryimp.tryimport():
                        module = compat.import_module_from_path(module_path)
                except BaseException:
                    logger.warn(
                        'Failed loading action module: {}'.format(module_path),
                        format_='[Protostar] [WARN]: %(message)s')
                    traceback.print_exc()
                    continue

                # cache action classes
                cls._MODULE_SET.add(module.__name__)
                for cname, action_cls in inspect.getmembers(
                        module, inspect.isclass):
                    if not inspect.isabstract(action_cls) and \
                       issubclass(action_cls, act.Action) and \
                       action_cls.__module__ == module.__name__:
                        action_cls._SOURCE = '{}:{}'.format(team_name, cname)
                        action_cls._UI_ICON_PATH = cls.get_icon_path(
                            action_cls, action_cls.__name__)
                        cls._ACTION_DICT[team_name][cname] = action_cls
                        cls._TAG_LIST += action_cls.tags

                        if verbose:
                            logger.info(
                                'Action loaded: {}:{} ({})'.format(
                                    team_name, cname, module_path),
                                format_='[Protostar]: %(message)s')
                        action_count += 1

        # cache action graphs
        root = os.path.join(lib_path, 'graphs')
        if os.path.isdir(root):
            paths = []
            _get_files(root, 'agraph', paths)
            for graph_path in paths:
                graph_name = os.path.splitext(
                    os.path.split(graph_path)[-1])[0]
                cls._GRAPH_DICT[team_name][graph_name] = graph_path

                if verbose:
                    logger.info(
                        'Graph loaded: {}:{} ({})'.format(
                            team_name, graph_name, graph_path),
                        format_='[Protostar]: %(message)s')
                graph_count += 1

        cls._TAG_LIST = set(cls._TAG_LIST)
        for each in (const.TAG_ACTION, const.TAG_GRAPH):
            cls._TAG_LIST.add(each)
        cls._TAG_LIST = sorted(list(cls._TAG_LIST))

        logger.info(
            'Loaded {} actions and {} action graphs from {}.'.format(
                action_count, graph_count, lib_path))

    @classmethod
    def process_icon_path(cls, icon_path):
        """Processes content in a given icon path and caches all
        contained icons into the Action Library.

        Args:
            icon_path (string): A icon path to register.

        Returns:
            None
        """
        if not os.path.isdir(icon_path):
            return
        paths = []
        _get_files(icon_path, const.ICON_EXT, paths)
        for path in paths:
            file_name = os.path.splitext(os.path.split(path)[-1])[0]
            cls._ICON_DICT[file_name] = path

    @classmethod
    def get_icon_path(cls, obj, obj_name):
        ui_icon = obj.ui_icon
        if ui_icon:
            icons = [ui_icon, obj_name]
        else:
            icons = [obj_name]
        for icon in icons:
            icon_path = cls._ICON_DICT.get(icon)
            if icon_path:
                return icon_path

    @classmethod
    def _resolve_args(cls, obj_name=None, team=None):
        """Resovle commom arguments."""
        if obj_name:
            if obj_name.find(const.SEP) != -1:
                team, obj_name = obj_name.split(const.SEP, 1)

        teams = set(cls._ACTION_DICT.keys()) | set(cls._GRAPH_DICT.keys())
        if team:
            teams = set([team]) & teams

        # default team always takes first priority
        if const.DEFAULT_TEAM in teams:
            teams.remove(const.DEFAULT_TEAM)
            teams = [const.DEFAULT_TEAM] + list(teams)
        else:
            teams = list(teams)

        return obj_name, teams

    @classmethod
    def get_tags(cls):
        """Returns a list of tags used in the library."""
        return cls._TAG_LIST

    @classmethod
    def iter_actions(
            cls, team=None, app=None, tag=None, name_match_str=None):
        """Iterates through all actions registered in the library.

        Args:
            team (None or string):
                If specified, only iterate objects under this team.
            app (None or string):
                If specified, only iterate objects for this app/DCC.
            tags (None or str or list):
                If specified, only iterate objects associated with the tag(s).
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).

        Yields:
            Action: action source names found.
        """
        _, teams = cls._resolve_args(team=team)
        for team in teams:
            for name in sorted(cls._ACTION_DICT[team].keys()):
                action_cls = cls._ACTION_DICT[team][name]
                if _action_filer(action_cls, app, tag, name_match_str):
                    yield team + const.SEP + name

    @classmethod
    def list_actions(
            cls, team=None, app=None, tag=None, name_match_str=None):
        """Lists actions registered in the library.

        Args:
            team (None or string):
                If specified, only iterate objects under this team.
            app (None or string):
                If specified, only iterate objects for this app/DCC.
            tags (None or str or list):
                If specified, only iterate objects associated with the tag(s).
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).

        Returns:
            list: A list of action source names.
        """
        return [x for x in cls.iter_actions(team, app, tag, name_match_str)]

    @classmethod
    def iter_graphs(cls, team=None, name_match_str=None):
        """Lists action graphs registered in the library.

        Args:
            team (None or string):
                If specified, only iterate objects under this team.
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).

        Yields:
            ActionGraph: graph source names found.
        """
        _, teams = cls._resolve_args(team=team)
        for team in teams:
            for name in sorted(cls._GRAPH_DICT[team].keys()):
                if _graph_filer(name, name_match_str):
                    yield team + const.SEP + name

    @classmethod
    def list_graphs(cls, team=None, name_match_str=None):
        """Lists action graphs registered in the library.

        Args:
            team (None or string):
                If specified, only iterate objects under this team.
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).

        Returns:
            list: A list of graph source names.
        """
        return [x for x in cls.iter_graphs(team, name_match_str)]

    @classmethod
    def has_action(cls, source, team=None, app=None):
        """Checks if an action exists.

        Args:
            source (string): Source name of an action to check.
            team (None or string):
                If specified, only list action graphs under this team.
                If None, list action graphsunder all teams.
                Ignored if source contains a team prefix (e.g. "team:graph").
            app (None or string):
                If specified, only search actions compatible with this app/DCC.
                If None, check all apps.

        Returns:
            bool: True if the action exists, otherwise False.
        """
        action_name, teams = cls._resolve_args(source, team)
        for team in teams:
            team_lib = cls._ACTION_DICT[team]
            if not app and action_name in team_lib:
                return True
            for name, action_cls in team_lib.items():
                if action_name == name and \
                   (not action_cls.app or action_cls.app == app):
                    return True
        return False

    @classmethod
    def has_graph(cls, source, team=None):
        """Checks if an action graph exists.

        Args:
            source (string): Source name of a graph to check.
            team (None or string):
                If specified, only list action graphs under this team.
                If None, list action graphsunder all teams.
                Ignored if source contains a team prefix (e.g. "team:graph").

        Returns:
            bool: True if the graph exists, otherwise False.
        """
        graph_name, teams = cls._resolve_args(source, team)
        for team in teams:
            team_lib = cls._GRAPH_DICT[team]
            if graph_name in team_lib and \
               os.path.isfile(team_lib[graph_name]):
                return True
        return False

    @classmethod
    def get_action(
            cls, source, team=None, app=None, tag=None, name_match_str=None):
        """Returns an action class registered in the library.

        Args:
            source (string): Source name of an action in the library.
                if a team prefix exists (e.g. "team:object"), return this exact
                action class. Otherwise, search under all teams and return the
                first one found.
            team (None or string): If specified, only search under this team.
                If None, search under all teams.
                Ignored if name contains a team prefix (e.g. team:object).
            app (None or string):
                If specified, only iterate objects compatible with this app/DCC.
            tags (None or str or list):
                If specified, only iterate objects associated with the tag(s).
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).

        Raises:
            ActionError: If requested action doesn't exist in the library.

        Returns:
            Action: The action class found.
        """
        action_name, teams = cls._resolve_args(source, team)
        for team in teams:
            action_cls = cls._ACTION_DICT[team].get(action_name)
            if action_cls:
                if _action_filer(action_cls, app, tag, name_match_str):
                    return action_cls
        raise exp.ActionError('Action not found: {}'.format(action_name))

    @classmethod
    def get_graph(cls, source, team=None, name_match_str=None):
        """Returns an action graph path registered in the library.

        Args:
            source (string): Source name of an action graph in the library.
                if a team prefix exists (e.g. "team:graph"), return this exact
                graph path. Otherwise, search under all teams and return the
                first one found.
            team (None or string):
                If specified, only search under this team.
                If None, search all teams.
                Ignored if name contains a team prefix (e.g. team:object).
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).

        Returns:
            (str, str): (team name, graph path)

        Raises:
            ActionError: If requested graph doesn't exist in the library.
        """
        graph_name, teams = cls._resolve_args(source, team)
        for team in teams:
            graph_path = cls._GRAPH_DICT[team].get(graph_name)
            if graph_path:
                if _graph_filer(graph_name, name_match_str):
                    return team, graph_path
        raise exp.ActionError('Action graph not found: {}'.format(graph_name))

    @classmethod
    def create_action(
            cls, source, team=None, app=None, tag=None, name_match_str=None,
            *args, **kwargs):
        """Instantiates an action registered in the library.

        Args:
            source (string): Source name of an action in the library.
                if a team prefix exists (e.g. "team:object"), create an instance
                of this exact action. Otherwise, search under all teams and
                create an instance of the first one found.
            team (None or string): If specified, only search under this team.
                If None, search under all teams.
                Ignored if name contains a team prefix (e.g. team:object).
            app (None or string):
                If specified, only iterate objects compatible with this app/DCC.
            tags (None or str or list):
                If specified, only iterate objects associated with the tag(s).
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).
            args: Action creation arguments.
            kwargs: Action creation keyword arguments.

        Returns:
            Action or None: The action object. None if not found.
        """
        action_cls = cls.get_action(source, team, app, tag, name_match_str)
        return action_cls(*args, **kwargs)

    @classmethod
    def create_graph(
            cls, source=None, team=None, name_match_str=None,
            *args, **kwargs):
        """Creates an action graph available in the library.

        Args:
            source (string or None): Source name of a graph in the library.
                if a team prefix exists (e.g. "team:graph"), create an instance
                of this exact graph. Otherwise, search this graph under all
                teams and create an instance of the first one found.
                If None, create an empty graph.
            team (None or string): If specified, only search under this team.
                If None, search all teams.
                Ignored if name contains a team prefix (e.g. team:object).
            name_match_str (None or str):
                If specified, only iterate objects match the search string
                (wild card ok).
            args: Action graph creation arguments.
            kwargs: Action graph creation keyword arguments.

        Returns:
            ActionGraph: The action graph object.
        """
        graph = ag.ActionGraph(*args, **kwargs)
        if source:
            team, path = cls.get_graph(source, team, name_match_str)
            source = source.split(':')[-1]
            graph._set_source('{}:{}'.format(team, source))
            graph._set_source_path(path)
            graph.revert_reference()
        graph._icon_path = cls.get_icon_path(graph, source)
        return graph
