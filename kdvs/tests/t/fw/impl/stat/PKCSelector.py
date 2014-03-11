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

from kdvs.fw.Stat import Results, DEFAULT_RESULTS, \
    DEFAULT_CLASSIFICATION_RESULTS, DEFAULT_SELECTION_RESULTS, NOTSELECTED, SELECTED
from kdvs.fw.impl.stat.PKCSelector import \
    OuterSelector_ClassificationErrorThreshold, \
    InnerSelector_ClassificationErrorThreshold_AllVars, \
    InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq
from kdvs.tests import resolve_unittest, TEST_INVARIANTS

unittest = resolve_unittest()

class TestOuterSelector_ClassificationErrorThreshold1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.ssname1 = 'SS'
        self.dof = 'DOF'
        self.results_cfg = list()
        self.results_cfg.extend(DEFAULT_RESULTS)
        self.results_cfg.extend(DEFAULT_CLASSIFICATION_RESULTS)
        self.results_cfg.extend(DEFAULT_SELECTION_RESULTS)
        self.results1 = Results(self.ssname1, self.results_cfg)
        self.results1['Classification Error'] = {self.dof : 0.5}
        self.results1['Selection'] = dict()
        self.osel_cfg1 = {'error_threshold' : 0.0}
        self.osel_cfg2 = {'error_threshold' : 1.0}
        self.ref_selres1 = NOTSELECTED
        self.ref_selres2 = SELECTED

    def test_init1(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg1)
        self.assertEqual(self.osel_cfg1, osel.parameters)

    def test_perform1(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg1)
        osel.perform([self.results1])
        self.assertEqual(1, len(self.results1['Selection']['outer'].keys()))
        selres = self.results1['Selection']['outer'][self.dof]
        self.assertEqual(self.ref_selres1, selres)

    def test_perform2(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg2)
        osel.perform([self.results1])
        self.assertEqual(1, len(self.results1['Selection']['outer'].keys()))
        selres = self.results1['Selection']['outer'][self.dof]
        self.assertEqual(self.ref_selres2, selres)


class TestInnerSelector_ClassificationErrorThreshold_AllVars1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.ssname1 = 'SS'
        self.dof = 'DOF'
        self.results_cfg = list()
        self.results_cfg.extend(DEFAULT_RESULTS)
        self.results_cfg.extend(DEFAULT_CLASSIFICATION_RESULTS)
        self.results_cfg.extend(DEFAULT_SELECTION_RESULTS)
        self.results1 = Results(self.ssname1, self.results_cfg)
        self.results1['Classification Error'] = {self.dof : 0.5}
        self.results1['Selection'] = dict()
        self.vars1 = ['V%d' % i for i in range(5)]
        self.osel_cfg1 = {'error_threshold' : 0.0}
        self.osel_cfg2 = {'error_threshold' : 1.0}
        self.isel_cfg1 = {}
        self.ref_selres1 = NOTSELECTED
        self.ref_selres2 = SELECTED
        self.ref_innersel1 = {self.dof : {'sel_vars' : {}, 'nsel_vars' : dict([(v, {'pass' : True}) for v in self.vars1])}}
        self.ref_innersel2 = {self.dof : {'sel_vars' : dict([(v, {'pass' : True}) for v in self.vars1]), 'nsel_vars' : {}}}

    def test_init1(self):
        isel = InnerSelector_ClassificationErrorThreshold_AllVars(**self.isel_cfg1)
        self.assertEqual(self.isel_cfg1, isel.parameters)

    def test_perform1(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg1)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_AllVars(**self.isel_cfg1)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel1, self.results1['Selection']['inner'])

    def test_perform2(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg2)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_AllVars(**self.isel_cfg1)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel2, self.results1['Selection']['inner'])


class TestInnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.ssname1 = 'SS'
        self.dof = 'mu0'
        self.results_cfg = list()
        self.results_cfg.extend(DEFAULT_RESULTS)
        self.results_cfg.extend(DEFAULT_CLASSIFICATION_RESULTS)
        self.results_cfg.extend(DEFAULT_SELECTION_RESULTS)
        self.results_cfg.extend(('MuExt',))
        self.results1 = Results(self.ssname1, self.results_cfg)
        self.results1['Classification Error'] = {self.dof : 0.5}
        self.results1['Selection'] = dict()
        self.vars1 = ['V%d' % i for i in range(5)]
        self.results1['MuExt'] = dict()
        self.results1['MuExt']['freqs'] = dict()
        self.results1['MuExt']['freqs'][0] = [1.0, 1.0, 1.0, 0.0, 0.0]
        self.osel_cfg1 = {'error_threshold' : 0.0}
        self.osel_cfg2 = {'error_threshold' : 1.0}
        self.isel_cfg1 = {'frequency_threshold' : 0.0, 'pass_variables_for_nonselected_pkcs' : True}
        self.isel_cfg2 = {'frequency_threshold' : 1.0, 'pass_variables_for_nonselected_pkcs' : True}
        self.isel_cfg3 = {'frequency_threshold' : 0.0, 'pass_variables_for_nonselected_pkcs' : False}
        self.ref_selres1 = NOTSELECTED
        self.ref_selres2 = SELECTED
        self.ref_innerres_sel1 = {}
        self.ref_innerres_nsel1 = {
                            'V0': {'pass': True},
                            'V1': {'pass': True},
                            'V2': {'pass': True},
                            'V3': {'pass': True},
                            'V4': {'pass': True},
                            }
        self.ref_innerres_sel2 = {
                            'V0': {'freq': 1.0, 'pass': True},
                            'V1': {'freq': 1.0, 'pass': True},
                            'V2': {'freq': 1.0, 'pass': True},
                            }
        self.ref_innerres_nsel2 = {
                            'V3': {'freq': 0.0, 'pass': True},
                            'V4': {'freq': 0.0, 'pass': True},
                            }
        self.ref_innerres_sel3 = {}
        self.ref_innerres_nsel3 = {
                            'V0': {'pass': True},
                            'V1': {'pass': True},
                            'V2': {'pass': True},
                            'V3': {'pass': True},
                            'V4': {'pass': True},
                            }
        self.ref_innerres_sel4 = {
                            'V0': {'freq': 1.0, 'pass': False},
                            'V1': {'freq': 1.0, 'pass': False},
                            'V2': {'freq': 1.0, 'pass': False}
                            }
        self.ref_innerres_nsel4 = {
                            'V3': {'freq': 0.0, 'pass': True},
                            'V4': {'freq': 0.0, 'pass': True}
                            }
        self.ref_innerres_sel5 = {}
        self.ref_innerres_nsel5 = {
                            'V0': {'pass': False},
                            'V1': {'pass': False},
                            'V2': {'pass': False},
                            'V3': {'pass': False},
                            'V4': {'pass': False},
                            }
        self.ref_innersel1 = {self.dof : {'sel_vars' : self.ref_innerres_sel1, 'nsel_vars' : self.ref_innerres_nsel1}}
        self.ref_innersel2 = {self.dof : {'sel_vars' : self.ref_innerres_sel2, 'nsel_vars' : self.ref_innerres_nsel2}}
        self.ref_innersel3 = {self.dof : {'sel_vars' : self.ref_innerres_sel3, 'nsel_vars' : self.ref_innerres_nsel3}}
        self.ref_innersel4 = {self.dof : {'sel_vars' : self.ref_innerres_sel4, 'nsel_vars' : self.ref_innerres_nsel4}}
        self.ref_innersel5 = {self.dof : {'sel_vars' : self.ref_innerres_sel5, 'nsel_vars' : self.ref_innerres_nsel5}}

    def test_init1(self):
        isel = InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(**self.isel_cfg1)
        self.assertEqual(self.isel_cfg1, isel.parameters)

    def test_perform1(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg1)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(**self.isel_cfg1)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel1, self.results1['Selection']['inner'])

    def test_perform2(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg2)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(**self.isel_cfg1)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel2, self.results1['Selection']['inner'])

    def test_perform3(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg1)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(**self.isel_cfg2)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel3, self.results1['Selection']['inner'])

    def test_perform4(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg2)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(**self.isel_cfg2)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel4, self.results1['Selection']['inner'])

    def test_perform5(self):
        osel = OuterSelector_ClassificationErrorThreshold(**self.osel_cfg1)
        osel.perform([self.results1])
        ssIndResults = {self.ssname1 : self.results1}
        oselRes = {self.ssname1 : self.results1['Selection']['outer']}
        subsets = {self.ssname1 : {'mat' : self.ssname1, 'vars' : self.vars1}}
        isel = InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(**self.isel_cfg3)
        isel.perform(oselRes, ssIndResults, subsets)
        self.assertEqual(self.ref_innersel5, self.results1['Selection']['inner'])

