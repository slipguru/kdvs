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
Provides layer for all DB operations performed by KDVS.
"""

from kdvs import SYSTEM_NAME_LC
from kdvs.core.error import Error
from kdvs.core.provider import SQLite3DBProvider
from kdvs.core.util import quote
import os
import socket

class DBManager(object):
    r"""
General manager of all DB operations performed by KDVS. It provides:
    
  * automatic handling of meta--database that contains information of all used subordinated databases
  * automated opening/closing of multiple subordinated databases
    """
    def __init__(self, arbitrary_data_root=None, provider=None, rootdbid=None):
        r"""
Parameters
----------
arbitrary_data_root : string/None
    path to directory containing all database objects managed by this manager
    instance; also, all new database objects will be created here; if None,
    default path '~/.kdvs/' will be used

provider : DBProvider/None
    concrete DBProvider instance that provides internal details about requested
    database system; if None, default provider for SQLite3 is used

rootdbid : string/None
    custom ID for meta--database; if not specified, the default one will be used

See Also
--------
os.path.expanduser
        """
        # resolve provider
        if provider:
            self.provider = provider
        else:
            # initialize default provider
            self.provider = SQLite3DBProvider()
        # resolve absolute data root
        self.def_config_path_root = os.path.expanduser('~/.%s/' % (SYSTEM_NAME_LC))
        if arbitrary_data_root is None:
            self.abs_data_root = self.def_config_path_root
        else:
            self.abs_data_root = arbitrary_data_root
        self.abs_data_root = os.path.abspath(self.abs_data_root)
        # ---- at this point check if data root is available at all
        if not os.path.exists(self.abs_data_root):
            raise Error('Could not access data root %s!' % quote(self.abs_data_root))
        # ---- create cache of opened connections
        self.db = {}
        self.db_loc = {}
        # ---- resolve root key
        if rootdbid is None:
            self.rootdb_key = '%s.root.db' % SYSTEM_NAME_LC
        else:
            self.rootdb_key = rootdbid
        # ---- init or open root db (where all non-dynamic metadata are stored)
        rootdb_loc = os.path.join(self.abs_data_root, self.rootdb_key)
        if not os.path.exists(rootdb_loc):
            # the trick here is to let sqlite3 create db file then init it
            rootdb = self.provider.connect(rootdb_loc)
            self.__init_rootdb(rootdb)
        else:
            # the trick here is just to connect to existing db file
            rootdb = self.provider.connect(rootdb_loc)
        self.db[self.rootdb_key] = rootdb
        self.db_loc[self.rootdb_key] = rootdb_loc
        # ---- create default path for db objects
        self.db_location = self.abs_data_root
        # ---- initialize always opened in-memory db
        self.memdb = self.__open_db('memdb')

    def __init_rootdb(self, rootdb):
        tct = self.provider.getTextColumnType()
        create_idx_st = "create table if not exists DB (db %s unique, created %s, db_loc %s unique)" % (tct, tct, tct)
        c = rootdb.cursor()
        c.execute(create_idx_st)
        rootdb.commit()
        c.close()

    def __open_db(self, db_id='memdb'):
        if not isinstance(db_id, basestring):
            raise Error('Invalid database ID! (got %s)' % db_id.__class__)
        if db_id != 'memdb':
            # file-based db requested, form proper name
            db_path = os.path.abspath(os.path.join(self.db_location, '%s.db' % db_id))
            if not os.path.exists(db_path):
                _created = True
                _msg = 'create'
            else:
                _created = False
                _msg = 'open'
        else:
            # new in-memory db requested
            db_path = ':memory:'
            _created = True
            _msg = 'create'
        try:
            db = self.provider.connect(db_path)
            if _created is True:
                self.db[db_id] = db
                self.db_loc[db_id] = db_path
                if db_id != 'memdb':
                    # record opened file-based database
                    hname = socket.gethostname()
                    if len(hname) == 0:
                        hname = '<unknown>'
                    db_path = hname + '://' + db_path
                    if _created is True:
                        cr_rec = '1'
                    else:
                        cr_rec = '0'
                    rootdb = self.db[self.rootdb_key]
                    c = rootdb.cursor()
                    c.execute('insert into DB values (?, ?, ?)', (db_id, cr_rec, quote(db_path)))
                    rootdb.commit()
                    c.close()
            return db
        except Exception, e:
            raise Error('Cannot %s database %s in %s! (Reason: %s)' % (_msg, quote(db_id), db_path, e))

    def getDB(self, db_id):
        r"""
Obtain connection for subordinated database with requested ID. If database does not
exist, create it. If underlying provider accepts it, special ID 'memdb' may be
used for single in--memory database.

Parameters
----------
db_id : string
    ID for requested database

Returns
-------
handle : connection (depends on provider)
    connection to the requested subordinated database
        """
        try:
            return self.db[db_id]
        except KeyError:
            return self.__open_db(db_id)

    def getDBloc(self, db_id):
        r"""
Obtain location for subordinated database with requested ID. If database with
requested ID has not been yet created, return None. The meaning of 'location'
depends on the provider. For instance, in case of SQLite3, single database is
stored in single file, and 'location' is the absolute path to that file.

Parameters
----------
db_id : string
    ID for requested database

Returns
-------
location : (depends on provider)
    location of the requested subordinated database, in the sense of provider;
    or None if database does not exist
        """
        try:
            return self.db_loc[db_id]
        except KeyError:
            return None

    def close(self, dbname=None):
        r"""
Closes requested subordinated database managed by this manager instance. If None
is requested, then all databases are closed.

Parameters
----------
dbname : string/None
    ID for requested database to close; if None, all databases wil be closed
        """
        # close all opened database handles
        if dbname is not None:
            try:
                self.db[dbname].close()
                del self.db[dbname]
                del self.db_loc[dbname]
            except KeyError:
                pass
        else:
            for db in self.db.values():
                db.close()
            self.db.clear()
            self.db_loc.clear()
