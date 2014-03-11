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
Provides low--level functionality of the management of database table under KDVS
DB manager. Also provides simple wrapper over templated database tables.
"""

from kdvs.core.db import DBManager
from kdvs.core.dep import verifyDepModule
from kdvs.core.error import Error
from kdvs.core.util import isListOrTuple, quote, className, emptyGenerator, \
    NPGenFromTxtWrapper
from kdvs.fw.DBResult import DBResult
import uuid


class DBTable(object):
    r"""
Low--level wrapper over database table managed by KDVS DB manager. KDVS uses
database tables to manage query--intensive information, such as the robust
generation of data subsets from single main input data set. The wrapper encapsulates
basic functionality incl. table creation, table filling from specific generator
function, querying with conditions over colums and rows (in case where first
column holds row IDs), generation of associated :class:`numpy.ndarray` object
(if possible), as well as basic counting routines.
    """
    def __init__(self, dbm, db_key, columns, name=None, id_col=None):
        r"""
Parameters
----------
dbm : :class:`~kdvs.core.db.DBManager`
    an instance of DB manager that is managing this table

db_key : string
    internal ID of the table used by DB manager instance; it is NOT the name of
    physical database table in underlying RDBMS; typically, user of DB manager
    refers to the table by this ID and not by its physical name

columns : list/tuple of strings
    column names for the table

name : string/None
    physical name of database table in underlying RDBMS; if None, the name is
    generated semi--randomly; NOTE: ordinary user of DB manager shall refer to
    the table with 'db_key' ID

id_col : string/None
    designates specific column to be "ID column"; if None, the first column is
    designated as ID column

Raises
------
Error
    if DBManager instance is not present
Error
    if list/tuple with column names is not present
Error
    if ID column name is not the one of existing columns
        """
        # ---- resolve DBManager
        if not isinstance(dbm, DBManager):
            raise Error('%s instance expected! (got %s)' % (DBManager.__class__, dbm.__class__))
        else:
            self.dbm = dbm
        # ---- get target DB
        db = dbm.getDB(db_key)
        self.db_key = db_key
        self.db = db
        # ---- resolve columns
        if isListOrTuple(columns):
            self.columns = tuple(columns)
        else:
            raise Error('List or tuple expected! (got %s)' % columns.__class__)
        # ---- resolve ID column
        if id_col is None:
            self.id_column_idx = 0
            self.id_column = self.columns[0]
        else:
            if id_col in self.columns:
                self.id_column_idx = self.columns.index(id_col)
                self.id_column = id_col
            else:
                raise Error('ID column must be one of the existing columns! (got %s)' % id_col)
        # ---- resolve table name
        if name is None:
            self.name = '%s%s' % (self.__class__.__name__, uuid.uuid4().hex)
        else:
            self.name = name

    def create(self, indexed_columns='*', debug=False):
        r"""
Physically create the table in underlying RDBMS; the creation is deferred until
this call. The table is created empty.

Parameters
----------
indexed_columns : list/tuple/'*'
    list/tuple of column names to be indexed by underlying RDBMS; if string '*'
    is specified, all columns will be indexed; '*' by default

debug : boolean
    provides debug mode for table creation; if True, collect all SQL statements
    produced by underlying RDBMS and return them as list of strings; if False,
    return None

Returns
-------
statements : list of strings/None
    RDBMS SQL statements issued during table creation, if debug mode is requested;
    or None otherwise

