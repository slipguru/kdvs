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
from kdvs.fw.impl.pk.go.GeneOntology import GOManager, isGOID, GO_ROOT_TERMS, \
    GO_id2num, GO_num2id, GO_DS, GO_DEF_RECOGNIZED_RELATIONS
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import datetime
import os
from kdvs.fw.Map import SetBDMap
from kdvs.fw.PK import PKC_DETAIL_ELEMENTS

unittest = resolve_unittest()

class TestGOManager1(unittest.TestCase):

    def test_init1(self):
        go = GOManager()
        self.assertFalse(go.configured)

    def test_configure1(self):
        go = GOManager()
        # configure with default values
        go.configure()
        self.assertTrue(go.configured)
        self.assertEquals(tuple(GO_DS), go.domains)
        self.assertEqual(GO_DEF_RECOGNIZED_RELATIONS, go.recognizedRelations)
        self.assertIsInstance(go.domain2concepts, SetBDMap)
        self.assertIsInstance(go.synonyms, SetBDMap)
        self.assertIsInstance(go.terms, dict)
        self.assertFalse(hasattr(go, 'domain2validTerms'))
        self.assertItemsEqual(GO_DEF_RECOGNIZED_RELATIONS, go.termsRelationsHierarchy.keys())

    def test_configure2(self):
        ref_domains = ('D1', 'D2', 'DX')
        ref_relations = ('A', 'B', 'C')
        go = GOManager()
        # configure with custom values
        go.configure(domains=ref_domains, recognized_relations=ref_relations)
        self.assertTrue(go.configured)
        self.assertEquals(ref_domains, go.domains)
        self.assertEquals(ref_relations, go.recognizedRelations)
        self.assertItemsEqual(ref_relations, go.termsRelationsHierarchy.keys())

