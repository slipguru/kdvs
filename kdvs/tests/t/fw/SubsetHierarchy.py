# Knowledge Driven Variable Selection (KDVS)
# Copyright (C) 2014 KDVS Developers. All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from kdvs.core.error import Error
from kdvs.fw.Categorizer import NOTCATEGORIZED, Categorizer
from kdvs.tests import resolve_unittest
from kdvs.fw.SubsetHierarchy import SubsetHierarchy

unittest = resolve_unittest()

def _c01(_):
    return 'C0-1'

def _cx(_):
    return NOTCATEGORIZED

def _c11(obj):
    if obj < 5:
        return 'C1-1'
    else:
        return NOTCATEGORIZED

def _c12(obj):
    if obj >= 5:
        return 'C1-2'
    else:
        return NOTCATEGORIZED

def _c21(obj):
    if obj < 2:
        return 'C2-1'
    else:
        return NOTCATEGORIZED

def _c22(obj):
    if obj >= 2:
        return 'C2-2'
    else:
        return NOTCATEGORIZED

def _c31(obj):
    if obj < 8:
        return 'C3-1'
    else:
        return NOTCATEGORIZED

def _c32(obj):
    if obj >= 8:
        return 'C3-2'
    else:
        return NOTCATEGORIZED

# mock that uses simple numbers as PK IDs and links them into hierarchy
class MockSubsetHierarchy1(SubsetHierarchy):

    def __init__(self):
        super(MockSubsetHierarchy1, self).__init__()

    def build(self, categorizers_list, categorizers_inst_dict, initial_symbols):
        super(MockSubsetHierarchy1, self).build(categorizers_list, categorizers_inst_dict, initial_symbols)

    def obtainDatasetFromSymbol(self, symbol):
        return symbol


class TestSubsetHierarchy1(unittest.TestCase):

    def test_init1(self):
        sh = SubsetHierarchy()
        self.assertEqual({}, sh.hierarchy)
        self.assertEqual({}, sh.symboltree)

    def test_build1(self):
        symbols = range(10)
        c0 = Categorizer('C0', {
            'C0-1' : _c01,
        })
        c1 = Categorizer('C1', {
            'C1-1' : _c11,
            'C1-2' : _c12,
        })
        cinst = {
            'C0' : c0,
            'C1' : c1,
        }
        cmap = ['C0', 'C1']
        sh = SubsetHierarchy()
        sh.build(cmap, cinst, symbols)
        self.assertIsNone(sh.symboltree)

    def test_obtainDatasetFromSymbol1(self):
        sh = SubsetHierarchy()
        with self.assertRaises(NotImplementedError):
            sh.obtainDatasetFromSymbol(0)


