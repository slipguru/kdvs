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

from kdvs.tests import resolve_unittest, TestError, TEST_INVARIANTS
from kdvs.tests.utils import test_dir_writable
from optparse import OptionParser
import os
import sys

unittest = resolve_unittest()

def main():

    desc = ("Test suite for Knowledge Driven Variable Selection (KDVS) system. "
    "There are three types of tests to run, with increasing complexity: "
    "unit tests, function test and system tests. "
    "By default, all tests are executed in succession: first unit tests, then function tests, then system tests. "
    "Individual types of tests may be selected with corresponding switches "
    "(default equals to specifying -t -f -s). "
    "Some tests require writing to specific directory; "
    "currently it is set to '%s'. This directory must be writable to proceed. "
    "It may be changed with '-w' option. "
    "The same directory is used for all types of tests." % TEST_INVARIANTS['test_write_root'])
    parser = OptionParser(description=desc)

    parser.add_option("-t", "--unit-tests", action="store_true", dest="unit_tests",
        help="execute unit tests", default=False)

    parser.add_option("-f", "--function-tests", action="store_true", dest="function_tests",
        help="execute function tests", default=False)

    parser.add_option("-s", "--system-tests", action="store_true", dest="system_tests",
        help="execute system tests", default=False)

    parser.add_option("-w", "--test-write-root", action="store", dest="write_root",
        help="set test write root directory path to TWRPATH", metavar="TWRPATH",
        default=None)
    parser.add_option("--verbose", action="store_true", dest="verbose",
        help="show more detailed test results", default=False)

    options = parser.parse_args()[0]

    if options.write_root is not None:
        if not test_dir_writable(options.write_root):
            raise TestError('Directory "%s" must be writable to run tests!' % options.write_root)
        else:
            # redefine default invariant
            TEST_INVARIANTS['test_write_root'] = options.write_root

    if options.verbose:
        vl = 2
    else:
        vl = 1

    print 'Use -h for more options.'

    tt = options.unit_tests
    ft = options.function_tests
    st = options.system_tests

    if tt is False and ft is False and st is False:
        tt = True
        ft = True
        st = True

    sys.path.insert(0, os.path.dirname(__file__))

    tl = unittest.TestLoader()
    tr = unittest.TextTestRunner(verbosity=vl)

    tts = 'unit tests' if tt else None
    fts = 'function tests' if ft else None
    sts = 'system tests' if st else None

    print 'To run: %s' % (', '.join([s for s in (tts, fts, sts) if s is not None]))

    ttm = tl.discover('kdvs/tests/t', pattern='*.py', top_level_dir='.') if tt else []
    ftm = tl.discover('kdvs/tests/f', pattern='*.py', top_level_dir='.') if ft else []
    stm = tl.discover('kdvs/tests/s', pattern='*.py', top_level_dir='.') if st else []

    atm = unittest.TestSuite()
    atm.addTests(ttm)
    atm.addTests(ftm)
    atm.addTests(stm)

    tr.run(atm)

    print 'All Done'

if __name__ == '__main__':
    main()
