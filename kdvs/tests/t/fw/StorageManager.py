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
from kdvs.core.error import Error
from kdvs.fw.StorageManager import StorageManager
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os
import shutil

unittest=resolve_unittest()

class TestFSStorageManager1(unittest.TestCase):

    def setUp(self):
        self.test_write_root=TEST_INVARIANTS['test_write_root']
        self.sample_data_root=self.test_write_root

    def tearDown(self):
        rootdb_path=os.path.abspath('%s/%s.root.db'%(self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)

    def test_init1(self):
        userdir=os.path.expanduser('~/.%s/'%(SYSTEM_NAME_LC))
        if os.path.exists(userdir):
            sm = StorageManager()
            self.assertEqual(1, len(sm.locations))
            self.assertRegexpMatches(sm.name, "[0-9a-f]{16}")
            self.assertRegexpMatches(sm.locations.keys()[0], 'ROOT_[0-9a-f]{16}')
            self.assertRegexpMatches(sm.locations.values()[0], os.path.abspath(userdir))
        else:
            self.skipTest('%s not present'%userdir)

    def test_init2(self):
        sm = StorageManager(root_path=self.sample_data_root)
        self.assertEqual(1, len(sm.locations))
        self.assertRegexpMatches(sm.name, "[0-9a-f]{16}")
        self.assertRegexpMatches(sm.locations.keys()[0], 'ROOT_[0-9a-f]{16}')
#        self.assertRegexpMatches(sm.locations.values()[0], os.path.abspath(self.sample_data_root))
        self.assertEqual(sm.locations.values()[0], os.path.abspath(self.sample_data_root))
        self.assertFalse(os.path.exists(os.path.join(self.sample_data_root, '%s.root.db'%SYSTEM_NAME_LC)))

    def test_init3(self):
        sname="StorageManager1"
        sm = StorageManager(name=sname, root_path=self.sample_data_root)
        self.assertEqual(sm.name, sname)

    def test_init4(self):
        sm = StorageManager(root_path=self.sample_data_root, create_dbm=True)
        self.assertEqual(1, len(sm.locations))
        self.assertRegexpMatches(sm.name, "[0-9a-f]{16}")
        self.assertRegexpMatches(sm.locations.keys()[0], 'ROOT_[0-9a-f]{16}')
#        self.assertRegexpMatches(sm.locations.values()[0], os.path.abspath(self.sample_data_root))
        self.assertEqual(sm.locations.values()[0], os.path.abspath(self.sample_data_root))
        self.assertTrue(os.path.exists(os.path.join(self.sample_data_root, '%s.root.db'%SYSTEM_NAME_LC)))
        self.assertEqual(os.path.abspath(self.sample_data_root), sm.dbm.abs_data_root)
        ref_keys=set(['memdb', '%s.root.db'%SYSTEM_NAME_LC])
        self.assertEqual(ref_keys, set(sm.dbm.db.keys()))
        sm.dbm.close()

class TestFSStorageManager2(unittest.TestCase):

    def setUp(self):
        self.test_write_root=TEST_INVARIANTS['test_write_root']
        self.sample_data_root=self.test_write_root
        self.sm0 = StorageManager(root_path=self.sample_data_root)
        self.locroot0='rootloc0'
        self.locroot0_path=os.path.abspath(os.path.join(self.sample_data_root, self.locroot0))
        self.sep0=self.sm0.sublocation_separator
        self.loc01='rootloc0%s1'%self.sep0
        self.loc01_path=os.path.abspath(os.path.join(self.sample_data_root, self.loc01))
        self.loc02='rootloc0%s2%sa%sbb'%(self.sep0, self.sep0, self.sep0)
        self.loc02_path=os.path.abspath(os.path.join(self.sample_data_root, self.loc02))
        self.loc02_sublocs=('rootloc0%s2'%self.sep0, 'rootloc0%s2%sa'%(self.sep0, self.sep0))

    def tearDown(self):
        if os.path.exists(self.locroot0_path):
            shutil.rmtree(self.locroot0_path)

    def test_createLocation1(self):
        self.assertIsNone(self.sm0.getLocation(self.locroot0))
        self.sm0.createLocation(self.locroot0)
        self.assertEqual(self.locroot0_path, self.sm0.getLocation(self.locroot0))
        self.assertTrue(os.path.exists(self.locroot0_path))

    def test_createLocation2(self):
        self.assertIsNone(self.sm0.getLocation(self.locroot0))
        self.sm0.createLocation(self.locroot0)
        self.assertIsNone(self.sm0.getLocation(self.loc01))
        self.sm0.createLocation(self.loc01)
        self.assertTrue(os.path.exists(self.locroot0_path))
        self.assertTrue(os.path.exists(self.loc01_path))
        self.assertEqual(self.locroot0_path, self.sm0.getLocation(self.locroot0))
        self.assertEqual(self.loc01_path, self.sm0.getLocation(self.loc01))

    def test_createLocation3(self):
        self.assertIsNone(self.sm0.getLocation(self.locroot0))
        self.sm0.createLocation(self.locroot0)
        self.assertIsNone(self.sm0.getLocation(self.loc01))
        self.sm0.createLocation(self.loc01)
        self.assertIsNone(self.sm0.getLocation(self.loc02))
        self.sm0.createLocation(self.loc02)
        self.assertTrue(os.path.exists(self.locroot0_path))
        self.assertTrue(os.path.exists(self.loc01_path))
        self.assertTrue(os.path.exists(self.loc02_path))
        self.assertEqual(self.locroot0_path, self.sm0.getLocation(self.locroot0))
        self.assertEqual(self.loc01_path, self.sm0.getLocation(self.loc01))
        self.assertEqual(self.loc02_path, self.sm0.getLocation(self.loc02))
        for sloc in self.loc02_sublocs:
            self.assertIn(sloc, self.sm0.locations.keys())

class TestFSStorageManager3(unittest.TestCase):

    def setUp(self):
        self.test_write_root=TEST_INVARIANTS['test_write_root']
        self.sample_data_root=self.test_write_root
        self.sm0 = StorageManager(root_path=self.sample_data_root)
        self.locroot0='rootloc0'
        self.locroot0_path=os.path.abspath(os.path.join(self.sample_data_root, self.locroot0))
        self.sep0=self.sm0.sublocation_separator
        self.loc01='rootloc0%s1'%self.sep0
        self.loc01_path=os.path.abspath(os.path.join(self.sample_data_root, self.loc01))
        self.loc02='rootloc0%s2%sa%sbb'%(self.sep0, self.sep0, self.sep0)
        self.loc02_path=os.path.abspath(os.path.join(self.sample_data_root, self.loc02))
        self.loc02_sublocs=('rootloc0%s2'%self.sep0, 'rootloc0%s2%sa'%(self.sep0, self.sep0))
        self.loc02_sublocs_paths={
            'rootloc0%s2'%self.sep0 : os.path.abspath(os.path.join(self.sample_data_root, 'rootloc0%s2'%self.sep0)),
            'rootloc0%s2%sa'%(self.sep0, self.sep0) : os.path.abspath(os.path.join(
                                                    self.sample_data_root, 'rootloc0%s2%sa'%(self.sep0, self.sep0))),
        }

    def tearDown(self):
        if os.path.exists(self.locroot0_path):
            shutil.rmtree(self.locroot0_path)

    def test_removeLocation1(self):
        with self.assertRaises(Error):
            self.sm0.removeLocation('AAA')

    def test_removeLocation2(self):
        self.assertIsNone(self.sm0.getLocation(self.locroot0))
        self.sm0.createLocation(self.locroot0)
        self.assertEqual(self.locroot0_path, self.sm0.getLocation(self.locroot0))
        self.assertTrue(os.path.exists(self.locroot0_path))
        self.sm0.removeLocation(self.locroot0)
        self.assertNotIn(self.locroot0, self.sm0.locations)
        self.assertIsNone(self.sm0.getLocation(self.locroot0))
        self.assertFalse(os.path.exists(self.locroot0_path))

    def test_removeLocation3(self):
        self.assertIsNone(self.sm0.getLocation(self.loc02))
        self.sm0.createLocation(self.loc02)
        self.assertTrue(os.path.exists(self.loc02_path))
        self.assertEqual(self.loc02_path, self.sm0.getLocation(self.loc02))
        for sloc in self.loc02_sublocs:
            self.assertIn(sloc, self.sm0.locations.keys())
        self.sm0.removeLocation(self.loc02, leafonly=True)
        self.assertNotIn(self.loc02, self.sm0.locations)
        self.assertIsNone(self.sm0.getLocation(self.loc02))
        self.assertFalse(os.path.exists(self.loc02_path))
        for sl, p in self.loc02_sublocs_paths.iteritems():
            self.assertIn(sl, self.sm0.locations)
            self.assertEqual(p, self.sm0.getLocation(sl))
            self.assertTrue(os.path.exists(p))

    def test_removeLocation4(self):
        self.assertIsNone(self.sm0.getLocation(self.loc02))
        self.sm0.createLocation(self.loc02)
        self.assertTrue(os.path.exists(self.loc02_path))
        self.assertEqual(self.loc02_path, self.sm0.getLocation(self.loc02))
        for sloc in self.loc02_sublocs:
            self.assertIn(sloc, self.sm0.locations.keys())
        self.sm0.removeLocation(self.loc02, leafonly=False)
        self.assertNotIn(self.loc02, self.sm0.locations)
        self.assertIsNone(self.sm0.getLocation(self.loc02))
        self.assertFalse(os.path.exists(self.loc02_path))
        for sl, p in self.loc02_sublocs_paths.iteritems():
            self.assertNotIn(sl, self.sm0.locations)
            self.assertNotEqual(p, self.sm0.getLocation(sl))
            self.assertFalse(os.path.exists(p))