class TestGOManager2(unittest.TestCase):

    def setUp(self):
        self.sample_data_root = TEST_INVARIANTS['test_data_root']
        self.sample_obo_xml = os.path.abspath(os.path.join(self.sample_data_root, 'sample.obo-xml'))
        self.sample_err_obo_xml = os.path.abspath(os.path.join(self.sample_data_root, 'sample-err.obo-xml'))
        self.sample_xml_fh = open(self.sample_obo_xml, 'rb')
        self.sample_err_xml_fh = open(self.sample_err_obo_xml, 'rb')
        self.sample_format = '1.2'
        self.sample_release_date = datetime.datetime(2012, 02, 21, 15, 03)
        self.sample_root_tag = 'obo'
        self.sample_recognized_relations = ['is_a', 'part_of', 'regulates',
                                          'positively_regulates', 'negatively_regulates']
        self.sample_terms = set(['GO:0000001', 'GO:0000002', 'GO:0000003', 'GO:0000005',
                               'GO:0000006', 'GO:0000007', 'GO:0000008', 'GO:0000009',
                               'GO:0000010', 'GO:0000011', 'GO:0000012', 'GO:0000014',
                               'GO:0000015', 'GO:0000016', 'GO:0000017', 'GO:0000018',
                               'GO:0000019', 'GO:0000020', 'GO:0000022'])
        self.sample_obsolete_terms = set(['GO:0000005', 'GO:0000008', 'GO:0000020'])
        self.sample_valid_terms = self.sample_terms - self.sample_obsolete_terms
        self.sample_t19 = {'obsolete': False,
                         'name': 'regulation of mitotic recombination',
                         'desc': 'Any process that modulates the frequency, rate or '
                                 'extent of DNA recombination during mitosis.'}
        self.sample_t16 = {'obsolete': False,
                         'name': 'lactase activity',
                         'desc': 'Catalysis of the reaction: lactose + H2O = '
                                'D-glucose + D-galactose.'}
        self.pkc_t16 = {'additionalInfo': {'obsolete': False},
                        'conceptID': 'GO:0000016',
                        'domainID': ('molecular_function',),
                        'description': 'Catalysis of the reaction: lactose + H2O = '
                                        'D-glucose + D-galactose.',
                        'conceptName': 'lactase activity'}

        self.pkc_t19 = {'additionalInfo': {'obsolete': False},
                        'conceptID': 'GO:0000019',
                        'domainID': ('biological_process',),
                        'description': 'Any process that modulates the frequency, '
                                    'rate or extent of DNA recombination during mitosis.',
                        'conceptName': 'regulation of mitotic recombination'}
        self.samples = {'GO:0000016' : self.sample_t16, 'GO:0000019' : self.sample_t19}
        self.root_tag_x = 'AAA'
        self.d2c_fwd = {'molecular_function' : set(['GO:0000006', 'GO:0000007',
                                                   'GO:0000005', 'GO:0000010',
                                                   'GO:0000014', 'GO:0000008',
                                                   'GO:0000009', 'GO:0000016']),
                        'cellular_component': set(['GO:0000015']),
                        'biological_process': set(['GO:0000017', 'GO:0000011',
                                                   'GO:0000003', 'GO:0000012',
                                                   'GO:0000001', 'GO:0000019',
                                                   'GO:0000018', 'GO:0000020',
                                                   'GO:0000002', 'GO:0000022'])}
        self.d2c_bwd = {'GO:0000015' : set(['cellular_component']),
                        'GO:0000014' : set(['molecular_function']),
                        'GO:0000016' : set(['molecular_function']),
                        'GO:0000020' : set(['biological_process']),
                        'GO:0000011' : set(['biological_process']),
                        'GO:0000022' : set(['biological_process']),
                        'GO:0000010' : set(['molecular_function']),
                        'GO:0000006' : set(['molecular_function']),
                        'GO:0000007' : set(['molecular_function']),
                        'GO:0000017' : set(['biological_process']),
                        'GO:0000005' : set(['molecular_function']),
                        'GO:0000002' : set(['biological_process']),
                        'GO:0000003' : set(['biological_process']),
                        'GO:0000001' : set(['biological_process']),
                        'GO:0000012' : set(['biological_process']),
                        'GO:0000019' : set(['biological_process']),
                        'GO:0000018' : set(['biological_process']),
                        'GO:0000008' : set(['molecular_function']),
                        'GO:0000009': set(['molecular_function'])}
        self.go = GOManager()
        self.go.configure()

    def tearDown(self):
        self.sample_xml_fh.close()
        self.sample_err_xml_fh.close()

    def test_load1(self):
        with self.assertRaises(Error):
            self.go.load(self.sample_xml_fh, self.root_tag_x)

    def test_load2(self):
        with self.assertRaises(Error):
            self.go.load(self.sample_err_xml_fh)

    def test_load3(self):
        self.go.load(self.sample_xml_fh)
        self.assertEqual(self.sample_format, self.go._format)
        self.assertEqual(self.sample_release_date, self.go._release_date)
        self.assertEqual(self.sample_root_tag, self.go.root_tag)
        self.assertEqual(self.sample_recognized_relations, self.go.recognizedRelations)
        self.assertNotEqual(dict(), self.go.terms)
        self.assertEqual(self.sample_terms, set(self.go.terms.keys()))
        self.assertEqual(self.sample_obsolete_terms, set(self.go.obsolete_terms))
        self.assertEqual(self.sample_valid_terms, set(self.go.valid_terms))
        for t, td in self.samples.iteritems():
            self.assertEqual(td, self.go.terms[t])
        self.assertItemsEqual(self.sample_recognized_relations, self.go.termsRelationsHierarchy.keys())
        d2c_fwd = self.go.domain2concepts.dumpFwdMap()
        d2c_bwd = self.go.domain2concepts.dumpBwdMap()
        self.assertEqual(self.d2c_fwd, d2c_fwd)
        self.assertEqual(self.d2c_bwd, d2c_bwd)

    def test_getPKC1(self):
        self.go.load(self.sample_xml_fh)
        pkc_t16 = self.go.getPKC('GO:0000016')
        self.assertEqual(self.pkc_t16, pkc_t16._pkc)
        for det_key in PKC_DETAIL_ELEMENTS:
            self.assertEqual(self.pkc_t16[det_key], pkc_t16[det_key])
        pkc_t19 = self.go.getPKC('GO:0000019')
        self.assertEqual(self.pkc_t19, pkc_t19._pkc)
        for det_key in PKC_DETAIL_ELEMENTS:
            self.assertEqual(self.pkc_t19[det_key], pkc_t19[det_key])

    def test_getPKC2(self):
        self.go.load(self.sample_xml_fh)
        pkc = self.go.getPKC('GO:XXXXXXX')
        self.assertIsNone(pkc)

