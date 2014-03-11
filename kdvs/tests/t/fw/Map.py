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
from kdvs.fw.Map import ChainMap, NOTMAPPED, ListBDMap, SetBDMap, PKCIDMap, \
    PKCGeneMap, GeneIDMap
from kdvs.tests import resolve_unittest
import collections
import itertools

unittest = resolve_unittest()

class TestChainMap1(unittest.TestCase):

    def setUp(self):
        self.emptyMap = dict()
        self.mdict1 = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}

    def tearDown(self):
        pass

    def test_init1(self):
        cm1 = ChainMap()
        self.assertDictEqual(self.emptyMap, cm1.getMap())

    def test_init2(self):
        cm1 = ChainMap(initial_dict=self.mdict1)
        self.assertDictEqual(self.mdict1, cm1.getMap())

class TestChainMap2(unittest.TestCase):

    def setUp(self):
        self.tomap1 = ('a', 'b', 'c', 'd')
        self.mapped1 = (1, 2, 3, 4)
        self.tomap2 = ('a', 'b', 'c', 'd')
        self.mapped2 = (11, 22, 33, 44)
        self.tomap3 = ()
        self.mapped3 = (1,)
        self.tomap4 = ('a',)
        self.mapped4 = ()

        self.mdict1 = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}
        self.mdict2 = {1 : 100, 2 : 200, 3 : 300, 4 : 400}
        self.mdict3 = {100 : 1, 200 : 2, 300 : 3, 400 : 4}
        self.mdict4 = {1 : 'a', 2 : 'b', 3 : 'c', 4 : 'd'}

        self.map1 = ChainMap(self.mdict1)
        self.map2 = ChainMap(self.mdict2)
        self.map3 = ChainMap(self.mdict3)
        self.map4 = ChainMap(self.mdict4)

        self.allmapped1 = {'a': 'a', 'c': 'c', 'b': 'b', 'd': 'd'}
        self.allinterms1 = [[1, 100, 1, 'a'], [2, 200, 2, 'b'], [3, 300, 3, 'c'], [4, 400, 4, 'd']]
        self.alllast1 = [None, None, None, None]

        self.errdict2 = {1 : 100, 2 : 444, 3 : 300, 4 : 400}
        self.map22 = ChainMap(self.errdict2)
        self.allmapped2 = {'a': 'a', 'c': 'c', 'b': NOTMAPPED, 'd': 'd'}
        self.allinterms2 = [[1, 100, 1, 'a'], [2, 444], [3, 300, 3, 'c'], [4, 400, 4, 'd']]
        self.alllast2 = [None, self.map3, None, None]

        self.mapchain1 = (self.map1, self.map2, self.map3, self.map4)
        self.mapchain2 = (self.map1, self.map22, self.map3, self.map4)
        self.mapthem = ('a', 'b', 'c', 'd')

    def tearDown(self):
        pass

    def test_getset1(self):
        cm1 = ChainMap()
        res_map = cm1.getMap()
        cm1['XXX'] = '111'
        self.assertEqual('111', res_map['XXX'])
        cm1['XXX'] = '222'
        self.assertNotEqual('111', res_map['XXX'])
        self.assertEqual('222', res_map['XXX'])

    def test_getset2(self):
        cm1 = ChainMap()
        for k, v in zip(self.tomap1, self.mapped1):
            cm1[k] = v
        self.assertDictEqual(self.mdict1, cm1.getMap())
        self.assertEqual(NOTMAPPED, cm1['XXX'])

    def test_update1(self):
        cm1 = ChainMap()
        content1 = dict([(k, v) for k, v in zip(self.tomap1, self.mapped1)])
        content2 = dict([(k, v) for k, v in zip(self.tomap2, self.mapped2)])
        cm1.update(content1, replace=True)
        self.assertDictEqual(content1, cm1.getMap())
        cm1.update(content2, replace=True)
        self.assertDictEqual(content2, cm1.getMap())
        with self.assertRaises(Error):
            cm1.update(content1, replace=False)
        self.assertNotEqual(content1, cm1.getMap())
        self.assertDictEqual(content2, cm1.getMap())

    def test_update2(self):
        cm1 = ChainMap()
        content1 = dict([(k, v) for k, v in itertools.izip_longest(self.tomap3, self.mapped3)])
        content2 = dict([(k, v) for k, v in itertools.izip_longest(self.tomap4, self.mapped4)])
        cm1.update(content1)
        cm1.update(content2)
        self.assertEqual(1, cm1[cm1['a']])

    def test_deriveMap1(self):
        for ix, tomap in enumerate(self.mapthem):
            derived, interm, last_map = ChainMap.deriveMap(tomap, self.mapchain1)
            self.assertEqual(self.allmapped1[tomap], derived)
            self.assertEqual(self.allinterms1[ix], interm)
            self.assertEqual(self.alllast1[ix], last_map)

    def test_deriveMap2(self):
        for ix, tomap in enumerate(self.mapthem):
            derived, interm, last_map = ChainMap.deriveMap(tomap, self.mapchain2)
            self.assertEqual(self.allmapped2[tomap], derived)
            self.assertEqual(self.allinterms2[ix], interm)
            self.assertEqual(self.alllast2[ix], last_map)

    def test_buildDerivedMap1(self):
        resmap, resinterm = ChainMap.buildDerivedMap(self.mapthem, self.mapchain1)
        self.assertEqual(self.allmapped1, resmap.getMap())
        self.assertEqual(self.allinterms1, resinterm)

    def test_buildDerivedMap2(self):
        resmap, resinterm = ChainMap.buildDerivedMap(self.mapthem, self.mapchain2)
        self.assertEqual(self.allmapped2, resmap.getMap())
        self.assertEqual(self.allinterms2, resinterm)

