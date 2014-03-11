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
Provides tests for KDVS. Three levels of testing are devised: unit tests (`t`),
function tests (`f`), system tests (`s`). Currently, only `t` tests are implemented;
some dummy `f` and `s` tests are also included for completion.
"""

import os
import platform

# directory with read-only test data
TEST_DATA_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test-data'))
r"""
Default directory that contains read--only test data.
"""
# default write directory for tests that require writing
TEST_WRITE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test-write'))
r"""
Default writable directory to be used by tests that require writing.
"""

class TestError(Exception):
    pass

def resolve_unittest():
    r"""
Resolve unit testing module depending on the Python version and return it:

    * `unittest2 <http://pypi.python.org/pypi/unittest2>`_ for Python 2.6
    * :mod:`unittest` for Python 2.7+

Raises
------
TestError
    if respective unit testing module is not available
    """
    major, minor = platform.python_version_tuple()[:2]
    if int(major) == 2 and int(minor) == 6:
        # check for Python 2.6
        try:
            ut = __import__('unittest2')
        except ImportError:
            raise TestError('To perform tests under Python 2.6, "unittest2" must be available!')
    elif int(major) == 2 and int(minor) >= 7:
        # check for Python 2.7+
        try:
            ut = __import__('unittest')
        except ImportError:
            raise TestError('To perform tests under Python 2.7+, "unittest" must be available!')
    else:
        raise TestError('To perform test Python 2.6+ is required!')
    return ut

# these values are constant for all tests
TEST_INVARIANTS = {
    'test_write_root' : TEST_WRITE_ROOT,
    'test_data_root' : TEST_DATA_ROOT,
    }
r"""
Constant values for all tests.
"""
