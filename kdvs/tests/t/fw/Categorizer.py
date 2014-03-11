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
from kdvs.fw.Categorizer import NOTCATEGORIZED, Categorizer, Orderer
from kdvs.tests import resolve_unittest
import collections

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

# def _c31(obj):
#    if obj<8:
#        return 'C3-1'
#    else:
#        return NOTCATEGORIZED
#
# def _c32(obj):
#    if obj>=8:
#        return 'C3-2'
#    else:
#        return NOTCATEGORIZED

class TestCategorizer1(unittest.TestCase):

    def test_init0(self):
        with self.assertRaises(Error):
            Categorizer(None, None)

    def test_init1(self):
        with self.assertRaises(Error):
            Categorizer('IDXXX', None)

    def test_init2(self):
        with self.assertRaises(Error):
            Categorizer(None, {})

    def test_init3(self):
        with self.assertRaises(Error):
            Categorizer('IDXXX', {})

    def test_init4(self):
        c0 = Categorizer('C0', {
            'C0-1' : _c01,
        })
        exp_categories = ['C0-1']
        self.assertEqual(exp_categories, c0.categories())
        self.assertEqual({'C0-1': _c01}, c0.categorizeC2F)
        self.assertEqual({_c01 : 'C0-1'}, c0.categorizeF2C)

    def test_init5(self):
        Categorizer('CX', {
            str(NOTCATEGORIZED) : _cx,
        })

    def test_categories1(self):
        c0 = Categorizer('C0', {
            'C0-1' : _c01,
        })
        self.assertSequenceEqual(['C0-1'], c0.categories())

class TestCategorizer2(unittest.TestCase):

    def setUp(self):
        self.symbols = range(10)
        self.c0 = Categorizer('C0', {
            'C0-1' : _c01,
        })
        self.c01 = 'C0-1'
        self.c1 = Categorizer('C1', {
            'C1-1' : _c11,
            'C1-2' : _c12,
        })
        self.c11 = 'C1-1'
        self.c12 = 'C1-2'
        self.c2 = Categorizer('C2', {
            'C2-1' : _c21,
            'C2-2' : _c22,
        })
        self.c21 = 'C2-1'
        self.c22 = 'C2-2'
#        self.c3=Categorizer('C3', {
#            'C3-1' : _c31,
#            'C3-2' : _c32,
#        })
        self.cx = Categorizer('CX', {
            str(NOTCATEGORIZED) : _cx,
        })

    def test_categorize1(self):
        categories = [self.c0.categorize(s) for s in self.symbols]
        expected_categories = [self.c01] * len(self.symbols)
        self.assertEqual(expected_categories, categories)

    def test_categorize2(self):
        categories = [self.cx.categorize(s) for s in self.symbols]
        expected_categories = [NOTCATEGORIZED] * len(self.symbols)
        self.assertEqual(expected_categories, categories)

    def test_categorize3(self):
        # C0, [0 1 2 3 4 5 6 7 8 9]
        produced_syms = list()
        ddcats0 = collections.defaultdict(list)
        for s in self.symbols:
            ddcats0[self.c0.categorize(s)].append(s)
        for sc in sorted(ddcats0.keys()):
            produced_syms.append(tuple([sc, ddcats0[sc]]))
        expected_syms = list()
        expected_syms.append(tuple([self.c01, self.symbols]))
        self.assertEqual(expected_syms, produced_syms)

    def test_categorize4(self):
        # C0->C1, [0 1 2 3 4 5 6 7 8 9] -> <5: [0 1 2 3 4] >=5: [5 6 7 8 9]
        produced_syms = list()
        # CO
        ddcats0 = collections.defaultdict(list)
        for s in self.symbols:
            ddcats0[self.c0.categorize(s)].append(s)
        for sc in sorted(ddcats0.keys()):
            produced_syms.append(tuple([sc, ddcats0[sc]]))
        # C1
        for scat0 in sorted(ddcats0.keys()):
            ddcats1 = collections.defaultdict(list)
            for s in ddcats0[scat0]:
                ddcats1[self.c1.categorize(s)].append(s)
            for sc in sorted(ddcats1.keys()):
                produced_syms.append(tuple([sc, ddcats1[sc]]))
        expected_syms = list()
        expected_syms.append(tuple([self.c01, self.symbols]))
        expected_syms.append(tuple([self.c11, self.symbols[:5]]))
        expected_syms.append(tuple([self.c12, self.symbols[5:]]))
        self.assertEqual(expected_syms, produced_syms)

    def test_categorize5(self):
        # C0->C1->C2
        # [0 1 2 3 4 5 6 7 8 9] -> <5: [0 1 2 3 4] >=5: [5 6 7 8 9]
        #    [0 1 2 3 4] -> <2: [0 1] >=2: [2 3 4]
        #    [5 6 7 8 9] -> <2: <None>, >=2: [5 6 7 8 9]
        produced_syms = list()
        # CO
        ddcats0 = collections.defaultdict(list)
        for s in self.symbols:
            ddcats0[self.c0.categorize(s)].append(s)
        for sc in sorted(ddcats0.keys()):
            produced_syms.append(tuple([sc, ddcats0[sc]]))
        # C1
        for scat0 in sorted(ddcats0.keys()):
            ddcats1 = collections.defaultdict(list)
            for s in ddcats0[scat0]:
                ddcats1[self.c1.categorize(s)].append(s)
            for sc in sorted(ddcats1.keys()):
                produced_syms.append(tuple([sc, ddcats1[sc]]))
        # C2
        for scat1 in sorted(ddcats1.keys()):
            ddcats2 = collections.defaultdict(list)
            for s in ddcats1[scat1]:
                ddcats2[self.c2.categorize(s)].append(s)
            for sc in sorted(ddcats2.keys()):
                produced_syms.append(tuple([sc, ddcats2[sc]]))
        expected_syms = list()
        # C0
        expected_syms.append(tuple([self.c01, self.symbols]))
        # C1
        expected_syms.append(tuple([self.c11, self.symbols[:5]]))
        expected_syms.append(tuple([self.c12, self.symbols[5:]]))
        # C2
        expected_syms.append(tuple([self.c21, self.symbols[:2]]))
        expected_syms.append(tuple([self.c22, self.symbols[2:5]]))
        # Nothing added for C2-1
        expected_syms.append(tuple([self.c22, self.symbols[5:]]))
        self.assertEqual(expected_syms, produced_syms)

    def test_uniquifyCategory1(self):
        uc = 'C[%s]->c[%s]'
        exp_categories = [uc % (self.c1.id, c) for c in self.c1.categories()]
        categories = [self.c1.uniquifyCategory(c) for c in self.c1.categories()]
        self.assertSequenceEqual(exp_categories, categories)

    def test_deuniquifyCategory1(self):
        ucategories = [self.c1.uniquifyCategory(c) for c in self.c1.categories()]
        dcategories = [Categorizer.deuniquifyCategory(uc) for uc in ucategories]
        exp_categories = [(self.c1.id, c) for c in self.c1.categories()]
        self.assertSequenceEqual(exp_categories, dcategories)

class TestOrderer1(unittest.TestCase):

    def test_init1(self):
        o = Orderer()
        self.assertIsNone(o.ordering)

    def test_build1(self):
        o = Orderer()
        with self.assertRaises(NotImplementedError):
            o.build()

    def test_order1(self):
        o = Orderer()
        with self.assertRaises(Error):
            o.order()

    def test_order2(self):
        mock_ordering = ('A', 'B')
        o = Orderer()
        o.ordering = mock_ordering
        ordering = o.order()
        self.assertSequenceEqual(mock_ordering, ordering)
