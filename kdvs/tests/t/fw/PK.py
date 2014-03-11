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
from kdvs.fw.PK import PriorKnowledgeConcept, PKC_DETAIL_ELEMENTS, PKCManager
from kdvs.tests import resolve_unittest

unittest = resolve_unittest()

class TestPKC1(unittest.TestCase):

    def setUp(self):
        self.concept1 = 'concept1'
        self.cname1 = 'cname1'
        self.refPKCElems1 = {'conceptID' : self.concept1,
                            'conceptName' : self.cname1,
                            'domainID' : None,
                            'description' : None,
                            'additionalInfo' : {},
                            }
        self.concept2 = 'concept2'
        self.cname2 = 'name2'
        self.domain2 = 'some_domain'
        self.desc2 = 'some description'
        self.addinfo2 = {'ik1' : 'iv1', 'ik2' : None, 'ik3' : 7000}
        self.refPKCElems2 = {'conceptID' : self.concept2,
                            'conceptName' : self.cname2,
                            'domainID' : self.domain2,
                            'description' : self.desc2,
                            'additionalInfo' : self.addinfo2,
                            }

    def test_init1(self):
        pkc = PriorKnowledgeConcept(self.concept1, self.cname1)
        for k, v in self.refPKCElems1.iteritems():
            self.assertEqual(v, pkc[k])

    def test_init2(self):
        pkc = PriorKnowledgeConcept(self.concept2, self.cname2, self.domain2, self.desc2, self.addinfo2)
        for k, v in self.refPKCElems2.iteritems():
            self.assertEqual(v, pkc[k])

    def test_keys1(self):
        pkc = PriorKnowledgeConcept(self.concept1, self.cname1)
        self.assertEqual(set(PKC_DETAIL_ELEMENTS), set(pkc.keys()))


class TestPKCManager1(unittest.TestCase):

    def test_init1(self):
        pkm = PKCManager()
        self.assertFalse(pkm.isConfigured())
        self.assertEqual(0, len(pkm.domains))
        self.assertEqual(0, len(pkm.domain2concepts.getFwdMap()))

    def test_load1(self):
        pkm = PKCManager()
        with self.assertRaises(Error):
            pkm.load(None)
