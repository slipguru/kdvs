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

from kdvs.core.db import DBManager
from kdvs.core.error import Error
from kdvs.core.util import quote
from kdvs.fw.DSV import DSV, DSV_DEFAULT_ID_COLUMN
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import csv
import os
from kdvs import SYSTEM_NAME_LC

unittest = resolve_unittest()

class TestDSV1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        # num.dsv
        self.num_dsv_path = os.path.abspath(os.path.join(self.test_data_root, 'num.dsv'))
        num_cols = ['S%d' % n for n in range(91)]
        self.num_dsv_actual_header = ['']
        self.num_dsv_actual_header.extend(num_cols)
        self.num_dsv_desired_header = [DSV_DEFAULT_ID_COLUMN]
        self.num_dsv_desired_header.extend(num_cols)

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
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV, dialect and delimiter sniffed
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname)
        self.assertFalse(dsv1.isCreated())
        self.assertEqual(',', dsv1.dialect.delimiter)
        dsv1.close()

    def test_init2(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # predefined delimiter, resolved successfully
        # NOTE: class does not check if delimiter is valid at this point
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, delimiter='\t')
        self.assertFalse(dsv1.isCreated())
        self.assertEqual(csv.get_dialect('excel-tab'), dsv1.dialect)
        self.assertEqual('\t', dsv1.dialect.delimiter)
        dsv1.close()

    def test_init3(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter not resolved
        with self.assertRaises(Error):
            DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, delimiter='AAAAAA')

    def test_init4(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter not resolved
        with self.assertRaises(Error):
            DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, delimiter=('A',))

    def test_init5(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter not resolved
        with self.assertRaises(Error):
            DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, delimiter=100)

    def test_init6(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, comment resolved successfully
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, comment='#')
        self.assertFalse(dsv1.isCreated())
        self.assertEqual('#', dsv1.comment)
        dsv1.close()

    def test_init7(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, comment not resolved
        with self.assertRaises(Error):
            DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, comment=('#',))

    def test_init8(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, comment not resolved
        with self.assertRaises(Error):
            DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, comment=1000)

    def test_init9(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, header extracted (default), ID resolved
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname)
        self.assertSequenceEqual(self.num_dsv_desired_header, dsv1.header)
        dsv1.create()
        self.assertTrue(dsv1.isCreated())
        self.assertTrue(dsv1.isEmpty())
        dsv1.close()

    def test_init10(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, header extracted (default), ID not resolved
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, make_missing_ID_column=False)
        self.assertSequenceEqual(self.num_dsv_actual_header, dsv1.header)
        dsv1.create()
        self.assertTrue(dsv1.isCreated())
        self.assertTrue(dsv1.isEmpty())
        dsv1.close()

    def test_init11(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, header auto-generated
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, header=())
        ref_header = tuple(['%d' % n for n in range(1, len(self.num_dsv_actual_header) + 1)])
        self.assertSequenceEqual(ref_header, dsv1.header)
        dsv1.create()
        self.assertTrue(dsv1.isCreated())
        self.assertTrue(dsv1.isEmpty())
        dsv1.close()

    def test_init12(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, header supplied (proper length)
        our_header = tuple(['C%d' % n for n in range(1, len(self.num_dsv_actual_header) + 1)])
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, header=our_header)
        self.assertSequenceEqual(our_header, dsv1.header)
        dsv1.create()
        self.assertTrue(dsv1.isCreated())
        self.assertTrue(dsv1.isEmpty())
        dsv1.close()

    def test_init13(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # delimiter sniffed, header supplied (improper length)
        our_header = tuple(['C%d' % n for n in range(1, len(self.num_dsv_actual_header) * 2 + 1)])
        with self.assertRaises(Error):
            DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname, header=our_header)

