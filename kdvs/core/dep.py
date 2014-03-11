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
Provides mechanism for dynamic verifying of dependences in KDVS.
"""

from kdvs.core.error import Error
import os
import sys

def verifyDepModule(modname):
    r"""
Verify that requested module is importable from within KDVS.

Parameters
----------
modname : string
    module name to be verified

Returns
-------
module_instance : module
    instance of the verified module, as present in 'sys.modules'

Raises
------
Error
    if requested module is not importable from within KDVS
    """
    try:
        __import__(modname)
        return sys.modules[modname]
    except ImportError:
        fp=os.path.abspath(__file__)
        fn=os.path.split(fp)[1]
        raise Error("To use this functionality in '%s', '%s' is required! (called in '%s')"%(fn, modname, fp))
