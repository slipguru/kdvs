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
Provides base functionality for categorizers and orderers. Categorizers can
divide data subsets into useful categories that can be nested and resemble a
tree. This could be useful for assigning selected statistical techniques to
specific data subsets only. Orderers control the order in which data subsets
are being processed; each category can have its own orderer.
"""

from kdvs.core.error import Error
from kdvs.core.util import Constant
import re

NOTCATEGORIZED = Constant('NotCategorized')
r"""
Informs KDVS that data subset could not be categorized, for whatever reason. Used
in concrete derivations of Categorizer.
"""

UC = 'C[%s]->c[%s]'
r"""
Standard way to present category stemming from categorizer, as follows:
C["categorizer_name"]->c["category_name"].
"""

_UC_PATTERN = re.compile('\C\[(.+)\]\-\>\c\[(.+)\]')

class Categorizer(object):
    r"""
Base class for categorizers. Categorizer must be supplied with dictionary of
functions that categorize given subsets. Each function accepts
:class:`~kdvs.fw.DataSet.DataSet` instance and outputs, as string, either chosen
category name or :data:`NOTCATEGORIZED`. Dictionary
maps category names to categorization functions. One must be careful to assign
only one category to single data subset; if not, dataset will be permanently
:data:`NOTCATEGORIZED` without warning.
    """
    def __init__(self, IDstr, categorizeFuncTable):
        r"""
Parameters
----------

IDstr : string
    identifier for the categorizer; usage of only alphanumerical characters is
    preferred; descriptive identifiers are preferred due to heavy usage in KDVS
    logs

categorizeFuncTable : dict(string->callable)
    function table for the categorizer; keys are category names that this categorizer
    will use; values are callables that return that exact category name or
    :data:`NOTCATEGORIZED`

Raises
------
Error
    if identifier is not a string
Error
    if function table is not a dictionary of it is empty
Error
    if any key in function table is not a string
        """
        if not isinstance(IDstr, basestring):
            raise Error('%s instance expected! (got %s)' % (basestring, IDstr.__class__))
        if not isinstance(categorizeFuncTable, dict) or len(categorizeFuncTable) < 1:
            raise Error('%s non-empty instance expected! (got %s)' % (dict.__class__, categorizeFuncTable.__class__))
        catkeysstr = all([isinstance(k, basestring) for k in categorizeFuncTable.keys()])
        if not catkeysstr:
            raise Error('Keys of categorizer function table must be strings!')
        self.id = IDstr
        # categorizeFuncTable: {category->categorize_function}
        self.categorizeC2F = dict(categorizeFuncTable)
        self.categorizeF2C = dict([(v, k) for k, v in self.categorizeC2F.iteritems()])

    def categories(self):
        r"""
Returns all categories that this categorizer handles. Essentially, returns keys from
categorization function table.
        """
        return self.categorizeC2F.keys()

    def categorize(self, dataset_inst):
        r"""
Categorizes given data subset by running all categorization functions on it,
collecting the categories, and checking for their uniqueness. If exactly one
single category is recognized, it is returned. If not, :data:`NOTCATEGORIZED`
is returned.

Parameters
----------
dataset_inst : :class:`~kdvs.fw.DataSet.DataSet`
    instance of data subset to be categorized

Returns
-------
category : string
    category this data subset falls under; can be :data:`NOTCATEGORIZED` in the following cases:
        * more than one function return different valid categories
        * all functions return :data:`NOTCATEGORIZED`
        """
        cats = [(cat, func(dataset_inst)) for cat, func in self.categorizeC2F.iteritems()]
        category = set([dc for oc, dc in cats if oc == dc])
        if len(category) == 1:
            # category determined unambiguously, retrieve single element
            catcall = next(iter(category))
        else:
            catcall = NOTCATEGORIZED
        return catcall

    def uniquifyCategory(self, category):
        r"""
Given category name, makes it unique by binding it to categorizer name. It uses
format specified in global variable :data:`UC`.

Parameters
----------
category : string
    category name to uniquify; typically one of the keys from function table

Returns
-------
uniquified_category : string
    uniquified category; format is taken from global variable :data:`UC`

See Also
--------
deuniquifyCategory
        """
        return UC % (self.id, category)

    @staticmethod
    def deuniquifyCategory(uniquified_category):
        r"""
Reverse the effect of 'uniquifying' the category name. Returns tuple (categorizer_name,
category_name).

Parameters
----------
uniquified_category : string
    uniquified category

Returns
-------
uniquified_components : tuple
    parsed elements as tuple: (categorizer_name, category_name), or (None, None)
    if parsing was not successful

See Also
--------
uniquifyCategory
UC
        """
        uc_match = _UC_PATTERN.match(uniquified_category)
        if uc_match is not None:
            internalID, internalCategory = uc_match.groups()
            return internalID, internalCategory
        else:
            return None, None

    def __str__(self):
        return '<<Categorizer:"%s">>' % self.id

    def __repr__(self):
        return self.__str__()

class Orderer(object):
    r"""
Base class for orderers. In general, orderer accepts an iterable of data subset IDs,
reorders it as it sees fit, and presents it through its API.
    """
    def __init__(self):
        r"""
        """
        # ordering : iterable of pkcIDs
        self.ordering = None

    def build(self, *args, **kwargs):
        r"""
Must be implemented in subclass. The implementation MUST assign reordered iterable
to `self.ordering`.
        """
        raise NotImplementedError('Must be implemented in subclass!')

    def order(self):
        r"""
Returns the ordering built by this orderer.

Returns
-------
ordering : iterable
    properly ordered iterable of data subset IDs

Raises
------
Error
    if ordering has not been built yet
        """
        if self.ordering is None:
            raise Error('Ordering has not been built!')
        else:
            return self.ordering
