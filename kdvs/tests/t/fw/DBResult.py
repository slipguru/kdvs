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
from kdvs.fw.DBResult import DBResult
from kdvs.fw.DBTable import DBTable
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os
import string

unittest = resolve_unittest()

class TestDBResult1(unittest.TestCase):

    def __gen1(self):
        nums = range(1, len(self.test_cols) + 1)
        for l in string.ascii_uppercase:
            yield tuple(["%s%s" % (l, n) for n in nums])

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        self.dt1 = DBTable(self.dbm, self.testdb, self.test_cols, name=self.test_dtname)
        self.dt1.create()
        self.dt1.load(self.__gen1())
        self.rcs = self.dt1.db.cursor()

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm = None

    def testDBR_get1(self):
        self.rcs.execute('select * from %s' % self.test_dtname)
        dbr = DBResult(self.dt1, self.rcs)
        # get generator within cursor size limits
        res = list(dbr.get())
        ref_res = list(self.dt1.get())
        self.assertSequenceEqual(ref_res, res)

    def testDBR_get2(self):
        self.rcs.execute('select * from %s' % self.test_dtname)
        dbr = DBResult(self.dt1, self.rcs)
        # get all as iterable within cursor size limits
        res = dbr.getAll()
        ref_res = list(self.dt1.get())
        self.assertSequenceEqual(ref_res, res)

    def testDBR_get3(self):
        self.rcs.execute('select * from %s' % self.test_dtname)
        dbr = DBResult(self.dt1, self.rcs)
        # get all as iterable within cursor size limits
        res = dbr.getAll(as_dict=False, dict_on_rows=False)
        ref_res = list(self.dt1.get())
        self.assertSequenceEqual(ref_res, res)

    def testDBR_get4(self):
        self.rcs.execute('select * from %s' % self.test_dtname)
        dbr = DBResult(self.dt1, self.rcs)
        # get all as dict within cursor size limits, keyed on columns
        res = dbr.getAll(as_dict=True, dict_on_rows=False)
        ref_res = {}
        for ix, c in enumerate(self.test_cols):
            ref_res[c] = [u"%s%d" % (l, ix + 1) for l in string.ascii_uppercase]
        self.assertDictEqual(ref_res, res)

    def testDBR_get5(self):
        self.rcs.execute('select * from %s' % self.test_dtname)
        dbr = DBResult(self.dt1, self.rcs)
        # get all as dict within cursor size limits, keyed on rows
        res = dbr.getAll(as_dict=True, dict_on_rows=True)
        ref_res = {}
        numsuffs = ["%d" % (i[0] + 1) for i in enumerate(self.test_cols)]
        for l in string.ascii_uppercase:
            key = u'%s%s' % (l, numsuffs[0])
            vls = [u'%s%s' % (l, ns) for ns in numsuffs[1:]]
            if l not in ref_res:
                ref_res[key] = vls
        self.assertDictEqual(ref_res, res)

    def testDBR_get6(self):
        # generate 100x load
        for _ in range(99):
            self.dt1.load(self.__gen1())
        self.rcs.execute('select * from %s' % self.test_dtname)
        # get all as iterable with limited cursor size, 26 internal loops
        dbr = DBResult(self.dt1, self.rcs, rowbufsize=100)
        # get all results at once
        res = list(dbr.get())
        numsuffs = ["%d" % (i[0] + 1) for i in enumerate(self.test_cols)]
        ref_res = []
        for i in range(100):
            for l in string.ascii_uppercase:
                tup = tuple([u'%s%s' % (l, ns) for ns in numsuffs])
                ref_res.append(tup)
        self.assertSequenceEqual(ref_res, res)

    def testDBR_get7(self):
        # generate 100x load
        for _ in range(99):
            self.dt1.load(self.__gen1())
        self.rcs.execute('select * from %s' % self.test_dtname)
        # get all as iterable with limited cursor size, 3 internal loops
        dbr = DBResult(self.dt1, self.rcs, rowbufsize=1000)
        # get all results at once
        res = list(dbr.get())
        numsuffs = ["%d" % (i[0] + 1) for i in enumerate(self.test_cols)]
        ref_res = []
        for i in range(100):
            for l in string.ascii_uppercase:
                tup = tuple([u'%s%s' % (l, ns) for ns in numsuffs])
                ref_res.append(tup)
        self.assertSequenceEqual(ref_res, res)

    def testDBR_get8(self):
        # generate 100x load
        for _ in range(99):
            self.dt1.load(self.__gen1())
        self.rcs.execute('select * from %s' % self.test_dtname)
        # get all as iterable with limited cursor size, 26 internal loops
        dbr = DBResult(self.dt1, self.rcs, rowbufsize=100)
        def __gen():
            numsuffs = ["%d" % (i[0] + 1) for i in enumerate(self.test_cols)]
            for i in range(100):
                for l in string.ascii_uppercase:
                    tup = tuple([u'%s%s' % (l, ns) for ns in numsuffs])
                    yield tup
        ref_gen = __gen()
        # iterate over single results
        for rtup in dbr.get():
            self.assertEqual(ref_gen.next(), rtup)
