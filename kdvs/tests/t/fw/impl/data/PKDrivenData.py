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
from kdvs.fw.DSV import DSV
from kdvs.fw.Map import PKCIDMap
from kdvs.fw.impl.data.PKDrivenData import PKDrivenDBDataManager, \
    PKDrivenDataManager, PKDrivenDBSubsetHierarchy
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import numpy
import os
from kdvs.fw.impl.data.SubsetSize import SubsetSizeCategorizer
from kdvs.fw.impl.data.Null import NullCategorizer

unittest = resolve_unittest()

class MockPKCIDMap(PKCIDMap):
    def __init__(self, pkc2id):
#        self.pkc2id = pkc2id
        self.pkc2emid = pkc2id
    def build(self, *args, **kwargs):
        pass

class TestPKDrivenDataManager1(unittest.TestCase):

    def test_init1(self):
        pkdm = PKDrivenDataManager()
        self.assertEqual({}, vars(pkdm))

    def test_getSubset1(self):
        pkdm = PKDrivenDataManager()
        with self.assertRaises(NotImplementedError):
            pkdm.getSubset()

class TestPKDrivenDBDataManager1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        # ssdata.dsv
        self.ssdata_dsv_path = os.path.abspath(os.path.join(self.test_data_root, 'ssdata.dsv'))
        self.ssdata_comment = '#'
        ssdata_dsv_fh = DSV.getHandle(self.ssdata_dsv_path)
        self.ssdata_dsv1 = DSV(self.dbm, self.testdb, ssdata_dsv_fh, dtname=self.test_dtname, comment=self.ssdata_comment)
        self.ssdata_dsv1.create()
        self.ssdata_dsv1.loadAll()
        self.ssdata_dsv1.close()
        self.ssdata_samples = ('S1', 'S2', 'S3', 'S4', 'S5')
        # pkcidmap
        self.pkc2id1 = {'PKC1' : ('R1', 'R2'), 'PKC2' : ('R3',), 'PKC3' : ('R4', 'R5')}
        self.pkc1 = ('PKC1', 'PKC2', 'PKC3')
        self.ss_cols1 = '*'
        self.ref_ss1 = [
            ({'pkcID' : 'PKC1', 'dtable' : self.ssdata_dsv1, 'rows' : ['R1', 'R2'], 'cols' : list(self.ssdata_samples)}, None),
            ({'pkcID' : 'PKC2', 'dtable' : self.ssdata_dsv1, 'rows' : ['R3'], 'cols' : list(self.ssdata_samples)}, None),
            ({'pkcID' : 'PKC3', 'dtable' : self.ssdata_dsv1, 'rows' : ['R4', 'R5'], 'cols' : list(self.ssdata_samples)}, None),
            ]
        self.ss_cols2 = ('S1', 'S4', 'S5')
        self.ref_ss2 = [
            ({'pkcID' : 'PKC1', 'dtable' : self.ssdata_dsv1, 'rows' : ['R1', 'R2'], 'cols' : list(self.ss_cols2)}, None),
            ({'pkcID' : 'PKC2', 'dtable' : self.ssdata_dsv1, 'rows' : ['R3'], 'cols' : list(self.ss_cols2)}, None),
            ({'pkcID' : 'PKC3', 'dtable' : self.ssdata_dsv1, 'rows' : ['R4', 'R5'], 'cols' : list(self.ss_cols2)}, None),
            ]
        self.pkc2 = ('PKC3', 'PKC1')
        self.ref_ss3 = [
            ({'pkcID' : 'PKC3', 'dtable' : self.ssdata_dsv1, 'rows' : ['R4', 'R5'], 'cols' : list(self.ss_cols2)}, None),
            ({'pkcID' : 'PKC1', 'dtable' : self.ssdata_dsv1, 'rows' : ['R1', 'R2'], 'cols' : list(self.ss_cols2)}, None),
            ]
        self.ref_ss4 = [
            (None, numpy.array([
                [2.44753543273, 42.9497086717, 30.8331998765],
                [42.1888598933, 39.1743921225, 15.9744094108],
                ])),
            (None, numpy.array([
                [16.5734780715, 14.8233987496, 21.7385342744],
                [60.0958378228, 98.4321570519, 71.9193619126],
                ])),
            ]
        # for categorization tests
        self.pkc2id2 = {'PKC1' : ('R1', 'R2', 'R3', 'R4'), 'PKC2' : ('R5',)}
        self.pkc3 = ('PKC1', 'PKC2')
        self.size_thr = 3
        self.cat1 = SubsetSizeCategorizer(self.size_thr)
        self.exp_categories1 = ['>', '<=']
        self.cat2 = NullCategorizer()
        self.exp_categories2 = [self.cat2.NULL] * len(self.pkc3)


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
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id1))
        self.assertEqual(self.pkc2id1, pkdm.pkcidmap.pkc2emid)
        self.assertSequenceEqual(self.ssdata_samples, pkdm.all_samples)

    def test_getSubset1(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id1))
        ss = [pkdm.getSubset(pkc, forSamples=self.ss_cols1, get_ssinfo=True, get_dataset=False) for pkc in self.pkc1]
        self.assertEqual(self.ref_ss1, ss)

    def test_getSubset2(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id1))
        ss = [pkdm.getSubset(pkc, forSamples=self.ss_cols2, get_ssinfo=True, get_dataset=False) for pkc in self.pkc1]
        self.assertEqual(self.ref_ss2, ss)

    def test_getSubset3(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id1))
        ss = [pkdm.getSubset(pkc, forSamples=self.ss_cols2, get_ssinfo=True, get_dataset=False) for pkc in self.pkc2]
        self.assertEqual(self.ref_ss3, ss)

    def test_getSubset4(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id1))
        ss = [pkdm.getSubset(pkc, forSamples=self.ss_cols2, get_ssinfo=False, get_dataset=True) for pkc in self.pkc2]
        for refss, actss in zip(self.ref_ss4, ss):
            self.assertEqual(refss[0], actss[0])
            numpy.testing.assert_array_equal(refss[1], actss[1].array)

    def test_categorizeSubset1(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id2))
        ss_dss = [pkdm.getSubset(pkc, forSamples=self.ss_cols2, get_ssinfo=False, get_dataset=True)[1] for pkc in self.pkc3]
        ss_categories = [PKDrivenDBDataManager.categorizeSubset(ss_ds, self.cat1) for ss_ds in ss_dss]
        self.assertSequenceEqual(self.exp_categories1, ss_categories)

    def test_categorizeSubset2(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id2))
        ss_dss = [pkdm.getSubset(pkc, forSamples=self.ss_cols2, get_ssinfo=False, get_dataset=True)[1] for pkc in self.pkc3]
        ss_categories = [PKDrivenDBDataManager.categorizeSubset(ss_ds, self.cat2) for ss_ds in ss_dss]
        self.assertSequenceEqual(self.exp_categories2, ss_categories)

