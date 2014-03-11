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
from kdvs.fw.Job import Job
from kdvs.fw.Stat import Results, RESULTS_RUNTIME_KEY
from kdvs.fw.impl.job.SimpleJob import SimpleJobExecutor
from kdvs.fw.impl.stat.L1L2 import L1L2_OLS, L1L2_L1L2, L1L2_RLS
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import csv
import numpy
import os
import types
try:
    import l1l2py
    l1l2pyFound = True
except ImportError:
    l1l2pyFound = False

unittest = resolve_unittest()


class MockL1L2_OLS(L1L2_OLS):
    # wrong version number
    version = 'XXXXX'


@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_OLS1(unittest.TestCase):

    def setUp(self):
        self.l1l2_ols_cfg1 = {
            'error_func' : l1l2py.tools.balanced_classification_error,
            'return_predictions' : True,
            'global_degrees_of_freedom' : None,
            'job_importable' : False,
            }
        self.ref_results_elements = ['Classification Error', 'Selection', 'Predictions', 'Beta', 'CM MCC']
        self.l1l2_ols_cfgX1 = {
            'error_func' : l1l2py.tools.balanced_classification_error,
            'return_predictions' : True,
            'global_degrees_of_freedom' : None,
            # missing parameter
            }
        self.l1l2_ols_cfgX2 = {
            'error_func' : l1l2py.tools.balanced_classification_error,
            'return_predictions' : True,
            'global_degrees_of_freedom' : None,
            'job_importable' : False,
            # extra parameter
            'extra_par' : 'XXXXX',
            }

    def test_init0(self):
        with self.assertRaises(Error):
            MockL1L2_OLS(**self.l1l2_ols_cfg1)

    def test_init1(self):
        t = L1L2_OLS(**self.l1l2_ols_cfg1)
        self.assertTrue(hasattr(t, 'techdata'))
        self.assertEqual({}, t.techdata)
        self.assertSequenceEqual(self.ref_results_elements, t.results_elements)
        self.assertEqual(self.l1l2_ols_cfg1, t.parameters)

    def test_init2(self):
        with self.assertRaises(Error):
            L1L2_OLS(**self.l1l2_ols_cfgX1)

    def test_init3(self):
        with self.assertRaises(Error):
            L1L2_OLS(**self.l1l2_ols_cfgX2)