class TestGOManager3(unittest.TestCase):

    def setUp(self):
        self.sample_data_root = TEST_INVARIANTS['test_data_root']
        self.sample_obo_xml = os.path.abspath(os.path.join(self.sample_data_root, 'sample.obo-xml'))
        with open(self.sample_obo_xml, 'rb') as f:
            self.go = GOManager()
            self.go.configure()
            self.go.load(f)
        self.sample_xml_fh1 = open(self.sample_obo_xml, 'rb')
        self.sample_recognized_relations = ['is_a', 'part_of', 'regulates',
                                          'positively_regulates', 'negatively_regulates']
        self.recognized_relations_1 = ['is_a']
        self.notpresent_fwd_1 = ['GO:0000019', 'GO:0000022']
        self.notpresent_bwd_1 = ['GO:0006310', 'GO:0006312', 'GO:0007052']
        self.recognized_relations_2 = ['positively_regulates', 'negatively_regulates']
        self.present_fwd_2 = list()
        self.present_bwd_2 = list()
        self.recognized_relations_x = ['AAA', 'BBB']
        self.present_fwd_x = list()
        self.present_bwd_x = list()

    def tearDown(self):
        self.sample_xml_fh1.close()

    def test_hierarchy1(self):
        go1 = GOManager()
        go1.configure(recognized_relations=self.recognized_relations_1)
        go1.load(self.sample_xml_fh1)
        # recognize only 'is_a'
        self.assertItemsEqual(self.recognized_relations_1, go1.termsRelationsHierarchy.keys())
        # compare detailed hierarchy maps for 'is_a'
        mfwd1 = self.go.termsRelationsHierarchy['is_a'].dumpFwdMap()
        mbwd1 = self.go.termsRelationsHierarchy['is_a'].dumpBwdMap()
        cfwd1 = go1.termsRelationsHierarchy['is_a'].dumpFwdMap()
        cbwd1 = go1.termsRelationsHierarchy['is_a'].dumpBwdMap()
        self.assertEqual(mfwd1, cfwd1)
        self.assertEqual(mbwd1, cbwd1)
        # compare plain hierarchy maps
        mfwd2 = set(self.go.termsPlainHierarchy.dumpFwdMap().keys())
        mbwd2 = set(self.go.termsPlainHierarchy.dumpBwdMap().keys())
        cfwd2 = set(go1.termsPlainHierarchy.dumpFwdMap().keys())
        cbwd2 = set(go1.termsPlainHierarchy.dumpBwdMap().keys())
        self.assertNotEqual(mfwd2, cfwd2)
        self.assertEqual(set(self.notpresent_fwd_1), mfwd2 - cfwd2)
        self.assertNotEqual(mbwd2, cbwd2)
        self.assertEqual(set(self.notpresent_bwd_1), mbwd2 - cbwd2)

    def test_hierarchy2(self):
        go1 = GOManager()
        go1.configure(recognized_relations=self.recognized_relations_2)
        go1.load(self.sample_xml_fh1)
        # recognize only 'positively_regulates', 'negatively_regulates'
        self.assertItemsEqual(self.recognized_relations_2, go1.termsRelationsHierarchy.keys())
        # compare plain hierarchy maps
        mfwd2 = set(self.go.termsPlainHierarchy.dumpFwdMap().keys())
        mbwd2 = set(self.go.termsPlainHierarchy.dumpBwdMap().keys())
        cfwd2 = set(go1.termsPlainHierarchy.dumpFwdMap().keys())
        cbwd2 = set(go1.termsPlainHierarchy.dumpBwdMap().keys())
        self.assertNotEqual(mfwd2, cfwd2)
        self.assertEqual(set(self.present_fwd_2), cfwd2)
        self.assertNotEqual(mbwd2, cbwd2)
        self.assertEqual(set(self.present_bwd_2), cbwd2)

    def test_hierarchy3(self):
        go1 = GOManager()
        go1.configure(recognized_relations=self.recognized_relations_x)
        go1.load(self.sample_xml_fh1)
        # recognize 'AAA', 'BBB'
        self.assertItemsEqual(self.recognized_relations_x, go1.termsRelationsHierarchy.keys())
        # compare plain hierarchy maps
        mfwd2 = set(self.go.termsPlainHierarchy.dumpFwdMap().keys())
        mbwd2 = set(self.go.termsPlainHierarchy.dumpBwdMap().keys())
        cfwd2 = set(go1.termsPlainHierarchy.dumpFwdMap().keys())
        cbwd2 = set(go1.termsPlainHierarchy.dumpBwdMap().keys())
        self.assertNotEqual(mfwd2, cfwd2)
        self.assertEqual(set(self.present_fwd_x), cfwd2)
        self.assertNotEqual(mbwd2, cbwd2)
        self.assertEqual(set(self.present_bwd_x), cbwd2)

