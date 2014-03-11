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
Provides low--level wrapper over tables that hold delimiter separated values (DSV).
Such tables are referred to as DSV tables.
"""

from kdvs.core.error import Error
from kdvs.core.provider import fileProvider
from kdvs.core.util import quote, isListOrTuple, CommentSkipper
from kdvs.fw.DBTable import DBTable
import StringIO
import csv
import itertools
import os

DSV_DEFAULT_ID_COLUMN = 'ID'
r"""
Default ID column for DSV table.
"""

# build reverse dictionary of dialects by their delimiters:
# {delim1 : dialect1, delim2 : dialect2, ...}
_dialects = dict([(csv.get_dialect(dn).delimiter, csv.get_dialect(dn)) for dn in csv.list_dialects()])

class DSV(DBTable):
    r"""
Create an instance of :class:`~kdvs.fw.DBTable.DBTable` and immediately wrap it
into DSV table. DSV table manages additional details such as initialization from
associated DSV file and handling underlying DSV dialect.
    """
    def __init__(self, dbm, db_key, filehandle, dtname=None, delimiter=None, comment=None, header=None, make_missing_ID_column=True):
        r"""
Parameters
----------
dbm : :class:`~kdvs.core.db.DBManager`
    an instance of DB manager that is managing this table

db_key : string
    internal ID of the table used by DB manager instance; it is NOT the name of
    physical database table in underlying RDBMS; typically, user of DB manager
    refers to the table by this ID and not by its physical name

filehandle : file--like
    file handle to associated DSV file that contains the data that DSV table
    will hold; the file remains open but the data loading is deferred until
    requested

dtname : string/None
    physical name of database table in underlying RDBMS; if None, the name is
    generated semi--randomly; NOTE: ordinary user of DB manager shall refer to
    the table with 'db_key' ID

delimiter : string/None
    delimiter string of length 1 that should be used for parsing of DSV data;
    if None, the constructor tries to deduce delimiter by looking into first 10
    lines of associated DSV file; None by default; NOTE: giving explicit delimiter
    instead of deducing it dynamically greatly reduces possibility of errors
    during parsing DSV data

comment : string/None
    comment prefix used in associated DSV file, or None if comments are not used;
    None by default

header : list/tuple of string / None
    if header is present in the form of list/tuple of strings, it will be used
    as list of columns for the underlying database table; if None, the constructor
    tries to deduce the correct header by looking into first two lines of
    associated DSV file; None by default; NOTE: for well formed DSV files, header
    should be present, so it is relatively safe to deduce it automatically

make_missing_ID_column : boolean
    used in connection with previous argument; sometimes one can encounter DSV
    files that contain NO first column name in the header (e.g. generated from
    various R functions), and while they contain correct data, such files are
    syntactically incorrect; if the constructor sees lack of the first column name,
    it can proceed according to this parameter; if True, it inserts the content
    of :data:`DSV_DEFAULT_ID_COLUMN` variable as the missing column name; if False, it
    inserts empty string "" as the missing column name; True by default

Raises
------
Error
    if proper comment string was not specified
Error
    if underlying DSV dialect of associated DSV file has not been resolved correctly
Error
    if delimiter has not been specified correctly
Error
    if header iterable has not been specified correctly
Error
    if parsing of DSV data during deducing was interrupted with an error; essentially,
    it reraises underlying csv.Error