class TestListBDMap1(unittest.TestCase):

    def setUp(self):
        self.emptyFwdMap = collections.defaultdict(list)
        self.emptyBwdMap = collections.defaultdict(list)
        self.mdict1 = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}
        self.fwdmap1 = {'a' : [1], 'b' : [2], 'c' : [3], 'd' : [4]}
        self.bwdmap1 = {1 : ['a'], 2 : ['b'], 3 : ['c'], 4 : ['d']}

    def tearDown(self):
        pass

    def test_init1(self):
        bd1 = ListBDMap()
        self.assertEqual(self.emptyFwdMap, bd1.getFwdMap())
        self.assertEqual(self.emptyBwdMap, bd1.getBwdMap())

    def test_init2(self):
        bd1 = ListBDMap(initial_map=self.mdict1)
        self.assertEqual(self.fwdmap1, bd1.dumpFwdMap())
        self.assertEqual(self.bwdmap1, bd1.dumpBwdMap())

class TestListBDMap2(unittest.TestCase):

    def setUp(self):
        self.mdict1 = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}
        self.fwdmap1 = {'a' : [1], 'b' : [2], 'c' : [3], 'd' : [4]}
        self.bwdmap1 = {1 : ['a'], 2 : ['b'], 3 : ['c'], 4 : ['d']}

        self.mdat2 = [('a', 1), ('a', 2), ('c', 3), ('d', 4)]
        self.fwdmap2 = {'a' : [1, 2], 'c' : [3], 'd' : [4]}
        self.bwdmap2 = {1 : ['a'], 2 : ['a'], 3 : ['c'], 4 : ['d']}

        self.mdat3 = [('a', 1), ('a', 2), ('c', 3), ('d', 4), ('e', 2), ('f', 1)]
        self.fwdmap3 = {'a' : [1, 2], 'c' : [3], 'd' : [4], 'e' : [2], 'f' : [1]}
        self.bwdmap3 = {1 : ['a', 'f'], 2 : ['a', 'e'], 3 : ['c'], 4 : ['d']}

        self.circular = {'a': [1], 1: ['a']}

    def tearDown(self):
        pass

    def test_set1(self):
        bd1 = ListBDMap()
        bd1['a'] = 1
        bd1[1] = 'a'
        self.assertEqual(self.circular, bd1.dumpFwdMap())
        self.assertEqual(self.circular, bd1.dumpBwdMap())

    def test_set2(self):
        bd1 = ListBDMap()
        for k, v in self.mdat2:
            bd1[k] = v
        self.assertEqual(self.fwdmap2, bd1.dumpFwdMap())
        self.assertEqual(self.bwdmap2, bd1.dumpBwdMap())

    def test_set3(self):
        bd1 = ListBDMap()
        for k, v in self.mdat3:
            bd1[k] = v
        self.assertEqual(self.fwdmap3, bd1.dumpFwdMap())
        self.assertEqual(self.bwdmap3, bd1.dumpBwdMap())

    def test_get1(self):
        bd1 = ListBDMap()
        bd1['a'] = 1
        self.assertEqual([1], bd1['a'])
        self.assertEqual(bd1.keyIsMissing(), bd1['XXX'])

    def test_del1(self):
        bd1 = ListBDMap()
        bd1['a'] = 1
        bd1['a'] = 1
        bd1['a'] = 2
        bd1['a'] = 2
        bd1['b'] = 1
        bd1['b'] = 1
        bd1['b'] = 2
        bd1['b'] = 2
        ref1_fwd = {'a': [1, 1, 2, 2], 'b': [1, 1, 2, 2]}
        ref1_bwd = {1: ['a', 'a', 'b', 'b'], 2: ['a', 'a', 'b', 'b']}
        self.assertEqual(ref1_fwd, bd1.dumpFwdMap())
        self.assertEqual(ref1_bwd, bd1.dumpBwdMap())
        del bd1['b']
        ref2_fwd = {'a': [1, 1, 2, 2]}
        ref2_bwd = {1: ['a', 'a'], 2: ['a', 'a']}
        self.assertEqual(ref2_fwd, bd1.dumpFwdMap())
        self.assertEqual(ref2_bwd, bd1.dumpBwdMap())

    def test_clear1(self):
        bd1 = ListBDMap()
        for k, v in self.mdat2:
            bd1[k] = v
        bd1.clear()
        self.assertItemsEqual({}, bd1.fwd_map)
        self.assertItemsEqual({}, bd1.bwd_map)