class TestSubsetHierarchy2(unittest.TestCase):

    def setUp(self):
        self.symbols = range(10)
        self.c0 = Categorizer('C0', {
            'C0-1' : _c01,
        })
        self.uniq_c01 = self.c0.uniquifyCategory('C0-1')
        self.c1 = Categorizer('C1', {
            'C1-1' : _c11,
            'C1-2' : _c12,
        })
        self.uniq_c11 = self.c1.uniquifyCategory('C1-1')
        self.uniq_c12 = self.c1.uniquifyCategory('C1-2')
        self.c2 = Categorizer('C2', {
            'C2-1' : _c21,
            'C2-2' : _c22,
        })
        self.uniq_c21 = self.c2.uniquifyCategory('C2-1')
        self.uniq_c22 = self.c2.uniquifyCategory('C2-2')
        self.c3 = Categorizer('C3', {
            'C3-1' : _c31,
            'C3-2' : _c32,
        })
        self.uniq_c31 = self.c3.uniquifyCategory('C3-1')
        self.uniq_c32 = self.c3.uniquifyCategory('C3-2')
        self.cinst = {
            'C0' : self.c0,
            'C1' : self.c1,
            'C2' : self.c2,
            'C3' : self.c3,
        }
        self.cinstx = {}
        self.cmap0 = []
        self.cmap1 = ['C0']
        self.cmap2 = ['C0', 'C1']
        self.cmap3 = ['C0', 'C2']
        self.cmap4 = ['C0', 'C3']
        self.cmap5 = ['C0', 'C1', 'C2']
        self.cmapX = ['C0', 'XXXXX']

    def test_init0(self):
        sh = MockSubsetHierarchy1()
        self.assertEqual({}, sh.hierarchy)
        self.assertEqual({}, sh.symboltree)

    def test_init1(self):
        sh = MockSubsetHierarchy1()
        sh.build(self.cmap0, self.cinst, self.symbols)
        self.assertEqual({}, sh.hierarchy)
        self.assertEqual({}, sh.symboltree)

    def test_init2(self):
        sh = MockSubsetHierarchy1()
        sh.build(self.cmap1, self.cinst, self.symbols)
        expected_hierarchy = {None : self.c0.id, self.uniq_c01 : None}
        expected_symboltree = {None : {self.uniq_c01 : self.symbols}}
        self.assertEqual(expected_hierarchy, sh.hierarchy)
        self.assertEqual(expected_symboltree, sh.symboltree)

    def test_init3(self):
        sh = MockSubsetHierarchy1()
        # wrong instance dictionary
        with self.assertRaises(Error):
            sh.build(self.cmap1, self.cinstx, self.symbols)

    def test_init4(self):
        sh = MockSubsetHierarchy1()
        # wrong categorizers list
        with self.assertRaises(Error):
            sh.build(self.cmapX, self.cinstx, self.symbols)

    def test_init5(self):
        sh = MockSubsetHierarchy1()
        sh.build(self.cmap2, self.cinst, self.symbols)
        expected_hierarchy = {}
        expected_hierarchy.update({None : self.c0.id})
        expected_hierarchy.update({self.uniq_c01 : self.c1.id})
        expected_hierarchy.update({self.uniq_c11 : None})
        expected_hierarchy.update({self.uniq_c12 : None})
        expected_symboltree = {}
        expected_symboltree.update({None : {self.uniq_c01 : self.symbols}})
        expected_symboltree.update({self.uniq_c01 : {self.uniq_c11 : self.symbols[:5], self.uniq_c12 : self.symbols[5:]}})
        self.assertEqual(expected_hierarchy, sh.hierarchy)
        self.assertEqual(expected_symboltree, sh.symboltree)

    def test_init6(self):
        sh = MockSubsetHierarchy1()
        sh.build(self.cmap3, self.cinst, self.symbols)
        expected_hierarchy = {}
        expected_hierarchy.update({None : self.c0.id})
        expected_hierarchy.update({self.uniq_c01 : self.c2.id})
        expected_hierarchy.update({self.uniq_c21 : None})
        expected_hierarchy.update({self.uniq_c22 : None})
        expected_symboltree = {}
        expected_symboltree.update({None : {self.uniq_c01 : self.symbols}})
        expected_symboltree.update({self.uniq_c01 : {self.uniq_c21 : self.symbols[:2], self.uniq_c22 : self.symbols[2:]}})
        self.assertEqual(expected_hierarchy, sh.hierarchy)
        self.assertEqual(expected_symboltree, sh.symboltree)

    def test_init7(self):
        sh = MockSubsetHierarchy1()
        sh.build(self.cmap4, self.cinst, self.symbols)
        expected_hierarchy = {}
        expected_hierarchy.update({None : self.c0.id})
        expected_hierarchy.update({self.uniq_c01 : self.c3.id})
        expected_hierarchy.update({self.uniq_c31 : None})
        expected_hierarchy.update({self.uniq_c32 : None})
        expected_symboltree = {}
        expected_symboltree.update({None : {self.uniq_c01 : self.symbols}})
        expected_symboltree.update({self.uniq_c01 : {self.uniq_c31 : self.symbols[:8], self.uniq_c32 : self.symbols[8:]}})
        self.assertEqual(expected_hierarchy, sh.hierarchy)
        self.assertEqual(expected_symboltree, sh.symboltree)

    def test_init8(self):
        sh = MockSubsetHierarchy1()
        sh.build(self.cmap5, self.cinst, self.symbols)
        expected_hierarchy = {}
        expected_hierarchy.update({None : self.c0.id})
        expected_hierarchy.update({self.uniq_c01 : self.c1.id})
        expected_hierarchy.update({self.uniq_c11 : self.c2.id})
        expected_hierarchy.update({self.uniq_c12 : self.c2.id})
        expected_hierarchy.update({self.uniq_c21 : None})
        expected_hierarchy.update({self.uniq_c22 : None})
        expected_symboltree = {}
        expected_symboltree.update({None : {self.uniq_c01 : self.symbols}})
        expected_symboltree.update({self.uniq_c01 : {self.uniq_c11 : self.symbols[:5], self.uniq_c12 : self.symbols[5:]}})
        expected_symboltree.update({self.uniq_c11 : {self.uniq_c21 : self.symbols[:2], self.uniq_c22 : self.symbols[2:5]}})
        # nothing is added for C2-1 below
        expected_symboltree.update({self.uniq_c12 : {self.uniq_c22 : self.symbols[5:]}})
        self.assertEqual(expected_hierarchy, sh.hierarchy)
        self.assertEqual(expected_symboltree, sh.symboltree)

