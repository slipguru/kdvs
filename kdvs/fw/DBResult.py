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
Provides unified wrapper over results from queries performed on underlying
database tables controlled by KDVS.
"""

from kdvs.core.error import Error

class DBResult(object):
    r"""
Wrapper class over query results. Before using this class, correct SQL query must
be issued and concrete Cursor instance must be obtained. Typically, all of this
is performed inside DBTable, but the class is exposed for those that want greater
control over querying. Essentially, this class wraps the the Cursor instance and
controls fetching process.
    """
    def __init__(self, dbtable, cursor, rowbufsize=1000):
        r"""
Parameters
----------
dbtable : :class:`~kdvs.fw.DBTable.DBTable`
    database table to be queried

cursor : Cursor
    cursor used to query the specified table

rowbufsize : integer
    size of internal buffer used during results fetching; 1000 by default

See Also
--------
:pep:`249`
        """
        self.dbt = dbtable
        self.cs = cursor
        self.rowbufsize = rowbufsize

    def get(self):
        r"""
Generator that yields fetched results one by one. Underlying fetching is buffered.
Results are returned as--is; the parsing is left to the user.

Returns
-------
result_row : iterable
    single row with query result; the format of the row depends on the underlying
    database table (obvious), but also on the database provider (not so obvious)

Raises
------
Error
    if whatever error prevented result row from being obtained; NOTE: essentially,
    it watches for raising of OperationalError specific for the database provider

See Also
--------
Cursor.fetchmany
OperationalError
        """
        dberror = self.dbt.dbm.provider.getOperationalError()
        while True:
            try:
                results = self.cs.fetchmany(self.rowbufsize)
            except dberror, e:
                raise Error('Cannot fetch results from cursor (desc: %s) for table %s in database %s! (Reason: %s)' % (
                                    self.cs.description, self.dbt.name, self.dbt.db_key, e))
            if not results:
                break
            for result in results:
                yield result

    def getAll(self, as_dict=False, dict_on_rows=True):
        r"""
Returns all fetched results at once, wrapped in desired structure (list or
dictionary). NOTE: depending on the query itself, it may consume a lot of memory.

Parameters
----------
as_dict : boolean
    specify if the results are to be wrapped in dictionary instead of a list;
    False by default

dict_on_rows : boolean
    valid if previous argument is True; specify if dictionary should be keyed
    by content of the first column (effectively creating dictionary on rows),
    instead of column name

Returns
-------
result : list/dict
    query results wrapped either in list or in dictionary; dictionary can be
    keyed by column name (dictionary on columns) or content of the first column
    (dictionary on rows); e.g. if database has columns

        * 'ID', 'A', 'B', 'C'

    and result comprises of two tuples

        * ('ID_111', 1.0, 2.0, 3.0)
        * ('ID_222', 4.0, 5.0, 6.0),

    the 'dictionary on columns' will contain:

        * {'ID' : ['ID_111', 'ID_222'], 'A' : [1.0, 4.0], 'B' : [2.0, 5.0], 'C' : [3.0, 6.0]}

    and the 'dictionary on rows' will contain:

        * {'ID_111' : [1.0 , 2.0, 3.0], 'ID_222' : [4.0, 5.0, 6.0]}

Raises
------
Error
    if whatever error prevented result row from being obtained; NOTE: essentially,
    it watches for raising of OperationalError specific for the database provider

See Also
--------
Cursor.fetchall
OperationalError
        """
        dberror = self.dbt.dbm.provider.getOperationalError()
        try:
            results = self.cs.fetchall()
        except dberror, e:
            raise Error('Cannot fetch results from cursor (desc: %s) for table %s in database %s! (Reason: %s)' % (
                                self.cs.description, self.dbt.name, self.dbt.db_key, e))
        # ---- determine output
        if as_dict:
            if dict_on_rows:
                # create dict of content [1:] keyed by column 0
                id2row = dict()
                for r in results:
                    id2row[r[0]] = list(r[1:])
                result = id2row
            else:
                # create dict of content 'slices' keyed by columns
                col2rs = dict()
                for col_idx, col in enumerate(self.dbt.columns):
                    col2rs[col] = [r[col_idx] for r in results]
                result = col2rs
        else:
            result = results
        return result

    def close(self):
        r"""
Closes wrapped Cursor instances and frees all the resouces allocated. Shall
always be used when DBResult object is no longer needed.
        """
        self.cs.close()
