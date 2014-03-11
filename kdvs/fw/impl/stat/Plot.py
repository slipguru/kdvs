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

r"""
Provides base plot class that uses `matplotlib <http://matplotlib.org/contents.html>`__,
if installed. It can be subclassed to create specific (single) plot. By default,
plot can be generated as PDF or PNG.
"""

from kdvs.core.dep import verifyDepModule
from kdvs.core.util import importComponent
from kdvs.fw.Stat import Plot
import cStringIO

MATPLOTLIB_GRAPH_BACKEND_PDF = {
    'driver' : 'matplotlib.pyplot',
    'backend' : 'pdf',
    'format' : 'pdf',
}
r"""
Default configuration options for PDF plotting. The physical matplotlib backend
used is 'pdf' (see :mod:`matplotlib.backends.backend_pdf`). The physical driver
is :mod:`matplotlib.pyplot`.
"""

MATPLOTLIB_GRAPH_BACKEND_PNG = {
    'driver' : 'matplotlib.pyplot',
    'backend' : 'agg',
    'format' : 'png',
}
r"""
Default configuration options for PNG plotting. The physical matplotlib backend
used is 'agg' (see :ref:`here <what-is-a-backend>` for detailed explanation).
The physical driver is :mod:`matplotlib.pyplot`.
"""

class MatplotlibPlot(Plot):
    r"""
Base plot class that uses :mod:`matplotlib` as plot generator. During initialization,
it is verified (:func:`~kdvs.core.dep.verifyDepModule`) that matplotlib library is present.
    """
    def __init__(self):
        super(MatplotlibPlot, self).__init__()
        # import matplotlib and store module instance
        matplotlib = verifyDepModule('matplotlib')
        self.matplotlib = matplotlib

    def configure(self, **kwargs):
        r"""
Configure matplotlib plotter. The following configuration options can be used:

    * 'backend' (string) -- physical matplotlib backend
    * 'driver' (string) -- physical matplotlib driver

See `matplotlib documentation <http://matplotlib.org/contents.html>`__ for more details.

Parameters
----------
kwargs : dict
    configuration parameters of this plotter
        """
        # resolve matplotlib backend
        try:
            backend = kwargs['backend']
            self.matplotlib.use(backend, warn=False)
        except KeyError:
            self.matplotlib.use('agg', warn=False)
        # resolve matplotlib driver
        try:
            driver = kwargs['driver']
            driver_inst = importComponent(driver)
        except KeyError:
            driver_inst = importComponent('matplotlib.pyplot')
        self.driver = driver_inst
        # physical KDVS backend
        self.backend = cStringIO.StringIO()

    def create(self, **kwargs):
        r"""
This method needs to be re--implemented for producing actual plot. It should
obtain a reference to physical matplotlib driver (via `self.driver`), and set--up
all plot parameters as done normally with matplotlib. There is no need to physically
save the plot afterwards, e.g. with :func:`matplotlib.pyplot.savefig`; it will be
done later automatically. By default, this method does nothing.

Parameters
----------
kwargs : dict
    any additional arguments needed to construct the plot
        """
        # to be overriden by specific subclass
        pass

    def plot(self, **kwargs):
        r"""
Finalize created plot and return its content (i.e. actual physical file content)
to be saved by KDVS :class:`~kdvs.fw.StorageManager.StorageManager` in proper
location. The following configuration options can be used:

    * 'format' (string) -- physical file format that is supported by the backend

See `matplotlib documentation <http://matplotlib.org/contents.html>`__ for more details.

Parameters
----------
kwargs : dict
    any additional plot parameters

Returns
-------
content : string
    physical content of generated plot that can be saved normally into a file
        """
        try:
            fmt = kwargs['format']
        except KeyError:
            fmt = None
        plotdata = dict()
        plotdata.update(format=fmt)
        self.driver.savefig(self.backend, **plotdata)
        self.driver.close()
        content = self.backend.getvalue()
        self.backend.close()
        return content
