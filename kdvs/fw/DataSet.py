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
Provides unified interface for data sets processed by KDVS.
"""

from kdvs.core.error import Error
from kdvs.core.util import className
from kdvs.fw.DBTable import DBTable
import gc
import numpy
from numpy import ndarray

class DataSet(object):
    r"""
Wrapper object that represents data set processed by KDVS. It can wrap two types
of objects:

    * an existing :class:`~kdvs.fw.DBTable.DBTable` object that KDVS uses for data storage in relational database
    * an existing :class:`numpy.ndarray`

In case of wrapping DBTable object, it creates additional numpy object of class `ndarray`,
as returned by :func:`numpy.loadtxt` family of functions. The additional `ndarray` object is
cached with the DataSet instance, and can be recached on demand; this may be
useful if the content of underlying DBTable object changes dynamically.
    """
    def __init__(self, input_array=None, dbtable=None, cols='*', rows='*', filter_clause=None, remove_id_col=True):
        r"""
Parameters
----------

input_array : :class:`numpy.ndarray`
    existing numpy.ndarray object to be wrapped, or None if DBTable is to be wrapped;
    NOTE: when this argument is not None, the next one must be None

dbtable : :class:`~kdvs.fw.DBTable.DBTable`
    existing DBTable object to be wrapped, or None if numpy.ndarray is to be wrapped;
    NOTE: when this argument is not None, the previous one must be None

cols : iterable/'*'
    valid for wrapping DBTable object, names of database columns to be used in
    extracting data set from database table, or '*' if using all columns; see
    DBTable for more details

rows : iterable/'*'
    valid for wrapping DBTable object, IDs of database rows to be used in
    extracting data set from database table, or '*' if using all rows; see
    DBTable for more details

filter_clause : string/None
    valid for wrapping DBTable object, SQL filter clause that allows more
    sophisticated selection of columns/rows of database table to be used in
    extracting data set from database table, or None if not used; see
    DBTable for more details

remove_id_col : boolean
    valid for wrapping DBTable object, specifies if the content of ID column of
    DBTable should be included in data set extracted from database table, True
    by default; NOTE: should be set to False for extracting purely numerical
    data sets; see DBTable for more details

Raises
------
Error
    if object of wrong type is presented to wrap, or if none of the object is
    presented at all
        """
        # either we wrap existing array or create new one from dbtable
        if input_array is None:
            if dbtable is not None:
                if not isinstance(dbtable, DBTable):
                    raise Error('%s instance expected! (%s found)' % (DBTable, className(dbtable)))
                # create physical array and keep it stored
                # note: we leave all error verification to dbtable
                self.cols = cols
                self.rows = rows
                self.dbtable = dbtable
                self._dbt_filter_clause = filter_clause
                self._dbt_remove_id_col = remove_id_col
                # create physical array and cache it
                self._cached_array = dbtable.getArray(columns=self.cols, rows=self.rows, filter_clause=self._dbt_filter_clause, remove_id_col=self._dbt_remove_id_col)
                self._wrapped = False
            else:
                # none of the above, report error
                raise Error('Either \'numpy.ndarray\' or %s instance expected! (none found)' % (DBTable))
        else:
            # store reference and mark as wrapped
            if isinstance(input_array, (numpy.ndarray, ndarray)):
                self._cached_array = input_array
                self._wrapped = True
                self.rows = ['__R%d__' % i for i in range(input_array.shape[0])]
                self.cols = ['__S%d__' % i for i in range(input_array.shape[1])]
                self.dbtable = None
            else:
                raise Error('\'numpy.ndarray\' instance expected! (%s found)' % (className(input_array)))
        self.array = self._cached_array

    def recache(self):
        r"""
Perform recaching of underlying ndarray object. Usable only when DBTable object
is wrapped.
        """
        if not self._wrapped:
            self._cached_array = self.dbtable.getArray(columns=self.cols, rows=self.rows, filter_clause=self._dbt_filter_clause, remove_id_col=self._dbt_remove_id_col)
            self.array = self._cached_array
            gc.collect()
