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

from kdvs.tests import resolve_unittest
from kdvs.fw.impl.data.SubsetSize import SubsetSizeCategorizer, \
    SubsetSizeOrderer
from kdvs.fw.Categorizer import NOTCATEGORIZED

unittest = resolve_unittest()

class MockDataset(object):
    def __init__(self, name, rows):
        self.name = name
        self.rows = rows

class TestSubsetSizeCategorizer1(unittest.TestCase):

    def setUp(self):
        self.size_thr = 50
        self.ds1 = (MockDataset('Data1', ['row'] * 99), MockDataset('Data2', ['row'] * 9))
        self.exp_cat1 = ['>', '<=']
        self.ds2 = [MockDataset('Data%d' % i, ['row'] * (i + 1)) for i in range(99)]
        self.exp_cat2 = ['>' if i >= self.size_thr else '<=' for i in range(99)]
        self.ds3 = (MockDataset('Data1', '*'), MockDataset('Data2', ['row'] * 9))
        self.exp_cat3 = [NOTCATEGORIZED, '<=']
        self.ds4 = (MockDataset('Data1', '*'), MockDataset('Data2', '*'))
        self.exp_cat4 = [NOTCATEGORIZED, NOTCATEGORIZED]

    def test_init1(self):
        sc = SubsetSizeCategorizer(self.size_thr)
        self.assertItemsEqual(['>', '<='], sc.categories())

    def test_categorize1(self):
        sc = SubsetSizeCategorizer(self.size_thr)
        categories = [sc.categorize(ds) for ds in self.ds1]
        self.assertSequenceEqual(self.exp_cat1, categories)

    def test_categorize2(self):
        sc = SubsetSizeCategorizer(self.size_thr)
        categories = [sc.categorize(ds) for ds in self.ds2]
        self.assertSequenceEqual(self.exp_cat2, categories)

    def test_categorize3(self):
        sc = SubsetSizeCategorizer(self.size_thr)
        categories = [sc.categorize(ds) for ds in self.ds3]
        self.assertSequenceEqual(self.exp_cat3, categories)

    def test_categorize4(self):
        sc = SubsetSizeCategorizer(self.size_thr)
        categories = [sc.categorize(ds) for ds in self.ds4]
        self.assertSequenceEqual(self.exp_cat4, categories)

class TestSubsetSizeOrderer1(unittest.TestCase):

    def setUp(self):
        self.size_thr = 50
        self.pkc2ss1 = (('Data1', 99), ('Data2', 9))
        self.exp_ordering1_desc = [('Data1', 99), ('Data2', 9)]
        self.exp_ordering1_asc = [('Data2', 9), ('Data1', 99)]
        self.pkc2ss2 = [('Data%d' % i, i + 1) for i in range(98, -1, -1)]
        self.exp_ordering2_asc = [('Data%d' % i, i + 1) for i in range(99)]
        self.exp_ordering2_desc = [('Data%d' % i, i + 1) for i in range(98, -1, -1)]

    def test_init1(self):
        so = SubsetSizeOrderer()
        self.assertTrue(hasattr(so, 'descending'))
        self.assertTrue(so.descending)

    def test_init2(self):
        so = SubsetSizeOrderer(descending=False)
        self.assertTrue(hasattr(so, 'descending'))
        self.assertFalse(so.descending)

    def test_build1(self):
        so = SubsetSizeOrderer()
        so.build(self.pkc2ss1)
        self.assertSequenceEqual(self.exp_ordering1_desc, so.ordering)

    def test_build2(self):
        so = SubsetSizeOrderer(descending=False)
        so.build(self.pkc2ss1)
        self.assertSequenceEqual(self.exp_ordering1_asc, so.ordering)

    def test_order1(self):
        so = SubsetSizeOrderer()
        so.build(self.pkc2ss2)
        self.assertSequenceEqual(self.exp_ordering2_desc, so.order())

    def test_order2(self):
        so = SubsetSizeOrderer(descending=False)
        so.build(self.pkc2ss2)
        self.assertSequenceEqual(self.exp_ordering2_asc, so.order())
