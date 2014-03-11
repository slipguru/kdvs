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
Provides root functionality for KDVS EnvOps (environment--wide operations).

IMPORTANT NOTE!
In principle, EnvOp is devised as a self-contained function that can access
and modify environment explicitly. Other modular execution blocks, such as
techniques, reporters, orderers and selectors, by default are **isolated** from
environment as much as possible and are accessible only through API. This is
done to minimize possible devastating impact of erroneous code
on the whole environment, that must manage other vital things and cannot
croak that easily. Therefore, operations should be used only if absolutely necessary
since they introduce states that are potentially very hard to debug.
"""

from kdvs.core.util import Parametrizable

DEFAULT_ENVOP_PARAMETERS = ()
r"""
Default parameters for EnvOp.
"""

class EnvOp(Parametrizable):
    r"""
Encapsulates an EnvOp. Environment--wide operation is parametrizable and affects
all execution environment. As such, it can potentially cause substantial problems
if applied incorrectly. The EnvOp is called automatically during execution in
callback fashion. In 'experiment' application, two types of EnvOps are available:
pre--EnvOp, that will be executed BEFORE all computational jobs produced by
statistical techniques for current category, and post--EnvOp, that will be
executed AFTER all computational jobs for current category. EnvOps are executed
at the category level.
    """
    def __init__(self, ref_parameters, **kwargs):
        r"""
Parameters
----------
ref_parameters : iterable
    reference parameters to be checked against during instantiation; empty tuple by default

kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones

Raises
------
Error
    if some supplied parameters are not on the reference list
        """
        super(EnvOp, self).__init__(ref_parameters, **kwargs)

    def perform(self, env):
        r"""
By default does nothing. Accepts an instance of execution environment.
        """
        pass