class TestDSV2(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.test_cols = ('A', 'B', 'C')
        self.test_dtname = 'Test1'
        self.dbm = DBManager(self.test_write_root)
        # num.dsv
        self.num_dsv_path = os.path.abspath(os.path.join(self.test_data_root, 'num.dsv'))
        num_cols = ['S%d' % n for n in range(91)]
        self.num_dsv_actual_header = ['']
        self.num_dsv_actual_header.extend(num_cols)
        self.num_dsv_desired_header = [DSV_DEFAULT_ID_COLUMN]
        self.num_dsv_desired_header.extend(num_cols)
        self.num_rows = ['V1', 'V2']
        self.num_column_3 = ['8.08785988003525', '2.37310583895584']
        # anno.dsv
        self.anno_dsv_path = os.path.abspath('%s/%s' % (self.test_data_root, 'anno.dsv'))
        self.anno_comment = '#'
        self.anno_header = ['ID', 'GB_ACC', 'SPOT_ID', 'Species Scientific Name', 'Annotation Date', 'Sequence Type',
                            'Sequence Source', 'Target Description', 'Representative Public ID', 'Gene Title', 'Gene Symbol',
                            'ENTREZ_GENE_ID', 'RefSeq Transcript ID', 'Gene Ontology Biological Process',
                            'Gene Ontology Cellular Component', 'Gene Ontology Molecular Function']
        self.anno_rows = ['1007_s_at', '1053_at']
        self.anno_columns = ['GB_ACC', 'Gene Symbol']
        self.anno_columns_dict = {'GB_ACC' : ['U48705', 'M87338'], 'Gene Symbol' : ['DDR1', 'RFC2']}

    def tearDown(self):
        self.dbm.close()
        db1_path = os.path.abspath('%s/%s.db' % (self.test_write_root, self.testdb))
        rootdb_path = os.path.abspath('%s/%s.root.db' % (self.test_write_root, SYSTEM_NAME_LC))
        if os.path.exists(db1_path):
            os.remove(db1_path)
        if os.path.exists(rootdb_path):
            os.remove(rootdb_path)
        self.dbm = None

    def test_loadall1(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname)
        self.assertSequenceEqual(self.num_dsv_desired_header, dsv1.header)
        dsv1.create()
        self.assertTrue(dsv1.isCreated())
        self.assertTrue(dsv1.isEmpty())
        # load from file
        st = dsv1.loadAll(debug=True)
        dsv1.close()
        ref_st = ['insert into "Test1" values ("V1","7.29865639942","7.1839394018853","8.08785988003525","8.43784327460378","7.56725674896063","7.17150350961048",'
                                               '"8.23772125375395","7.26860393651388","6.74186036580687","7.55493056104098","7.37521470969549","6.35468766815909",'
                                               '"7.03794441889888","6.75197742759923","7.26608934160658","8.70335292880697","6.85443361759566","7.59055769774248",'
                                               '"8.01751559655053","6.99993079846214","7.10871523619365","7.65161630470663","6.71058065426046","6.64437907655326",'
                                               '"6.93172233805358","7.61870427987243","6.9634175191832","6.37433009206648","6.34485366708736","6.0977075555399",'
                                               '"6.9061361459302","6.54264897912374","6.31961323363347","6.16533391728077","6.90481905323935","6.7168440158265",'
                                               '"7.22535319774288","6.20123577217092","6.93391118518623","6.82985307889579","6.35468239627533","7.09693639659124",'
                                               '"7.60449775270475","7.12266778930967","6.35835046528365","6.76414046791","6.17508883882112","6.52508274039929",'
                                               '"7.11162248509395","6.89152906126555","6.49949720627377","6.69448041622817","6.37526926527225","5.80401273298264",'
                                               '"7.12987703240072","6.05831629170905","6.81624397767137","6.66820808623227","6.64998519558867","6.42308111524492",'
                                               '"7.58672787003923","3.84767749509431","6.71665724008276","6.35468766815909","6.54859953448512","7.23447515724748",'
                                               '"6.70007125889196","6.28445976227631","6.75206243946758","6.7168440158265","6.55922419484843","6.93675713126568",'
                                               '"6.80067557800434","6.50103393612957","6.91542815411986","6.19960368164491","7.6448783709798","6.2125929974423",'
                                               '"6.35468766815909","7.32784699996015","6.14659907126786","6.7168440158265","6.8825610653412","6.72831600642366",'
                                               '"6.46374697412319","5.79584776993902","6.0825372527799","7.1204899554919","6.39620062779895","6.35814627516342",'
                                               '"6.35814627516342")',
                  'insert into "Test1" values ("V2","2.38904325749261","2.37588862645719","2.37310583895584","2.38904325749261","2.42091222425779","2.38904325749261",'
                                               '"2.38626046999126","2.38904325749261","2.38904325749261","2.41002306956031","2.38904325749261","2.38904325749261",'
                                               '"2.38904325749261","2.37310583895584","2.38626046999126","2.34429782913723","2.38904325749261","2.98112952430922",'
                                               '"2.34553574786241","2.37310583895584","2.39660701797421","2.38904325749261","2.40955866820479","2.38626046999126",'
                                               '"2.35577218230877","2.39443448171899","2.34433277775847","2.69053923836483","2.38430054425455","2.86158891209344",'
                                               '"2.34595261411454","2.89813268468409","2.42777977950130","2.38626046999126","2.44904175049461","3.55795174775419",'
                                               '"2.66896481156844","2.38626046999126","2.71772299956764","2.61602731442131","2.56996895766296","3.86202701130675",'
                                               '"2.38904325749261","2.35577218230877","2.60505670342601","3.12697260562512","2.38904325749261","3.15740854425796",'
                                               '"2.65364423092787","2.45124596034905","3.14913252263311","2.38904325749261","2.39700474393300","2.38904325749261",'
                                               '"2.46188514405506","3.23873137510437","2.55373906857937","3.39601442806742","3.16936129560691","3.18777558546775",'
                                               '"2.38904325749261","2.38904325749261","2.38626046999126","2.34553574786241","2.35577218230877","2.38624782221570",'
                                               '"2.35577218230877","2.38904325749261","2.74265374191966","2.37188401381886","2.37588862645719","2.38904325749261",'
                                               '"2.35577218230877","2.35121946858936","2.49946444329392","2.38904325749261","2.34553574786241","2.93960156829307",'
                                               '"2.38904325749261","2.39182604499395","2.38904325749261","2.35315614841910","2.47149945385376","2.38626046999126",'
                                               '"2.39596753440869","2.38904325749261","2.40223987191512","2.34715558421848","2.38210356896247","2.34719053283972",'
                                               '"2.76820667786915")']
        self.assertSequenceEqual(ref_st, st)

    def test_loadall2(self):
        dsv1_fh = DSV.getHandle(self.num_dsv_path)
        # default DSV
        dsv1 = DSV(self.dbm, self.testdb, dsv1_fh, dtname=self.test_dtname)
        self.assertSequenceEqual(self.num_dsv_desired_header, dsv1.header)
        dsv1.create()
        dsv1.loadAll()
        dsv1.close()
        # low level checks
        cs = dsv1.db.cursor()
        cs.execute('select %s from %s' % (self.num_dsv_desired_header[0], dsv1.name))
        rres = cs.fetchall()
        res = [str(r[0]) for r in rres]
        self.assertSequenceEqual(self.num_rows, res)
        cs.execute('select %s from %s' % (self.num_dsv_desired_header[3], dsv1.name))
        rres = cs.fetchall()
        res = [str(r[0]) for r in rres]
        self.assertSequenceEqual(self.num_column_3, res)

    def test_loadall3(self):
        dsv2_fh = DSV.getHandle(self.anno_dsv_path)
        dsv2 = DSV(self.dbm, self.testdb, dsv2_fh, dtname=self.test_dtname, comment=self.anno_comment)
        dsv2.create()
        st = dsv2.loadAll(debug=True)
        dsv2.close()
        ref_st = ['insert into "Test1" values ("1007_s_at","U48705","","Homo sapiens","Mar 11, 2009",'
                                               '"Exemplar sequence","Affymetrix Proprietary Database",'
                                               '"U48705 /FEATURE=mRNA /DEFINITION=HSU48705 Human receptor tyrosine kinase DDR gene, complete cds",'
                                               '"U48705","discoidin domain receptor tyrosine kinase 1",'
                                               '"DDR1","780","NM_001954 /// NM_013993 /// NM_013994",'
                                               '"0006468 // protein amino acid phosphorylation // inferred from electronic annotation ///'
                                               ' 0007155 // cell adhesion // traceable author statement ///'
                                               ' 0007155 // cell adhesion // inferred from electronic annotation ///'
                                               ' 0007169 // transmembrane receptor protein tyrosine kinase signaling pathway // inferred from electronic annotation",'
                                               '"0005887 // integral to plasma membrane // traceable author statement ///'
                                               ' 0016020 // membrane // inferred from electronic annotation ///'
                                               ' 0016021 // integral to membrane // inferred from electronic annotation",'
                                               '"0000166 // nucleotide binding // inferred from electronic annotation ///'
                                               ' 0004672 // protein kinase activity // inferred from electronic annotation ///'
                                               ' 0004713 // protein tyrosine kinase activity // inferred from electronic annotation ///'
                                               ' 0004714 // transmembrane receptor protein tyrosine kinase activity // traceable author statement ///'
                                               ' 0004714 // transmembrane receptor protein tyrosine kinase activity // inferred from electronic annotation ///'
                                               ' 0004872 // receptor activity // inferred from electronic annotation ///'
                                               ' 0005515 // protein binding // inferred from physical interaction ///'
                                               ' 0005524 // ATP binding // inferred from electronic annotation ///'
                                               ' 0016301 // kinase activity // inferred from electronic annotation ///'
                                               ' 0016740 // transferase activity // inferred from electronic annotation")',
                'insert into "Test1" values ("1053_at","M87338","","Homo sapiens","Mar 11, 2009",'
                                               '"Exemplar sequence","GenBank",'
                                               '"M87338 /FEATURE= /DEFINITION=HUMA1SBU Human replication factor C, 40-kDa subunit (A1) mRNA, complete cds",'
                                               '"M87338","replication factor C (activator 1) 2, 40kDa",'
                                               '"RFC2","5982","NM_002914 /// NM_181471",'
                                               '"0006260 // DNA replication // not recorded ///'
                                               ' 0006260 // DNA replication // inferred from electronic annotation ///'
                                               ' 0006297 // nucleotide-excision repair, DNA gap filling // not recorded",'
                                               '"0005634 // nucleus // inferred from electronic annotation ///'
                                               ' 0005654 // nucleoplasm // not recorded ///'
                                               ' 0005663 // DNA replication factor C complex // inferred from direct assay ///'
                                               ' 0005663 // DNA replication factor C complex // inferred from electronic annotation",'
                                               '"0000166 // nucleotide binding // inferred from electronic annotation ///'
                                               ' 0003677 // DNA binding // inferred from electronic annotation ///'
                                               ' 0003689 // DNA clamp loader activity // inferred from electronic annotation ///'
                                               ' 0005515 // protein binding // inferred from physical interaction ///'
                                               ' 0005524 // ATP binding // traceable author statement ///'
                                               ' 0005524 // ATP binding // inferred from electronic annotation ///'
                                               ' 0017111 // nucleoside-triphosphatase activity // inferred from electronic annotation")']
        self.assertSequenceEqual(ref_st, st)

    def test_loadall4(self):
        dsv2_fh = DSV.getHandle(self.anno_dsv_path)
        dsv2 = DSV(self.dbm, self.testdb, dsv2_fh, dtname=self.test_dtname, comment=self.anno_comment)
        self.assertSequenceEqual(self.anno_header, dsv2.header)
        dsv2.create()
        dsv2.loadAll()
        dsv2.close()
        # low level checks
        cs = dsv2.db.cursor()
        cs.execute('select %s from %s' % (self.anno_header[0], dsv2.name))
        rres = cs.fetchall()
        res = [str(r[0]) for r in rres]
        self.assertSequenceEqual(self.anno_rows, res)
        cols = ','.join([quote(c) for c in self.anno_columns])
        cs.execute('select %s from %s' % (cols, dsv2.name))
        rres = cs.fetchall()
        res = {}
        for ix, ac in enumerate(self.anno_columns):
            res[ac] = [str(r[ix]) for r in rres]
        self.assertDictEqual(self.anno_columns_dict, res)

    def test_close1(self):
        dsv2_fh = DSV.getHandle(self.anno_dsv_path)
        dsv2 = DSV(self.dbm, self.testdb, dsv2_fh, dtname=self.test_dtname, comment=self.anno_comment)
        dsv2.create()
        dsv2.loadAll()
        dsv2.close()
        with self.assertRaises(Error):
            dsv2.loadAll()