See Also
--------
csv
        """
        # ---- resolve comment
        if comment is not None and not isinstance(comment, basestring):
            raise Error('String or None expected! (got %s)' % comment)
        else:
            self.comment = comment
        # ---- resolve delimiter and dialect
        if delimiter is None:
            self._resolve_dialect(filehandle)
        else:
            if isinstance(delimiter, basestring) and len(delimiter) == 1:
                self.delimiter = delimiter
                try:
                    self.dialect = _dialects[delimiter]
                except KeyError:
                    raise Error('Dialect not identified for delimiter %s! (Sniffing required?)' % quote(delimiter))
            else:
                raise Error('Single character expected! (got %s)' % (delimiter))
        # ---- resolve header
        if header is None:
            self._extract_header(filehandle, make_missing_ID_column)
        else:
            if isListOrTuple(header):
                if len(header) == 0:
                    self._autogenerate_header(filehandle, make_missing_ID_column)
                else:
                    self._verify_header(filehandle, header)
                    self.header = header
            else:
                raise Error('List or tuple expected! (got %s)' % header.__class__)
        # ---- DSV analysis finished, initialize underlying instance
        self.handle = filehandle
        super(DSV, self).__init__(dbm, db_key, self.header, dtname)

    def _resolve_dialect(self, filehandle, sniff_line_count=10):
        peek_lines = list(itertools.islice(filehandle, sniff_line_count))
        cf = self.getCommentSkipper(peek_lines)
        cflines = ''.join([l for l in cf])
        buf = StringIO.StringIO(cflines).getvalue()
        try:
            self.dialect = csv.Sniffer().sniff(buf)
            self.delimiter = self.dialect.delimiter
            filehandle.seek(0)
        except csv.Error, e:
            raise Error('Could not determine dialect for file %s! (Reason: %s)' % (quote(filehandle.name), e))

    def _extract_header(self, filehandle, makeMissingID):
        cf = self.getCommentSkipper(filehandle)
        l1 = cf.next()
        l2 = cf.next()
        l1_spl = [s.strip() for s in l1.split(self.delimiter)]
        l2_spl = [s.strip() for s in l2.split(self.delimiter)]
        if len(l1_spl) == len(l2_spl):
            if makeMissingID:
                if len(l1_spl[0]) == 0:
                    l1_spl.pop(0)
                    l1_spl.insert(0, DSV_DEFAULT_ID_COLUMN)
            self.header = l1_spl
            # rewind exactly after header
            # first rewind file to the beginning
            filehandle.seek(0)
            # then consume header
            cf.next()
        else:
            raise Error('Could not determine header for file %s! (Wrong header line?)' % quote(filehandle.name))

    def _autogenerate_header(self, filehandle, makeMissingID):
        cf = self.getCommentSkipper(filehandle)
        l = cf.next()
        l_spl = l.split(self.delimiter)
        if makeMissingID:
            if len(l_spl[0]) == 0:
                l_spl.pop(0)
                l_spl.insert(0, DSV_DEFAULT_ID_COLUMN)
        self.header = tuple(['%d' % n for n in range(1, len(l_spl) + 1)])
        # rewind file -- header autogenerated
        filehandle.seek(0)

    def _verify_header(self, filehandle, header):
        cf = self.getCommentSkipper(filehandle)
        l = cf.next()
        l_spl = l.split(self.delimiter)
        if len(l_spl) != len(header):
            raise Error('Number of columns in header must match number of columns in file!')
        # rewind file -- checked first line
        filehandle.seek(0)

    @staticmethod
    def getHandle(file_path, *args, **kwargs):
        r"""
Open specified file and return its handle. Uses :meth:`~kdvs.core.provider.fileProvider`
to transparently open and read compressed files; additional arguments are passed
to file provider directly.

Parameters
----------
file_path : string
    filesystem path to specified file

args : iterable
    positional arguments to pass to file provider

kwargs : dict
    keyword arguments to pass to file provider

Returns
-------
handle : file--like
    opened handle to the file

Raises
------
Error
    if the file could not be accessed
        """
        fp = os.path.abspath(file_path)
        if not os.path.exists(fp):
            raise Error('Could not access %s!' % fp)
        else:
            return fileProvider(fp, *args, **kwargs)

    def getCommentSkipper(self, iterable):
        r"""
Build instance of :data:`~kdvs.core.util.CommentSkipper` for this DSV table
using specified 'comment' string.

Parameters
----------
iterable : iterable
    iterable of strings to be used by CommentSkipper

Returns
-------
cs : :data:`~kdvs.core.util.CommentSkipper`
    an instance of CommentSkipper
        """
        return CommentSkipper(iterable, self.comment)

    def loadAll(self, debug=False):
        r"""
Fill the DSV table with data coming from associated DSV file. The input generator
is the :data:`~kdvs.core.util.CommentSkipper` instance that is obtained automatically.
This method handles all underlying low--level activities. NOTE: the associated
DSV file remains open until closed with :meth:`close` method manually.

Parameters
----------
debug : boolean
    provides debug mode for table filling; if True, collect all SQL statements
    produced by underlying RDBMS and return them as list of strings; if False,
    return None

Returns
-------
statements : list of string/None
    RDBMS SQL statements issued during table filling, if debug mode is requested;
    or None otherwise

Raises
------
Error
    if underlying table has not yet been created
Error
    if data could not be loaded for whatever reason; see DBTable.load for more
    details

See Also
--------
kdvs.fw.DBTable.DBTable.load
        """
        if not self.isCreated():
            raise Error('Underlying table must be created first!')
        else:
            try:
                cf = self.getCommentSkipper(self.handle)
                csvf = csv.reader(cf, self.dialect)
                return super(DSV, self).load(content=csvf, debug=debug)
            except Exception, e:
                raise Error('Could not load file content! (Reason: %s)' % e)

    def close(self):
        r"""
Close associated DSV file.
        """
        self.handle.close()
