import unittest

import mhy.maya.standard.name as napi


class TestName(unittest.TestCase):
    """
    Test node name api
    """

    def test_name_init(self):
        # initialization with different args
        name = napi.NodeName('a_b_1_L_c', desc='d', num=4, ext='a')
        self.assertEqual(name, 'a_d_04_L_a')

        name = napi.NodeName('nsa:parent|nsb:a_b_1_L_c')
        self.assertEqual(name, 'a_b_01_L_c')

        name = napi.NodeName('a_b_1_L_c')
        self.assertEqual(name, 'a_b_01_L_c')

        name = napi.NodeName(desc='d', num=2)
        self.assertEqual(name, 'part_d_02_EXT')

        name = napi.NodeName('a_b_M_t')
        self.assertEqual(name, 'a_b_M_t')

        name = napi.NodeName('a_b_3_t')
        self.assertEqual(name, 'a_b_03_t')

        name = napi.NodeName('a_3_L_t')
        self.assertEqual(name, 'a_03_L_t')

        name = napi.NodeName('a_3_t')
        self.assertEqual(name, 'a_03_t')

        name = napi.NodeName('a_b_t')
        self.assertEqual(name, 'a_b_t')

        name = napi.NodeName('a_R_t')
        self.assertEqual(name, 'a_R_t')

        name = napi.NodeName('a_t')
        self.assertEqual(name, 'a_t')

        with self.assertRaises(ValueError):
            name = napi.NodeName('a_R_t', 'b')

        with self.assertRaises(ValueError):
            name = napi.NodeName('a_R_t', aaa='a')

    def test_name_property(self):
        name = napi.NodeName('a_b_1_L_c')
        self.assertEqual(name, 'a_b_01_L_c')
        self.assertEqual(name.part, 'a')
        self.assertEqual(name.desc, 'b')
        self.assertEqual(name.num, 1)
        self.assertEqual(name.side, 'L')
        self.assertEqual(name.ext, 'c')

        # property setters
        name = name.replace_part('Part')
        name = name.replace_desc('Desc')
        name = name.replace_num('033')
        with self.assertRaises(ValueError):
            name = name.replace_side('a')
        with self.assertRaises(ValueError):
            name = name.replace_num('a')
        name = name.replace_side('R')
        name = name.replace_ext('Type')

        self.assertEqual(name, 'Part_Desc_33_R_Type')
        self.assertEqual(name.part, 'Part')
        self.assertEqual(name.desc, 'Desc')
        self.assertEqual(name.num, 33)
        self.assertEqual(name.side, 'R')
        self.assertEqual(name.ext, 'Type')

        name = name.replace_num(2)
        self.assertEqual(name.num, 2)
        self.assertEqual(name, 'Part_Desc_02_R_Type')

    def test_name_flip(self):
        name = napi.NodeName('Part_Desc_02_L_Type')
        fname = name.flip()
        self.assertEqual(name.side, 'L')
        self.assertEqual(name, 'Part_Desc_02_L_Type')
        self.assertEqual(fname.side, 'R')
        self.assertEqual(fname, 'Part_Desc_02_R_Type')

        # sanitization
        name = name.replace_part('ads_aa!d@@__ $FF')
        self.assertEqual(name.part, 'adsaadFF')
        self.assertEqual(name, 'adsaadFF_Desc_02_L_Type')

    def test_name_optional_token(self):
        name = napi.NodeName('a_main_00_L_T')
        self.assertEqual(name, 'a_00_L_T')
        self.assertIsNone(name.desc)
        self.assertEqual(name.num, 0)

        name = name.replace_desc(None)
        self.assertEqual(name, 'a_00_L_T')
        self.assertIsNone(name.desc)

        name = name.flip()
        self.assertEqual(name, 'a_00_R_T')
        self.assertIsNone(name.desc)

        name = name.replace_num(None)
        self.assertEqual(name, 'a_R_T')
        self.assertIsNone(name.desc)
        self.assertIsNone(name.num)

        name = name.flip()
        self.assertEqual(name, 'a_L_T')
        self.assertIsNone(name.desc)
        self.assertIsNone(name.num)

        name = name.replace_desc('de')
        self.assertEqual(name, 'a_de_L_T')
        self.assertEqual(name.desc, 'de')
        self.assertIsNone(name.num)

        name = name.replace_num(3)
        self.assertEqual(name, 'a_de_03_L_T')
        self.assertEqual(name.desc, 'de')
        self.assertEqual(name.num, 3)

        name = name.replace_side(None)
        self.assertEqual(name, 'a_de_03_T')
        self.assertIsNone(name.side)
        self.assertEqual(name.num, 3)

        name = name.replace_desc(None)
        name = name.replace_num(None)
        self.assertEqual(name, 'a_T')

    def test_name_str_substitute(self):
        name = napi.NodeName('a_main_00_L_T')
        new_name = name.replace('_00_', '_01_')
        self.assertEqual(new_name, 'a_01_L_T')
        self.assertFalse(new_name.isdigit())
        self.assertEqual(new_name.find('L'), 5)
        self.assertEqual(new_name.rfind('x'), -1)

        new_name = new_name.replace_part('{}')
        self.assertEqual(new_name, '{}_01_L_T')
        new_name = new_name.format('abc')
        self.assertEqual(new_name, 'abc_01_L_T')
        self.assertEqual(new_name.part, 'abc')

        new_name += 'stuff'
        self.assertEqual(new_name, 'abc_01_L_Tstuff')
        self.assertEqual(new_name.ext, 'Tstuff')

        new_name = new_name.upper()
        self.assertEqual(new_name, 'ABC_01_L_TSTUFF')
        self.assertEqual(new_name.ext, 'TSTUFF')


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestName))
    unittest.TextTestRunner(failfast=True).run(suite)
