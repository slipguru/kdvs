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
from kdvs.fw.DSV import DSV
from kdvs.fw.Stat import Labels, Results, Technique, calculateConfusionMatrix, \
    calculateMCC, RESULTS_SUBSET_ID_KEY, RESULTS_PLOTS_ID_KEY, \
    RESULTS_RUNTIME_KEY
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import numpy
import numpy as np
import os

unittest = resolve_unittest()

class TestLabels1(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.sample_data_root = self.test_write_root
        self.testdb = 'DB1'
        self.dbm = DBManager(self.sample_data_root)
        #
        self.test_dtname1 = 'LABELS1'
        self.lab1_dsv_path = os.path.abspath(os.path.join(self.test_data_root, 'labels1.dsv'))
        self.lab1_fh = DSV.getHandle(self.lab1_dsv_path, 'rb')
        self.lab1_dsv = DSV(self.dbm, self.testdb, self.lab1_fh, dtname=self.test_dtname1)
        self.lab1_dsv.create()
        self.lab1_dsv.loadAll()
        self.lab1_dsv.close()
        self.lab1_cnt = {'A1': '1', 'A2': '1', 'A3': '1', 'A4': '1', 'B1': '-1', 'B2': '-1', 'B3': '-1', 'B4': '-1', }
        self.lab1_samples1 = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        self.lab1_resp1 = ['1', '1', '1', '1', '-1', '-1', '-1', '-1']
        self.lab1_samples_resp1 = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        self.lab1_samples2 = ['B4', 'B3', 'B2', 'B1', 'A4', 'A3', 'A2', 'A1']
        self.lab1_resp2 = ['-1', '-1', '-1', '-1', '1', '1', '1', '1']
        self.lab1_samples_resp2 = ['B4', 'B3', 'B2', 'B1', 'A4', 'A3', 'A2', 'A1']
        self.lab1_samples3 = ['A1', 'B1', 'A2', 'B2', 'A3', 'B3', 'A4', 'B4']
        self.lab1_resp3 = ['1', '-1', '1', '-1', '1', '-1', '1', '-1']
        self.lab1_samples_resp3 = ['A1', 'B1', 'A2', 'B2', 'A3', 'B3', 'A4', 'B4']
        self.lab1_samples4 = ['A1', 'B1', 'B4', 'A3']
        self.lab1_resp4 = ['1', '-1', '-1', '1']
        self.lab1_samples_resp4 = ['A1', 'B1', 'B4', 'A3']
        self.lab1_samples5 = ['A1', 'B1', None, 'A3']
        self.lab1_resp5 = ['1', '-1', '1']
        self.lab1_samples_resp5 = ['A1', 'B1', 'A3']
        self.lab1_samples6 = ['A1', 'XXX1', 'B4' 'QQQ7546dsfsdfs453']
        self.lab1_resp6 = ['1']
        self.lab1_samples_resp6 = ['A1']
        #
        self.test_dtname2 = 'LABELS2'
        self.lab2_dsv_path = os.path.abspath(os.path.join(self.test_data_root, 'labels2.dsv'))
        self.lab2_fh = DSV.getHandle(self.lab2_dsv_path, 'rb')
        self.lab2_dsv = DSV(self.dbm, self.testdb, self.lab2_fh, dtname=self.test_dtname2)
        self.lab2_dsv.create()
        self.lab2_dsv.loadAll()
        self.lab2_dsv.close()
        self.lab2_cntN = {'A1': '1', 'A2': '1', 'A3': '1', 'A4': '1',
                       'B1': '-1', 'B2': '-1', 'B3': '-1', 'B4': '-1',
                       'PP': '0', 'QQ': '0', 'RR': '0', 'SS': '0'}
        self.lab2_cntY = {'A1': '1', 'A2': '1', 'A3': '1', 'A4': '1',
                        'B1': '-1', 'B2': '-1', 'B3': '-1', 'B4': '-1'}
        self.lab2_samples_order1 = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        self.lab2_samples_resp1 = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']
        self.lab2_samples_order2 = ['A1', 'A2', 'QQ', 'A3', 'A4', 'SS', 'B1', 'B2', 'B3', 'RR', 'B4', 'PP']
        self.lab2_samples_resp2 = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4']

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm = None

    def test_init1(self):
        lab = Labels(self.lab1_dsv)
        self.assertEqual(self.lab1_cnt, lab.labels)
        self.assertEqual('0', lab.unused_sample_label)

    def test_init2(self):
        lab = Labels(self.lab1_dsv, unused_sample_label='XXX')
        self.assertEqual('XXX', lab.unused_sample_label)
        self.assertEqual(self.lab1_cnt, lab.labels)

    def test_getLabels1(self):
        lab = Labels(self.lab1_dsv)
        resp1 = lab.getLabels(self.lab1_samples1)
        self.assertEqual(self.lab1_resp1, resp1)
        resp2 = lab.getLabels(self.lab1_samples2)
        self.assertEqual(self.lab1_resp2, resp2)
        resp3 = lab.getLabels(self.lab1_samples3)
        self.assertEqual(self.lab1_resp3, resp3)
        resp4 = lab.getLabels(self.lab1_samples4)
        self.assertEqual(self.lab1_resp4, resp4)
        resp5 = lab.getLabels(self.lab1_samples5)
        self.assertEqual(self.lab1_resp5, resp5)
        resp6 = lab.getLabels(self.lab1_samples6)
        self.assertEqual(self.lab1_resp6, resp6)

    def test_getLabels2(self):
        lab = Labels(self.lab1_dsv)
        resp1 = lab.getLabels(self.lab1_samples1, as_array=True)
        num1 = np.array([float(l) for l in self.lab1_resp1])
        np.testing.assert_array_equal(resp1, num1)
        resp2 = lab.getLabels(self.lab1_samples2, as_array=True)
        num2 = np.array([float(l) for l in self.lab1_resp2])
        np.testing.assert_array_equal(resp2, num2)
        resp3 = lab.getLabels(self.lab1_samples3, as_array=True)
        num3 = np.array([float(l) for l in self.lab1_resp3])
        np.testing.assert_array_equal(resp3, num3)
        resp4 = lab.getLabels(self.lab1_samples4, as_array=True)
        num4 = np.array([float(l) for l in self.lab1_resp4])
        np.testing.assert_array_equal(resp4, num4)
        resp5 = lab.getLabels(self.lab1_samples5, as_array=True)
        num5 = np.array([float(l) for l in self.lab1_resp5])
        np.testing.assert_array_equal(resp5, num5)
        resp6 = lab.getLabels(self.lab1_samples6, as_array=True)
        num6 = np.array([float(l) for l in self.lab1_resp6])
        np.testing.assert_array_equal(resp6, num6)

    def test_getLabels3(self):
        lab = Labels(self.lab2_dsv)
        self.assertNotEqual(self.lab2_cntN, lab.labels)
        self.assertEqual(self.lab2_cntY, lab.labels)
        resp1 = lab.getLabels(self.lab1_samples1)
        self.assertEqual(self.lab1_resp1, resp1)
        resp2 = lab.getLabels(self.lab1_samples2)
        self.assertEqual(self.lab1_resp2, resp2)
        resp3 = lab.getLabels(self.lab1_samples3)
        self.assertEqual(self.lab1_resp3, resp3)
        resp4 = lab.getLabels(self.lab1_samples4)
        self.assertEqual(self.lab1_resp4, resp4)
        resp5 = lab.getLabels(self.lab1_samples5)
        self.assertEqual(self.lab1_resp5, resp5)
        resp6 = lab.getLabels(self.lab1_samples6)
        self.assertEqual(self.lab1_resp6, resp6)

    def test_getLabels4(self):
        lab = Labels(self.lab2_dsv)
        resp1 = lab.getLabels(self.lab1_samples1, as_array=True)
        num1 = np.array([float(l) for l in self.lab1_resp1])
        np.testing.assert_array_equal(resp1, num1)
        resp2 = lab.getLabels(self.lab1_samples2, as_array=True)
        num2 = np.array([float(l) for l in self.lab1_resp2])
        np.testing.assert_array_equal(resp2, num2)
        resp3 = lab.getLabels(self.lab1_samples3, as_array=True)
        num3 = np.array([float(l) for l in self.lab1_resp3])
        np.testing.assert_array_equal(resp3, num3)
        resp4 = lab.getLabels(self.lab1_samples4, as_array=True)
        num4 = np.array([float(l) for l in self.lab1_resp4])
        np.testing.assert_array_equal(resp4, num4)
        resp5 = lab.getLabels(self.lab1_samples5, as_array=True)
        num5 = np.array([float(l) for l in self.lab1_resp5])
        np.testing.assert_array_equal(resp5, num5)
        resp6 = lab.getLabels(self.lab1_samples6, as_array=True)
        num6 = np.array([float(l) for l in self.lab1_resp6])
        np.testing.assert_array_equal(resp6, num6)

    def test_getSamples1(self):
        lab1 = Labels(self.lab1_dsv)
        samples1 = lab1.getSamples(self.lab1_samples1)
        self.assertEqual(self.lab1_samples_resp1, samples1)
        samples2 = lab1.getSamples(self.lab1_samples2)
        self.assertEqual(self.lab1_samples_resp2, samples2)
        samples3 = lab1.getSamples(self.lab1_samples3)
        self.assertEqual(self.lab1_samples_resp3, samples3)
        samples4 = lab1.getSamples(self.lab1_samples4)
        self.assertEqual(self.lab1_samples_resp4, samples4)
        samples5 = lab1.getSamples(self.lab1_samples5)
        self.assertEqual(self.lab1_samples_resp5, samples5)
        samples6 = lab1.getSamples(self.lab1_samples6)
        self.assertEqual(self.lab1_samples_resp6, samples6)

    def test_getSamples2(self):
        lab2 = Labels(self.lab2_dsv)
        samples1 = lab2.getSamples(self.lab2_samples_order1)
        self.assertEqual(self.lab2_samples_resp1, samples1)
        samples2 = lab2.getSamples(self.lab2_samples_order2)
        self.assertEqual(self.lab2_samples_resp2, samples2)

class TestResults1(unittest.TestCase):

    def setUp(self):
        self.ss1 = 'S1'
        self.res1 = ('R1', 'R2', 'R3', 'R4',)
        self.r1 = { 'R1' : 1, 'R2' : 2, 'R3' : 3, 'R4' : 4}
        self.r2 = { 'R1' : 1, 'R2' : 2 }
        self.rxkey = 'XXXX'
        self.rxval = 9999

    def test_init1(self):
        r = Results(self.ss1)
        self.assertTrue(len(r._elements) == 0)
        self.assertIn(RESULTS_SUBSET_ID_KEY, r._results)
        self.assertIn(RESULTS_PLOTS_ID_KEY, r._results)
        self.assertIn(RESULTS_RUNTIME_KEY, r._results)
        self.assertEqual(self.ss1, r[RESULTS_SUBSET_ID_KEY])
        self.assertEqual({}, r[RESULTS_PLOTS_ID_KEY])
        self.assertEqual({}, r[RESULTS_RUNTIME_KEY])

    def test_init2(self):
        r = Results(self.ss1, self.res1)
        self.assertEqual(self.ss1, r[RESULTS_SUBSET_ID_KEY])
        self.assertSequenceEqual(self.res1, r._elements)
        for rk, rv in self.r1.iteritems():
            r[rk] = rv
        for rk in self.res1:
            self.assertEqual(self.r1[rk], r[rk])

    def test_init3(self):
        r = Results(self.ss1, self.res1)
        self.assertEqual(self.ss1, r[RESULTS_SUBSET_ID_KEY])
        self.assertSequenceEqual(self.res1, r._elements)
        for rk, rv in self.r2.iteritems():
            r[rk] = rv
        for rk in self.r2.keys():
            self.assertEqual(self.r2[rk], r[rk])

    def test_init4(self):
        r = Results(self.ss1, self.res1)
        self.assertEqual(self.ss1, r[RESULTS_SUBSET_ID_KEY])
        with self.assertRaises(Error):
            r[self.rxkey] = self.rxval

class TestTechnique1(unittest.TestCase):

    def setUp(self):
        self.par1 = ('P1', 'P2', 'P3', 'P4')
        self.p1 = { 'P1' : 1, 'P2' : 2, 'P3' : 3, 'P4' : 4}
        self.p2 = { 'P1' : 1, 'P2' : 2 }
        self.p3 = { 'P1' : 1, 'P2' : 2, 'P3' : 3, 'P4' : 4, 'P5' : 5}
        self.ss1 = 'S1'
        self.empty_array = numpy.array([]).reshape((1, 0))
        self.runtime1 = {}

    def test_init1(self):
        with self.assertRaises(Error):
            Technique(self.par1)

    def test_init2(self):
        with self.assertRaises(Error):
            Technique(self.par1, **self.p2)

    def test_init3(self):
        with self.assertRaises(Error):
            Technique(self.par1, **self.p3)

    def test_init4(self):
        t = Technique(self.par1, **self.p1)
        self.assertEqual(self.p1, t.parameters)
        self.assertEqual({}, t.techdata)
        self.assertEqual([], t.results_elements)

    def test_createJob1(self):
        t = Technique(self.par1, **self.p1)
        with self.assertRaises(Error):
            t.createJob(self.ss1, 'XXXXX', 'XXXXX')

    def test_createJob2(self):
        t = Technique(self.par1, **self.p1)
        with self.assertRaises(Error):
            t.createJob(self.ss1, self.empty_array, 'XXXXX')

    def test_createJob3(self):
        t = Technique(self.par1, **self.p1)
        with self.assertRaises(Error):
            t.createJob(self.ss1, 'XXXXX', self.empty_array)

    def test_createJob4(self):
        t = Technique(self.par1, **self.p1)
        j = t.createJob(self.ss1, self.empty_array, self.empty_array)
        self.assertIsNone(j)

    def test_produceResults1(self):
        t = Technique(self.par1, **self.p1)
        j = t.createJob(self.ss1, self.empty_array, self.empty_array)
        # not available in superclass
        with self.assertRaises(NotImplementedError):
            t.produceResults(self.ss1, j, self.runtime1)


class TestStatUtils1(unittest.TestCase):

    def setUp(self):
        self.lab1 = [1, 1, 1, 1, -1, -1, -1, -1]
        self.l1_self_ccm = (4, 4, 0, 0)
        self.l1_self_mcc = 1.0
        self.lab2 = [1, 1, 1, 1, 1, 1, 1, 1]
        self.l1_l2_ccm = (4, 0, 4, 0)
        self.l1_l2_mcc = 0.0
        self.lab3 = [-1, -1, -1, -1, 1, 1, 1, 1]
        self.l1_l3_ccm = (0, 0, 4, 4)
        self.l1_l3_mcc = -1.0
        self.lab4 = [0, 0, 0, 0, 0, 0, 0, 0]
        self.lab5 = ['1', '1', '1', '1', '-1', '-1', '-1', '-1']
        self.l5_self_ccm = (4, 4, 0, 0)
        self.lab6 = ['1', '1', '1', '1', '1', '1', '1', '1']
        self.l5_l6_ccm = (4, 0, 4, 0)

    def test_calculateConfusionMatrix1(self):
        l1_self_ccm = calculateConfusionMatrix(self.lab1, self.lab1)
        self.assertEqual(self.l1_self_ccm, l1_self_ccm)
        l1_l2_ccm = calculateConfusionMatrix(self.lab1, self.lab2)
        self.assertEqual(self.l1_l2_ccm, l1_l2_ccm)
        l1_l3_ccm = calculateConfusionMatrix(self.lab1, self.lab3)
        self.assertEqual(self.l1_l3_ccm, l1_l3_ccm)

    def test_calculateConfusionMatrix2(self):
        with self.assertRaises(Error):
            calculateConfusionMatrix(self.lab1, self.lab4)
        with self.assertRaises(Error):
            calculateConfusionMatrix(self.lab1, self.lab4, positive_label=0)
        with self.assertRaises(Error):
            calculateConfusionMatrix(self.lab1, self.lab4, negative_label=0)
        with self.assertRaises(Error):
            calculateConfusionMatrix(self.lab1, self.lab5)

    def test_calculateConfusionMatrix3(self):
        l5_self_ccm = calculateConfusionMatrix(self.lab5, self.lab5, positive_label='1', negative_label='-1')
        self.assertEqual(self.l5_self_ccm, l5_self_ccm)
        l5_l6_ccm = calculateConfusionMatrix(self.lab5, self.lab6, positive_label='1', negative_label='-1')
        self.assertEqual(self.l5_l6_ccm, l5_l6_ccm)

    def test_calculateMCC1(self):
        l1_self_ccm = calculateConfusionMatrix(self.lab1, self.lab1)
        l1_self_mcc = calculateMCC(*l1_self_ccm)
        self.assertAlmostEqual(self.l1_self_mcc, l1_self_mcc)
        l1_l2_ccm = calculateConfusionMatrix(self.lab1, self.lab2)
        l1_l2_mcc = calculateMCC(*l1_l2_ccm)
        self.assertAlmostEqual(self.l1_l2_mcc, l1_l2_mcc)
        l1_l3_ccm = calculateConfusionMatrix(self.lab1, self.lab3)
        l1_l3_mcc = calculateMCC(*l1_l3_ccm)
        self.assertAlmostEqual(self.l1_l3_mcc, l1_l3_mcc)
