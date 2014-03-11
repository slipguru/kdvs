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
Provides abstract functionality of applications built on KDVS API. Each concrete
application class must be derived from App class.
"""

from kdvs.core.error import Error
from kdvs.core.util import quote, Configurable

class App(object):
    r"""
Abstract KDVS application.
    """
    def __init__(self):
        r"""
By default, the constructor calls 'self.prepareEnv'.

See Also
--------
prepareEnv
        """
        self.env = None
        self.prepareEnv()

    def prepareEnv(self):
        r"""
Must be implemented in subclass. The implementation MUST assign fully configured
concrete :class:`~kdvs.core.env.ExecutionEnvironment` instance to `self.env` in
order for application to be
runnable from within KDVS in normal way. However, if one wants greater control
over application behavior, 'run' method must be re--implemented as well. See
'run' for more details.
        """
        raise NotImplementedError('Must be implemented in subclass!')

    def appProlog(self):
        r"""
By default it does nothing.
        """
        pass

    def appEpilog(self):
        r"""
By default it does nothing.
        """
        pass

    def prepare(self):
        r"""
By default it does nothing.
        """
        pass

    def run(self):
        r"""
By default it performs the following sequence of calls:
`self.appProlog`, `self.prepare`, `self.env.execute`, `self.appEpilog`.
        """
        self.appProlog()
        self.prepare()
        self.env.execute()
        self.appEpilog()


class AppProfile(Configurable):
    r"""
Abstract class for application profile. Concrete KDVS application uses specialized
profile for configuration; it reads the profile and verifies if all the
configuration elements are present and valid. See profile for 'experiment'
application in 'example_experiment' directory for the complete example.
    """
    pass

