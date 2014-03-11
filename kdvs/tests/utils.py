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

import contextlib
import os
import sys
import uuid

def test_dir_writable(directory):
    r"""
Return True if directory is writable (checked by creating dummy temporary file in it), False otherwise
    """
    # check if directory is writable by creating dummy temporary file in it
    tmpf = uuid.uuid1().hex + os.path.extsep + 'tmp'
    tmpname = os.path.join(directory, tmpf)
    try:
        t = open(tmpname, 'wb')
        t.close()
        os.remove(tmpname)
        return True
    except:
        return False

def count_lines(test_stream):
    r"""
Return number of newlines ("\\n") in the stream.
    """
    nls = test_stream.getvalue().count("\n")
    if not test_stream.getvalue().endswith("\n"):
        nls += 1
    return nls

@contextlib.contextmanager
def nostderr():
    r"""
Context manager that consumes all output directed to :class:`sys.stderr` without emitting it.
    """
    savestderr = sys.stderr
    class Devnull(object):
        def write(self, _):
            pass
        def flush(self):
            pass
    sys.stderr = Devnull()
    yield
    sys.stderr = savestderr

@contextlib.contextmanager
def nostdout():
    r"""
Context manager that consumes all output directed to :class:`sys.stdout` without emitting it.
    """
    savestdout = sys.stdout
    class Devnull(object):
        def write(self, _):
            pass
        def flush(self):
            pass
    sys.stdout = Devnull()
    yield
    sys.stdout = savestdout

def check_min_numpy_version(nmaj, nmin, nrel):
    r"""
Return True if version of installed numpy is greater or equal than provided,
False otherwise.
    """
    import numpy
    anmaj, anmin, anmrc = numpy.__version__.split('.')
    anrel = anmrc.split('rc')[0]
    anmaj = int(anmaj)
    anmin = int(anmin)
    anrel = int(anrel)
    if anmaj >= nmaj and anmin >= nmin and anrel >= nrel:
        return True
    else:
        return False
