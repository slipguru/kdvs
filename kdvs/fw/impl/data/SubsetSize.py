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
Provides specific functionality for activities connected to size of the data
subsets. For instance, data subsets can be categorized based on their size.
"""

from kdvs.fw.Categorizer import Categorizer, NOTCATEGORIZED, Orderer

class SubsetSizeCategorizer(Categorizer):
    r"""
Categorizer that checks the size of the data subset (in terms of number of variables
associated; also 'rows' in KDVS internal implementation terminology), and classifies
it into one of two categories: 'lesser than' (if size <= threshold) or 'greater
than' (if size > threshold).
    """
    ROW_SIZE_LESSER = '<='
    ROW_SIZE_GREATER = '>'

    def __init__(self, size_threshold, ID='SubsetSizeCategorizer', size_lesser_category='<=', size_greater_category='>'):
        r"""
Parameters
----------
size_threshold : integer
    size threshold that categorized data subset will be checked against

ID : string
    identifier of this categorizer; can be skipped to use default value;
    'SubsetSizeCategorizer' by default

size_lesser_category : string
    identifier of 'lesser than' category; can be skipped to use default value;
    '<=' by default

size_greater_category : string
    identifier of 'greater than' category; can be skipped to use default value;
    '>' by default
        """
        self.size_threshold = size_threshold
        self.ROW_SIZE_LESSER = size_lesser_category
        self.ROW_SIZE_GREATER = size_greater_category
        funcTable = {
            size_lesser_category : self._row_size_lesser,
            size_greater_category : self._row_size_greater,
        }
        super(SubsetSizeCategorizer, self).__init__(ID, funcTable)

    def _row_size_lesser(self, dataset_inst):
        if dataset_inst.rows != '*':
            if len(dataset_inst.rows) <= self.size_threshold:
                return self.ROW_SIZE_LESSER
            else:
                return NOTCATEGORIZED
        else:
            return NOTCATEGORIZED

    def _row_size_greater(self, dataset_inst):
        if dataset_inst.rows != '*':
            if len(dataset_inst.rows) > self.size_threshold:
                return self.ROW_SIZE_GREATER
            else:
                return NOTCATEGORIZED
        else:
            return NOTCATEGORIZED

    def getThreshold(self):
        r"""
Return size threshold for that categorizer as an integer.
        """
        return self.size_threshold


class SubsetSizeOrderer(Orderer):
    r"""
Concrete Orderer that is closely associated with data--driven activities. It is
used to change ordering of the elements associated with subset sizes. For instance,
one may expect data subsets to be processed starting from the largest ones and
going progressively towards smaller ones. The :meth:`build` method of this class
accepts iterable of tuples (pkcID, size), where 'pkcID' is PKC (prior knowledge
concept) ID, and 'size' is the size of associated data subset (in terms of number
of variables associated; also 'rows' in KDVS internal implementation terminology).
NOTE: this class must be given as input the already sorted iterable, when sort
is done according to descending size of associated data subsets.
    """

    def __init__(self, descending=True):
        r"""
Parameters
----------
descending : boolean
    if True, the order is descending wrt subset size; if False, the order is
    ascending wrt subset size; True by default
        """
        self.descending = descending
        super(SubsetSizeOrderer, self).__init__()

    def build(self, pkc2ss):
        r"""
Build appropriate order from given iterable of tuples (pkcID, size). This
method expects iterable that is already sorted in descending way (i.e. starting
from largest data subsets).

Parameters
----------
pkc2ss : iterable of (string, integer)
    iterable of tuples (pkcID, size), sorted in descending order wrt subset size (i.e. starting from largest)
        """
        # pkc2ss is an iterable of PKC IDs, sorted in descending order wrt subset
        # size (i.e. starting from largest)
        self.pkc2ss = pkc2ss
        # make a copy of iterable to sort it
        ordering = [ss for ss in self.pkc2ss]
        # reverse the iterable if requested
        if not self.descending:
            ordering.reverse()
        self.ordering = ordering

    def order(self):
        r"""
Return specific order for this orderer. NOTE: the order is the iterable of
pkcIDs alone; the size information is omitted, but the original iterable can
still be accessed as `self.pkc2ss`.

Returns
-------
order : iterable of string
    ordered iterable of PKC IDs
        """
        return super(SubsetSizeOrderer, self).order()
