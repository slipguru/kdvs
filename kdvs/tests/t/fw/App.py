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
from kdvs.fw.App import AppProfile
from kdvs.tests import resolve_unittest

unittest = resolve_unittest()

class TestAppProfile1(unittest.TestCase):

    def setUp(self):
        self.def_p1 = {'key1' : '', 'key2' : 0.0, 'key3' : (), 'key4' : [], 'key5' : {}}
        self.p1 = {'key1' : 'val1',
                   'key2' : 1.0,
                   'key3' : ('val31', 'val32'),
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'}
                   }
        self.p2 = {'key1' : 'val1',
                   'key2' : 1.0,
                   'key3' : ('val31', 'val32'),
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'},
                   'key6' : 'Additional val',
                   }
        self.px1 = {'key1' : 'val1',
                   'key2' : 1.0,
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'},
                   }
        self.px2 = {'key1' : 'val1',
                   'key2' : 'XXXXXX',
                   'key3' : ('val31', 'val32'),
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'},
                   }

    def test_init1(self):
        p = AppProfile(self.def_p1, self.p1)
        self.assertEqual(self.p1, p._cfg)
        self.assertItemsEqual(self.p1.keys(), p.keys())
        for pk in self.p1.keys():
            self.assertEqual(self.p1[pk], p[pk])

    def test_init2(self):
        # profile definition specifies only the required components
        p = AppProfile(self.def_p1, self.p2)
        self.assertEqual(self.p1, p._cfg)
        # extra profile components are silently ignored
        self.assertNotIn('key6', p.keys())

    def test_init3(self):
        # missing required component
        with self.assertRaises(Error):
            AppProfile(self.def_p1, self.px1)

    def test_init4(self):
        # wrong type of component
        with self.assertRaises(Error):
            AppProfile(self.def_p1, self.px2)
