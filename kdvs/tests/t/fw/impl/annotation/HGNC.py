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
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os
from kdvs.fw.impl.annotation.HGNC import correctHGNCApprovedSymbols, \
    generateHGNCPreviousSymbols, generateHGNCSynonyms

unittest = resolve_unittest()

class TestHGNC1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.hgncTable = 'HGNC'
        self.dbm = DBManager(self.test_write_root)
        #
        hgnc_path = os.path.abspath(os.path.join(self.test_data_root, 'hgnc_sample_2.txt'))
        hgnc_comment = '#'
        hgnc_delimiter = '\t'
        hgnc_fh = DSV.getHandle(hgnc_path)
        self.hgnc_dsv = DSV(self.dbm, self.testdb, hgnc_fh, dtname=self.hgncTable, delimiter=hgnc_delimiter, comment=hgnc_comment)
        self.hgnc_dsv.create()
        self.hgnc_dsv.loadAll()
        self.hgnc_dsv.close()
        #
        self.withdrawn_pattern = '%~withdrawn'
        self.symbol_col = 'Approved Symbol'
        #
        # NOTE: we use unicode since we do not reparse immediately after querying
        self.ref_previous1 = {
                              u'NTRK4' : [u'DDR1'],
                              u'PTK3A' : [u'DDR1'],
                              u'NEP' : [u'DDR1'],
                              u'CAK' : [u'DDR1'],
                              u'EDDR1' : [u'DDR1'],
                              u'C19orf72' : [u'DCAF15'],
                              }
        self.ref_synonyms1 = {
                              u'A1': [u'RFC2'],
                              u'BEHAB': [u'BCAN'],
                              u'CD167': [u'DDR1'],
                              u'CSPG7': [u'BCAN'],
                              u'DRC3': [u'EPS8L1'],
                              u'FLJ20258': [u'EPS8L1'],
                              u'MGC13038': [u'BCAN'],
                              u'MGC23164': [u'EPS8L1'],
                              u'MGC4642': [u'EPS8L1'],
                              u'MGC99481': [u'DCAF15'],
                              u'RFC40': [u'RFC2'],
                              u'RTK6': [u'DDR1']
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

    def test_correctHGNCApprovedSymbols1(self):
        correctHGNCApprovedSymbols(self.hgnc_dsv)
        # check that no symbol has '~withdrawn' suffix
        c = self.hgnc_dsv.db.cursor()
        st = 'select "%s" from %s where "%s" like "%s"' % (self.symbol_col, self.hgncTable, self.symbol_col, self.withdrawn_pattern)
        c.execute(st)
        res = list([r for r in c])
        self.assertEqual([], res)
        c.close()

    def test_generateHGNCPreviousSymbols1(self):
        previous_dt = generateHGNCPreviousSymbols(self.hgnc_dsv, self.testdb)
        res = previous_dt.getAll(as_dict=True, dict_on_rows=True)
        self.assertEqual(self.ref_previous1, res)

    def test_generateHGNCSynonyms1(self):
        synonyms_dt = generateHGNCSynonyms(self.hgnc_dsv, self.testdb)
        res = synonyms_dt.getAll(as_dict=True, dict_on_rows=True)
        self.assertEqual(self.ref_synonyms1, res)