Raises
------
Error
    if table creation or indexing was interrupted with an error; essentially,
    reraise OperationalError from underlying RDBMS
        """
        statements = []
        # ---- create table
        cs = self.db.cursor()
        dberror = self.dbm.provider.getOperationalError()
        ctype = self.dbm.provider.getTextColumnType()
        # make columns
        cols = ','.join(['%s %s' % (quote(c), ctype) for c in self.columns])
        # make statement
        st = 'create table %s (%s)' % (quote(self.name), cols)
        if debug:
            statements.append(st)
        else:
            try:
                cs.execute(st)
            except dberror, e:
                raise Error('Cannot create table %s in database %s! (Reason: %s)' % (quote(self.name), quote(self.db_key), e))
        # ---- create indexes
        # resolve indexed columns
        if indexed_columns == '*':
            indexed = tuple(self.columns)
        else:
            if isListOrTuple(indexed_columns):
                indexed = tuple(indexed_columns)
            else:
                raise Error('List or tuple expected! (got %s)' % indexed_columns.__class__)
        # make indexes
        for ic in indexed:
            idx_name = '%s__%s' % (self.name, ic)
            idx_st = 'create index %s on %s(%s)' % (quote(idx_name), quote(self.name), quote(ic))
            if debug:
                statements.append(idx_st)
            else:
                try:
                    cs.execute(idx_st)
                except dberror, e:
                    raise Error('Cannot create index on column %s for table %s in database %s! (Reason: %s)' % (quote(ic), quote(self.name), quote(self.db_key), e))
        # ---- finish
        if not debug:
            self.db.commit()
            cs.close()
        if debug:
            return statements
        else:
            return None

    def load(self, content=emptyGenerator(), debug=False):
        r"""
Fill the already created table with some data, coming from specified generator
callable.

Parameters
----------
content : generator callable
    generator callable that furnish the data; this method DOES NOT check the
    correctness of furnished data, this is left to the user; by default, empty
    generator callable is used

debug : boolean
    provides debug mode for table filling; if True, collect all SQL statements
    produced by underlying RDBMS and return them as list of strings; if False,
    return None

Returns
-------
statements : list of strings/None
    RDBMS SQL statements issued during table filling, if debug mode is requested;
    or None otherwise

Raises
------
Error
    if table filling was interrupted with an error; essentially, reraise
    OperationalError from underlying RDBMS
        """
        statements = []
        cs = self.db.cursor()
        dberror = self.dbm.provider.getOperationalError()
        # ---- load content
        for cont in content:
            if len(cont) > 0:
                ct = ','.join([quote(f) for f in cont])
                st = 'insert into %s values (%s)' % (quote(self.name), ct)
                if debug:
                    statements.append(st)
                else:
                    try:
                        cs.execute(st)
                    except dberror, e:
                        raise Error('Cannot insert content %s into table %s in database %s! (Reason: %s)' % (quote(ct), quote(self.name), quote(self.db_key), e))
        # ---- finish
        if not debug:
            self.db.commit()
            cs.close()
        if debug:
            return statements
        else:
            return None

    def get(self, columns='*', rows='*', filter_clause=None, debug=False):
        r"""
Perform query from the table under specified conditions and return corresponding
Cursor instance; the Cursor may be used immediately in straightforward manner or
may be wrapped in :class:`~kdvs.fw.DBResult.DBResult` instance.

Parameters
----------
columns : list/tuple/'*'
    list of column names that the quering will be performed from; if string '*'
    is specified instead, all columns will be queried; '*' by default

rows: list/tuple/'*'
    list of rows (i.e. list of values from designated ID column) that the
    quering will be performed for; if string '*' is specified instead, all rows
    (i.e. whole content of ID column) will be queried; '*' by default

filter_clause : string/None
    additional filtering conditions stated in the form of correct SQL WHERE
    clause suitable for underlying RDBMS; if None, no additional filtering is
    added; None by default

debug : boolean
    provides debug mode for table querying; if True, collect all SQL statements
    produced by underlying RDBMS and return them as list of strings; if False,
    return None; False by default; NOTE: for this method, debug mode DOES NOT
    perform any physical querying, it just produces underlyng SQL statements
    and returns them

Returns
-------
cs/statements : Cursor/list of strings
    if debug mode was not requested: proper Cursor instance that may be used
    immediately or wrapped into DBResult object; if debug mode was requested:
    RDBMS SQL statements issued during table querying