@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_OLS2(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.example_real_data_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_data.dsv'))
        self.example_real_labels_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_labels.dsv'))
        self.example_real_samples_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_samples.dsv'))
        self.data = numpy.loadtxt(self.example_real_data_path)
        self.labels = numpy.loadtxt(self.example_real_labels_path)
        with open(self.example_real_samples_path, 'rb') as f:
            self.samples = [s for s in csv.reader(f)]
        self.ref_data_shape = (30, 20)
        self.ref_labels_shape = (20,)
        self.l1l2_ols_cfg1 = {
            'error_func' : l1l2py.tools.balanced_classification_error,
            'return_predictions' : True,
            'global_degrees_of_freedom' : None,
            'job_importable' : False,
            }
        self.ssname1 = 'SS1'
        self.initial_additionalJobData1 = {
            'samples' : self.samples
            }
        self.additionalJobData1 = {
            'depfuncs' : (),
            'modules' : ['os', 'l1l2py', 'numpy'],
            'samples' : self.samples
            }
        self.runtime1 = {'techID' : 'TECH_ID_OLS'}
        self.runtime2 = {}
        # taken from default_cfg.py
        self.default_null_dof = 'dof0'
        self.ref_beta_shape = (30, 1)
        self.ref_cls_error = {self.default_null_dof : 0.0}

    def test_createJob1(self):
        t = L1L2_OLS(**self.l1l2_ols_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels, self.initial_additionalJobData1)
        self.assertIsInstance(jobGen, types.GeneratorType)
        jid, job = jobGen.next()
        self.assertIsNotNone(jid)
        self.assertIsInstance(job, Job)
        ref_ajd = self.additionalJobData1
        ajd = job.additional_data
        self.assertItemsEqual(ref_ajd.keys(), ajd.keys())
        for k in ref_ajd.keys():
            self.assertItemsEqual(ref_ajd[k], ajd[k])

    def test_produceResults1(self):
        t = L1L2_OLS(**self.l1l2_ols_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels, self.initial_additionalJobData1)
        _, job = jobGen.next()
        jobContainer = SimpleJobExecutor([job])
        jobContainer.run()
        exc = jobContainer.close()
        self.assertEqual([], exc)
        jr = jobContainer.getJobResults()
        self.assertEqual(1, len(jr))
        beta, error, labels, labels_predicted = jr[0]
        self.assertEqual(self.data.shape[0], len(beta))
        numpy.testing.assert_almost_equal(error, 0.0)
        numpy.testing.assert_equal(self.labels, labels)
        self.assertEqual(self.labels.shape[0], len(labels_predicted))
        # emulate normal way of resolving degrees of freedom
        t.parameters['global_degrees_of_freedom'] = (self.default_null_dof,)
        # provide standard runtime data
        res1 = t.produceResults(self.ssname1, [job], self.runtime1)
        self.assertIsInstance(res1, Results)
        self.assertEqual(self.ref_beta_shape, res1['Beta'].shape)
        self.assertEqual(self.ref_cls_error, res1['Classification Error'])
        self.assertEqual(self.ssname1, res1['SubsetID'])
        for rk, rv in self.runtime1.iteritems():
            self.assertIn(rk, res1[RESULTS_RUNTIME_KEY])
            self.assertEqual(rv, res1[RESULTS_RUNTIME_KEY][rk])
        # provide empty runtime data
        with self.assertRaises(KeyError):
            t.produceResults(self.ssname1, [job], self.runtime2)
        # other errors
        with self.assertRaises(KeyError):
            res1['XXXXX']
        with self.assertRaises(Error):
            res1['XXXXX'] = 111

    def test_produceResults2(self):
        t = L1L2_OLS(**self.l1l2_ols_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels)
        _, job = jobGen.next()
        with self.assertRaises(Error):
            t.produceResults(self.ssname1, [job, job], self.runtime1)


@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_L1L2_1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.example_real_data_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_data.dsv'))
        self.example_real_labels_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_labels.dsv'))
        self.example_real_samples_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_samples.dsv'))
        self.data = numpy.loadtxt(self.example_real_data_path)
        self.labels = numpy.loadtxt(self.example_real_labels_path)

        self.labels = numpy.sign(self.labels)

        with open(self.example_real_samples_path, 'rb') as f:
            self.samples = [s for s in csv.reader(f)]
        self.ref_data_shape = (30, 20)
        self.ref_labels_shape = (20,)

        self.external_k = 5
        self.internal_k = 4

        self.l1l2_l1l2_cfg1 = {
            # external splits
            'external_k' : self.external_k,
            # internal splits
            'internal_k' : self.internal_k,
            # tau min, max, number, range
            'tau_min_scale' : 1. / 3,
            'tau_max_scale' : 1. / 8,
            'tau_number' : 10,
            'tau_range_type' : 'geometric',
             # mu min, max, number, range
            'mu_scaling_factor_min' : 0.005,
            'mu_scaling_factor_max' : 1,
            'mu_number' : 3,
            'mu_range_type' : 'geometric',
             # lambda min, max, number, range
            'lambda_min' : 1e-1,
            'lambda_max' : 1e4,
            'lambda_range_type' : 'geometric',
            'lambda_number' : 15,
             # specific lambda range if desired, None otherwise
            'lambda_range' : None,
            # error functions
            'error_func' : l1l2py.tools.balanced_classification_error,
            'cv_error_func' : l1l2py.tools.balanced_classification_error,
            # sparse/regularized solution (mutually exclusive)
            'sparse' : True,
            'regularized' : False,
            # normalizers
            'data_normalizer' : l1l2py.tools.center,
            'labels_normalizer' : None,
            # return predictions?
            'return_predictions' : True,
            # here to use mu_number value
            'global_degrees_of_freedom' : tuple(['mu%d' % i for i in range(3)]),
            # placeholder for external splits
            'ext_split_sets' : None,
            # is job importable for remote job containers?
            'job_importable' : False,
        }
        self.ssname1 = 'SS1'
        self.initial_additionalJobData1 = {
            'samples' : self.samples
            }

        self.additionalJobData1 = list()
        for i in range(self.external_k):
            jd = {
                'depfuncs' : (),
                'modules' : ('os', 'l1l2py', 'numpy'),
                'samples' : self.samples,
                'ext_split' : i,
                'ssname' : self.ssname1,
                'calls' : None,
                'data_shape' : self.data.shape,
                'labels' : self.labels,
            }
            self.additionalJobData1.append(jd)
        self.additionalJobData_comparables = [
            'depfuncs', 'modules', 'samples', 'ext_split', 'ssname',
            'data_shape', 'labels'
            ]
        self.runtime1 = {'techID' : 'TECH_ID_L1L2'}

    def test_createJob1(self):
        t = L1L2_L1L2(**self.l1l2_l1l2_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels, self.initial_additionalJobData1)
        self.assertIsInstance(jobGen, types.GeneratorType)
        for (jid, job), ref_ajd in zip(jobGen, self.additionalJobData1):
            self.assertIsNotNone(jid)
            self.assertIsInstance(job, Job)
            ajd = job.additional_data
            self.assertItemsEqual(ref_ajd.keys(), ajd.keys())
            for k in self.additionalJobData_comparables:
                try:
                    self.assertItemsEqual(ref_ajd[k], ajd[k])
                except TypeError:
                    self.assertEqual(ref_ajd[k], ajd[k])

    def test_produceResults1(self):
        t = L1L2_L1L2(**self.l1l2_l1l2_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels, self.initial_additionalJobData1)
        jps = [jp for jp in jobGen]
        jobs = [jp[1] for jp in jps]

        jobContainer = SimpleJobExecutor(jobs)
        jobContainer.run()
        exc = jobContainer.close()
        self.assertEqual([], exc)
        outputs = jobContainer.getJobResults()
        results = t.produceResults(self.ssname1, jobs, self.runtime1)

        mvec = [[0 for _ in range(30)], [0 for _ in range(30)], [0 for _ in range(30)]]

        for m in range(3):
            for i in range(self.external_k):
                vv = outputs[i]['selected_list'][m]
                for idx in range(len(vv)):
                    if vv[idx]:
                        mvec[m][idx] += 1
        for m in range(3):
            for idx in range(len(mvec[m])):
                mvec[m][idx] = float(mvec[m][idx]) / float(self.external_k)

        for m in range(3):
            v1 = mvec[m]
            v2 = results['MuExt']['freqs'][m]
            for val1, val2 in zip(v1, v2):
                self.assertEqual(float(val1), float(val2))

@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_RLS_1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.example_real_data_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_data.dsv'))
        self.example_real_labels_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_labels.dsv'))
        self.example_real_samples_path = os.path.abspath(os.path.join(self.test_data_root, 'example_real_samples.dsv'))
        self.data = numpy.loadtxt(self.example_real_data_path)
        self.labels = numpy.loadtxt(self.example_real_labels_path)
        self.labels = numpy.sign(self.labels)
        with open(self.example_real_samples_path, 'rb') as f:
            self.samples = [s for s in csv.reader(f)]
        self.ref_data_shape = (30, 20)
        self.ref_labels_shape = (20,)
        self.external_k = 5
        self.internal_k = 4

        self.l1l2_rls_cfg1 = {
            # external splits
            'external_k' : self.external_k,
             # lambda min, max, number, range
            'lambda_min' : 1e-1,
            'lambda_max' : 1e4,
            'lambda_range_type' : 'geometric',
            'lambda_number' : 15,
             # specific lambda range if desired, None otherwise
            'lambda_range' : None,
            # error function(s)
            'error_func' : l1l2py.tools.balanced_classification_error,
            # normalizers
            'data_normalizer' : l1l2py.tools.center,
            'labels_normalizer' : None,
            # return predictions?
            'return_predictions' : True,
            # ---- global parameters
            # use null DOF
            'global_degrees_of_freedom' : None,
            # placeholder for external splits
            'ext_split_sets' : None,
            # ---- job related parameters
            # is job importable for remote job containers?
#                'job_importable' : True,
            'job_importable' : False,
        }
        self.ssname1 = 'SS1'
        self.initial_additionalJobData1 = {
            'samples' : self.samples
            }
        self.additionalJobData1 = {
            'depfuncs' : (),
            'modules' : ('l1l2py', 'numpy', 'os'),
            'external_k' : self.external_k,
            'ext_split_sets' : None,
            'ssname' : self.ssname1,
            'calls' : None,
            'data_shape' : self.data.shape,
            'samples' : self.samples,
            'labels' : self.labels,
        }
        self.additionalJobData_comparables = [
            'depfuncs', 'modules', 'samples', 'ext_split_sets', 'ssname',
            'data_shape', 'labels'
            ]
        self.runtime1 = {'techID' : 'TECH_ID_RLS'}
        self.default_null_dof = 'dof0'

    def test_createJob1(self):
        t = L1L2_RLS(**self.l1l2_rls_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels, self.initial_additionalJobData1)
        self.assertIsInstance(jobGen, types.GeneratorType)
        jid, job = jobGen.next()
        self.assertIsNotNone(jid)
        self.assertIsInstance(job, Job)
        ref_ajd = self.additionalJobData1
        ajd = job.additional_data
        self.assertItemsEqual(ref_ajd.keys(), ajd.keys())
        for k in self.additionalJobData_comparables:
            try:
                self.assertItemsEqual(ref_ajd[k], ajd[k])
            except TypeError:
                self.assertEqual(ref_ajd[k], ajd[k])

    def test_produceResults1(self):
        t = L1L2_RLS(**self.l1l2_rls_cfg1)
        jobGen = t.createJob(self.ssname1, self.data, self.labels, self.initial_additionalJobData1)
        jps = [jp for jp in jobGen]
        jobs = [jp[1] for jp in jps]
        # emulate normal way of resolving degrees of freedom
        t.parameters['global_degrees_of_freedom'] = (self.default_null_dof,)
        jobContainer = SimpleJobExecutor(jobs)
        jobContainer.run()
        exc = jobContainer.close()
        self.assertEqual([], exc)
        outputs = jobContainer.getJobResults()
        results = t.produceResults(self.ssname1, jobs, self.runtime1)
        self.assertIsNotNone(outputs)
        self.assertIsNotNone(results)