class TestPKDrivenDBSubsetHierarchy1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        # ssdata.dsv
        self.ssdata_dsv_path = os.path.abspath(os.path.join(self.test_data_root, 'ssdata.dsv'))
        self.ssdata_comment = '#'
        ssdata_dsv_fh = DSV.getHandle(self.ssdata_dsv_path)
        self.ssdata_dsv1 = DSV(self.dbm, self.testdb, ssdata_dsv_fh, dtname=self.test_dtname, comment=self.ssdata_comment)
        self.ssdata_dsv1.create()
        self.ssdata_dsv1.loadAll()
        self.ssdata_dsv1.close()
        self.ssdata_samples = ('S1', 'S2', 'S3', 'S4', 'S5')
        # hierarchy tests
        self.pkc2id = {'PKC1' : ('R1', 'R2', 'R3', 'R4'), 'PKC2' : ('R5',)}
        self.pkc = ('PKC1', 'PKC2')
        self.size_thr1 = 2
        self.cat1 = SubsetSizeCategorizer(self.size_thr1, ID='Cat1')
        self.cat1_uniq_le = self.cat1.uniquifyCategory(self.cat1.ROW_SIZE_LESSER)
        self.cat1_uniq_gt = self.cat1.uniquifyCategory(self.cat1.ROW_SIZE_GREATER)
        self.size_thr2 = 3
        self.cat2 = SubsetSizeCategorizer(self.size_thr2, ID='Cat2')
        self.cat2_uniq_le = self.cat2.uniquifyCategory(self.cat2.ROW_SIZE_LESSER)
        self.cat2_uniq_gt = self.cat2.uniquifyCategory(self.cat2.ROW_SIZE_GREATER)
        self.size_thr3 = 0
        self.cat3 = SubsetSizeCategorizer(self.size_thr3, ID='Cat3')
        self.cat3_uniq_le = self.cat3.uniquifyCategory(self.cat3.ROW_SIZE_LESSER)
        self.cat3_uniq_gt = self.cat3.uniquifyCategory(self.cat3.ROW_SIZE_GREATER)
        self.cinst = {
            'Cat1' : self.cat1,
            'Cat2' : self.cat2,
            'Cat3' : self.cat3,
        }
        self.cmap1 = ['Cat1', 'Cat2', 'Cat3']
        self.cmap2 = ['Cat3', 'Cat1', 'Cat2']
        self.symbols = list(self.pkc)

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
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id))
        pkdss = PKDrivenDBSubsetHierarchy(pkdm, self.ssdata_samples)
        pkdss.build(self.cmap1, self.cinst, self.symbols)
        # ['Cat1', 'Cat2', 'Cat3']
        expected_hierarchy = dict()
        expected_hierarchy.update({None : self.cat1.id})
        expected_hierarchy.update({self.cat1_uniq_le : self.cat2.id})
        expected_hierarchy.update({self.cat1_uniq_gt : self.cat2.id})
        expected_hierarchy.update({self.cat2_uniq_le : self.cat3.id})
        expected_hierarchy.update({self.cat2_uniq_gt : self.cat3.id})
        expected_hierarchy.update({self.cat3_uniq_gt : None})
        expected_hierarchy.update({self.cat3_uniq_le : None})
        self.assertEqual(expected_hierarchy, pkdss.hierarchy)
        #            [PKC1 PKC2]
        # Cat1  [PKC1]>2     [PKC2]<=2
        # Cat2  [PKC1]>3     [PKC2]<=3
        # Cat3  [PKC1]>0     [PKC2]>0
        expected_symboltree = dict()
        expected_symboltree.update({None : {self.cat1_uniq_gt : ['PKC1'], self.cat1_uniq_le : ['PKC2']}})
        expected_symboltree.update({self.cat1_uniq_gt : {self.cat2_uniq_gt : ['PKC1']}})
        expected_symboltree.update({self.cat1_uniq_le : {self.cat2_uniq_le : ['PKC2']}})
        expected_symboltree.update({self.cat2_uniq_gt : {self.cat3_uniq_gt : ['PKC1']}})
        expected_symboltree.update({self.cat2_uniq_le : {self.cat3_uniq_gt : ['PKC2']}})
        self.assertEqual(expected_symboltree, pkdss.symboltree)

    def test_init2(self):
        pkdm = PKDrivenDBDataManager(self.ssdata_dsv1, MockPKCIDMap(self.pkc2id))
        pkdss = PKDrivenDBSubsetHierarchy(pkdm, self.ssdata_samples)
        pkdss.build(self.cmap2, self.cinst, self.symbols)
        # ['Cat3', 'Cat1', 'Cat2']
        expected_hierarchy = dict()
        expected_hierarchy.update({None : self.cat3.id})
        expected_hierarchy.update({self.cat3_uniq_le : self.cat1.id})
        expected_hierarchy.update({self.cat3_uniq_gt : self.cat1.id})
        expected_hierarchy.update({self.cat1_uniq_le : self.cat2.id})
        expected_hierarchy.update({self.cat1_uniq_gt : self.cat2.id})
        expected_hierarchy.update({self.cat2_uniq_gt : None})
        expected_hierarchy.update({self.cat2_uniq_le : None})
        self.assertEqual(expected_hierarchy, pkdss.hierarchy)
        #                   [PKC1 PKC2]
        # Cat3      [PKC1 PKC2]>0      []<=0
        # Cat1    [PKC1]>2  [PKC2]<=2
        # Cat2    [PKC1]>3  [PKC2]<=3
        expected_symboltree = dict()
        expected_symboltree.update({None : {self.cat3_uniq_gt : ['PKC1', 'PKC2']}})
        expected_symboltree.update({self.cat3_uniq_gt : {self.cat1_uniq_gt : ['PKC1'], self.cat1_uniq_le : ['PKC2']}})
        expected_symboltree.update({self.cat1_uniq_gt : {self.cat2_uniq_gt : ['PKC1']}})
        expected_symboltree.update({self.cat1_uniq_le : {self.cat2_uniq_le : ['PKC2']}})
        self.assertEqual(expected_symboltree, pkdss.symboltree)

#        for k, v in pkdss.symboltree.iteritems():
#            if v is not None:
#                print k, dict(v)
#            else:
#                print k, v