Raises
------
Error
    if list/tuple of columns/rows was specified incorrectly
    if specified list of columns/rows is empty
    if table querying was interrupted with an error; essentially, reraise
    OperationalError from underlying RDBMS

See Also
--------
:pep:`249`
        """
        statements = []
        cs = self.db.cursor()
        dberror = self.dbm.provider.getOperationalError()
        # ---- resolve columns
        if columns == '*':
            cols_st = columns
        else:
            if isListOrTuple(columns):
                if len(columns) == 0:
                    raise Error('Non-empty list of columns expected!')
            else:
                raise Error('List or tuple expected! (got %s)' % columns.__class__)
            cols_st = ','.join([quote(c) for c in columns])
        # ---- resolve rows
        if rows != '*':
            if isListOrTuple(rows):
                if len(rows) > 0:
                    rs = tuple(rows)
                else:
                    raise Error('Non-empty list of rows expected!')
            else:
                raise Error('List or tuple expected! (got %s)' % rows.__class__)
            rows_st = ','.join([quote(r) for r in rs])
        else:
            rows_st = rows
        # ---- make statement
        if rows_st == '*':
            # resolve filter clause
            if filter_clause is not None:
                flt_cl = ' where %s' % filter_clause
            else:
                flt_cl = ''
            get_st = 'select %s from %s%s' % (cols_st, quote(self.name), flt_cl)
        else:
            # resolve filter clause
            if filter_clause is not None:
                flt_cl = ' and %s' % filter_clause
            else:
                flt_cl = ''
            get_st = 'select %s from %s where %s in (%s)%s' % (cols_st, quote(self.name), quote(self.id_column), rows_st, flt_cl)
        # ---- get content
        if debug:
            statements.append(get_st)
        else:
            try:
                cs.execute(get_st)
            except dberror, e:
                raise Error('Cannot select from table %s in database %s! (Reason: %s) (Cols: %s) (Rows: %s)' % (
                                quote(self.name), quote(self.db_key), e, columns, rows))
        if debug:
            return statements
        else:
            return cs

    def getAll(self, columns='*', rows='*', filter_clause=None, as_dict=False, dict_on_rows=False, debug=False):
        r"""
Convenient wrapper that does the following: performs query under specified
conditions, wraps resulting Cursor into :class:`~kdvs.fw.DBResult.DBResult`
instance, and gets ALL the results wrapped into desired data structure, as per
DBResult.getAll.

Parameters
----------
columns : list/tuple/'*'
    list of column names that the quering will be performed from; if string '*'
    is specified instead, all columns will be queried; '*' by default

rows: list/tuple/'*'
    list of rows (i.e. list of values from designated ID column) that the
    quering will be performed for; if string '*' is specified instead, all rows
    (i.e. whole content of ID column) will be queried; '*' by default

filter_clause : string/None
    additional filtering conditions stated in the form of correct SQL WHERE
    clause suitable for underlying RDBMS; if None, no additional filtering is
    added; None by default

as_dict : boolean
    specify if the results are to be wrapped in dictionary instead of a list;
    False by default

dict_on_rows : boolean
    valid if previous argument is True; specify if dictionary should be keyed
    by content of the first column (effectively creating dictionary on rows),
    instead of column name

debug : boolean
    if True, activates debug mode identical to one used for method 'get', i.e.
    collect all SQL statements produced by underlying RDBMS and return them as
    list of strings; if False, perform physical querying and return results
    in desired data structure as per DBResult

Returns
-------
results/statements : list/dict / list of strings
    if debug mode was requested, return list of underlying SQL statements; if
    debug mode was not requested, return all results in requested data structure
        """
        res = self.get(columns=columns, rows=rows, filter_clause=filter_clause, debug=debug)
        if not debug:
            dbr = DBResult(self, res)
            return dbr.getAll(as_dict=as_dict, dict_on_rows=dict_on_rows)
        else:
            return res

    def getArray(self, columns='*', rows='*', filter_clause=None, remove_id_col=True, debug=False):
        r"""
