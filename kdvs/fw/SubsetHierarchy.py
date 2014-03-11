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
Provides high--level functionality for management of hierarchy of data subsets.
Subsets can be hierarchical according to prior knowledge domains, or according
to user specific criteria. Hierarchy is built based on categorizers.
"""

from kdvs.core.error import Error
from kdvs.core.util import pairwise
import collections

class SubsetHierarchy(object):
    r"""
Abstract subset hierarchy manager. It constructs and manages two entities available
as global attributes: :attr:`hierarchy` and :attr:`symboltree`. Data subsets may
be categorized with categorizers, and categories may be nested. Hierarchy refers
to the nested categories as the dictionary of the following format:

    * {parent_category : child_categorizer_id}

where root categorizer is keyed with None (because of no parent), and categories
in last categorizer are valued with None (because of no children). Symboltree
refers to symbols categorized by categories as the dictionary of the following format:

    * {parent_category : {child_category1 : [associated symbols], ..., child_categoryN : [associated symbols]}}

In contrast to hierarchy, symboltree does not contain 'None' keys/values. Typically,
symbols refer to prior knowledge concepts. Concrete implementation must implement
:meth:`obtainDatasetFromSymbol` method.
    """
    def __init__(self):
        r"""
        """
        self.hierarchy = dict()
        self.symboltree = dict()

    def build(self, categorizers_list, categorizers_inst_dict, initial_symbols):
        r"""
Build categories hierarchy and symboltree.

Parameters
----------
categorizers_list : iterable of string
    iterable of identifiers of :class:`~kdvs.fw.Categorizer.Categorizer` instances,
    starting from root of the tree

categorizers_inst_dict : dict
    dictionary of :class:`~kdvs.fw.Categorizer.Categorizer` instances, identified
    by specified identifiers

initial_symbols : iterable of string
    initial pool of symbols to be 'partitioned' with nested categorizers into
    symboltree; typically, contains all prior knowledge concepts (from single
    domain or all domains if necessary)

Raises
------
Error
    if requested :class:`~kdvs.fw.Categorizer.Categorizer` instance is not found
    in the instances dictionary
        """
        self._categorizersInst = categorizers_inst_dict
        try:
            self._categorizersList = [(cid, self._categorizersInst[cid]) for cid in categorizers_list]
        except KeyError:
            raise Error('Categorizer %s not found in instances dictionary! (got %s)' % (cid, self._categorizersInst))
        self._symbols = initial_symbols
        for (_, pcat), (chcatID, _) in pairwise(self._categorizersList):
            pcategories = pcat.categories()
            for pcategory in pcategories:
                self.hierarchy[pcat.uniquifyCategory(pcategory)] = chcatID
        try:
            # first categories are rooted with None
            firstcat = self._categorizersList[0][0]
            self.hierarchy[None] = firstcat
        except IndexError:
            pass
        try:
            # final categories are leafed with None
            finalcat = self._categorizersList[-1][1]
            finalcts = finalcat.categories()
            for finalct in finalcts:
                self.hierarchy[finalcat.uniquifyCategory(finalct)] = None
        except IndexError:
            pass
        try:
            self._buildSymbols(None, self._symbols)
        except NotImplementedError:
            self.symboltree = None

    def obtainDatasetFromSymbol(self, symbol):
        r"""
Must be implemented in subclass. It shall return an instance of
:class:`~kdvs.fw.DataSet.DataSet` for given symbol.
        """
        raise NotImplementedError('Must be implemented in subclass!')

    def _buildSymbols(self, hierarchyKey, symbols):
        if hierarchyKey in self.hierarchy:
            categorizerID = self.hierarchy[hierarchyKey]
            if categorizerID is not None:
                categorizer = self._categorizersInst[categorizerID]
                self.symboltree[hierarchyKey] = collections.defaultdict(list)
                for symbol in symbols:
                    dataset_inst = self.obtainDatasetFromSymbol(symbol)
                    symbol_cat = categorizer.categorize(dataset_inst)
                    self.symboltree[hierarchyKey][categorizer.uniquifyCategory(symbol_cat)].append(symbol)
#                _symtelem=dict(self.symboltree[hierarchyKey])
#                self.symboltree[hierarchyKey]=_symtelem
                for symcat, syms in self.symboltree[hierarchyKey].iteritems():
                    self._buildSymbols(symcat, syms)
#            else:
#                self.symboltree[hierarchyKey] = None
