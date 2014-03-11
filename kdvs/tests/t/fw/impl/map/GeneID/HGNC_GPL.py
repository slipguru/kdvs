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
from kdvs.fw.Annotation import get_em2annotation
from kdvs.fw.DBTable import DBTable
from kdvs.fw.DSV import DSV
from kdvs.fw.impl.map.GeneID.HGNC_GPL import GeneIDMapHGNCGPL
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os

unittest = resolve_unittest()

class TestGeneIDMapHGNCGPL1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.annoTable = 'ANNO_GPL'
        self.hgncTable = 'HGNC'
        self.dbm = DBManager(self.test_write_root)
        self.ref_fwd1 = {
                         '': set(['91952_at', 'AFFX-TrpnX-3_at', 'AFFX-TrpnX-5_at', 'AFFX-TrpnX-M_at']),
                         'BCAN': set(['91920_at']),
                         'DDR1': set(['1007_s_at']),
                         'EPS8L1': set(['91826_at']),
                         'HSPA6': set(['117_at']),
                         'RFC2': set(['1053_at'])
                         }
        self.ref_bwd1 = {
                         '1007_s_at': set(['DDR1']),
                         '1053_at': set(['RFC2']),
                         '117_at': set(['HSPA6']),
                         '91826_at': set(['EPS8L1']),
                         '91920_at': set(['BCAN']),
                         '91952_at': set(['']),
                         'AFFX-TrpnX-3_at': set(['']),
                         'AFFX-TrpnX-5_at': set(['']),
                         'AFFX-TrpnX-M_at': set([''])
                         }
        self.ref_em2a = {
                         '1007_s_at': ['DDR1',
                                       'AFFX:U48705',
                                       'U48705',
                                       '780',
                                       'ENSG00000204580',
                                       'NM_013994'],
                         '1053_at': ['RFC2',
                                     'GB:M87338',
                                     'M87338',
                                     '5982',
                                     'ENSG00000049541',
                                     'NM_181471'],
                         '117_at': ['HSPA6',
                                    'AFFX:X51757',
                                    'X51757',
                                    '3310',
                                    'ENSG00000173110',
                                    'NM_002155'],
                         '91826_at': ['EPS8L1',
                                      'GB:AI219073',
                                      'AI219073',
                                      '54869',
                                      '',
                                      'NM_017729'],
                         '91920_at': ['BCAN',
                                      'GB:AI205180',
                                      'AI205180',
                                      '63827',
                                      'ENSG00000132692',
                                      'NM_021948'],
                         '91952_at': ['',
                                      'GB:AI363375',
                                      'AI363375',
                                      '',
                                      '',
                                      ''],
                         'AFFX-TrpnX-3_at': ['', 'AFFX:AFFX-TrpnX-3', '', '', '', ''],
                         'AFFX-TrpnX-5_at': ['', 'AFFX:AFFX-TrpnX-5', '', '', '', ''],
                         'AFFX-TrpnX-M_at': ['', 'AFFX:AFFX-TrpnX-M', '', '', '', '']
                         }

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
        geneidmap = GeneIDMapHGNCGPL()
        self.assertFalse(geneidmap.built)
        self.assertIsNone(geneidmap.dbt)

    def test_build1(self):
        geneidmap = GeneIDMapHGNCGPL()
        # GPL96.txt
        gpl_path = os.path.abspath(os.path.join(self.test_data_root, 'gpl96_sample.txt'))
        gpl_comment = '#'
        gpl_delimiter = '\t'
        gpl_fh = DSV.getHandle(gpl_path)
        gpl_dsv = DSV(self.dbm, self.testdb, gpl_fh, dtname=self.annoTable, delimiter=gpl_delimiter, comment=gpl_comment)
        gpl_dsv.create()
        gpl_dsv.loadAll()
        gpl_dsv.close()
        # HGNC.tsv
        hgnc_path = os.path.abspath(os.path.join(self.test_data_root, 'hgnc_sample.txt'))
        hgnc_comment = '#'
        hgnc_delimiter = '\t'
        hgnc_fh = DSV.getHandle(hgnc_path)
        hgnc_dsv = DSV(self.dbm, self.testdb, hgnc_fh, dtname=self.hgncTable, delimiter=hgnc_delimiter, comment=hgnc_comment)
        hgnc_dsv.create()
        hgnc_dsv.loadAll()
        hgnc_dsv.close()
        # build test map
        geneidmap.build(gpl_dsv, hgnc_dsv, self.testdb)
        self.assertTrue(geneidmap.built)
        self.assertIsInstance(geneidmap.dbt, DBTable)
        fwdmap = dict(geneidmap.gene2emid.getFwdMap())
        self.assertEqual(self.ref_fwd1, fwdmap)
        bwdmap = dict(geneidmap.gene2emid.getBwdMap())
        self.assertEqual(self.ref_bwd1, bwdmap)

    def test_em2annotation1(self):
        geneidmap = GeneIDMapHGNCGPL()
        # GPL96.txt
        gpl_path = os.path.abspath(os.path.join(self.test_data_root, 'gpl96_sample.txt'))
        gpl_comment = '#'
        gpl_delimiter = '\t'
        gpl_fh = DSV.getHandle(gpl_path)
        gpl_dsv = DSV(self.dbm, self.testdb, gpl_fh, dtname=self.annoTable, delimiter=gpl_delimiter, comment=gpl_comment)
        gpl_dsv.create()
        gpl_dsv.loadAll()
        gpl_dsv.close()
        # HGNC.tsv
        hgnc_path = os.path.abspath(os.path.join(self.test_data_root, 'hgnc_sample.txt'))
        hgnc_comment = '#'
        hgnc_delimiter = '\t'
        hgnc_fh = DSV.getHandle(hgnc_path)
        hgnc_dsv = DSV(self.dbm, self.testdb, hgnc_fh, dtname=self.hgncTable, delimiter=hgnc_delimiter, comment=hgnc_comment)
        hgnc_dsv.create()
        hgnc_dsv.loadAll()
        hgnc_dsv.close()
        # build test map
        geneidmap.build(gpl_dsv, hgnc_dsv, self.testdb)
        em2a = get_em2annotation(geneidmap.dbt)
        self.assertEqual(self.ref_em2a, em2a)