Convenient wrapper that does the following: performs query under specified
conditions, and builds corresponding numpy.ndarray object that contains queried
data. Uses :func:`numpy.loadtxt` function for building the instance of
:class:`numpy.ndarray`. If resulting ndarray has dimension of 1 (i.e. (p,)),
reshape it into one--dimensional matrix (i.e. (1,p)).

Parameters
----------
columns : list/tuple/'*'
    list of column names that the quering will be performed from; if string '*'
    is specified instead, all columns will be queried; '*' by default

rows: list/tuple/'*'
    list of rows (i.e. list of values from designated ID column) that the
    quering will be performed for; if string '*' is specified instead, all rows
    (i.e. whole content of ID column) will be queried; '*' by default

filter_clause : string/None
    additional filtering conditions stated in the form of correct SQL WHERE
    clause suitable for underlying RDBMS; if None, no additional filtering is
    added; None by default

remove_id_col : boolean
    discard content of ID column if such effect is desired; True by default

debug : boolean
    if True, activates debug mode identical to one used for method 'get', i.e.
    collect all SQL statements produced by underlying RDBMS and return them as
    list of strings; if False, perform physical querying, build corresponding
    numpy.ndarray object and return it; False by default

Returns
-------
mat/statements : :class:`numpy.ndarray`/list of strings
    if debug mode was not requested: numpy.ndarray object that contains queried
    data; if debug mode was requested: RDBMS SQL statements issued during table
    querying

Raises
------
Error
    if list/tuple of columns/rows was specified incorrectly
Error
    if specified list of columns/rows is empty
Error
    if table querying was interrupted with an error; essentially, reraise
    OperationalError from underlying RDBMS
Error
    if error was encountered during building of numpy.ndarray object; refer to
    numpy documentation for more details about possible errors

See Also
--------
kdvs.core.util.NPGenFromTxtWrapper
        """
        np = verifyDepModule('numpy')
        res = self.get(columns=columns, rows=rows, filter_clause=filter_clause, debug=debug)
        if not debug:
            dbr = DBResult(self, res)
            if remove_id_col:
                id_col_idx = self.id_column_idx
            else:
                id_col_idx = None
            npltwrapper = NPGenFromTxtWrapper(dbr, id_col_idx=id_col_idx)
            try:
                mat = np.loadtxt(npltwrapper)
                # reshape vector of length p (p,) into matrix (1,p)
                if mat.ndim == 1:
                    mat = mat.reshape((1, -1))
                return mat
            except Exception, e:
                raise Error('Could not generate matrix! (Reason: %s)' % (e))
        else:
            return res

    def countRows(self):
        r"""
Counts number of rows for the table. Table must be filled to obtain count >0.
Counting is performed with SQL standard function 'count' in underlying RDBMS.

Returns
-------
count : integer/None
    row count for the table, or None if underlying 'count' returns null

Raises
------
Error
    if table is not yet created
Error
    if counting was interrupted with an error; essentially, reraise
    OperationalError from underlying RDBMS
        """
        if not self.isCreated():
            raise Error('DataTable %s in %s must be first created!' % (quote(self.name), quote(self.db_key)))
        cs = self.db.cursor()
        cnt_st = 'select count(%s) from %s' % (quote(self.id_column), self.name)
        dberror = self.dbm.provider.getOperationalError()
        try:
            cs.execute(cnt_st)
        except dberror, e:
            raise Error('Cannot count from table %s in database %s! (Reason: %s)' % (quote(self.name), quote(self.db_key), e))
        res = cs.fetchone()
        if res:
            cnt = int(res[0])
        else:
            cnt = None
        return cnt

    def getIDs(self):
        r"""
Get content of designated ID column and return it as list of values.

Returns
-------
IDs : list of strings
    list of values from ID column, as queried by underlying RDBMS; the list is
    sorted in insert order

Raises
------
Error
    if table has not yet been created
