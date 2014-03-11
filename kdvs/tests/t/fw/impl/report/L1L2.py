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

from kdvs.fw.StorageManager import StorageManager
from kdvs.fw.impl.job.SimpleJob import SimpleJobExecutor
from kdvs.fw.impl.report.L1L2 import L1L2_VarFreq_Reporter, \
    L1L2_VarCount_Reporter
from kdvs.fw.impl.stat.L1L2 import L1L2_OLS
from kdvs.fw.impl.stat.PKCSelector import \
    OuterSelector_ClassificationErrorThreshold, \
    InnerSelector_ClassificationErrorThreshold_AllVars
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import csv
import numpy
import os
import shutil
try:
    import l1l2py
    l1l2pyFound = True
except ImportError:
    l1l2pyFound = False

unittest = resolve_unittest()

class Mock_em2annotation(dict):
    def __getitem__(self, _):
        return [''] * 7

@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_VarFreq_Reporter1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.data_range = range(1, 6)
        self.skiprows = 1
        self.data_usecols = range(1, 11)
        self.labels_usecols = (1,)
        self.data = list()
        for d in self.data_range:
            data_path = os.path.abspath(os.path.join(self.test_data_root, 'l1l2_t2_data%d.txt' % d))
            self.data.append(numpy.loadtxt(data_path, skiprows=self.skiprows, usecols=self.data_usecols, delimiter='\t'))
        labels_path = os.path.join(self.test_data_root, 'l1l2_t2_labels.txt')
        self.labels = numpy.loadtxt(labels_path, skiprows=self.skiprows, usecols=self.labels_usecols)
        with open(labels_path, 'rb') as f:
            self.samples = [r['Samples'] for r in csv.DictReader(f, dialect='excel-tab')]
        self.ref_data_shape = (30, 10)
        self.ref_labels_shape = (10,)
        self.dof = 'DOF'
        self.l1l2_ols_cfg1 = {
            'error_func' : l1l2py.tools.balanced_classification_error,
            'return_predictions' : True,
            'global_degrees_of_freedom' : [self.dof],
            'job_importable' : False,
            }
        self.ssname1 = ['SS%d' % i for i in self.data_range]
        self.pkcid1 = ['SS%d' % i for i in self.data_range]
        self.vars1 = ['M%d' % i for i in range(1, 31)]
        self.initial_additionalJobData1 = {
            'samples' : self.samples,
            }
        self.additionalJobData1 = {
            'depfuncs' : (),
            'modules' : ['os', 'l1l2py', 'numpy'],
            }
        self.runtime1 = {'techID' : 'TECH_ID_OLS'}
        self.additionalReportData1 = {'em2annotation' : Mock_em2annotation()}
        self.storageManager1 = StorageManager(root_path=self.test_write_root)
        self.ssloc1 = 'ss'
        self.reporter_name_part = '_vars_freqs.txt'
        self.reports_loc1 = os.path.join(self.test_write_root, self.ssloc1)
        self.reports_names1 = ['%s_%s_%s' % (ss, self.dof, self.reporter_name_part) for ss in self.ssname1]
        self.reports_paths1 = [os.path.join(self.reports_loc1, ss, rname) for ss, rname in zip(self.ssname1, self.reports_names1)]

    def tearDown(self):
        if os.path.exists(self.reports_loc1):
            shutil.rmtree(self.reports_loc1)

    def test_L1L2_VarFreq_Reporter_1(self):
        t = L1L2_OLS(**self.l1l2_ols_cfg1)
        jobs = list()
        for ds in self.data:
            jobGen = t.createJob(self.ssname1, ds, self.labels, self.initial_additionalJobData1)
            _, job = jobGen.next()
            jobs.append(job)
        jobContainer = SimpleJobExecutor(jobs)
        jobContainer.run()
        exc = jobContainer.close()
        self.assertEqual([], exc)
        results = list()
        ssIndResults = dict()
        subsets = dict()
        for ss, j in zip(self.ssname1, jobs):
            r = t.produceResults(ss, [j], self.runtime1)
            results.append(r)
            ssIndResults[ss] = r
            subsets[ss] = dict()
            subsets[ss]['vars'] = self.vars1
            subsets[ss]['mat'] = ss
        outerSel = OuterSelector_ClassificationErrorThreshold(**{'error_threshold' : 0.0})
        innerSel = InnerSelector_ClassificationErrorThreshold_AllVars()
        outerSel.perform(results)
        outerSelRes = dict([(ss, sor['Selection']['outer']) for (ss, sor) in zip(self.pkcid1, results)])
        innerSel.perform(outerSelRes, ssIndResults, subsets)
        reporter = L1L2_VarFreq_Reporter()
        reporter.initialize(self.storageManager1, self.ssloc1, self.additionalReportData1)
        reporter.produce(results)
        reporter.finalize()
        self.assertTrue(os.path.exists(self.reports_loc1))
        self.assertEqual(set(self.ssname1), set(os.listdir(self.reports_loc1)))
        for rp in self.reports_paths1:
            self.assertTrue(os.path.exists(rp))