class TestSetBDMap1(unittest.TestCase):

    def setUp(self):
        self.emptyFwdMap = collections.defaultdict(set)
        self.emptyBwdMap = collections.defaultdict(set)
        self.mdict1 = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}
        self.fwdmap1 = {'a' : set([1]), 'b' : set([2]), 'c' : set([3]), 'd' : set([4])}
        self.bwdmap1 = {1 : set(['a']), 2 : set(['b']), 3 : set(['c']), 4 : set(['d'])}

    def tearDown(self):
        pass

    def test_init1(self):
        bd1 = SetBDMap()
        self.assertEqual(self.emptyFwdMap, bd1.getFwdMap())
        self.assertEqual(self.emptyBwdMap, bd1.getBwdMap())

    def test_init2(self):
        bd1 = SetBDMap(initial_map=self.mdict1)
        self.assertEqual(self.fwdmap1, bd1.dumpFwdMap())
        self.assertEqual(self.bwdmap1, bd1.dumpBwdMap())

class TestSetBDMap2(unittest.TestCase):

    def setUp(self):
        self.mdict1 = {'a' : 1, 'b' : 2, 'c' : 3, 'd' : 4}
        self.fwdmap1 = {'a' : set([1]), 'b' : set([2]), 'c' : set([3]), 'd' : set([4])}
        self.bwdmap1 = {1 : set(['a']), 2 : set(['b']), 3 : set(['c']), 4 : set(['d'])}

        self.mdat2 = [('a', 1), ('a', 2), ('c', 3), ('d', 4)]
        self.fwdmap2 = {'a' : set([1, 2]), 'c' : set([3]), 'd' : set([4])}
        self.bwdmap2 = {1 : set(['a']), 2 : set(['a']), 3 : set(['c']), 4 : set(['d'])}

        self.mdat3 = [('a', 1), ('a', 2), ('c', 3), ('d', 4), ('e', 2), ('f', 1)]
        self.fwdmap3 = {'a' : set([1, 2]), 'c' : set([3]), 'd' : set([4]), 'e' : set([2]), 'f' : set([1])}
        self.bwdmap3 = {1 : set(['a', 'f']), 2 : set(['a', 'e']), 3 : set(['c']), 4 : set(['d'])}

        self.circular = {'a': set([1]), 1: set(['a'])}

    def tearDown(self):
        pass

    def test_set1(self):
        bd1 = SetBDMap()
        bd1['a'] = 1
        bd1[1] = 'a'
        self.assertEqual(self.circular, bd1.dumpFwdMap())
        self.assertEqual(self.circular, bd1.dumpBwdMap())

    def test_set2(self):
        bd1 = SetBDMap()
        for k, v in self.mdat2:
            bd1[k] = v
        self.assertEqual(self.fwdmap2, bd1.dumpFwdMap())
        self.assertEqual(self.bwdmap2, bd1.dumpBwdMap())

    def test_set3(self):
        bd1 = SetBDMap()
        for k, v in self.mdat3:
            bd1[k] = v
        self.assertEqual(self.fwdmap3, bd1.dumpFwdMap())
        self.assertEqual(self.bwdmap3, bd1.dumpBwdMap())

    def test_get1(self):
        bd1 = SetBDMap()
        bd1['a'] = 1
        self.assertEqual(set([1]), bd1['a'])
        self.assertEqual(bd1.keyIsMissing(), bd1['XXX'])

    def test_del1(self):
        bd1 = SetBDMap()
        bd1['a'] = 1
        bd1['a'] = 1
        bd1['a'] = 2
        bd1['a'] = 2
        bd1['b'] = 1
        bd1['b'] = 1
        bd1['b'] = 2
        bd1['b'] = 2
        ref1_fwd = {'a': set([1, 2]), 'b': set([1, 2])}
        ref1_bwd = {1: set(['a', 'b']), 2: set(['a', 'b'])}
        self.assertEqual(ref1_fwd, bd1.dumpFwdMap())
        self.assertEqual(ref1_bwd, bd1.dumpBwdMap())
        del bd1['b']
        ref2_fwd = {'a': set([1, 2])}
        ref2_bwd = {1: set(['a']), 2: set(['a'])}
        self.assertEqual(ref2_fwd, bd1.dumpFwdMap())
        self.assertEqual(ref2_bwd, bd1.dumpBwdMap())

    def test_clear1(self):
        bd1 = SetBDMap()
        for k, v in self.mdat2:
            bd1[k] = v
        bd1.clear()
        self.assertItemsEqual({}, bd1.fwd_map)
        self.assertItemsEqual({}, bd1.bwd_map)