Error
    if querying of ID column was interrupted with an error; essentially, reraise
    OperationalError from underlying RDBMS
        """
        if not self.isCreated():
            raise Error('DataTable %s in %s must be first created!' % (quote(self.name), quote(self.db_key)))
        cs = self.db.cursor()
        st = 'select %s from %s' % (quote(self.id_column), self.name)
        dberror = self.dbm.provider.getOperationalError()
        try:
            cs.execute(st)
        except dberror, e:
            raise Error('Cannot get IDs from table %s in database %s! (Reason: %s)' % (quote(self.name), quote(self.db_key), e))
        res = [str(r[0]) for r in cs.fetchall()]
        return res

    def isCreated(self):
        r"""
Returns True if the table has been physically created, False otherwise.
        """
        return any([self.dbm.provider.checkTableExistence(conn, self.name) for conn in self.dbm.db.values()])

    def isEmpty(self):
        r"""
Returns True if the table is empty, False otherwise.

Raises
------
Error
    if table has not yet been created
        """
        if not self.isCreated():
            raise Error('DataTable %s must be created in %s first!' % (quote(self.name), quote(self.db_key)))
        return self.countRows() == 0

    @staticmethod
    def fromTemplate(dbm, db_key, template):
        r"""
Create an instance of DBTable based on specified DBTemplate instance.

Parameters
----------
dbm : :class:`~kdvs.core.db.DBManager`
    an instance of DB manager that is managing the requested table

db_key : string
    internal ID of the table used by DB manager instance; it is NOT the name of
    physical database table in underlying RDBMS; typically, user of DB manager
    refers to the table by this ID and not by its physical name

template : :class:`~kdvs.fw.DBTable.DBTemplate`
    an DBTemplate instance that contains specification for new table

Returns
-------
dbtable : :class:`~kdvs.fw.DBTable.DBTable`
    instance of DBTable built based on the specified template; the table is not
    created physically until 'create' method is called

Raises
------
Error
    if proper template was not specified
        """
        if not isinstance(template, DBTemplate):
            raise Error('%s instance expected! (got %s)' % (DBTemplate.__class__, template.__class__))
        else:
            return DBTable(dbm, db_key, template['columns'], template['name'], template['id_column'])

    def __str__(self):
        cls = ','.join([quote(c) for c in self.columns])
        return "<'%s'[%s](ID:%s) on '%s' in '%s'>" % (self.name, cls, quote(self.id_column), self.db_key, self.dbm.abs_data_root)

# ----

dbtemplate_keys = ('name', 'columns', 'id_column', 'indexes')
r"""
Recognized keys used in DBTemplate wrapper object.
"""

class DBTemplate(object):
    r"""
The template object that contains simplified directives how to build a database
table. It is essentially a wrapper over a dictionary that contains the following
elements:

    * 'name' -- specifies the physical name of the table for underlying RDBMS,
    * 'columns' -- non--empty list/tuple of column names of standard type (the type is taken from getTextColumnType() method of the underlying DB provider),
    * 'id_column' -- name of the column designated to be an ID column for that table,
    * 'indexes' -- list/tuple of column names to be indexed by underlying RDBMS, or string '*' for indexing all columns.
    """
    def __init__(self, in_dict):
        r"""
Parameters
----------
in_dict : dict
    dictionary containing simplified directives; the constructor checks if all
    required elements are present

Raises
------
Error
    if list/tuple of column names are not specified and/or empty
    if input dictionary is missing any of required elements
        """
        self._tmpl = dict()
        if all(k in in_dict for k in dbtemplate_keys):
            cls = in_dict['columns']
            if not isListOrTuple(cls) or len(cls) == 0:
                raise Error('Non-empty list or tuple expected! (got %s)' % cls.__class__)
            self._tmpl.update(in_dict)
        else:
            raise Error('%s must contain all of the following keys: %s !' % (
                           quote(className(self)), quote(' '.join(dbtemplate_keys))))

    def __getitem__(self, key):
        return self._tmpl.__getitem__(key)

