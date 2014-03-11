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
from kdvs.fw.DataSet import DataSet
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os
import warnings
try:
    import numpy
    numpyFound = True
except ImportError:
    numpyFound = False
from kdvs.tests.utils import check_min_numpy_version

unittest = resolve_unittest()

@unittest.skipUnless(numpyFound, 'numpy not found')
class TestDataSet1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        # num.dsv
        self.num_dsv_path = os.path.abspath('%s/%s' % (self.test_data_root, 'num.dsv'))
        self.sample_rows_none = ()
        self.sample_rows_1 = ('V1',)
        self.sample_cols_none = ()
        self.sample_cols_with_id = ['ID']

        self.empty_array = numpy.array([]).reshape((1, 0))
        self.array1 = numpy.array([
            [7.29865639942, 7.1839394018853, 8.08785988003525, 8.43784327460378,
             7.56725674896063, 7.17150350961048, 8.23772125375395, 7.26860393651388,
             6.74186036580687, 7.55493056104098, 7.37521470969549, 6.35468766815909,
             7.03794441889888, 6.75197742759923, 7.26608934160658, 8.70335292880697,
             6.85443361759566, 7.59055769774248, 8.01751559655053, 6.99993079846214,
             7.10871523619365, 7.65161630470663, 6.71058065426046, 6.64437907655326,
             6.93172233805358, 7.61870427987243, 6.9634175191832, 6.37433009206648,
             6.34485366708736, 6.0977075555399, 6.9061361459302, 6.54264897912374,
             6.31961323363347, 6.16533391728077, 6.90481905323935, 6.7168440158265,
             7.22535319774288, 6.20123577217092, 6.93391118518623, 6.82985307889579,
             6.35468239627533, 7.09693639659124, 7.60449775270475, 7.12266778930967,
             6.35835046528365, 6.76414046791, 6.17508883882112, 6.52508274039929,
             7.11162248509395, 6.89152906126555, 6.49949720627377, 6.69448041622817,
             6.37526926527225, 5.80401273298264, 7.12987703240072, 6.05831629170905,
             6.81624397767137, 6.66820808623227, 6.64998519558867, 6.42308111524492,
             7.58672787003923, 3.84767749509431, 6.71665724008276, 6.35468766815909,
             6.54859953448512, 7.23447515724748, 6.70007125889196, 6.28445976227631,
             6.75206243946758, 6.7168440158265, 6.55922419484843, 6.93675713126568,
             6.80067557800434, 6.50103393612957, 6.91542815411986, 6.19960368164491,
             7.6448783709798, 6.2125929974423, 6.35468766815909, 7.32784699996015,
             6.14659907126786, 6.7168440158265, 6.8825610653412, 6.72831600642366,
             6.46374697412319, 5.79584776993902, 6.0825372527799, 7.1204899554919,
             6.39620062779895, 6.35814627516342, 6.35814627516342],
            [2.38904325749261, 2.37588862645719, 2.37310583895584, 2.38904325749261,
             2.42091222425779, 2.38904325749261, 2.38626046999126, 2.38904325749261,
             2.38904325749261, 2.41002306956031, 2.38904325749261, 2.38904325749261,
             2.38904325749261, 2.37310583895584, 2.38626046999126, 2.34429782913723,
             2.38904325749261, 2.98112952430922, 2.34553574786241, 2.37310583895584,
             2.39660701797421, 2.38904325749261, 2.40955866820479, 2.38626046999126,
             2.35577218230877, 2.39443448171899, 2.34433277775847, 2.69053923836483,
             2.38430054425455, 2.86158891209344, 2.34595261411454, 2.89813268468409,
             2.42777977950130, 2.38626046999126, 2.44904175049461, 3.55795174775419,
             2.66896481156844, 2.38626046999126, 2.71772299956764, 2.61602731442131,
             2.56996895766296, 3.86202701130675, 2.38904325749261, 2.35577218230877,
             2.60505670342601, 3.12697260562512, 2.38904325749261, 3.15740854425796,
             2.65364423092787, 2.45124596034905, 3.14913252263311, 2.38904325749261,
             2.39700474393300, 2.38904325749261, 2.46188514405506, 3.23873137510437,
             2.55373906857937, 3.39601442806742, 3.16936129560691, 3.18777558546775,
             2.38904325749261, 2.38904325749261, 2.38626046999126, 2.34553574786241,
             2.35577218230877, 2.38624782221570, 2.35577218230877, 2.38904325749261,
             2.74265374191966, 2.37188401381886, 2.37588862645719, 2.38904325749261,
             2.35577218230877, 2.35121946858936, 2.49946444329392, 2.38904325749261,
             2.34553574786241, 2.93960156829307, 2.38904325749261, 2.39182604499395,
             2.38904325749261, 2.35315614841910, 2.47149945385376, 2.38626046999126,
             2.39596753440869, 2.38904325749261, 2.40223987191512, 2.34715558421848,
             2.38210356896247, 2.34719053283972, 2.76820667786915],
            ])
        self.array_v1 = numpy.array([
            [7.29865639942, 7.1839394018853, 8.08785988003525, 8.43784327460378,
             7.56725674896063, 7.17150350961048, 8.23772125375395, 7.26860393651388,
             6.74186036580687, 7.55493056104098, 7.37521470969549, 6.35468766815909,
             7.03794441889888, 6.75197742759923, 7.26608934160658, 8.70335292880697,
             6.85443361759566, 7.59055769774248, 8.01751559655053, 6.99993079846214,
             7.10871523619365, 7.65161630470663, 6.71058065426046, 6.64437907655326,
             6.93172233805358, 7.61870427987243, 6.9634175191832, 6.37433009206648,
             6.34485366708736, 6.0977075555399, 6.9061361459302, 6.54264897912374,
             6.31961323363347, 6.16533391728077, 6.90481905323935, 6.7168440158265,
             7.22535319774288, 6.20123577217092, 6.93391118518623, 6.82985307889579,
             6.35468239627533, 7.09693639659124, 7.60449775270475, 7.12266778930967,
             6.35835046528365, 6.76414046791, 6.17508883882112, 6.52508274039929,
             7.11162248509395, 6.89152906126555, 6.49949720627377, 6.69448041622817,
             6.37526926527225, 5.80401273298264, 7.12987703240072, 6.05831629170905,
             6.81624397767137, 6.66820808623227, 6.64998519558867, 6.42308111524492,
             7.58672787003923, 3.84767749509431, 6.71665724008276, 6.35468766815909,
             6.54859953448512, 7.23447515724748, 6.70007125889196, 6.28445976227631,
             6.75206243946758, 6.7168440158265, 6.55922419484843, 6.93675713126568,
             6.80067557800434, 6.50103393612957, 6.91542815411986, 6.19960368164491,
             7.6448783709798, 6.2125929974423, 6.35468766815909, 7.32784699996015,
             6.14659907126786, 6.7168440158265, 6.8825610653412, 6.72831600642366,
             6.46374697412319, 5.79584776993902, 6.0825372527799, 7.1204899554919,
             6.39620062779895, 6.35814627516342, 6.35814627516342],
            ])
        self.array1_rows = ['__R%d__' % i for i in range(2)]
        self.array1_cols = ['__S%d__' % i for i in range(91)]

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
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.close()
        with self.assertRaises(Error):
            DataSet()

    def test_init2(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.close()
        with self.assertRaises(Error):
            DataSet(dbtable=dsv, rows='AAA')

    def test_init3(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.close()
        with self.assertRaises(Error):
            DataSet(dbtable=dsv, cols='BBB')

    def test_init4(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.close()
        with self.assertRaises(Error):
            DataSet(dbtable=dsv, rows=self.sample_rows_none, cols=self.sample_cols_none)

    def test_init5(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV, dialect and delimiter sniffed
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        # data set by default spanning all rows and all columns
        # data not loaded, we shall see empty array
        dsv.create()
        dsv.close()
        # NOTE: before numpy 1.6.0, empty file in loadtxt() generates IOError,
        # with 1.6.0+ only warning
        if check_min_numpy_version(1, 6, 0):
            # suppress numpy warning of empty source file
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ds = DataSet(dbtable=dsv)
            numpy.testing.assert_equal(self.empty_array, ds.array)
        else:
            with self.assertRaises(Error):
                DataSet(dbtable=dsv)

    def test_init6(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV, dialect and delimiter sniffed
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.loadAll()
        dsv.close()
        # data set by default spanning all rows and all columns
        ds = DataSet(dbtable=dsv)
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)

    def test_init7(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV, dialect and delimiter sniffed
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.loadAll()
        dsv.close()
        # get only first row
        ds = DataSet(dbtable=dsv, rows=self.sample_rows_1)
        numpy.testing.assert_array_almost_equal(self.array_v1, ds.array)

    def test_init8(self):
        # wrap existing numpy array
        ds = DataSet(input_array=self.array1)
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)

    def test_init9(self):
        with self.assertRaises(Error):
            DataSet(input_array='XXXXX')

    def test_rowscols1(self):
        # wrap existing numpy array
        ds = DataSet(input_array=self.array1)
        # check default rows and columns
        self.assertSequenceEqual(self.array1_rows, ds.rows)
        self.assertSequenceEqual(self.array1_cols, ds.cols)

@unittest.skipUnless(numpyFound, 'numpy not found')
class TestDataSet2(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        # num.dsv
        self.num_dsv_path = os.path.abspath('%s/%s' % (self.test_data_root, 'num.dsv'))
        self.sample_rows_none = ()
        self.sample_rows_1 = ('V1',)
        self.sample_cols_none = ()
        self.sample_cols_1 = ('S1', 'S5',)
        self.sample_cols_with_id = ['ID']

        self.empty_array = numpy.array([]).reshape((1, 0))
        self.array1 = numpy.array([
            [7.29865639942, 7.1839394018853, 8.08785988003525, 8.43784327460378,
             7.56725674896063, 7.17150350961048, 8.23772125375395, 7.26860393651388,
             6.74186036580687, 7.55493056104098, 7.37521470969549, 6.35468766815909,
             7.03794441889888, 6.75197742759923, 7.26608934160658, 8.70335292880697,
             6.85443361759566, 7.59055769774248, 8.01751559655053, 6.99993079846214,
             7.10871523619365, 7.65161630470663, 6.71058065426046, 6.64437907655326,
             6.93172233805358, 7.61870427987243, 6.9634175191832, 6.37433009206648,
             6.34485366708736, 6.0977075555399, 6.9061361459302, 6.54264897912374,
             6.31961323363347, 6.16533391728077, 6.90481905323935, 6.7168440158265,
             7.22535319774288, 6.20123577217092, 6.93391118518623, 6.82985307889579,
             6.35468239627533, 7.09693639659124, 7.60449775270475, 7.12266778930967,
             6.35835046528365, 6.76414046791, 6.17508883882112, 6.52508274039929,
             7.11162248509395, 6.89152906126555, 6.49949720627377, 6.69448041622817,
             6.37526926527225, 5.80401273298264, 7.12987703240072, 6.05831629170905,
             6.81624397767137, 6.66820808623227, 6.64998519558867, 6.42308111524492,
             7.58672787003923, 3.84767749509431, 6.71665724008276, 6.35468766815909,
             6.54859953448512, 7.23447515724748, 6.70007125889196, 6.28445976227631,
             6.75206243946758, 6.7168440158265, 6.55922419484843, 6.93675713126568,
             6.80067557800434, 6.50103393612957, 6.91542815411986, 6.19960368164491,
             7.6448783709798, 6.2125929974423, 6.35468766815909, 7.32784699996015,
             6.14659907126786, 6.7168440158265, 6.8825610653412, 6.72831600642366,
             6.46374697412319, 5.79584776993902, 6.0825372527799, 7.1204899554919,
             6.39620062779895, 6.35814627516342, 6.35814627516342],
            [2.38904325749261, 2.37588862645719, 2.37310583895584, 2.38904325749261,
             2.42091222425779, 2.38904325749261, 2.38626046999126, 2.38904325749261,
             2.38904325749261, 2.41002306956031, 2.38904325749261, 2.38904325749261,
             2.38904325749261, 2.37310583895584, 2.38626046999126, 2.34429782913723,
             2.38904325749261, 2.98112952430922, 2.34553574786241, 2.37310583895584,
             2.39660701797421, 2.38904325749261, 2.40955866820479, 2.38626046999126,
             2.35577218230877, 2.39443448171899, 2.34433277775847, 2.69053923836483,
             2.38430054425455, 2.86158891209344, 2.34595261411454, 2.89813268468409,
             2.42777977950130, 2.38626046999126, 2.44904175049461, 3.55795174775419,
             2.66896481156844, 2.38626046999126, 2.71772299956764, 2.61602731442131,
             2.56996895766296, 3.86202701130675, 2.38904325749261, 2.35577218230877,
             2.60505670342601, 3.12697260562512, 2.38904325749261, 3.15740854425796,
             2.65364423092787, 2.45124596034905, 3.14913252263311, 2.38904325749261,
             2.39700474393300, 2.38904325749261, 2.46188514405506, 3.23873137510437,
             2.55373906857937, 3.39601442806742, 3.16936129560691, 3.18777558546775,
             2.38904325749261, 2.38904325749261, 2.38626046999126, 2.34553574786241,
             2.35577218230877, 2.38624782221570, 2.35577218230877, 2.38904325749261,
             2.74265374191966, 2.37188401381886, 2.37588862645719, 2.38904325749261,
             2.35577218230877, 2.35121946858936, 2.49946444329392, 2.38904325749261,
             2.34553574786241, 2.93960156829307, 2.38904325749261, 2.39182604499395,
             2.38904325749261, 2.35315614841910, 2.47149945385376, 2.38626046999126,
             2.39596753440869, 2.38904325749261, 2.40223987191512, 2.34715558421848,
             2.38210356896247, 2.34719053283972, 2.76820667786915],
            ])

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm = None

    def test_recache1(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV, dialect and delimiter sniffed
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.loadAll()
        # data set by default spanning all rows and all columns
        ds = DataSet(dbtable=dsv)
        dsv.close()
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)
        # perform recache (we shall see no change)
        ds.recache()
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)

    def test_recache2(self):
        dsv_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV, dialect and delimiter sniffed
        dsv = DSV(self.dbm, self.testdb, dsv_fh, dtname=self.test_dtname)
        dsv.create()
        dsv.loadAll()
        # data set by default spanning all rows and all columns
        ds = DataSet(dbtable=dsv)
        dsv.close()
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)
        # wipe out underlying table
        wipe_cs = dsv.db.cursor()
        wipe_cs.execute('delete from "%s";' % self.test_dtname)
        dsv.db.commit()
        wipe_cs.execute('vacuum;')
        dsv.db.commit()
        # NOTE: before numpy 1.6.0, empty file in loadtxt() generates IOError,
        # with 1.6.0+ only warning
        if check_min_numpy_version(1, 6, 0):
            # perform recache (we shall see empty array)
            # suppress numpy warning of empty source file
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                ds.recache()
            numpy.testing.assert_array_almost_equal(self.empty_array, ds.array)
        else:
            with self.assertRaises(Error):
                ds.recache()

    def test_recache3(self):
        # wrap existing numpy array
        ds = DataSet(input_array=self.array1)
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)
        # perform recache (we shall see no change)
        ds.recache()
        numpy.testing.assert_array_almost_equal(self.array1, ds.array)
