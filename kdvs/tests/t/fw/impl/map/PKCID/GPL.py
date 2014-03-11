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
from kdvs.fw.DBTable import DBTable
from kdvs.fw.DSV import DSV
from kdvs.fw.Map import SetBDMap
from kdvs.fw.impl.map.PKCID.GPL import PKCIDMapGOGPL
from kdvs.fw.impl.pk.go.GeneOntology import GO_DS
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os

unittest = resolve_unittest()

class TestPKCIDMapGOGPL1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.testdb = 'DB1'
        self.annoTable = 'MA_GPL_ANNO'
        self.dbm = DBManager(self.test_write_root)
        # three first and three last (non-control)
        self.test_probes = ['1007_s_at', '1053_at', '117_at', '91826_at', '91920_at', '91952_at']
        # three last control probes
        self.test_ctrl_probes = ['AFFX-TrpnX-3_at', 'AFFX-TrpnX-5_at', 'AFFX-TrpnX-M_at']
        # reference bwd mapping
        self.test_bwd = {
            '1007_s_at' : set([ 'GO:0000166',
                     'GO:0004672',
                     'GO:0004713',
                     'GO:0004714',
                     'GO:0004872',
                     'GO:0005515',
                     'GO:0005524',
                     'GO:0005887',
                     'GO:0006468',
                     'GO:0007155',
                     'GO:0007169',
                     'GO:0016020',
                     'GO:0016021',
                     'GO:0016301',
                     'GO:0016740']),
            '1053_at' : set([ 'GO:0000166',
                   'GO:0003677',
                   'GO:0003689',
                   'GO:0005515',
                   'GO:0005524',
                   'GO:0005634',
                   'GO:0005654',
                   'GO:0005663',
                   'GO:0006260',
                   'GO:0006297',
                   'GO:0017111']),
            '117_at' : set(['GO:0000166',
                    'GO:0005524',
                    'GO:0006950',
                    'GO:0006986']),
            '91826_at' : set(['GO:0004872',
                    'GO:0005737',
                    'GO:0016301']),
            '91920_at': set([ 'GO:0005488',
                    'GO:0005529',
                    'GO:0005540',
                    'GO:0005576',
                    'GO:0005578',
                    'GO:0005634',
                    'GO:0005730',
                    'GO:0005737',
                    'GO:0005739',
                    'GO:0007155',
                    'GO:0016020',
                    'GO:0016021',
                    'GO:0031225']),
            '91952_at': set(['GO:0006511']),
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
        pkcidmap = PKCIDMapGOGPL()
        self.assertFalse(pkcidmap.built)
        self.assertIsNone(pkcidmap.dbt)
        self.assertItemsEqual(GO_DS, pkcidmap.domains_map.keys())
        for dm in pkcidmap.domains_map.values():
            self.assertIsInstance(dm, SetBDMap)
            self.assertEqual(0, len(dm.getFwdMap().keys()))

    def test_build1(self):
        pkcidmap = PKCIDMapGOGPL()
        # GPL96.txt
#        gpl_path = os.path.abspath(os.path.join(self.test_data_root, 'GPL96.txt.bz2'))
        gpl_path = os.path.abspath(os.path.join(self.test_data_root, 'gpl96_sample.txt'))
        gpl_comment = '#'
        gpl_delimiter = '\t'
        gpl_fh = DSV.getHandle(gpl_path)
        gpl_dsv = DSV(self.dbm, self.testdb, gpl_fh, dtname=self.annoTable, delimiter=gpl_delimiter, comment=gpl_comment)
        gpl_dsv.create()
        gpl_dsv.loadAll()
        gpl_dsv.close()
        pkcidmap.build(gpl_dsv, self.testdb)
        self.assertTrue(pkcidmap.built)
        self.assertIsInstance(pkcidmap.dbt, DBTable)
        # test bidirectional map
        bwdmap = pkcidmap.pkc2emid.getBwdMap()
        fwdmap = pkcidmap.pkc2emid.getFwdMap()
        # check valid probes and terms for existence
        for ref_probe, ref_terms in self.test_bwd.iteritems():
            # backward map
            self.assertIn(ref_probe, bwdmap)
            terms = bwdmap[ref_probe]
            self.assertEqual(ref_terms, terms)
            # forward map
            for term in terms:
                self.assertIn(term, fwdmap)
                probes = fwdmap[term]
                self.assertIn(ref_probe, probes)
        # check control probes for nonexistence
        for test_ctrl in self.test_ctrl_probes:
            # backward map
            self.assertNotIn(test_ctrl, bwdmap)
        for probes in fwdmap.values():
            # forward map
            self.assertNotIn(test_ctrl, probes)

#        import pprint
#        with open('pkcidmap.txt', 'wb') as f:
#            pprint.pprint(pkcidmap.pkc2emid.dumpFwdMap(), f, indent=2)
#            pprint.pprint(pkcidmap.pkc2emid.dumpBwdMap(), f, indent=2)
#        with open('domainsmap_fwd.txt', 'wb') as f:
#            for go_ds, gm in pkcidmap.domains_map.iteritems():
#                f.write("%s\n" % go_ds)
#                pprint.pprint(gm.dumpFwdMap(), f, indent=2)
#        with open('domainsmap_bwd.txt', 'wb') as f:
#            for go_ds, gm in pkcidmap.domains_map.iteritems():
#                f.write("%s\n" % go_ds)
#                pprint.pprint(gm.dumpBwdMap(), f, indent=2)



