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

from kdvs import SYSTEM_NAME_LC
from kdvs.core.db import DBManager
from kdvs.fw.DBShelve import DBShelve, DBSHELVE_TMPL
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os

unittest=resolve_unittest()

class TestDTShelve1(unittest.TestCase):

    def setUp(self):
        self.test_write_root=TEST_INVARIANTS['test_write_root']
        self.testdb='DB1'
        self.dbm=DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path=os.path.abspath('%s/%s.db'%(self.test_write_root, self.testdb))
        rootdb_path=os.path.abspath('%s/%s.root.db'%(self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm=None

    def test_init1(self):
        dtsh = DBShelve(self.dbm, self.testdb, None)
        self.assertSequenceEqual(DBSHELVE_TMPL['columns'], (dtsh.key, dtsh.val))

class TestDTShelve2(unittest.TestCase):

    def setUp(self):
        self.test_write_root=TEST_INVARIANTS['test_write_root']
        self.testdb='DB1'
        self.dbm=DBManager(self.test_write_root)
        self.dbsh = DBShelve(self.dbm, self.testdb, None)

    def tearDown(self):
        self.dbsh.clear()
        self.dbm.close()
        db1_path=os.path.abspath('%s/%s.db'%(self.test_write_root, self.testdb))
        rootdb_path=os.path.abspath('%s/%s.root.db'%(self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm=None

    def test_getset1(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        self.assertEqual('1', self.dbsh['A'])
        self.assertEqual('2', self.dbsh['B'])
        self.assertEqual('3', self.dbsh['C'])
        self.assertEqual(3, len(self.dbsh))

    def test_contains1(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        self.assertTrue('A' in self.dbsh)
        self.assertFalse('XXX' in self.dbsh)

    def test_del1(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        del self.dbsh['B']
        with self.assertRaises(KeyError):
            self.dbsh['B']
        self.assertSequenceEqual(['A', 'C'], self.dbsh.keys())
        self.assertSequenceEqual(['1', '3'], self.dbsh.values())

    def test_update1(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        self.dbsh.update(items=(('D', '4'), ('E', '5')))
        self.assertEqual(5, len(self.dbsh))
        self.assertEqual('4', self.dbsh['D'])
        self.assertEqual('5', self.dbsh['E'])

    def test_update2(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        self.dbsh.update({'D':'4', 'E':'5'})
        self.assertEqual(5, len(self.dbsh))
        self.assertEqual('4', self.dbsh['D'])
        self.assertEqual('5', self.dbsh['E'])

    def test_clear1(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        self.dbsh.clear()
        self.assertEqual(0, len(self.dbsh))
        with self.assertRaises(KeyError):
            self.dbsh['A']
            self.dbsh['B']
            self.dbsh['C']

    def test_view1(self):
        self.dbsh['A'] = '1'
        self.dbsh['B'] = '2'
        self.dbsh['C'] = '3'
        self.assertEqual({'A':'1', 'B':'2', 'C':'3'}, self.dbsh.view())
        self.dbsh.clear()
        self.assertEqual({}, self.dbsh.view())
