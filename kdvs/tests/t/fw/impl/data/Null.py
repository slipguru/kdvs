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
from kdvs.fw.impl.data.Null import NullCategorizer, NullOrderer

unittest = resolve_unittest()

class TestNullCategorizer1(unittest.TestCase):

    def test_init1(self):
        nc = NullCategorizer()
        self.assertSequenceEqual(['__all__'], nc.categories())

    def test_init2(self):
        nc = NullCategorizer(null_category='TestNC')
        self.assertSequenceEqual(['TestNC'], nc.categories())

    def test_init3(self):
        nc = NullCategorizer()
        mock_datasets = ('Data1', 'Data2')
        categories = [nc.categorize(ds) for ds in mock_datasets]
        exp_categories = [nc.NULL] * len(mock_datasets)
        self.assertSequenceEqual(exp_categories, categories)

class TestNullOrderer1(unittest.TestCase):

    def test_init1(self):
        no = NullOrderer()
        self.assertIsNone(no.ordering)

    def test_build1(self):
        mock_pkc2ss = (('SS1', 99), ('SS2', 9))
        no = NullOrderer()
        no.build(mock_pkc2ss)
        exp_ordering = (('SS1', 99), ('SS2', 9))
        self.assertSequenceEqual(exp_ordering, no.ordering)

    def test_order1(self):
        mock_pkc2ss = (('SS1', 99), ('SS2', 9))
        no = NullOrderer()
        no.build(mock_pkc2ss)
        ordering = no.order()
        exp_ordering = (('SS1', 99), ('SS2', 9))
        self.assertSequenceEqual(exp_ordering, ordering)
