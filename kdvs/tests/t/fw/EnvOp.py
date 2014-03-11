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

from kdvs.tests import resolve_unittest
from kdvs.core.env import ExecutionEnvironment
from kdvs.fw.EnvOp import EnvOp

unittest = resolve_unittest()

class TestEnvOp1(unittest.TestCase):

    def setUp(self):
        self.env1 = ExecutionEnvironment({}, {})
        self.params1 = {}
        self.params2 = {
            'att1' : 'val1',
            'att2' : 'val2',
            }
        self.ref_params1 = ()
        self.ref_params2 = ('att1', 'att2')

    def test_init1(self):
        eop = EnvOp(self.ref_params1, **self.params1)
        self.assertEqual(self.params1, eop.parameters)

    def test_init2(self):
        eop = EnvOp(self.ref_params2, **self.params2)
        self.assertEqual(self.params2, eop.parameters)

    def test_perform1(self):
        eop = EnvOp(self.ref_params2, **self.params2)
        eop.perform(self.env1)
