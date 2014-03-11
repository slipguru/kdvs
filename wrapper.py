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
Wrapper that executes KDVS applications and companion scripts without the need
of installation of KDVS as Python module. To be executed by this wrapper,
application/companion script must have the following structure::

    def main():
        # body of the application/companion script
        # ...

    if __name__=='__main__':
        main()

"""
import inspect
import os
import sys

if __name__ == '__main__':
    # add current directory to Python lookup path
    sys.path.append(os.path.abspath(os.getcwd()))
    # replace name of this script with the script being executed
    # (for help options to display correctly)
    sys.argv[0] = sys.argv[1]
    # turn application/script path into a module path
    pmodraw = sys.argv[1].replace(os.sep, '.')
    # cut Python suffix if present
    pmodname = pmodraw.rpartition('.')[0] if pmodraw.endswith('.py') else pmodraw
    # get module name
    pmodlast = pmodname.rpartition('.')[2]
    # import module (A.B.mod) and return it (mod)
    pmod = __import__(pmodname, fromlist=[pmodlast])
    # find 'main' method and execute it
    dict(inspect.getmembers(pmod))['main']()
