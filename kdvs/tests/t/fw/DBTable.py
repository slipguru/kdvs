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
from kdvs.core.error import Error
from kdvs.core.util import quote
from kdvs.fw.DBTable import DBTable, DBTemplate
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import itertools
import os
import re
import string
import warnings
try:
    import numpy
    numpyFound = True
except ImportError:
    numpyFound = False
from kdvs.tests.utils import check_min_numpy_version

unittest = resolve_unittest()

class TestDBTable1(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm = None

    def testDBT_init1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname)
        self.assertFalse(dt1.isCreated())

    def testDBT_init2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols)
        self.assertFalse(dt1.isCreated())
        self.assertIsNotNone(re.match('DBTable[a-f0-9]{16}', dt1.name))

    def testDBT_init3(self):
        with self.assertRaises(Error):
            DBTable(None, self.testdb, self.test_cols)

    def testDBT_init4(self):
        with self.assertRaises(Error):
            DBTable(self.dbm, None, self.test_cols)

    def testDBT_init5(self):
        with self.assertRaises(Error):
            DBTable(self.dbm, self.testdb, None)

    def testDBT_init6(self):
        with self.assertRaises(Error):
            DBTable(self.dbm, self.testdb, '30000000')

    def testDBT_init7(self):
        with self.assertRaises(Error):
            DBTable(self.dbm, self.testdb, 300000)

    def testDBT_init8(self):
        with self.assertRaises(Error):
            DBTable(self.dbm, self.testdb, self.test_cols, id_col='AAAAA')