class TestGOManager4(unittest.TestCase):

    def setUp(self):
        self.sample_data_root = TEST_INVARIANTS['test_data_root']
        self.sample_obo_xml = os.path.abspath(os.path.join(self.sample_data_root, 'sample.obo-xml'))
        with open(self.sample_obo_xml, 'rb') as f:
            self.go = GOManager()
            self.go.configure()
            self.go.load(f)
        self.sample_xml_fh1 = open(self.sample_obo_xml, 'rb')
        self.sample_recognized_relations = ['is_a', 'part_of', 'regulates',
                                          'positively_regulates', 'negatively_regulates']
        self.sample_descendants_nodepth = {'GO:0000019' : set(['GO:0006312']),
                            'GO:0000018' : set(['GO:0006310', 'GO:0006312', 'GO:0000019']),
                            'GO:0000022' : set(['GO:0007052'])}
        self.sample_descendants_depth = {'GO:0000019' : set([('GO:0006312', 1)]),
                            'GO:0000018' : set([('GO:0006310', 1), ('GO:0000019', 1), ('GO:0006312', 2)]),
                            'GO:0000022' : set(set([('GO:0007052', 1)]))}
        self.sample_ancestors_nodepth = {'GO:0000006' : set(['GO:0005385']),
                                         'GO:0000007' : set(['GO:0005385']),
                                         'GO:0000017' : set(['GO:0042946']),
                                         'GO:0000002' : set(['GO:0007005']),
                                         'GO:0000003' : set(['GO:0008150']),
                                         'GO:0000001' : set(['GO:0048308', 'GO:0048311']),
                                         'GO:0000015' : set(['GO:0043234', 'GO:0044445']),
                                         'GO:0000012' : set(['GO:0006281']),
                                         'GO:0000019' : set(['GO:0000018', 'GO:0051052']),
                                         'GO:0000018' : set(['GO:0051052']),
                                         'GO:0000009' : set(['GO:0000030']),
                                         'GO:0000016' : set(['GO:0004553']),
                                         'GO:0000014' : set(['GO:0004520']),
                                         'GO:0000011' : set(['GO:0048308', 'GO:0007033']),
                                         'GO:0000022' : set(['GO:0051231']),
                                         'GO:0000010' : set(['GO:0016765'])}
        self.sample_ancestors_depth = {'GO:0000006' : set([('GO:0005385', -1)]),
                                     'GO:0000007' : set([('GO:0005385', -1)]),
                                     'GO:0000017' : set([('GO:0042946', -1)]),
                                     'GO:0000002' : set([('GO:0007005', -1)]),
                                     'GO:0000003' : set([('GO:0008150', -1)]),
                                     'GO:0000001' : set([('GO:0048308', -1), ('GO:0048311', -1)]),
                                     'GO:0000015' : set([('GO:0043234', -1), ('GO:0044445', -1)]),
                                     'GO:0000012' : set([('GO:0006281', -1)]),
                                     'GO:0000019' : set([('GO:0000018', -1), ('GO:0051052', -2)]),
                                     'GO:0000018' : set([('GO:0051052', -1)]),
                                     'GO:0000009' : set([('GO:0000030', -1)]),
                                     'GO:0000016' : set([('GO:0004553', -1)]),
                                     'GO:0000014' : set([('GO:0004520', -1)]),
                                     'GO:0000011' : set([('GO:0048308', -1), ('GO:0007033', -1)]),
                                     'GO:0000022' : set([('GO:0051231', -1)]),
                                     'GO:0000010' : set([('GO:0016765', -1)])}
        self.sample_synonyms = {'GO:0000003' : set(['GO:0050876', 'GO:0019952'])}

    def tearDown(self):
        self.sample_xml_fh1.close()

    def test_getDescendants1(self):
        descendants = dict()
        for term in self.go.valid_terms:
            desc = self.go.getDescendants(term, depth=False)
            if len(desc) > 0:
                descendants[term] = desc
        self.assertEqual(self.sample_descendants_nodepth, descendants)

    def test_getDescendants2(self):
        descendants = dict()
        for term in self.go.valid_terms:
            desc = self.go.getDescendants(term, depth=True)
            if len(desc) > 0:
                descendants[term] = desc
        self.assertEqual(self.sample_descendants_depth, descendants)

    def test_getAncestors1(self):
        ancestors = dict()
        for term in self.go.valid_terms:
            ancs = self.go.getAncestors(term, depth=False)
            if len(ancs) > 0:
                ancestors[term] = ancs
        self.assertEqual(self.sample_ancestors_nodepth, ancestors)

    def test_getAncestors2(self):
        ancestors = dict()
        for term in self.go.valid_terms:
            ancs = self.go.getAncestors(term, depth=True)
            if len(ancs) > 0:
                ancestors[term] = ancs
        self.assertEqual(self.sample_ancestors_depth, ancestors)

    def test_getSynonyms(self):
        synonyms = dict()
        for term in self.go.terms:
            syn = self.go.getSynonyms(term)
            if syn is not None:
                synonyms[term] = syn
        self.assertEqual(self.sample_synonyms, synonyms)


