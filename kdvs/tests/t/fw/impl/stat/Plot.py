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

from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import os
from kdvs.fw.impl.stat.Plot import MatplotlibPlot, MATPLOTLIB_GRAPH_BACKEND_PDF
import cStringIO
import imghdr
try:
    import matplotlib
    matplotlibFound = True
except ImportError:
    matplotlibFound = False

unittest = resolve_unittest()

@unittest.skipUnless(matplotlibFound, 'matplotlib not found')
class TestMatplotlibPlot1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.cfg1 = {}
        self.cfg2 = MATPLOTLIB_GRAPH_BACKEND_PDF
        self.plotcfg1 = {}
        self.plotcfg2 = {'format' : MATPLOTLIB_GRAPH_BACKEND_PDF['format']}
        self.plot_path1 = os.path.join(self.test_write_root, 'plot1')
#        matplotlib.rcdefaults()
#        matplotlib.rc_file_defaults()

    def test_init1(self):
        mplot = MatplotlibPlot()
        self.assertIsNone(mplot.driver)
        self.assertIsNone(mplot.backend)
        self.assertEqual({}, mplot.components)

    def test_configure1(self):
        mplot = MatplotlibPlot()
        mplot.configure(**self.cfg1)
        self.assertIsInstance(mplot.driver, mplot.matplotlib.pyplot.__class__)
        self.assertIsInstance(mplot.backend, cStringIO.StringIO().__class__)
        self.assertEqual({}, mplot.components)

    def test_configure2(self):
        mplot = MatplotlibPlot()
        mplot.configure(**self.cfg2)
        self.assertIsInstance(mplot.driver, mplot.matplotlib.pyplot.__class__)
        self.assertIsInstance(mplot.backend, cStringIO.StringIO().__class__)
        self.assertEqual({}, mplot.components)

    def test_plot1(self):
        mplot = MatplotlibPlot()
        mplot.configure(**self.cfg1)
        content = mplot.plot(**self.plotcfg1)
        self.assertTrue(len(content) > 0)
        contenttype = imghdr.what(self.plot_path1, content)
        if contenttype is None:
            if content.startswith('%PDF'):
                contenttype = 'pdf'
        filetypes = mplot.driver.figure().canvas.get_supported_filetypes()
        self.assertIn(contenttype, filetypes)

    def test_plot2(self):
        mplot = MatplotlibPlot()
        mplot.configure(**self.cfg2)
        content = mplot.plot(**self.plotcfg2)
        self.assertTrue(content.startswith("%PDF"))