class TestDBTable2(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.test_dtname2 = 'Test2'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def testDBT_create1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        # low level checks
        cs = dt1.db.cursor()
        ref_cols = self.test_cols
        # check that columns are proper
        cs.execute('pragma table_info(%s);' % self.test_dtname1)
        res = cs.fetchall()
        cols = [str(c[1]) for c in res]
        self.assertSequenceEqual(ref_cols, cols)
        # check that indexes were created properly
        for c in ref_cols:
            idx = '%s__%s' % (dt1.name, c)
            cs.execute('select name from sqlite_master where type="index" and name="%s"' % idx)
            res = cs.fetchone()
            if res:
                iname = str(res[0])
                self.assertEqual(idx, iname)
            else:
                self.fail()

    def testDBT_create2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create(indexed_columns=('A',))
        self.assertTrue(dt1.isCreated())
        # low level checks
        cs = dt1.db.cursor()
        ref_cols = self.test_cols
        ref_indexed_cols = ('A')
        ref_nonindexed_cols = list(set(ref_cols) - set(ref_indexed_cols))
        # check that requested indexes were created properly
        for c in ref_indexed_cols:
            idx = '%s__%s' % (dt1.name, c)
            cs.execute('select name from sqlite_master where type="index" and name="%s"' % idx)
            res = cs.fetchone()
            if res:
                iname = str(res[0])
                self.assertEqual(idx, iname)
            else:
                self.fail()
        # check that remaining indexes do not exist
        for c in ref_nonindexed_cols:
            idx = '%s__%s' % (dt1.name, c)
            cs.execute('select name from sqlite_master where type="index" and name="%s"' % idx)
            res = cs.fetchone()
            self.assertIsNone(res)

    def testDBT_create3(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        statements = dt1.create(debug=True)
        self.assertFalse(dt1.isCreated())
        ref_statements = ['create table "Test1" ("A" TEXT,"B" TEXT,"C" TEXT)',
                          'create index "Test1__A" on "Test1"("A")',
                          'create index "Test1__B" on "Test1"("B")',
                          'create index "Test1__C" on "Test1"("C")']
        self.assertSequenceEqual(ref_statements, statements)

    def testDBT_create4(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        statements = dt1.create(indexed_columns=('A',), debug=True)
        self.assertFalse(dt1.isCreated())
        ref_statements = ['create table "Test1" ("A" TEXT,"B" TEXT,"C" TEXT)',
                          'create index "Test1__A" on "Test1"("A")']
        self.assertSequenceEqual(ref_statements, statements)

    def testDBT_create5(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt2 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname2)
        dt2.create()
        self.assertTrue(dt2.isCreated())
        # low level checks
        cs = dt1.db.cursor()
        for dt in (self.test_dtname1, self.test_dtname2):
            cs.execute('pragma table_info(%s);' % dt)
            cols = [str(c[1]) for c in cs.fetchall()]
            self.assertSequenceEqual(self.test_cols, cols)

    def testDBT_create6(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt2 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        self.assertTrue(dt2.isCreated())
        with self.assertRaises(Error):
            dt2.create()

class TestDBTable3(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def testDBT_load1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load()
        # low level checks
        cs = dt1.db.cursor()
        cs.execute('select count(*) from %s' % self.test_dtname1)
        cnt = int(cs.fetchone()[0])
        self.assertEqual(0, cnt)

    def testDBT_load2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        def __gen_load2():
            nums = range(1, len(self.test_cols) + 1)
            for l in string.ascii_uppercase:
                yield tuple(["%s%s" % (l, n) for n in nums])
        statements = dt1.load(content=__gen_load2(), debug=True)
        # compare statements
        ref_statements = []
        nums = range(1, len(self.test_cols) + 1)
        for l in string.ascii_uppercase:
            vals = ','.join([quote("%s%s" % (l, n)) for n in nums])
            st = 'insert into %s values (%s)' % (quote(self.test_dtname1), vals)
            ref_statements.append(st)
        self.assertSequenceEqual(ref_statements, statements)

    def testDBT_load3(self):
        cols = list(itertools.chain(('ID',), self.test_cols))
        dt1 = DBTable(self.dbm, self.testdb, cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        # load from generator
        def __gen_load3():
            nums = range(1, len(self.test_cols) + 1)
            for ix, l in enumerate(string.ascii_uppercase):
                ytp = ["%s%s" % (l, n) for n in nums]
                ytp.insert(0, str(ix + 1))
                yield ytp
        dt1.load(content=__gen_load3(), debug=False)
        # low level checks
        cs = dt1.db.cursor()
        cs.execute('select ID from %s' % self.test_dtname1)
        ids = [int(r[0]) for r in cs.fetchall()]
        isum = sum(ids)
        ref_sum = sum(range(1, len(string.ascii_uppercase) + 1))
        self.assertEqual(ref_sum, isum)

    def testDBT_load4(self):
        cols = list(itertools.chain(('ID',), self.test_cols))
        dt1 = DBTable(self.dbm, self.testdb, cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        # load from two consecutive generators under common ID
#        idgen=itertools.count(start=1)
        idgen = itertools.count(1)
        nums = range(1, len(self.test_cols) + 1)
        def __gen_load4_1():
            for l in string.ascii_lowercase:
                ytp = ["%s%s" % (l, n) for n in nums]
                ytp.insert(0, str(idgen.next()))
                yield ytp
        def __gen_load4_2():
            for l in string.ascii_uppercase:
                ytp = ["%s%s" % (l, n) for n in nums]
                ytp.insert(0, str(idgen.next()))
                yield ytp
        dt1.load(content=__gen_load4_1())
        dt1.load(content=__gen_load4_2())
        # low level checks
        cs = dt1.db.cursor()
        cs.execute('select ID from %s' % self.test_dtname1)
        ids = [int(r[0]) for r in cs.fetchall()]
        isum = sum(ids)
        ref_sum = sum(range(1, len(string.ascii_uppercase) + len(string.ascii_lowercase) + 1))
        self.assertEqual(ref_sum, isum)

    def testDBT_count1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        cnt = dt1.countRows()
        # low level checks
        cs = dt1.db.cursor()
        cs.execute('select count(*) from %s' % self.test_dtname1)
        refcnt = int(cs.fetchone()[0])
        self.assertEqual(refcnt, cnt)

    def testDBT_count2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        def __gen_count2():
            nums = range(1, len(self.test_cols) + 1)
            for l in string.ascii_uppercase:
                yield tuple(["%s%s" % (l, n) for n in nums])
        dt1.load(content=__gen_count2())
        cnt = dt1.countRows()
        self.assertEqual(len(string.ascii_uppercase), cnt)

class TestDBTable4(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def __gen_get1(self):
        nums = range(1, len(self.test_cols) + 1)
        for l in string.ascii_uppercase:
            yield tuple(["%s%s" % (l, n) for n in nums])

    def testDBT_get1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        statements = dt1.get(debug=True)
        ref_statements = ['select * from "Test1"']
        self.assertSequenceEqual(ref_statements, statements)

    def testDBT_get2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        statements = dt1.get(columns=('B',), debug=True)
        ref_statements = ['select "B" from "Test1"']
        self.assertSequenceEqual(ref_statements, statements)

    def testDBT_get3(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        with self.assertRaises(Error):
            dt1.get(columns='AAAAA', debug=True)

    def testDBT_get4(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        rcs = dt1.get()
        res = list(rcs)
        self.assertSequenceEqual([], res)

    def testDBT_get5(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        rcs = dt1.get(columns=('AAAAAAA',))
        res = list(rcs)
        self.assertSequenceEqual([], res)

    def testDBT_get6(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get from all columns all rows
        rcs = dt1.get()
        res = list(rcs)
        self.assertEqual(set((len(self.test_cols),)), set([len(r) for r in res]))
        for cidx in range(len(self.test_cols)):
            col = [r[cidx] for r in res]
            ref_col = [u"%s%d" % (l, cidx + 1) for l in string.ascii_uppercase]
            self.assertSequenceEqual(ref_col, col)

    def testDBT_get7(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get from subset of columns all rows
        rcs = dt1.get(columns=('B',))
        res = list(rcs)
        self.assertEqual(set((1,)), set([len(r) for r in res]))
        col = [r[0] for r in res]
        ref_col = [u"%s%d" % (l, 2) for l in string.ascii_uppercase]
        self.assertSequenceEqual(ref_col, col)

    def testDBT_get8(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get from all columns subset of rows
        rids = 'BGPZ'
        rows_subset = ["%s1" % l for l in rids]
        rcs = dt1.get(rows=rows_subset)
        res = list(rcs)
        # reference results
        ref_res = []
        for rid in rids:
            rtup = tuple([u"%s%d" % (rid, n) for n in range(1, len(self.test_cols) + 1)])
            ref_res.append(rtup)
        self.assertEqual(ref_res, res)

    def testDBT_get9(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get from subset of columns subset of rows
        cols_subset = ('B', 'C')
        rids = 'BGPZ'
        rows_subset = ["%s1" % l for l in rids]
        cidxs = (1, 2)
        ref_subset = []
        for rid in rids:
            rtup = tuple([u"%s%d" % (rid, ci + 1) for ci in cidxs])
            ref_subset.append(rtup)
        rcs = dt1.get(columns=cols_subset, rows=rows_subset)
        res = list(rcs)
        self.assertSequenceEqual(ref_subset, res)

    def testDBT_get10(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        with self.assertRaises(Error):
            dt1.get(columns=3000000)
        with self.assertRaises(Error):
            dt1.get(rows=3000000)
        with self.assertRaises(Error):
            dt1.get(columns=3000000, rows=3000000)

class TestDBTable5(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def __gen(self):
        nums = range(1, len(self.test_cols) + 1)
        for l in string.ascii_uppercase:
            yield tuple(["%s%s" % (l, n) for n in nums])

    def testDBT_isEmpty1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        self.assertTrue(dt1.isEmpty())

    def testDBT_isEmpty2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen())
        self.assertFalse(dt1.isEmpty())

class TestDBTable6(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def __gen(self):
        nums = range(1, len(self.test_cols) + 1)
        for l in string.ascii_uppercase:
            yield tuple(["%s%s" % (l, n) for n in nums])

    def testDBT_getIDs1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        self.assertFalse(dt1.isCreated())
        with self.assertRaises(Error):
            dt1.getIDs()

    def testDBT_getIDs2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        rcs = dt1.getIDs()
        ids = list(rcs)
        ref_ids = []
        self.assertEqual(ref_ids, ids)

    def testDBT_getIDs3(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        dt1.load(self.__gen())
        rcs = dt1.getIDs()
        ids = list(rcs)
        ref_ids = ["%s1" % l for l in string.ascii_uppercase]
        self.assertEqual(ref_ids, ids)

class TestDBTable7(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def __gen_get1(self):
        nums = range(1, len(self.test_cols) + 1)
        for l in string.ascii_uppercase:
            yield tuple(["%s%s" % (l, n) for n in nums])

    def testDBT_getAll1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get all results as list
        res = dt1.getAll()
        self.assertEqual(set((len(self.test_cols),)), set([len(r) for r in res]))
        for cidx in range(len(self.test_cols)):
            col = [r[cidx] for r in res]
            ref_col = [u"%s%d" % (l, cidx + 1) for l in string.ascii_uppercase]
            self.assertSequenceEqual(ref_col, col)

    def testDBT_getAll2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get all results as dict (on cols)
        res = dt1.getAll(as_dict=True)
        self.assertEqual(set(self.test_cols), set(res.keys()))
        for cidx, c in enumerate(self.test_cols):
            vals = res[c]
            ref_vals = [u"%s%d" % (l, cidx + 1) for l in string.ascii_uppercase]
            self.assertSequenceEqual(ref_vals, vals)

    def testDBT_getAll3(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get all results as dict (on rows)
        res = dt1.getAll(as_dict=True, dict_on_rows=True)
        ref_keys = [u"%s1" % (l) for l in string.ascii_uppercase]
        self.assertEqual(set(ref_keys), set(res.keys()))
        for l in string.ascii_uppercase:
            ref_content = [u"%s%d" % (l, cidx + 1) for cidx in range(len(self.test_cols))]
            ref_key = ref_content[0]
            ref_vals = ref_content[1:]
            self.assertIn(ref_key, res)
            self.assertSequenceEqual(ref_vals, res[ref_key])

    def testDBT_getAll4(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # test debug output
        statements = dt1.getAll(debug=True)
        ref_statements = ['select * from "Test1"']
        self.assertSequenceEqual(ref_statements, statements)


@unittest.skipUnless(numpyFound, 'numpy not found')
class TestDBTable8(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('ID', 'A', 'B', 'C')
        self.test_col_idxs = range(1, len(self.test_cols))
        self.test_row_ids = ('ID1', 'ID2', 'ID3')
        self.test_row_idxs = range(1, len(self.test_row_ids) + 1)
        self.test_dtname1 = 'Test1'
        self.test_array = numpy.array([[1., 2., 3.], [4., 5., 6.], [7., 8., 9.]])
        self.test_row_ids_2 = ('1', '2', '3')
        self.test_row_idxs_2 = range(1, len(self.test_row_ids_2) + 1)
        self.test_array_2 = numpy.array([[1., 1., 2., 3.], [2., 4., 5., 6.], [3., 7., 8., 9.]])

        self.test_cols_3 = self.test_cols[:-2]
        self.test_array_3 = numpy.array([1., 4., 7.]).reshape((1, -1))

        self.test_rows_4 = ('1',)
        self.test_array_4 = numpy.array([1., 2., 3.]).reshape((1, -1))

        self.test_array_5 = numpy.array([1.]).reshape((1, -1))

        self.test_cols_only_id = ('ID',)
        self.test_array_only_id = numpy.array([]).reshape((1, -1))

        self.test_array_only_id_present = numpy.array([1., 2., 3.]).reshape((1, -1))

# TODO:
        self.filter_clause_grthan_5 = ' and '.join(['cast("%s" as real)>=5.0' % c for c in self.test_cols[1:]])
        self.test_array_grthan_5 = numpy.array([7., 8., 9.]).reshape((1, -1))

        self.dbm = DBManager(self.test_write_root)

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        os.remove(db1_path)
        os.remove(rootdb_path)
        self.dbm = None

    def __gen_get1(self):
        for row_idx, rid in zip(self.test_row_idxs, self.test_row_ids):
            row = list()
            row.append(rid)
            for col in self.test_col_idxs:
                row.append(float(((row_idx - 1) * len(self.test_col_idxs)) + col))
            yield tuple(row)

    def __gen_get2(self):
        for row_idx, rid in zip(self.test_row_idxs_2, self.test_row_ids_2):
            row = list()
            row.append(rid)
            for col in self.test_col_idxs:
                row.append(float(((row_idx - 1) * len(self.test_col_idxs)) + col))
            yield tuple(row)

    def testDBT_getArray1(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get default array
        res = dt1.getArray()
        numpy.testing.assert_array_equal(self.test_array, res)

    def testDBT_getArray2(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # get array but do not remove ID column
        # we cannot because ID column contains strings not convertible to numericals
        with self.assertRaises(Error):
            dt1.getArray(remove_id_col=False)

    def testDBT_getArray3(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array but do not remove ID column
        # now we can because ID column contains numerical strings
        res = dt1.getArray(remove_id_col=False)
        numpy.testing.assert_array_equal(self.test_array_2, res)

    def testDBT_getArray4(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array without some last columns
        res = dt1.getArray(columns=self.test_cols_3)
        numpy.testing.assert_array_equal(self.test_array_3, res)

    def testDBT_getArray5(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array without some last rows
        res = dt1.getArray(rows=self.test_rows_4)
        numpy.testing.assert_array_equal(self.test_array_4, res)

    def testDBT_getArray6(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array without some last columns and last rows
        res = dt1.getArray(columns=self.test_cols_3, rows=self.test_rows_4)
        numpy.testing.assert_array_equal(self.test_array_5, res)

    def testDBT_getArray7(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # NOTE: before numpy 1.6.0, empty file in loadtxt() generates IOError,
        # with 1.6.0+ only warning
        if check_min_numpy_version(1, 6, 0):
            # get array with only ID column that is removed by default
            # we also suppress numpy warning of empty input file (since we are getting empty array)
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                res = dt1.getArray(columns=self.test_cols_only_id)
                numpy.testing.assert_array_equal(self.test_array_only_id, res)
        else:
            with self.assertRaises(Error):
                dt1.getArray(columns=self.test_cols_only_id)

    def testDBT_getArray8(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array with only ID column that is not removed
        res = dt1.getArray(columns=self.test_cols_only_id, remove_id_col=False)
        numpy.testing.assert_array_equal(self.test_array_only_id_present, res)

    def testDBT_getArray9(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array with all columns and use SQL filter clause
        # we look for all numbers in the same row greater than 5.0
        # we should receive the last row
        res = dt1.getArray(filter_clause=self.filter_clause_grthan_5)
        numpy.testing.assert_array_equal(self.test_array_grthan_5, res)

    def testDBT_getArray10(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get2())
        # get array with all columns and use SQL filter clause
        # we pass wrongly formulated filter clause
        with self.assertRaises(Error):
            dt1.getArray(filter_clause='XXXXX')

    def testDBT_getArray11(self):
        dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname1)
        dt1.create()
        self.assertTrue(dt1.isCreated())
        dt1.load(self.__gen_get1())
        # test debug output
        statements = dt1.getArray(debug=True)
        ref_statements = ['select * from "Test1"']
        self.assertSequenceEqual(ref_statements, statements)

class TestDBTable9(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname1 = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        self.test_cols = ('A', 'B', 'C')
        self.test_id_column = 'A'
        self.test_indexes = ()
        self.dbt_template1 = {'name' : self.test_dtname1,
                              'columns' : self.test_cols,
                              'id_column' : self.test_id_column,
                              'indexes' : self.test_indexes}
        self.dbt_template2 = {}

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        try:
            os.remove(db1_path)
        except OSError:
            pass
        os.remove(rootdb_path)
        self.dbm = None

    def testDBT_fromTemplate1(self):
        dbt_template1 = DBTemplate(self.dbt_template1)
        dt1 = DBTable.fromTemplate(self.dbm, self.testdb, dbt_template1)
        self.assertFalse(dt1.isCreated())

    def testDBT_fromTemplate2(self):
        with self.assertRaises(Error):
            DBTable.fromTemplate(self.dbm, self.testdb, self.dbt_template2)

class TestDBTemplate1(unittest.TestCase):

    def setUp(self):
        self.test_dtname1 = 'Test1'
        self.test_cols = ('A', 'B', 'C')
        self.test_cols_bad = 'XXXXX'
        self.test_id_column = 'A'
        self.test_indexes1 = ()
        self.test_indexes2 = ('B',)
        self.extra_data_key = 'extradata'
        self.extra_data = 'YYYYY'
        self.dbt_template1 = {'name' : self.test_dtname1,
                              'columns' : self.test_cols,
                              'id_column' : self.test_id_column,
                              'indexes' : self.test_indexes1}
        self.dbt_template2 = {'name' : self.test_dtname1,
                              'columns' : self.test_cols,
                              'indexes' : self.test_indexes1}
        self.dbt_template3 = {'name' : self.test_dtname1,
                              'columns' : self.test_cols,
                              'id_column' : self.test_id_column,
                              'indexes' : self.test_indexes1,
                              self.extra_data_key : self.extra_data}
        self.dbt_template4 = {'name' : self.test_dtname1,
                              'columns' : self.test_cols_bad,
                              'id_column' : self.test_id_column,
                              'indexes' : self.test_indexes1}

    def test_init1(self):
        dbt1 = DBTemplate(self.dbt_template1)
        self.assertEqual(self.test_dtname1, dbt1['name'])
        self.assertEqual(self.test_cols, dbt1['columns'])
        self.assertEqual(self.test_id_column, dbt1['id_column'])
        self.assertEqual(self.test_indexes1, dbt1['indexes'])

    def test_init2(self):
        with self.assertRaises(Error):
            DBTemplate(self.dbt_template2)

    def test_init3(self):
        dbt1 = DBTemplate(self.dbt_template3)
        self.assertEqual(self.test_dtname1, dbt1['name'])
        self.assertEqual(self.test_cols, dbt1['columns'])
        self.assertEqual(self.test_id_column, dbt1['id_column'])
        self.assertEqual(self.test_indexes1, dbt1['indexes'])
        self.assertEqual(self.extra_data, dbt1[self.extra_data_key])

    def test_init4(self):
        with self.assertRaises(Error):
            DBTemplate(self.dbt_template4)
