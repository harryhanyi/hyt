import os
import unittest
import shutil
from collections import OrderedDict

import mhy.protostar.core.parameter_base as pb
import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp
import mhy.protostar.constants as const
from mhy.protostar.constants import DEFAULT_TEAM, ExecStatus
from mhy.protostar.lib import LIB_ENV_VAR, ICON_ENV_VAR
from mhy.protostar.lib import ActionLibrary as alib


# Add the userlib path in this module
path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
path = os.path.join(path, 'py', 'mhy', 'protostar', 'userlib')
if LIB_ENV_VAR not in os.environ:
    os.environ[LIB_ENV_VAR] = path
else:
    os.environ[LIB_ENV_VAR] += os.pathsep + path

# Add the icon path
path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
icon_path_root = os.path.join(path, 'resource', 'icons')
if ICON_ENV_VAR not in os.environ:
    os.environ[ICON_ENV_VAR] = icon_path_root
else:
    os.environ[ICON_ENV_VAR] += os.pathsep + icon_path_root

alib.refresh()

BT_ACTIONS = [
    DEFAULT_TEAM + ':NullAction',
    DEFAULT_TEAM + ':ScriptAction',
    DEFAULT_TEAM + ':SwitchAction']


TEST_VAR = 0


class TestAction(unittest.TestCase):
    """
    Test action features
    """

    def test_lib(self):

        null = alib.get_action('NullAction')

        class NullAction(null):
            _APP = 'test_app_a'

        class TestAction(null):
            _APP = 'test_app_b'
            _TAGS = ['a', 'b']

        alib._GRAPH_DICT['test_team'] = {}
        alib._ACTION_DICT['test_team'] = {
            'NullAction': NullAction,
            'TestAction': TestAction
        }

        self.assertEqual(alib.get_tags(), [const.TAG_ACTION, const.TAG_GRAPH, 'util'])
        self.assertFalse(alib.has_action('_TestABC'))
        self.assertTrue(alib.has_action('NullAction'))
        self.assertTrue(alib.has_action(DEFAULT_TEAM + ':NullAction'))
        self.assertTrue(alib.has_action('test_team:NullAction'))
        self.assertEqual(
            alib.get_action('NullAction'),
            alib.get_action(DEFAULT_TEAM + ':NullAction'))
        self.assertNotEqual(
            alib.get_action('NullAction'),
            alib.get_action('test_team:NullAction'))

        self.assertEqual(
            alib.list_actions(tag='a'), ['test_team:TestAction'])
        self.assertEqual(
            alib.list_actions(tag=['a', 'c']), ['test_team:TestAction'])
        self.assertEqual(
            alib.list_actions(name_match_str='te*ion'), ['test_team:TestAction'])

        self.assertTrue(
            alib.has_action('NullAction', team=DEFAULT_TEAM, app='maya'))
        self.assertTrue(
            alib.has_action('NullAction', team=DEFAULT_TEAM, app='test_team'))
        self.assertTrue(
            alib.get_action('NullAction', team='test_team') == NullAction)
        self.assertFalse(
            alib.has_action('non_exist_team:NullAction'))
        self.assertFalse(
            alib.has_action('NullAction', team='non_exist_team'))
        with self.assertRaises(exp.ActionError):
            alib.create_action('non_exist_team:NullAction')

        self.assertEqual(
            alib.list_actions(),
            BT_ACTIONS + ['test_team:NullAction', 'test_team:TestAction'])
        self.assertEqual(
            alib.list_actions(team='test_team'),
            ['test_team:NullAction', 'test_team:TestAction'])
        self.assertEqual(
            alib.list_actions(team=DEFAULT_TEAM), BT_ACTIONS)
        self.assertEqual(alib.list_actions(team='non_exist_team'), [])
        self.assertEqual(alib.list_graphs(team='non_exist_team'), [])

        graph = alib.create_graph()
        action = alib.create_action('TestAction', graph=graph)
        alib.create_action('NullAction', team=DEFAULT_TEAM, graph=graph)
        self.assertEqual(graph.app, action.app, 'test_app_b')
        alib.create_action(DEFAULT_TEAM + ':NullAction', graph=graph)

        self.assertEqual(alib.get_action('TestAction').tags, ('a', const.TAG_ACTION, 'b'))
        self.assertEqual(action.tags, ('a', const.TAG_ACTION, 'b'))
        self.assertTrue(action.has_tag('a'))
        self.assertFalse(action.has_tag('aa'))
        self.assertEqual(graph.tags, [])
        graph.tags = ['c']
        self.assertEqual(graph.tags, ('action graph', 'c'))

        self.assertEqual(action.ui_color, const.DEFAULT_ACTION_UI_COLOR)
        self.assertEqual(
            alib.get_action('TestAction').ui_color,
            const.DEFAULT_ACTION_UI_COLOR)
        with self.assertRaises(exp.ActionError):
            action.ui_color = (1, 1, 1)

        self.assertEqual(graph.ui_color, const.DEFAULT_GRAPH_UI_COLOR)
        graph.ui_color = (1, 1, 1)
        self.assertEqual(graph.ui_color, (1, 1, 1))

        # adding 2 actions with the different apps should fail
        with self.assertRaises(exp.ActionError):
            alib.create_action('NullAction', team='test_team', graph=graph)

        graph.remove_object(action)
        action = alib.create_action('NullAction', team='test_team', graph=graph)

        self.assertEqual(graph.app, action.app, 'test_app_a')

    def test_action_properties(self):
        graph = alib.create_graph()

        with self.assertRaises(exp.ActionError):
            alib.create_action('NoneExistAction', graph=graph)

        self.assertEqual(graph.doc, 'No documentation.')
        graph.doc = 'abc'
        self.assertEqual(graph.doc, 'abc')

        actionA = alib.create_action('NullAction', graph=graph)
        self.assertEqual(actionA.__class__.__name__, 'NullAction')
        self.assertEqual(actionA.param_count, 4)
        self.assertEqual(graph.object_count, 1)
        with self.assertRaises(exp.ActionError):
            actionA.doc = 'abc'
        self.assertEqual(actionA.doc, alib.get_action('NullAction').doc)

        # next available name
        self.assertEqual(actionA.name, 'NullAction')
        actionB = alib.create_action('NullAction', graph=graph)
        self.assertEqual(actionB.name, 'NullAction1')

        # name sanitization
        actionB.name = '@my  &Act$ion!#'
        self.assertEqual(actionB.name, 'my_Action')
        # rename should update graph properly
        self.assertTrue(graph.has_object('my_Action'))
        self.assertEqual(graph.get_object('my_Action'), actionB)

        # long name
        self.assertEqual(graph.long_name, graph.name)
        self.assertEqual(graph.long_name, 'ActionGraph')
        self.assertEqual(actionB.long_name, 'ActionGraph:my_Action')
        graph.name = 'root_graph'
        self.assertEqual(actionB.long_name, 'root_graph:my_Action')

        # nested graph
        sub_graph = alib.create_graph(name='sub_graph', graph=graph)
        sub_graph.add_object(actionB)
        self.assertEqual(actionB.graph, sub_graph)
        self.assertFalse(graph.has_object(actionB))
        self.assertTrue(sub_graph.has_object(actionB))
        self.assertEqual(actionB.root_graph, graph)
        self.assertEqual(actionB.long_name, 'root_graph:sub_graph:my_Action')

        # exchange ownership
        actionB.graph = graph
        self.assertTrue(graph.has_object(actionB))
        self.assertFalse(sub_graph.has_object(actionB))

    def test_action_callback(self):
        graph = alib.create_graph()

        actionA = alib.create_action('NullAction', graph=graph)

        def func(exec_name, status):
            global TEST_VAR
            TEST_VAR = 1

        actionA.status_changed.connect(func)

        self.assertEqual(TEST_VAR, 0)
        actionA.set_status(ExecStatus.kRunning)
        self.assertEqual(TEST_VAR, 1)

    def test_action_parameters(self):
        graph = alib.create_graph()
        action = alib.create_action('NullAction', graph=graph)
        paramA = action.add_dynamic_param('int', name='paramA')
        paramB = action.add_dynamic_param('float', name='paramB')
        paramC = action.add_dynamic_param('str', name='paramC', output=True)

        exe_param = action.execution
        msg_param = action.message
        enb_param = action.enabled
        brk_param = action.break_point
        self.assertIsNone(msg_param.value)
        self.assertTrue(enb_param.value)
        self.assertTrue(action.has_param(msg_param))

        self.assertTrue(action.has_param(paramB))
        self.assertTrue(action.has_param('paramB'))
        self.assertEqual(paramC, action.paramC)

        self.assertEqual(action.get_params(input_=False), [msg_param, paramC])
        self.assertEqual(
            action.get_params(static=False), [paramA, paramB, paramC])
        self.assertEqual(
            action.get_params(output=False),
            [exe_param, enb_param, brk_param, paramA, paramB])

        # self connection
        paramA >> paramB
        paramA.value = 3
        self.assertEqual(
            paramB.script.code, '{{{}.paramA}}'.format(pb.THIS_OBJECT))
        self.assertEqual(paramB.value, 3)
        paramB.script = '{NullAction}'
        self.assertEqual(
            paramB.script.code, '{{{}}}'.format(pb.THIS_OBJECT))

        action.remove_dynamic_param(paramB)
        self.assertFalse(action.has_param(paramB))
        self.assertFalse(action.has_param('paramB'))
        self.assertIsNone(paramB.owner)

    def test_action_connection(self):
        graph = alib.create_graph()
        actionA = alib.create_action('NullAction', graph=graph)
        actionB = alib.create_action('NullAction', graph=graph)
        actionC = alib.create_action('NullAction', graph=graph)
        actionD = alib.create_action('NullAction', graph=graph)

        actionA.enabled >> actionB.enabled
        actionA.enabled >> actionC.enabled
        actionB.connect('enabled', actionD, 'enabled')
        self.assertTrue(actionD.enabled.has_input)
        # non-force connecting to params with existing connection should fail
        with self.assertRaises(exp.PConnectionError):
            actionA.connect('enabled', actionD, 'enabled', force=False)

        with self.assertRaises(exp.PConnectionError):
            actionA >> actionB.execution
        actionA.execution >> actionB.execution

        param = actionB.enabled
        self.assertTrue(param.script_enabled)
        self.assertEqual(
            param.script.code, '{{{}.enabled}}'.format(actionA.name))

        self.assertEqual(
            actionA.get_connected_objects(
                input_=True, output=False, as_set=True),
            set())
        self.assertEqual(
            actionA.get_connected_objects(
                input_=False, output=True, as_set=True),
            set([actionB, actionC]))
        self.assertEqual(
            actionB.get_connected_objects(
                input_=True, output=False, as_set=True),
            set([actionA]))
        self.assertEqual(
            actionB.get_connected_objects(
                input_=False, output=True, as_set=True, param='enabled'),
            set([actionD]))
        self.assertEqual(
            actionC.get_connected_objects(
                input_=True, output=False, as_set=True),
            set([actionA]))
        self.assertEqual(
            actionC.get_connected_objects(
                input_=False, output=True, as_set=True),
            set())
        self.assertEqual(
            actionD.get_connected_objects(
                input_=True, output=False, as_set=True),
            set([actionB]))
        self.assertEqual(
            actionD.get_connected_objects(
                input_=False, output=True, as_set=True),
            set())

        # non-force remove action with output connection should fail
        with self.assertRaises(exp.PConnectionError):
            graph.remove_object(actionA)

        graph.remove_object(actionA, force=True)
        self.assertFalse(graph.has_object(actionA))
        self.assertIsNone(actionA.graph)

    def test_action_switch(self):
        graph = alib.create_graph()

        # create a complex graph:
        '''
        A >> B >> C >> E >> switch >> G
             B >> D >> E
        A >>           F >> switch
        '''
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        actionC = alib.create_action('NullAction', name='actionC', graph=graph)
        actionD = alib.create_action('NullAction', name='actionD', graph=graph)
        actionE = alib.create_action('NullAction', name='actionE', graph=graph)
        actionF = alib.create_action('NullAction', name='actionF', graph=graph)
        actionG = alib.create_action('NullAction', name='actionG', graph=graph)
        switch = alib.create_action('SwitchAction', name='switch', graph=graph)

        actionA.execution >> actionB.execution
        actionA.execution >> actionF.execution
        actionB.execution >> actionC.execution
        actionB.execution >> actionD.execution
        actionE.enabled.script = '{actionC.enabled} and {actionD.enabled}'

        switch.inputs.script = '{actionE}, {actionF}'
        actionG.add_dynamic_param('message', name='msgp')
        switch.output >> actionG.msgp

        graph.execute()

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionC.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionD.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionE.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionF.get_status(), ExecStatus.kNone)
        self.assertEqual(actionG.get_status(), ExecStatus.kSuccess)
        self.assertEqual(switch.get_status(), ExecStatus.kSuccess)

        switch.selector.value = 1
        graph.execute()

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kNone)
        self.assertEqual(actionC.get_status(), ExecStatus.kNone)
        self.assertEqual(actionD.get_status(), ExecStatus.kNone)
        self.assertEqual(actionE.get_status(), ExecStatus.kNone)
        self.assertEqual(actionF.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionG.get_status(), ExecStatus.kSuccess)
        self.assertEqual(switch.get_status(), ExecStatus.kSuccess)

        graph = alib.create_graph()

        switch = alib.create_action('SwitchAction', name='switch', graph=graph)
        switch.inputs.value = [1, 2, 'abc']

        graph.execute()
        self.assertEqual(switch.output.value, 1)

        switch.selector.value = 2
        graph.execute()
        self.assertEqual(switch.output.value, 'abc')

        with self.assertRaises(exp.ActionError):
            switch.selector.value = 3
            graph.execute()

    def test_action_execution(self):
        graph = alib.create_graph()
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionA.execute()
        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)

        # create a complex graph:
        # A + B >> C >> E, B >> D, F >> G
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        actionG = alib.create_action('NullAction', name='actionG', graph=graph)
        actionC = alib.create_action('NullAction', name='actionC', graph=graph)
        paramC = actionC.add_dynamic_param('str', name='paramC')
        actionD = alib.create_action('NullAction', name='actionD', graph=graph)
        actionF = alib.create_action('NullAction', name='actionF', graph=graph)
        actionE = alib.create_action('NullAction', name='actionE', graph=graph)

        paramC.script = 'str({actionA}) + str({actionB})'
        self.assertEqual(paramC.value, 'actionAactionB')
        actionC.execution >> actionE.execution
        actionB.execution >> actionD.execution
        actionF.execution >> actionG.execution

        self.assertEqual(
            actionC.get_connected_objects(
                input_=True, output=False, as_set=True),
            set([actionA, actionB]))

        self.assertEqual(
            actionE.get_connected_objects(
                input_=True, output=False, as_set=True),
            set([actionC]))

        self.assertEqual(
            actionE.get_connected_objects(
                input_=True, output=False, recursive=True, as_set=True),
            set([actionA, actionB, actionC]))

        self.assertEqual(
            actionB.get_connected_objects(
                input_=False, output=True, recursive=False, as_set=True),
            set([actionC, actionD]))

        self.assertEqual(
            actionB.get_connected_objects(
                input_=False, output=True, recursive=True, as_set=True),
            set([actionC, actionE, actionD]))

        # test execution order
        self.assertEqual(
            graph.get_sorted_objects(),
            [actionA, actionB, actionF, actionG, actionC, actionD, actionE])
        graph.execute()
        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionE.get_status(), ExecStatus.kSuccess)
        self.assertEqual(graph.get_status(), ExecStatus.kSuccess)

        # disable an action and its downstream
        actionA.enabled.value = False
        self.assertEqual(
            graph.get_sorted_objects(skip_disabled=True),
            [actionB, actionF, actionG, actionC, actionD, actionE])
            # [actionB, actionF, actionG, actionD])
        graph.execute()
        self.assertEqual(graph.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionA.get_status(), ExecStatus.kNone)
        self.assertEqual(actionC.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionE.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionG.get_status(), ExecStatus.kSuccess)

    def test_action_data(self):
        graph = alib.create_graph()
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        paramA = actionA.add_dynamic_param('int', name='paramA', default=1)
        paramA.value = 3

        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        paramB = actionB.add_dynamic_param('str', name='paramB', default='abc')
        paramA >> paramB

        # action copy
        actionC = actionB.copy(name='actionC')
        paramC = actionC.paramB
        self.assertEqual(actionC.name, 'actionC')
        self.assertEqual(paramC.value, paramB.value)
        self.assertEqual(paramC.default, paramB.default)
        self.assertEqual(paramC.script_enabled, paramB.script_enabled)
        self.assertEqual(paramC.script.code, paramB.script.code)

        actionD = actionA.copy()
        self.assertEqual(actionD.name, 'actionA1')
        paramD = actionD.paramA
        paramD.script = """
    if {actionB.paramB} == '3':
        return 4
    return 5
    """
        self.assertEqual(paramD.value, 4)

        # save graph
        path = os.path.split(os.path.realpath(__file__))[0]
        path = os.path.join(path, 'test.txt')

        with self.assertRaises(exp.ActionError):
            graph.write(path)
        path = path.replace('.txt', '.agraph')
        graph.tags = [1, 2, 3]
        graph.ui_color = [1, 2, 3]
        graph.write(path)
        self.assertTrue(os.path.isfile(path))

        # load graph
        graph_copy = alib.create_graph()
        graph_copy.read(path)
        self.assertEqual(graph_copy.tags, ('1', '2', '3', 'action graph'))
        self.assertEqual(graph_copy.ui_color, (1, 2, 3))
        graph_copy.name = 'graph_copy'

        actionD_copy = graph_copy.get_object('actionA1')
        paramD_copy = actionD_copy.paramA
        self.assertEqual(graph_copy.object_count, graph.object_count)
        self.assertEqual(actionD_copy.name, actionD.name)
        self.assertEqual(actionD_copy.param_count, actionD.param_count)
        self.assertEqual(paramD_copy.default, paramD.default)
        self.assertEqual(paramD_copy.value, paramD.value)
        self.assertEqual(paramD_copy.script_enabled, paramD.script_enabled)
        self.assertEqual(paramD_copy.script.code, paramD.script.code)
        self.assertEqual(paramD_copy.is_output, paramD.is_output)
        self.assertEqual(paramD_copy.is_dynamic, paramD.is_dynamic)

        graph.execute()
        graph_copy.execute()
        self.assertEqual(graph_copy.get_status(), graph.get_status())

        actionB.enabled.value = False
        graph.write(path)
        graph_copy.read(path)
        actionA_copy = graph_copy.get_object('actionA')
        actionB_copy = graph_copy.get_object('actionB')
        actionD_copy = graph_copy.get_object('actionA1')
        self.assertFalse(actionB_copy.enabled.value)

        graph.execute()
        graph_copy.execute()
        self.assertEqual(
            graph_copy.get_status(), graph.get_status(), ExecStatus.kSuccess)
        self.assertEqual(
            actionD_copy.get_status(), actionD.get_status(), ExecStatus.kNone)
        self.assertEqual(
            actionA_copy.get_status(), actionA.get_status(),
            ExecStatus.kSuccess)

        # remove test graph
        if os.path.exists(path):
            os.remove(path)

    def test_graph_reference(self):
        # make a tmp graph and store it in the userlib
        lib_graph = alib.create_graph()
        lib_action = alib.create_action(
            'NullAction', name='action', graph=lib_graph)
        in_param = lib_action.add_dynamic_param(
            'int', name='in_param', default=1)
        out_param = lib_action.add_dynamic_param(
            'int', name='out_param', default=2)
        p_in_param = lib_action.promote(in_param, output=False)
        p_out_param = lib_action.promote(out_param, output=True)
        self.assertFalse(p_in_param.is_output)
        self.assertEqual(p_in_param.owner, lib_graph)
        self.assertTrue(p_out_param.is_output)
        self.assertEqual(p_out_param.owner, lib_graph)

        self.assertEqual(lib_action.get_promoted_param(in_param), p_in_param)
        self.assertEqual(lib_action.get_promoted_param(out_param), p_out_param)
        self.assertIsNone(lib_graph.get_promoted_param(p_in_param))
        self.assertIsNone(lib_graph.get_promoted_param(p_out_param))

        libpath = os.path.split(os.path.split(os.path.realpath(__file__))[0])[0]
        libpath = os.path.join(
            libpath, 'py', 'mhy', 'protostar', 'userlib', 'graphs')
        if not os.path.isdir(libpath):
            os.makedirs(libpath)
        libfile = os.path.join(libpath, 'test_lib_graph.agraph')
        lib_graph.write(libfile)
        # create temp icon
        icon_path = os.path.join(icon_path_root, 'test_lib_graph.png').replace('\\', '/')
        if not os.path.isfile(icon_path):
            with open(icon_path, 'w+'):
                os.utime(icon_path, None)

        # refresh library
        alib.refresh()

        # load this tmp graph from library (by default it's referenced)
        root_graph = alib.create_graph(name='root_graph')
        sub_graph = alib.create_graph(
            DEFAULT_TEAM + ':test_lib_graph',
            name='sub_graph', graph=root_graph)
        self.assertEqual(
            sub_graph.get_object('action').in_param.script.code,
            '{{{}.in_param}}'.format(pb.OWNER_GRAPH))
        self.assertEqual(root_graph.object_count, 1)
        self.assertTrue(sub_graph.referenced)
        self.assertEqual(sub_graph.name, 'sub_graph')
        self.assertEqual(sub_graph.type_name, DEFAULT_TEAM + ':test_lib_graph')
        self.assertTrue(sub_graph.is_equivalent(
            lib_graph, check_referenced=False, check_child=False))
        self.assertTrue(sub_graph.has_object('action'))
        self.assertEqual(
            sub_graph.get_object('action').in_param.script.code,
            '{{{}.in_param}}'.format(pb.OWNER_GRAPH))
        self.assertEqual(sub_graph.icon_path, icon_path)

        with self.assertRaises(exp.ActionError):
            alib.create_action('NullAction', graph=sub_graph)

        # connect this subgraph
        actionA = alib.create_action(
            'NullAction', name='root_actionA', graph=root_graph)
        paramA = actionA.add_dynamic_param('float', name='paramA', default=3)
        paramA >> sub_graph.in_param
        self.assertTrue(sub_graph.has_param('out_param'))

        actionB = alib.create_action(
            'NullAction', name='root_actionB', graph=root_graph)
        paramB = actionB.add_dynamic_param('str', name='paramB', default=3)
        sub_graph.out_param >> paramB
        sub_action = sub_graph.get_object('action')

        # root_graph.print_detail()
        # actionB.print_detail()
        # sub_graph.print_detail()
        self.assertEqual(sub_action.in_param.value, 3)
        self.assertEqual(paramB.value, '2')

        # save root graph with sub_graph referenced
        root_path = os.path.split(os.path.realpath(__file__))[0]
        path = os.path.join(root_path, 'test.agraph')
        root_graph.write(path)

        # load root graph as a copy
        root_copy = alib.create_graph(name='root_copy')
        root_copy.read(path)
        sub_graph_copy = root_copy.get_object('sub_graph')
        sub_action_copy = sub_graph_copy.get_object('action')
        # see if everything is still the same
        self.assertTrue(sub_action_copy.is_equivalent(sub_action))
        self.assertTrue(sub_graph_copy.is_equivalent(sub_graph))
        self.assertTrue(root_copy.is_equivalent(root_graph))

        # import sub graph and make some changes
        sub_graph_copy.import_reference()
        null = alib.create_action(
            'NullAction', name='new_null', graph=sub_graph_copy)
        null.add_dynamic_param('message', name='msgp')
        sub_action_copy >> null.msgp

        # write root graph again
        root_copy.write(path)

        # load root graph as a copy
        root_copy2 = alib.create_graph(name='root_copy2')
        root_copy2.read(path)
        # see if everything is still the same
        self.assertTrue(root_copy2.is_equivalent(root_copy))

        # revert reference
        sub_graph_copy2 = root_copy2.get_object('sub_graph')
        sub_graph_copy2.revert_reference()
        self.assertFalse(root_copy2.is_equivalent(root_copy))
        self.assertTrue(root_copy2.is_equivalent(root_graph))

        if os.path.isfile(icon_path):
            os.remove(icon_path)
        if os.path.exists(libpath):
            shutil.rmtree(libpath)
        if os.path.exists(path):
            os.remove(path)

    def test_action_copy(self):
        graph = alib.create_graph()

        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        intp = actionA.add_dynamic_param('int', name='intp', default=1)
        listp = actionA.add_dynamic_param('list', name='listp')
        listp.value = (1, 2, 3)
        dictp = actionA.add_dynamic_param('dict', name='dictp')
        dictp.value = {'a': 'A', 'b': 'B'}
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)

        actionB.enabled >> actionA.enabled
        actionA.enabled >> intp
        actionA.listp.script = '[{actionA}, {actionA.enabled}]'
        actionA.dictp.script = 'dict([({actionA}, {actionA.enabled})])'

        actionB.enabled.value = False

        action_copy = actionA.copy(name='cc', bake_script=False)
        self.assertEqual(
            action_copy.enabled.script.code, '{actionB.enabled}')
        self.assertEqual(
            action_copy.listp.script.code,
            '[{actionA}, {actionA.enabled}]')
        self.assertEqual(
            action_copy.dictp.script.code,
            'dict([({actionA}, {actionA.enabled})])')
        self.assertEqual(
            action_copy.intp.script.code, '{actionA.enabled}')

        action_copy = actionA.copy(name='cc', bake_script=True)
        p = action_copy.enabled
        self.assertIsNone(p.script)
        self.assertFalse(p.script_enabled)
        self.assertFalse(p.value)
        p = action_copy.listp
        self.assertIsNone(p.script)
        self.assertFalse(p.script_enabled)
        self.assertEqual(p.value, ['actionA', False])
        p = action_copy.dictp
        self.assertIsNone(p.script)
        self.assertFalse(p.script_enabled)
        self.assertEqual(p.value, OrderedDict([('actionA', False)]))
        p = action_copy.intp
        self.assertIsNone(p.script)
        self.assertFalse(p.script_enabled)
        self.assertEqual(p.value, 0)

    def test_action_execution2(self):
        graph = alib.create_graph()

        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        actionC = alib.create_action('NullAction', name='actionC', graph=graph)
        actionD = alib.create_action('NullAction', name='actionD', graph=graph)
        actionE = alib.create_action('NullAction', name='actionE', graph=graph)

        actionC.break_point.value = True

        graph.execute()

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionC.get_status(), ExecStatus.kNone)
        self.assertEqual(actionD.get_status(), ExecStatus.kNone)
        self.assertEqual(actionE.get_status(), ExecStatus.kNone)

        graph.execute(mode='step')

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionC.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionD.get_status(), ExecStatus.kNone)
        self.assertEqual(actionE.get_status(), ExecStatus.kNone)

        graph.execute(mode='step')

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionC.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionD.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionE.get_status(), ExecStatus.kNone)

        actionB.break_point.value = True
        actionC.break_point.value = False

        graph.execute()

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kNone)
        self.assertEqual(actionC.get_status(), ExecStatus.kNone)
        self.assertEqual(actionD.get_status(), ExecStatus.kNone)
        self.assertEqual(actionE.get_status(), ExecStatus.kNone)

        graph.execute(mode='resume')

        self.assertEqual(actionA.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionB.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionC.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionD.get_status(), ExecStatus.kSuccess)
        self.assertEqual(actionE.get_status(), ExecStatus.kSuccess)

    def test_action_missing(self):

        null = alib.get_action('NullAction')

        class TestAction(null):

            _SOURCE = 'test_team:TestAction'

            @pa.int_param(default=3)
            def my_int(self):
                """my int param"""

        alib._ACTION_DICT['test_team'] = {'TestAction': TestAction}

        graph = alib.create_graph(name='root_graph')
        null_act = alib.create_action('NullAction', name='null', graph=graph)
        test_act = alib.create_action('TestAction', name='test', graph=graph)

        null_act.enabled >> test_act.my_int

        self.assertEqual(test_act.my_int.value, 1)

        path = os.path.split(os.path.realpath(__file__))[0]
        path = os.path.join(path, 'test_missing.agraph')
        graph.write(path)

        alib.refresh()

        new_graph = alib.create_graph(name='new_graph')
        new_graph.read(path)

        new_test_act = new_graph.get_object('test')
        self.assertTrue(new_test_act.type_name, 'default:NullAction')
        self.assertFalse(new_test_act.has_param('my_int'))

        # new_graph.write(path)

        if os.path.exists(path):
            os.remove(path)

    def test_graph_missing(self):

        lib_graph = alib.create_graph(name='lib_graph')
        null_act = alib.create_action('NullAction', name='null', graph=lib_graph)
        null_act.add_dynamic_param('int', name='dyn_input')
        null_act.add_dynamic_param('int', name='dyn_output', output=True)
        null_act.promote('dyn_input')
        null_act.promote('dyn_output', output=True)

        lib_path = os.path.split(os.path.realpath(__file__))[0]
        lib_path = os.path.join(lib_path, 'lib_graph.agraph')
        lib_graph.write(lib_path)

        alib._GRAPH_DICT['test_team'] = {'test_graph': lib_path}

        root_graph = alib.create_graph(name='root_graph')
        alib.create_graph('test_graph', name='sub_graph', graph=root_graph)

        path = os.path.split(os.path.realpath(__file__))[0]
        path = os.path.join(path, 'test_missing.agraph')
        root_graph.write(path)

        alib.refresh()

        new_graph = alib.create_graph(name='new_graph')
        new_graph.read(path)
        sub_graph = new_graph.get_object('sub_graph')
        self.assertEqual(sub_graph.object_count, 0)
        sub_graph.print_detail()
        param = sub_graph.dyn_input
        self.assertFalse(param.script_enabled)
        self.assertEqual(param.value, 0)
        param = sub_graph.dyn_output
        self.assertTrue(param.script_enabled)
        self.assertEqual(param.script.code, '{null.dyn_output}')

        # new_graph.write(path)

        if os.path.exists(lib_path):
            os.remove(lib_path)
        if os.path.exists(path):
            os.remove(path)

    def test_icon(self):

        alib.refresh()
        graph = alib.create_graph()

        null = alib.create_action('NullAction', graph=graph)
        switch = alib.create_action('SwitchAction', graph=graph)
        script = alib.create_action('ScriptAction', graph=graph)

        self.assertEqual(graph.icon_path, const.DEF_GRAPH_ICON)
        self.assertEqual(null.icon_path, const.DEF_ACTION_ICON)
        root = os.path.split(const.DEF_GRAPH_ICON)[0]
        path = os.path.join(root, 'SwitchAction.png').replace('\\', '/')
        self.assertEqual(switch.icon_path, path)
        path = os.path.join(root, 'ScriptAction.png').replace('\\', '/')
        self.assertEqual(script.icon_path, path)