class TestGeneOntology1(unittest.TestCase):

    def test_isGOID1(self):
        self.assertTrue(isGOID('GO:0000001'))
        self.assertFalse(isGOID('0000001'))
        self.assertFalse(isGOID('XXX'))
        for t in GO_ROOT_TERMS.values():
            self.assertTrue(isGOID(t))

    def test_id2num1(self):
        ref_nonumint = {
            'GO:0008150' : '0008150',
            'GO:0005575' : '0005575',
            'GO:0003674' : '0003674',
        }
        ref_numint = {
            'GO:0008150' : 8150,
            'GO:0005575' : 5575,
            'GO:0003674' : 3674,
        }
        for t in GO_ROOT_TERMS.values():
            self.assertTrue(ref_numint[t], GO_id2num(t, numint=True))
        for t in GO_ROOT_TERMS.values():
            self.assertTrue(ref_nonumint[t], GO_id2num(t, numint=False))

    def test_num2id1(self):
        ref_nonumint = {
            '0008150' : 'GO:0008150',
            '0005575' : 'GO:0005575',
            '0003674' : 'GO:0003674',
        }
        ref_numint = {
            8150 : 'GO:0008150',
            5575 : 'GO:0005575',
            3674 : 'GO:0003674',
        }
        for t in ('0008150', '0005575', '0003674'):
            self.assertTrue(ref_nonumint[t], GO_num2id(t))
        for t in (8150, 5575, 3674):
            self.assertTrue(ref_numint[t], GO_num2id(t))

    def test_num2id2(self):
        with self.assertRaises(Error):
            GO_num2id(None)
        with self.assertRaises(Error):
            GO_num2id('XXX')
        # cut one zero
        with self.assertRaises(Error):
            GO_num2id('008150')
