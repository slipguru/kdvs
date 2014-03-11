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
Provides simple wrapper over database table to act like a dictionary that can
hold any Python object, essentially a :mod:`shelve` with database backend.
"""

from kdvs.fw.DBTable import DBTemplate, DBTable
import base64
import cPickle
import collections


DBSHELVE_TMPL = DBTemplate({
    'name' : 'shelve',
    'columns' : ('key', 'value'),
    'id_column' : 'key',
    'indexes' : ('key',),
    })
r"""
Instance of default DBTemplate used to construct underlying database table that serves under
DBShelve. It defines the name 'shelve' and columns 'key', 'value'. The ID column
'key' is indexed.
"""

class DBShelve(collections.MutableMapping):
    r"""
Class that exposes dictionary behavior of database table that can hold any Python object.
By default, it governs database table created according to :class:`~kdvs.fw.DBTable.DBTemplate`
template :data:`DBSHELVE_TMPL`.
    """
    def __init__(self, dbm, db_key, protocol=None):
        r"""
Parameters
----------
dbm : :class:`~kdvs.core.db.DBManager`
    instance of DBManager that will control the database table

db_key : string
    identifier of the database table that will be used by DBManager

protocol : integer/None
    pickling protocol; if None, then the highest one will be used

See Also
--------
pickle
        """
        self.tmpl = DBSHELVE_TMPL
        self.dtsh = DBTable.fromTemplate(dbm, db_key, template=self.tmpl)
        if protocol is not None:
            self.protocol = protocol
        else:
            self.protocol = cPickle.HIGHEST_PROTOCOL
        self.dtsh.create(indexed_columns=self.tmpl['indexes'])
        self.key = self.tmpl['columns'][0]
        self.val = self.tmpl['columns'][1]
        self.name = self.tmpl['name']
        self.cs = self.dtsh.db.cursor()

    def __len__(self):
        return self.dtsh.countRows()

    def keys(self):
        r"""
See Also
--------
dict.keys
        """
        return self.dtsh.getIDs()

    def values(self):
        r"""
See Also
--------
dict.values
        """
        st = 'select %s from %s' % (self.val, self.name)
        self.cs.execute(st)
        rs = [self._retrValue(r[0]) for r in self.cs.fetchall()]
        return rs

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        st = 'select %s from %s where %s=?' % (self.val, self.name, self.key)
        self.cs.execute(st, (key,))
        return self.cs.fetchone() is not None

    def __getitem__(self, key):
        st = 'select %s from %s where %s=?' % (self.val, self.name, self.key)
        self.cs.execute(st, (key,))
        item = self.cs.fetchone()
        if item is None:
            raise KeyError(key)
        return self._retrValue(item[0])

    def __setitem__(self, key, value):
        st = 'replace into %s (%s,%s) values (?,?)' % (self.name, self.key, self.val)
        self.cs.execute(st, (key, self._storeValue(value)))
        self.dtsh.db.commit()

    def __delitem__(self, key):
        if key not in self:
            raise KeyError(key)
        st = 'delete from %s where %s=?' % (self.name, self.key)
        self.cs.execute(st, (key,))
        self.dtsh.db.commit()

    def update(self, items=(), **kwds):
        r"""
See Also
--------
dict.update
        """
        if isinstance(items, collections.Mapping):
            items = items.items()
        st = 'replace into %s (%s,%s) values (?,?)' % (self.name, self.key, self.val)
        items_enc = [(k, self._storeValue(v)) for k, v in items]
        self.cs.executemany(st, items_enc)
        self.dtsh.db.commit()
        if kwds:
            self.update(kwds)

    def clear(self):
        r"""
See Also
--------
dict.clear
        """
        st = 'delete from %s;' % (self.name)
        self.cs.execute(st)
        st = 'vacuum;'
        self.cs.execute(st)
        self.dtsh.db.commit()

    def close(self):
        r"""
See Also
--------
dict.close
        """
        pass

    def __del__(self):
        self.close()

    def view(self):
        r"""
See Also
--------
dict.view
        """
        return dict([(k, self.__getitem__(k)) for k in self.keys()])

    def _storeValue(self, value):
        pd = cPickle.dumps(value, protocol=self.protocol)
        return base64.b64encode(pd)

    def _retrValue(self, vrepr):
        pd = base64.b64decode(vrepr)
        return cPickle.loads(pd)
