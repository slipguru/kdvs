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

from kdvs.fw.Report import Reporter, DEFAULT_REPORTER_PARAMETERS
from kdvs.fw.StorageManager import StorageManager
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import itertools
import os
import shutil

unittest = resolve_unittest()


class TestReporter1(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.reportname1 = 'report1'
        self.refparams1 = ()
        self.refparams2 = ('param1', 'param2', 'param3')
        self.reportparams1 = {}
        self.reportparams2 = {'param1' : 'val1', 'param2' : None, 'param3' : 7000}
        self.resloc1 = 'res1'
        self.addata1 = {}
        self.repdir1 = os.path.join(self.test_write_root, self.resloc1)

    def test_init1(self):
        rep1 = Reporter(self.refparams1, **self.reportparams1)
        self.assertEqual(self.reportparams1, rep1.parameters)
        self.assertEqual(0, len(rep1.getReports()))
        self.assertIsNone(rep1.getAdditionalData())

    def test_init2(self):
        rep2 = Reporter(self.refparams2, **self.reportparams2)
        self.assertEqual(self.reportparams2, rep2.parameters)

    def test_initialize1(self):
        sm = StorageManager(root_path=self.test_write_root)
        rep1 = Reporter(self.refparams1, **self.reportparams1)
        rep1.initialize(sm, self.resloc1, self.addata1)
        self.assertEqual(self.addata1, rep1.getAdditionalData())

    def test_finalize1(self):
        sm = StorageManager(root_path=self.test_write_root)
        rep1 = Reporter(self.refparams1, **self.reportparams1)
        rep1.initialize(sm, self.resloc1, self.addata1)
        self.assertEqual(0, len(rep1.getReports()))
        rep1.finalize()
        with self.assertRaises(OSError):
            os.listdir(self.repdir1)


class TestReporter2(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.reportname1 = 'report1'
        self.reportname2 = 'report2'
        self.reportcontent1 = ['line%d -- %s\n' % (i, '*' * 80) for i in range(100)]
        self.reportcontent2 = []
        self.refparams1 = ()
        self.reportparams1 = {}
        self.reportparams2 = {'param1' : 'val1', 'param2' : None, 'param3' : 7000}
        self.resloc1 = 'res1'
        self.addata1 = {}
        self.repdir1 = os.path.join(self.test_write_root, self.resloc1)
        self.reploc1 = 'rep1'
        self.reploc2 = 'rep2'
        self.reppath1 = os.path.join(self.test_write_root, self.resloc1, self.reploc1)
        self.reppath2 = os.path.join(self.test_write_root, self.resloc1, self.reploc2)

    def tearDown(self):
        sm_path = os.path.join(self.test_write_root, self.resloc1)
        shutil.rmtree(sm_path)

    def test_openReport1(self):
        sm = StorageManager(root_path=self.test_write_root)
        rep1 = Reporter(self.refparams1, **self.reportparams1)
        rep1.initialize(sm, self.resloc1, self.addata1)
        rep1.openReport(self.reploc1, self.reportcontent1)
        rep1.finalize()
        self.assertTrue(os.path.exists(self.reppath1))
        self.assertTrue(1, len(os.listdir(self.repdir1)))

    def test_openReport2(self):
        sm = StorageManager(root_path=self.test_write_root)
        rep1 = Reporter(self.refparams1, **self.reportparams1)
        rep1.initialize(sm, self.resloc1, self.addata1)
        rep1.openReport(self.reploc1, self.reportcontent1)
        rep1.openReport(self.reploc2, self.reportcontent2)
        rep1.finalize()
        self.assertTrue(os.path.exists(self.reppath1))
        self.assertTrue(os.path.exists(self.reppath2))
        self.assertTrue(2, len(os.listdir(self.repdir1)))

