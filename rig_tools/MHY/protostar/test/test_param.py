from json import encoder
import os
import unittest
from functools import partial
from collections import OrderedDict

from mhy.protostar.constants import ExecStatus
import mhy.protostar.constants as const
import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp
from mhy.protostar.lib import LIB_ENV_VAR
from mhy.protostar.lib import ActionLibrary as alib

# Add the userlib path in this module
path = os.path.split(os.path.dirname(os.path.realpath(__file__)))[0]
path = os.path.join(path, 'py', 'mhy', 'protostar', 'userlib')
if LIB_ENV_VAR not in os.environ:
    os.environ[LIB_ENV_VAR] = path
else:
    os.environ[LIB_ENV_VAR] += os.pathsep + path


alib.refresh()


class TestParameter(unittest.TestCase):
    """
    Test action custom executions
    """

    def test_param_properties(self):
        graph = alib.create_graph(name='my_graph')
        action = alib.create_action('NullAction', name='my_action', graph=graph)

        # action param
        param = action.message
        self.assertEqual(param.name, const.SELF_PARAM_NAME)
        self.assertEqual(param.full_name, 'my_action.' + const.SELF_PARAM_NAME)
        self.assertEqual(param.long_name, 'my_graph:my_action.' + const.SELF_PARAM_NAME)
        self.assertEqual(param.owner, action)
        self.assertTrue(param.is_output)
        self.assertFalse(param.is_dynamic)

        # int param
        param = action.add_dynamic_param('int', name='my_int', default=3)
        self.assertEqual(param.ui_label, param.name)
        self.assertEqual(param.default, 3)
        self.assertEqual(param.value, param.default)
        param.value = 10.2
        self.assertEqual(param.value, 10)
        self.assertFalse(param.is_output)
        self.assertTrue(param.is_dynamic)

        # assgin string to int param should cause error
        with self.assertRaises(exp.ParameterError):
            param.value = 'abc'

        # float param
        param = action.add_dynamic_param(
            'float', name='my_float', output=True, ui_label='Hi',
            min_value=-1, max_value=10)
        self.assertEqual(param.ui_label, 'Hi')
        self.assertEqual(param.default, 0)
        self.assertEqual(param.value, param.default)
        param.value = 11.3
        self.assertEqual(param.value, 10)
        param.value = -2
        self.assertEqual(param.value, -1)
        param.value = 5.4
        self.assertEqual(param.value, 5.4)
        self.assertTrue(param.is_output)
        self.assertTrue(param.is_dynamic)

        # remove static param should cause an error
        with self.assertRaises(exp.ParameterError):
            action.remove_dynamic_param(action.enabled)

        # bool param
        param = action.add_dynamic_param('bool', name='my_bool')
        param.value = 'abc'
        self.assertTrue(param.value)
        self.assertFalse(param.default)

        # vector3 parameters
        param = action.add_dynamic_param('vector3', name='my_v3', default=(1, 2, 3))
        self.assertEqual(param.value, (1, 2, 3))
        param.value = (3, 3, 4)
        self.assertEqual(param.value, (3, 3, 4))
        param.script = '(3, 4, 5)'
        self.assertEqual(param.value, (3, 4, 5))

        # enum param
        param = action.add_dynamic_param(
            'enum', name='my_enum', items=['a', 'b', 'c'], default='b')
        self.assertEqual(param.value, 1)
        self.assertEqual(param.enum_value, 'b')
        self.assertEqual(param.min_value, 0)
        self.assertEqual(param.max_value, 2)
        param.value = 4
        self.assertEqual(param.value, 2)
        self.assertEqual(param.enum_value, 'c')

        # str param
        param = action.add_dynamic_param('str', name='my_str', default='abc')
        self.assertEqual(param.value, 'abc')
        param.value = 12
        self.assertEqual(param.value, '12')

        # dir param
        param = action.add_dynamic_param('dir', name='my_dir', default='abc')
        param.value = '\\a\\b\\c\\'
        self.assertEqual(param.value, '/a/b/c')
        param.value = '\\a\\b\\c/d.txt'
        self.assertEqual(param.value, '/a/b/c')
        param.value = '\\a.b.c\\d'
        self.assertEqual(param.value, '/a.b.c/d')

        # file param
        param = action.add_dynamic_param(
            'file', name='my_file', default='abc.py', ext='py')
        with self.assertRaises(exp.ParameterError):
            param.value = '\\a\\b\\c\\'
        param.value = '\\a\\b\\c/d.py'
        self.assertEqual(param.value, '/a/b/c/d.py')
        with self.assertRaises(exp.ParameterError):
            param.value = 'aaa.txt'

        # callback param
        call_param = pa._create_parameter(
            'callback', name='my_call', dynamic=False, owner=action)
        call_param.value = 'get_params'
        self.assertEqual(call_param.value, action.get_params())
        call_param.value = partial(action.get_params, dynamic=False)
        self.assertEqual(call_param.value, action.get_params(dynamic=False))

        # callback param cannot be connected
        with self.assertRaises(exp.PConnectionError):
            param >> call_param
        with self.assertRaises(exp.PConnectionError):
            call_param >> param

        action.remove_dynamic_param(param)
        self.assertFalse(action.has_param(param))
        self.assertIsNone(param.owner)

    def test_param_script_simple(self):
        graph = alib.create_graph(name='my_graph')
        actionA = alib.create_action('NullAction', graph=graph)
        actionB = alib.create_action('NullAction', graph=graph)
        actionC = alib.create_action('NullAction', graph=graph)

        paramA = actionA.add_dynamic_param('int', default=3)
        paramA2 = actionA.add_dynamic_param('int')
        paramB = actionB.add_dynamic_param('str')
        paramB2 = actionB.add_dynamic_param('str')
        paramC = actionC.add_dynamic_param('enum', items=['a', 'b', 'c'])

        paramA >> paramB
        self.assertTrue(paramB.script_enabled)
        self.assertEqual(paramB.value, '3')
        self.assertTrue(paramB.has_input)
        self.assertTrue(paramA.has_output)
        self.assertEqual(paramB.input_params, set([paramA]))
        self.assertEqual(paramA.output_params, set([paramB]))
        self.assertTrue(paramB.has_direct_input)

        # paramB is already connected
        with self.assertRaises(exp.PConnectionError):
            paramC.connect(paramB)

        # connection cycle
        with self.assertRaises(exp.PConnectionError):
            paramB2.connect(paramA2)

        # test remove script
        paramB.value = 'abc'
        self.assertEqual(paramB.value, '3')
        paramB.clear_script()
        self.assertFalse(paramB.has_direct_input)
        self.assertFalse(paramB.script_enabled)
        self.assertEqual(paramB.value, '3')

        # value compatible
        paramB.value = 'abc'
        with self.assertRaises(exp.PConnectionError):
            paramB >> paramA

        paramB.value = '1'
        with self.assertRaises(exp.PConnectionError):
            paramB >> paramA

    def test_param_script_complex(self):
        graph = alib.create_graph(name='my_graph')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        actionC = alib.create_action('NullAction', name='actionC', graph=graph)

        paramA = actionA.add_dynamic_param('int', name='paramA', default=3)
        paramB = actionB.add_dynamic_param(
            'enum', name='paramB', items=['a', 'b', 'c'], default=1)
        paramC = actionC.add_dynamic_param('str', name='paramC')
        paramC.value = 'abc'

        # expression with 2 input references
        paramC.script = '{actionA.paramA} + {actionB.paramB}'
        self.assertEqual(paramC.value, '4')
        self.assertFalse(paramC.has_direct_input)
        self.assertTrue(paramC.has_input)
        self.assertTrue(paramA.has_output and paramB.has_output)
        self.assertEqual(paramC.input_params, set([paramA, paramB]))
        self.assertEqual(paramA.output_params, set([paramC]))
        self.assertEqual(paramB.output_params, set([paramC]))

        paramA.value = 4
        paramB.value = 'c'
        self.assertEqual(paramC.value, '6')

        # complex script
        paramC.script = """
    if {actionA.paramA} > 4:
        return 'pa'
    elif {actionB.paramB} == 2:
        return 'pb'
    return 'none'"""
        self.assertFalse(paramC.has_direct_input)
        self.assertTrue(paramC.script_enabled)
        self.assertEqual(paramC.value, 'pb')
        paramA.value = 5
        self.assertEqual(paramC.value, 'pa')
        self.assertEqual(paramC.input_params, set([paramA, paramB]))
        self.assertEqual(paramA.output_params, set([paramC]))
        self.assertEqual(paramB.output_params, set([paramC]))

        # test rename action
        actionA.name = 'new_action_name'
        self.assertEqual(paramC.value, 'pa')
        self.assertEqual(paramC.input_params, set([paramA, paramB]))
        self.assertEqual(paramA.output_params, set([paramC]))
        self.assertEqual(paramB.output_params, set([paramC]))

        # test rename parameter
        paramA.name = 'new_param_name'
        self.assertEqual(paramC.value, 'pa')
        self.assertEqual(paramC.input_params, set([paramA, paramB]))
        self.assertEqual(paramA.output_params, set([paramC]))
        self.assertEqual(paramB.output_params, set([paramC]))

        # try a broken script
        paramC.script = 'a + b'
        self.assertTrue(paramC.script_enabled)
        self.assertEqual(paramC.input_params, set())
        self.assertEqual(paramA.output_params, set())
        self.assertEqual(paramB.output_params, set())

        # try an env var reference
        os.environ['TEST_VAR'] = 'test_var'
        paramC.script = '{$TEST_VAR}aaa'
        self.assertFalse(paramC.has_direct_input)
        self.assertEqual(paramC.value, 'test_varaaa')
        paramC.script = '{$TEST_VAR}'
        self.assertFalse(paramC.has_direct_input)

        os.environ.pop('TEST_VAR')

        # test remove script
        paramC.clear_script()
        self.assertFalse(paramC.script_enabled)
        self.assertEqual(paramC.value, '')

    def test_param_list(self):
        graph = alib.create_graph(name='my_graph')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)

        strA = actionA.add_dynamic_param('str', name='str_a', default='str_a')
        listB = actionB.add_dynamic_param('list', name='list_b')

        # test default value
        self.assertEqual(listB.default, [])
        self.assertEqual(len(listB), 0)
        listB.append(2)
        self.assertEqual(listB[0], 2)
        self.assertEqual(len(listB), 1)

        listB.default = [1, 'a']
        listB.reset_value()
        self.assertEqual(listB.default, [1, 'a'])
        self.assertEqual(listB[0], 1)
        listB.append(2)
        self.assertEqual(listB[1], 'a')
        self.assertEqual(listB[2], 2)

        # test setting list value directly
        listB.value = ['a', 'b', 'c']
        self.assertEqual(len(listB), 3)
        self.assertEqual(listB[0], 'a')
        self.assertEqual(listB[2], 'c')

        # test connection
        listB.script = '''[
            1,
            {actionA.str_a},
            "c"]'''
        self.assertEqual(listB[1], 'str_a')
        self.assertTrue(listB.has_input)
        self.assertFalse(listB.has_direct_input)
        self.assertEqual(listB.input_params, set([strA]))
        strA.value = 'new_val'
        self.assertEqual(listB[1], 'new_val')
        self.assertEqual(listB.value, [1, 'new_val', 'c'])

        # test pop
        listB.clear_script()
        listB.value = ['a', 'b', 3]
        listB.pop(0)
        self.assertEqual(listB.value, ['b', 3])

        # test reference list value
        strA.script = '{actionB.list_b}[1]'
        self.assertEqual(strA.value, '3')
        self.assertFalse(strA.has_direct_input)

        # test non-serializable object
        class Foo(object):

            def __str__(self):
                return 'foo'

            __repr__ = __str__

        foo = Foo()
        listB[1] = foo
        self.assertEqual(strA.value, 'foo')
        self.assertEqual(listB[1], 'foo')
        self.assertNotEqual(listB.value[1], foo)

        # editable test
        listB.editable = False
        with self.assertRaises(exp.ParameterError):
            listB.value = [0, 1, 2]
        with self.assertRaises(exp.ParameterError):
            listB.script_enabled = True
        with self.assertRaises(exp.ParameterError):
            listB.script = None
        with self.assertRaises(exp.ParameterError):
            listB.clear_script()
        with self.assertRaises(exp.ParameterError):
            listB.default = 4

        # var test
        listC = actionB.add_dynamic_param(
            'list', name='list_c', item_type='str', min_count=2, max_count=3)
        self.assertEqual(listC.value, [])
        with self.assertRaises(exp.ParameterError):
            listC.append(3)
        listC.value = (1, 2)
        self.assertEqual(listC.value, ['1', '2'])
        listC.append(3)
        with self.assertRaises(exp.ParameterError):
            listC.append(3)
        self.assertEqual(listC.value, ['1', '2', '3'])
        listC.pop(1)
        self.assertEqual(listC.value, ['1', '3'])
        with self.assertRaises(exp.ParameterError):
            listC.pop(1)

        listD = actionB.add_dynamic_param(
            'list', name='list_d', max_count=3)
        self.assertEqual(listD.value, [])
        listD.append(3)
        self.assertEqual(listD.value, [3])
        listD.pop(0)
        listD.append(True)
        self.assertEqual(listD.value, [True])

    def test_param_dict(self):
        graph = alib.create_graph(name='my_graph')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)

        strA = actionA.add_dynamic_param('str', name='str_a', default='str_a')
        dictB = actionB.add_dynamic_param('dict', name='dict_b')

        # test default value
        self.assertEqual(dictB.default, OrderedDict())
        self.assertEqual(len(dictB), 0)
        dictB[1] = None
        self.assertEqual(dictB[1], None)
        self.assertEqual(len(dictB), 1)

        dictB.default = OrderedDict(((1, 'a'), ('b', 2)))
        dictB.reset_value()
        self.assertEqual(dictB.default, OrderedDict(((1, 'a'), ('b', 2))))
        self.assertEqual(dictB[1], 'a')
        self.assertEqual(dictB['b'], 2)
        dictB['c'] = 'abc'
        self.assertEqual(dictB['c'], 'abc')

        # test setting dict value directly
        dictB.value = {'a': 'A', 1: 2}
        self.assertEqual(len(dictB), 2)
        self.assertEqual(dictB[1], 2)
        self.assertEqual(dictB['a'], 'A')

        # test connection
        dictB.script = '''dict((
            (1, "a"),
            ("b", {actionA.str_a})
        ))'''
        self.assertEqual(dictB['b'], 'str_a')
        self.assertFalse(dictB.has_direct_input)
        self.assertTrue(dictB.has_input)
        self.assertEqual(dictB.input_params, set([strA]))
        strA.value = 'new_val'
        self.assertEqual(dictB['b'], 'new_val')
        self.assertEqual(dictB.value, OrderedDict(((1, 'a'), ('b', 'new_val'))))

        # test popping out sub-param
        dictB.clear_script()
        dictB.value = {'a': 'A', 1: 2}
        dictB.pop(1)
        with self.assertRaises(exp.ParameterError):
            dictB[1]

        # test reference dict value
        strA.script = '{actionB.dict_b}["a"]'
        self.assertEqual(strA.value, 'A')
        self.assertFalse(strA.has_direct_input)

        # test non-serializable object
        class Foo(object):

            def __str__(self):
                return 'foo'

            __repr__ = __str__

        foo = Foo()
        dictB['a'] = foo
        self.assertEqual(strA.value, 'foo')
        self.assertEqual(dictB['a'], 'foo')
        self.assertNotEqual(dictB.value['a'], foo)

        # editable test
        dictB.editable = False
        with self.assertRaises(exp.ParameterError):
            dictB.value = {0: 1}
        with self.assertRaises(exp.ParameterError):
            dictB.script_enabled = True
        with self.assertRaises(exp.ParameterError):
            dictB.script = None
        with self.assertRaises(exp.ParameterError):
            dictB.clear_script()
        with self.assertRaises(exp.ParameterError):
            dictB.default = 4

        # var test
        dictC = actionB.add_dynamic_param(
            'dict', name='dict_c', key_type='int', item_type='str', min_count=2, max_count=3)
        self.assertEqual(dictC.value, OrderedDict())
        with self.assertRaises(exp.ParameterError):
            dictC['2'] = 3
        dictC.value = OrderedDict((('1', 1), ('2', 2), ('3', 3)))
        self.assertEqual(dictC.value, OrderedDict(((1, '1'), (2, '2'), (3, '3'))))
        with self.assertRaises(exp.ParameterError):
            dictC['4'] = 4
        self.assertEqual(dictC.value, OrderedDict(((1, '1'), (2, '2'), (3, '3'))))
        dictC.pop(1)
        self.assertEqual(dictC.value, OrderedDict(((2, '2'), (3, '3'))))
        with self.assertRaises(exp.ParameterError):
            dictC.pop(0)

        dictD = actionB.add_dynamic_param(
            'dict', name='dict_d', max_count=3)
        self.assertEqual(dictD.value, OrderedDict())
        dictD['2'] = 3
        self.assertEqual(dictD.value, OrderedDict((('2', 3),)))
        dictD[3] = True
        self.assertEqual(dictD.value, OrderedDict((('2', 3), (3, True))))

    def test_param_iter(self):
        graph = alib.create_graph(name='root')
        iparam = graph.add_dynamic_param(
            'iter', name='iter_param')
        self.assertEqual(iparam.default, [])
        iparam.value = [0, 1, 2]
        self.assertEqual(iparam.default, [])
        self.assertEqual(iparam.iter_value, 0)
        self.assertEqual(iparam.iter_id, 0)

        action = alib.create_action('NullAction', name='null', graph=graph)
        self.assertTrue(action.enabled.value)
        param = action.add_dynamic_param('str', name='null_str')
        with self.assertRaises(exp.ParameterError):
            action.add_dynamic_param('iter')

        iparam >> param

        graph.execute()
        self.assertEqual(iparam.iter_value, 2)
        self.assertEqual(iparam.iter_id, 2)
        self.assertEqual(param.value, '2')
        self.assertEqual(action.get_status(), ExecStatus.kSuccess)
        self.assertEqual(graph.get_status(), ExecStatus.kSuccess)

    def test_param_data(self):
        graph = alib.create_graph(name='root')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)

        # pyobject
        pparam = pa._create_parameter(
            'pyobject', name='pop', dynamic=False, output=True, owner=actionA)

        class MyObj(object):
            pass
        o = MyObj()

        pparam.value = o
        self.assertEqual(pparam.value, o)
        pparam.value = 3
        self.assertEqual(pparam.value, 3)
        o = set([1, 2, 3])
        pparam.value = o
        self.assertEqual(pparam.value, o)

        # int
        iparam = actionA.add_dynamic_param('int', name='intp', default=3)
        iparam.value = 2
        self.assertEqual(iparam.default, 3)
        data = iparam._get_data()
        iparam._set_data(data)
        self.assertFalse('ui_label' in data['creation'])
        self.assertEqual(data['value'], 2)
        self.assertEqual(iparam.value, 2)
        self.assertEqual(iparam.default, 3)

        iparam.value = 3
        iparam.ui_label = 'haha'
        data = iparam._get_data()
        iparam._set_data(data)
        self.assertFalse('value' in data)
        self.assertEqual(data['creation']['default'], 3)
        self.assertEqual(iparam.value, 3)
        self.assertEqual(iparam.default, 3)
        self.assertEqual(iparam.ui_label, 'haha')

        # simple connection
        inputp = actionB.add_dynamic_param('float', name='input_float', default=5.1)
        inputp >> iparam
        self.assertEqual(iparam.value, 5)
        data = iparam._get_data()
        iparam._set_data(data)
        self.assertEqual(iparam.value, 5)
        self.assertTrue(iparam.script_enabled)
        self.assertEqual(iparam.script.code, '{actionB.input_float}')

        # copy
        cparam = iparam.copy(name='copy')
        self.assertEqual(cparam.name, 'copy')
        self.assertTrue(cparam.script_enabled)
        self.assertEqual(cparam.script.code, '{actionB.input_float}')
        self.assertEqual(cparam.value, 5)
        self.assertEqual(cparam.default, 3)

        # enum
        eparam = actionA.add_dynamic_param(
            'enum', name='enump', items=['a', 'b', 'c'], default=1)
        data = eparam._get_data()
        self.assertEqual(eparam.name, 'enump')
        eparam._set_data(data)
        self.assertEqual(eparam.name, 'enump')
        self.assertFalse('ui_label' in data['creation'])
        self.assertEqual(data['creation']['items'], eparam.items)
        self.assertFalse('value' in data)
        self.assertEqual(eparam.value, 1)
        self.assertEqual(eparam.enum_value, 'b')
        self.assertEqual(eparam.default, 1)

        iparam._set_data(data)
        self.assertEqual(iparam.name, 'enump1')

        self.assertIsNone(iparam.min_value)
        self.assertIsNone(iparam.max_value)
        self.assertEqual(iparam.value, 1)
        self.assertEqual(iparam.default, 1)
        self.assertFalse(iparam.script_enabled)
        self.assertIsNone(iparam.script)

        # message
        nparam = actionA.add_dynamic_param('message', name='messagep', default=1)
        data = nparam._get_data()
        self.assertFalse('value' in data)

        # str
        sparam = actionA.add_dynamic_param('str', name='strp', default=1)
        sparam.value = 'abc'
        data = sparam._get_data()
        self.assertEqual(data['creation']['default'], '1')
        self.assertEqual(data['value'], 'abc')
        self.assertFalse('max_value' in data['creation'])

        # list
        lparam = actionA.add_dynamic_param(
            'list', name='listp', item_type='str', min_count=1, max_count=3)
        lparam.value = [1, '2', True]
        data = lparam._get_data()
        self.assertEqual(data['creation']['item_type'], 'str')
        self.assertEqual(data['creation']['min_count'], 1)
        self.assertEqual(data['creation']['max_count'], 3)
        self.assertEqual(data['value'], ['1', '2', 'True'])

        lparam = actionA.add_dynamic_param('list', name='listp2', max_count=3)
        lparam.value = [1, '2', True]
        data = lparam._get_data()
        self.assertFalse('item_type' in data['creation'])
        self.assertFalse('min_count' in data['creation'])
        self.assertEqual(data['creation']['max_count'], 3)
        self.assertEqual(data['value'], [1, '2', True])

    def test_param_message(self):

        graph = alib.create_graph(name='root')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        param = actionB.add_dynamic_param('message', name='msgp')

        self.assertIsNone(actionA.message.value, None)

        actionA.message >> param

        self.assertIsNone(actionA.message.value, None)
        self.assertTrue(param.value, actionA)

    def test_param_group(self):
        graph = alib.create_graph(name='my_graph')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        pa = actionA.add_dynamic_param('int', name='pa', group='ga', priority=10)
        pb = actionA.add_dynamic_param('int', name='pb', group='gb', priority=100)
        pc = actionA.add_dynamic_param('int', name='pc', group='gb', priority=10)

        self.assertEqual(pa.priority, 10)
        self.assertEqual(actionA.execution.priority, 0)
        self.assertEqual(actionA.message.priority, -1)

        params = actionA.get_params(sort=True)
        self.assertEqual(params, [
            actionA.execution, actionA.enabled, actionA.break_point,
            pa, pb, pc, actionA.message])
        self.assertEqual(actionA.get_params(group='ga', sort=True), [pa])
        self.assertEqual(actionA.get_params(group='gb', sort=True), [pb, pc])

    def test_message_param_eval(self):
        graph = alib.create_graph(name='my_graph')
        actionA = alib.create_action('NullAction', name='actionA', graph=graph)
        actionB = alib.create_action('NullAction', name='actionB', graph=graph)
        param = actionB.add_dynamic_param('message')

        param.script = '{actionA}'

        self.assertEqual(param.value, actionA)

        param.script = '{actionA.message}'

        self.assertEqual(param.value, actionA)
        self.assertEqual(param.script.code, '{actionA}')
