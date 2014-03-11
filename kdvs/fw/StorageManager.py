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
Provides functionality for path and subdirectory management.
"""

from kdvs import SYSTEM_NAME_LC
from kdvs.core.db import DBManager
from kdvs.core.error import Error
from kdvs.core.util import quote
import uuid
import os
import shutil

# in future: based on http://code.google.com/p/pyfilesystem/

SUBLOCATION_SEPARATOR = '/'
r"""
Standard separator used for specifying sublocations. It may differ from path
separator on current platform.
"""

class StorageManager(object):
    r"""
Storage manager that operates on file system provided by operating system and
accessible by Python interpreter through :mod:`os` module. Storage manager manages
'locations' that refer to subdirectories under specified root path, and
manipulation of concrete directory paths are hidden from the user.
    """
    def __init__(self, name=None, root_path=None, create_dbm=False):
        r"""
Parameters
----------
name : string/None
    name of the current instance; it will be used to identify all managed locations;
    if None, the name is generated randomly (UUID4)

root_path : string/None
    directory path that refers to the root of locations that will be managed by
    this instance; if None, default root path will be used ('~/.kdvs/')

create_dbm : boolean
    if True, default :class:`~kdvs.core.db.DBManager` instance will be created
    as well, rooted on specified root path; False by default

See Also
--------
uuid
os.path.expanduser
        """
        # ---- resolve instance name
        if name is None:
            self.name = uuid.uuid4().hex
        else:
            self.name = name
        # ---- resolve root_path
        self.def_root_path = os.path.expanduser('~/.%s/' % (SYSTEM_NAME_LC))
        if root_path is None:
            self.root_path = self.def_root_path
        else:
            self.root_path = root_path
        self.abs_root_path = os.path.abspath(self.root_path)
        # ---- check if root path is available and writable
        if not os.path.exists(self.abs_root_path):
            raise Error('Could not access root path %s for manager %s!' % (quote(self.abs_root_path), quote(self.name)))
        if not self._check_path_writable(self.abs_root_path):
            raise Error('Could not write to root path %s of manager %s!' % (quote(self.abs_root_path), quote(self.name)))
        # ---- setup locations management
        self.locations = {}
        self.sublocation_separator = SUBLOCATION_SEPARATOR
        # add ROOT location
        self.root_location_id = 'ROOT_%s' % self.name
        self.locations[self.root_location_id] = self.abs_root_path
        # ---- resolve DBM
        if create_dbm:
            # create default DBManager with file-based SQLite3 provider
            self.dbm = DBManager(self.root_path)
        else:
            self.dbm = None

    def createLocation(self, location=None):
        r"""
Create specified location. Location may be specified as

    * 'loc'

or

    * 'loc/loc1/loc2/.../locN'

In the first case, subdirectory

    * 'loc'

will be created under the root path of the manager, with concrete path

    * 'root/loc'

In the second case, all nested subdirectories will be created, if not created
already, and the concrete path will be

    * 'root/loc/loc1/loc2/.../locN'

In addition, all partial sublocations

    * 'root/loc'
    * 'root/loc/loc1'
    * 'root/loc/loc1/loc2'
    * ...

will be managed as well under the names
    * 'loc'
    * 'loc/loc1'
    * 'loc/loc1/loc2'
    * ...

Path separators may differ with the platform.

Parameters
----------
location : string/None
    new location to create under the manager root path; if None, random location
    name will be used (UUID4)

See Also
--------
uuid
os.path
        """
        if location is None:
            sublocs = [uuid.uuid4().hex]
            self._finalize_new_location(sublocs)
        else:
            for sloc in self._get_nested_sublocs(location):
                self._finalize_new_location(sloc)

    def getLocation(self, location):
        r"""
Return physical directory path for given location.

Parameters
----------
location : string
    managed location

Returns
-------
path : string/None
    physical path associated with specified location, or None if location does not
    exist
        """
        if location in self.locations:
            return self.locations[location]
        else:
            return None

    def removeLocation(self, location, leafonly=True):
        r"""
Remove location from managed locations. This method considers two cases. When
location is e.g.

    * 'loc/loc1/loc2'

and leaf mode is not requested, physical subdirectory

    * 'root/loc/loc1/loc2'

will be deleted along with all nested subdirectories, and all managed sublocations.
If leaf mode is requested, only the most nested subdirectory

    * 'root/loc/loc1/loc2'

will be deleted and

    * 'root/loc/loc1'

will be left, along with all managed sublocations.

Parameters
----------
location : string
    managed location to remove

leafonly : boolean
    if True, leaf mode will be used during removal; True by default
        """
        if leafonly is True:
            subloc = self._get_sublocs_for_location(location)
            self._delete_location_from_sublocs(subloc)
        else:
            for subloc in self._get_nested_sublocs(location, fromleaf=True):
                self._delete_location_from_sublocs(subloc)

    def getRootLocationID(self):
        r"""
Return identifier of root location for this manager instance.
        """
        return self.root_location_id

    def getRootLocation(self):
        r"""
Return physical directory path of root location for this manager instance.
        """
        return self.getLocation(self.root_location_id)

    def _check_path_writable(self, path):
        tmpf = uuid.uuid1().hex + os.path.extsep + 'tmp'
        tmpname = os.path.join(path, tmpf)
        try:
            t = open(tmpname, 'wb')
            t.close()
            os.remove(tmpname)
            return True
        except:
            return False

    def _finalize_new_location(self, sublocs):
        locname = self.sublocation_separator.join(sublocs)
        locpathelem = os.path.sep.join(sublocs)
        locpath = os.path.join(self.abs_root_path, locpathelem)
        if self.getLocation(locname) is None:
            self.locations[locname] = locpath
            if not os.path.exists(locpath):
                try:
                    os.makedirs(locpath)
                except os.error, e:
                    raise Error('Could not create location %s under manager %s! (Reason: %s)' % (quote(self.name), quote(locname), e))

    def _delete_location_from_sublocs(self, sublocs):
        locname = self.sublocation_separator.join(sublocs)
        locpath = self.getLocation(locname)
        try:
            del self.locations[locname]
        except KeyError:
            raise Error('Location %s not found under manager %s!' % (quote(locname), quote(self.name)))
        try:
            shutil.rmtree(locpath)
        except (OSError, os.error) as e:
            raise Error('Could not remove location %s under manager %s! (Reason: %s)' % (quote(locname), quote(self.name), e))

    def _get_sublocs_for_location(self, location):
        return [l for l in location.split(self.sublocation_separator) if len(l) > 0]

    def _get_nested_sublocs(self, location, fromleaf=False):
        slocs = self._get_sublocs_for_location(location)
        if fromleaf is False:
            srange = range(1, len(slocs) + 1)
        else:
            srange = range(len(slocs), 0, -1)
        for i in srange:
            yield slocs[:i]

    def __repr__(self):
        return '<%s on %s>' % (self.__class__.__name__, self.getRootLocation())

    def __str__(self):
        return self.__repr__()
