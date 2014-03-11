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
Provides root paths and top--level elements for KDVS.
"""

import os

SYSTEM_NAME_LC='kdvs'
r"""
Name of KDVS, lower case
"""

SYSTEM_NAME_UC='KDVS'
r"""
Name of KDVS, upper case
"""

from core._version import version

ROOT_IMPORT_PATH=os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
r"""
Root path used for dynamic import. It points to the parent location of this file.
"""

SYSTEM_ROOT_PATH=os.path.abspath(os.path.join(os.path.dirname(__file__)))
r"""
Root path of KDVS system. It points to the location of this file.
"""
