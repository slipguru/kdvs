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
Provides version for the release of KDVS.
"""

def _get_version(version, status=None):
    if status:
        return '%s-%s' % (version, status)
    return version

# major number for main changes
# minor number for new features
# release number for bug fixes and minor updates
# status = {'alpha', 'beta', None}
version = _get_version('2.0.0', status=None)
r"""
Major number for main changes. Minor number for new features. Release number
for bug fixes and minor updates. Status = 'alpha'/'beta'/None.
"""
