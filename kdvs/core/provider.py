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
Contains set of useful providers for various generic classes of objects handled by KDVS.
"""

from kdvs.core.error import Error
from kdvs.core.util import quote
import bz2
import gzip
import sqlite3

# ----- db providers

class DBProvider(object):
    r"""
Abstract class for providers of database services. All methods must be implemented
in subclasses.

See Also
--------
SQLite3DBProvider
    """
    def connect(self, *args, **kwargs):
        r"""
Appropriately connect to specified database and return connection object.
        """
        raise NotImplementedError('Must be implemented in the subclass!')
    def getConnectionFunc(self):
        r"""
Return appropriate low--level connection function.
        """
        raise NotImplementedError('Must be implemented in the subclass!')
    def getOperationalError(self):
        r"""
Return appropriate instance of OperationalError.
        """
        raise NotImplementedError('Must be implemented in the subclass!')
    def getTextColumnType(self):
        r"""
Return appropriate type for DB column that contains unformatted text data.
        """
        raise NotImplementedError('Must be implemented in the subclass!')
    def checkTableExistence(self, *args, **kwargs):
        r"""
Perform appropriate check if table is present in the database.
        """
        raise NotImplementedError('Must be implemented in the subclass!')
    def getEngine(self):
        r"""
Get appropriate information about DB engine, as the following dictionary:
{'name' : name, 'version' : version}.
        """
        raise NotImplementedError('Must be implemented in the subclass!')


class SQLite3DBProvider(DBProvider):
    r"""
Provider for SQLite3 database based on :mod:`sqlite3`.
    """
    def connect(self, *args, **kwargs):
        r"""
Connect to specified database. All positional arguments are passed to :func:`sqlite3.connect`
function. All keyworded arguments may be used by the user. Currently the following
arguments are recognized:

 * 'unicode_strings' (boolean)
     if True, all strings returned by sqlite3 will be Unicode, and normal strings
     otherwise; sets global attribute :data:`sqlite3.text_factory` appropriately; False by
     default (may be omitted)

Parameters
----------
args : iterable
    positional arguments passed directly to appropriate connection function

kwargs : dict
    keyworded arguments to be used by the user

Raises
------
Error
    if could not connect to specified database for whatever reason; essentially,
    re--raise OperationalError with details
        """
        try:
            conn = self.getConnectionFunc()(*args)
        except self.getOperationalError(), e:
            raise Error('Cannot connect to database (parameters: %s)! (Reason: %s)' % (args, e))
        # resolve additional arguments
        try:
            if kwargs['unicode_strings'] is False:
                conn.text_factory = str
        except KeyError:
            pass
        return conn

    def getConnectionFunc(self):
        r"""
Returns :func:`sqlite3.connect` instance.
        """
        return sqlite3.connect

    def getOperationalError(self):
        r"""
Returns :class:`sqlite3.OperationalError` instance.
        """
        return sqlite3.OperationalError

    def getTextColumnType(self):
        r"""
Returns 'TEXT' as the default unformatted table content. See
`SQLite documentation <http://www.sqlite.org/datatype3.html>`__
for more details.
        """
        return 'TEXT'

    def checkTableExistence(self, *args):
        r"""
Check if specific table exists in given database. The check is performed as a
query of 'sqlite_master' table. See
`SQLite documentation <http://www.sqlite.org/fileformat2.html#sqlite_master>`__
for more details.

Parameters
----------
conn : :class:`sqlite3.Connection`
    opened connection to database

tablename : string
    name of the table to be checked

Raises
------
Error
    if could not check table existence; essentially, re--raise OperationalError with details
        """
        return self._checkTableExists(*args)

    def getEngine(self):
        r"""
Get version information if the SQLite engine as dictionary {'name' : name, 'version' : version}.
Version information is obtained as the result of SQLite function 'sqlite_version'
executed from in--memory database. See
`SQLite documentation <http://www.sqlite.org/lang_corefunc.html#sqlite_version>`__
for more details.

Raises
------
Error
    if could not get engine version; essentially, re--raise OperationalError with details
        """
        return self._checkEngine()

    # ---- methods for specific provider

    def _checkEngine(self):
        c = self.connect(':memory:').cursor()
        c.execute('select sqlite_version();')
        version = str(c.fetchone()[0])
        c.close()
        return {'name' : 'SQLite', 'version' : version}

    def _checkTableExists(self, conn, tablename):
        try:
            c = conn.cursor()
            c.execute('select name from sqlite_master where type="table" and name="%s"' % tablename)
            tname = c.fetchone()
            if tname:
                tname = tname[0]
            return str(tname) == tablename
        except self.getOperationalError(), e:
            raise Error('Cannot check existence of table %s! (Reason: %s)' % (quote(tablename), e))


# ----- file providers

def fileProvider(filename, *args, **kwargs):
    r"""
Return opened file object suitable for use with context manager, regardless of
file type. Provides transparent handling of compressed files.

Parameters
----------
filename : string
    path to specific file

args : iterable
    any positional arguments passed into opener function

kwargs : dictionary
    any keyword arguments passed into opener function

Returns
-------
file_object : file_like
    opened file object, suitable for use with context manager
    """
    if filename.endswith('.gz'):
        opener = fpGzipFile(filename, *args, **kwargs)
    elif filename.endswith('.bz2'):
        opener = fpBzip2File(filename, *args, **kwargs)
    else:
        opener = open(filename, *args, **kwargs)
    return opener

class fpGzipFile(gzip.GzipFile):
    r"""
Wrapper class to allow opening gzip-ed files with context manager.
    """
    def __enter__(self):
        if self.fileobj is None:
            raise ValueError("I/O operation on closed GzipFile object")
        return self
    def __exit__(self, *args):
        self.close()

class fpBzip2File(bz2.BZ2File):
    r"""
Wrapper class to allow opening bzip2-ed files with context manager.
    """
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.close()

RECOGNIZED_FILE_PROVIDERS = (file, fpGzipFile, fpBzip2File)
r"""
File providers currently recognized by KDVS.

See Also
--------
file
fpGzipFile
fpBzip2File
"""