class TestPKCIDMap1(unittest.TestCase):

    def setUp(self):
        self.emptyFwdMap = collections.defaultdict(set)
        self.emptyBwdMap = collections.defaultdict(set)

    def tearDown(self):
        pass

    def test_init1(self):
        bd = PKCIDMap()
        self.assertIsInstance(bd.pkc2emid, SetBDMap)
        self.assertEqual(self.emptyFwdMap, bd.pkc2emid.getFwdMap())
        self.assertEqual(self.emptyBwdMap, bd.pkc2emid.getBwdMap())

    def test_build1(self):
        bd = PKCIDMap()
        with self.assertRaises(NotImplementedError):
            bd.build()

class TestPKCGeneMap1(unittest.TestCase):

    def setUp(self):
        self.emptyFwdMap = collections.defaultdict(set)
        self.emptyBwdMap = collections.defaultdict(set)

    def tearDown(self):
        pass

    def test_init1(self):
        bd = PKCGeneMap()
        self.assertIsInstance(bd.pkc2gene, SetBDMap)
        self.assertEqual(self.emptyFwdMap, bd.pkc2gene.getFwdMap())
        self.assertEqual(self.emptyBwdMap, bd.pkc2gene.getBwdMap())

    def test_build1(self):
        bd = PKCGeneMap()
        with self.assertRaises(NotImplementedError):
            bd.build()

class TestGeneIDMap1(unittest.TestCase):

    def setUp(self):
        self.emptyFwdMap = collections.defaultdict(set)
        self.emptyBwdMap = collections.defaultdict(set)

    def tearDown(self):
        pass

    def test_init1(self):
        bd = GeneIDMap()
        self.assertIsInstance(bd.gene2emid, SetBDMap)
        self.assertEqual(self.emptyFwdMap, bd.gene2emid.getFwdMap())
        self.assertEqual(self.emptyBwdMap, bd.gene2emid.getBwdMap())

    def test_build1(self):
        bd = GeneIDMap()
        with self.assertRaises(NotImplementedError):
            bd.build()