@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_VarCount_Reporter1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.data_range = range(1, 6)
        self.skiprows = 1
        self.data_usecols = range(1, 11)
        self.labels_usecols = (1,)
        self.data = list()
        for d in self.data_range:
            data_path = os.path.abspath(os.path.join(self.test_data_root, 'l1l2_t2_data%d.txt' % d))
            self.data.append(numpy.loadtxt(data_path, skiprows=self.skiprows, usecols=self.data_usecols, delimiter='\t'))
        labels_path = os.path.join(self.test_data_root, 'l1l2_t2_labels.txt')
        self.labels = numpy.loadtxt(labels_path, skiprows=self.skiprows, usecols=self.labels_usecols)
        with open(labels_path, 'rb') as f:
            self.samples = [r['Samples'] for r in csv.DictReader(f, dialect='excel-tab')]
        self.ref_data_shape = (30, 10)
        self.ref_labels_shape = (10,)
        self.dof = 'DOF'
        self.l1l2_ols_cfg1 = {
            'error_func' : l1l2py.tools.balanced_classification_error,
            'return_predictions' : True,
            'global_degrees_of_freedom' : [self.dof],
            'job_importable' : False,
            }
        self.ssname1 = ['SS%d' % i for i in self.data_range]
        self.pkcid1 = ['SS%d' % i for i in self.data_range]
        self.vars1 = ['M%d' % i for i in range(1, 31)]
        self.initial_additionalJobData1 = {
            'samples' : self.samples,
            }
        self.additionalJobData1 = {
            'depfuncs' : (),
            'modules' : ['os', 'l1l2py', 'numpy'],
            }
        self.techID1 = 'TECH_ID_OLS'
        self.runtime1 = {'techID' : self.techID1}
        self.mock_technique2DOF = {self.techID1 : {'DOFs' : [self.dof]}}
        self.additionalReportData1 = {'em2annotation' : Mock_em2annotation(),
                                      'technique2DOF' : self.mock_technique2DOF,
                                      }
        self.storageManager1 = StorageManager(root_path=self.test_write_root)
        self.ssloc1 = 'ss'
        self.reporter_name_part_sel = 'vars_count_sel.txt'
        self.reporter_name_part_nsel = 'vars_count_nsel.txt'
        self.reports_loc1 = os.path.join(self.test_write_root, self.ssloc1)
        self.reports_names1 = ['%s_%s_%s' % (self.techID1, self.dof, self.reporter_name_part_sel),
                               '%s_%s_%s' % (self.techID1, self.dof, self.reporter_name_part_nsel)]
        self.reports_paths1 = [os.path.join(self.reports_loc1, rname) for rname in self.reports_names1]

    def tearDown(self):
        if os.path.exists(self.reports_loc1):
            shutil.rmtree(self.reports_loc1)

    def test_L1L2_VarCount_Reporter_1(self):
        t = L1L2_OLS(**self.l1l2_ols_cfg1)
        jobs = list()
        for ds in self.data:
            jobGen = t.createJob(self.ssname1, ds, self.labels, self.initial_additionalJobData1)
            _, job = jobGen.next()
            jobs.append(job)
        jobContainer = SimpleJobExecutor(jobs)
        jobContainer.run()
        exc = jobContainer.close()
        self.assertEqual([], exc)
        results = list()
        ssIndResults = dict()
        subsets = dict()
        for ss, j in zip(self.ssname1, jobs):
            r = t.produceResults(ss, [j], self.runtime1)
            results.append(r)
            ssIndResults[ss] = r
            subsets[ss] = dict()
            subsets[ss]['vars'] = self.vars1
            subsets[ss]['mat'] = ss
        outerSel = OuterSelector_ClassificationErrorThreshold(**{'error_threshold' : 0.0})
        innerSel = InnerSelector_ClassificationErrorThreshold_AllVars()
        outerSel.perform(results)
        outerSelRes = dict([(ss, sor['Selection']['outer']) for (ss, sor) in zip(self.pkcid1, results)])
        innerSel.perform(outerSelRes, ssIndResults, subsets)
        reporter = L1L2_VarCount_Reporter()
        reporter.initialize(self.storageManager1, self.ssloc1, self.additionalReportData1)
        reporter.produce(results)
        reporter.finalize()
        self.assertTrue(os.path.exists(self.reports_loc1))
        self.assertEqual(set(self.reports_names1), set(os.listdir(self.reports_loc1)))
        for rp in self.reports_paths1:
            self.assertTrue(os.path.exists(rp))


    # TODO: finish!

