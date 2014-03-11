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

from kdvs.core.env import ExecutionEnvironment
from kdvs.core.error import Error
from kdvs.fw.impl.envop.L1L2 import L1L2_UniformExtSplitProvider
from kdvs.tests import resolve_unittest
try:
    import l1l2py
    l1l2pyFound = True
except ImportError:
    l1l2pyFound = False

unittest = resolve_unittest()

# TODO: finish when operations map is transformed into API controlled object

@unittest.skipUnless(l1l2pyFound, 'l1l2py not found')
class TestL1L2_UniformExtSplitProvider1(unittest.TestCase):

    def setUp(self):
        self.env1 = ExecutionEnvironment({}, {})
        self.params1 = {
            'enclosingCategorizerID' : 'Null',
            'extSplitParamName' : 'external_k',
            'extSplitPlaceholderParam' : 'ext_split_sets',
        }
        self.params2 = {}

    def test_init1(self):
        uesp = L1L2_UniformExtSplitProvider(**self.params1)
        self.assertEqual(self.params1, uesp.parameters)

    def test_init2(self):
        with self.assertRaises(Error):
            L1L2_UniformExtSplitProvider(**self.params2)

    def test_perform1(self):
        uesp = L1L2_UniformExtSplitProvider(**self.params1)
        with self.assertRaises(ValueError):
            uesp.perform(self.env1)

