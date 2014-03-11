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
Provides specialized functionality for data--driven activities. This includes the
concrete producer of data subsets, according to the philosophy of creating smaller
subsets according to prior knowledge. The subset producer also categorizes them
actively with given categorizer(s).
"""

from kdvs.core.error import Error
from kdvs.core.util import isListOrTuple, className
from kdvs.fw.DBTable import DBTable
from kdvs.fw.DataSet import DataSet
from kdvs.fw.Map import PKCIDMap
from kdvs.fw.SubsetHierarchy import SubsetHierarchy

class PKDrivenDataManager(object):
    r"""
Base class for data--driven subset producer. The concrete subclass needs to
implement :meth:`getSubset` method that returns single :class:`~kdvs.fw.DataSet.DataSet`
instance for single prior knowledge concept specified. The implementation shall
create subset according to prior knowledge information. It may also re--implement
:meth:`categorizeSubset` method if necessary.
    """
    def __init__(self):
        r"""
By default, the constructor does nothing.
        """
        pass

    def getSubset(self, *args, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')

    @staticmethod
    def categorizeSubset(subset_inst, subsetCategorizer):
        r"""
Categorize input DataSet using categories from specified categorizer.

Parameters
----------
subset_inst : :class:`~kdvs.fw.DataSet.DataSet`
    instance of a subset to be categorized

subsetCategorizer : :class:`~kdvs.fw.Categorizer.Categorizer`
    instance of Categorizer to be used

Returns
-------
category : string
    category that has been associated by categorizer to input data subset
        """
        return subsetCategorizer.categorize(subset_inst)


class PKDrivenDBDataManager(PKDrivenDataManager):
    r"""
Concrete implementation of data--driven subset producer that creates overlapping
:class:`~kdvs.fw.DataSet.DataSet` instances based on prior knowledge information.
    """
    def __init__(self, main_dtable, pkcidmap_inst):
        r"""
Parameters
----------
main_dbtable : :class:`~kdvs.fw.DBTable.DBTable`
    database table that holds primary non--partitioned input data set with all
    measurements; overlapping subsets will be created based on it

pkcidmap_inst : :class:`~kdvs.fw.Map.PKCIDMap`
    concrete instance of fully constructed PKCIDMap that contains mapping between
    individual measurements and prior knowledge concepts; overlapping subsets
    will be created based on that mapping
        """
        super(PKDrivenDBDataManager, self).__init__()
        if not isinstance(main_dtable, DBTable):
            raise Error('%s instance expected! (%s found)' % (DBTable, className(main_dtable)))
        if not isinstance(pkcidmap_inst, PKCIDMap):
            raise Error('%s instance expected! (%s found)' % (PKCIDMap, className(pkcidmap_inst)))
        self.pkcidmap = pkcidmap_inst
        self.dtable = main_dtable
        self.all_samples = self._get_all_samples()

    def getSubset(self, pkcID, forSamples='*', get_ssinfo=True, get_dataset=True):
        r"""
Generate data subset for specific prior knowledge concept, and wrap it into
:class:`~kdvs.fw.DataSet.DataSet` instance if requested. Optionally, it can also
generate only the information needed to create subset manually and not the subset
itself; this may be useful e.g. if data come from remote source that offers no
complete control over querying.

Parameters
----------
pkcID : string
    identifier of prior knowledge concept for which the data subset will be generated

forSamples : iterable/string
    samples that will be used to generate data subset; by default, prior knowledge
    is associated with individual measurements and treats samples as equal; this
    may be changed by specifying the individual samples to focus on (as tuple of
    strings) or specifying string '*' for considering all samples; '*' by default

get_ssinfo : boolean
    if True, generate runtime information about the data subset and return it;
    True by default

get_dataset : boolean
    if True, generate an instance of :class:`~kdvs.fw.DataSet.DataSet` that wraps
    the data subset and return it; True by default

Returns
-------
ssinfo : dict/None
    runtime information as a dictionary of the following elements

        * 'dtable' -- :class:`~kdvs.fw.DBTable.DBTable` instance of the primary input data set
        * 'rows' -- row IDs for the subset (typically, measurement IDs)
        * 'cols' -- column IDs for the subset (typically, sample names)
        * 'pkcID' -- prior knowledge concept ID used to generate the subset; can be None if 'get_ssinfo' parameter was False

subset_ds : :class:`~kdvs.fw.DataSet.DataSet`/None
    DataSet instance that holds the numerical information of the subset; can be
    None if 'get_dataset' parameter was False

Raises
------
Error
    if `forSamples` parameter value was incorrectly specified
        """
        if forSamples == '*':
            subset_cols = self.all_samples
        elif isListOrTuple(forSamples):
            subset_cols = list(forSamples)
        else:
            raise Error('Non-empty list, tuple, or "*" expected! (got %s)' % (forSamples.__class__))
        # TODO: variables ID sorting introduced for compatibility with V1.0
        subset_vars = sorted(list(self.pkcidmap.pkc2emid[pkcID]))
        if get_ssinfo:
            ssinfo = dict()
            ssinfo['dtable'] = self.dtable
            ssinfo['rows'] = subset_vars
            ssinfo['cols'] = subset_cols
            ssinfo['pkcID'] = pkcID
        else:
            ssinfo = None
        if get_dataset:
            subset_ds = DataSet(dbtable=self.dtable, cols=subset_cols, rows=subset_vars, remove_id_col=False)
        else:
            subset_ds = None
        return ssinfo, subset_ds

    def _get_all_samples(self):
        alls = list(self.dtable.columns)
        alls.pop(self.dtable.id_column_idx)
        return alls


class PKDrivenDBSubsetHierarchy(SubsetHierarchy):
    r"""
Concrete instance of SubsetHierarchy class that generates proper data subsets
for given symbol (i.e. prior knowledge concept). This implementation uses
data--driven subset producer as a subset generator.
    """
    def __init__(self, pkdm_inst, samples_iter):
        r"""
Parameters
----------
pkdm_inst : :class:`PKDrivenDBDataManager`
    concrete instance of data--driven subset producer

samples_iter : iterable of string
    iterable of sample names that will be used during subset generation; typically,
    it contains all sample names as read from primary input data set
        """
        super(PKDrivenDBSubsetHierarchy, self).__init__()
        self.pkdm = pkdm_inst
        self.samples = samples_iter

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
        super(PKDrivenDBSubsetHierarchy, self).build(categorizers_list, categorizers_inst_dict, initial_symbols)

    def obtainDatasetFromSymbol(self, symbol):
        r"""
Obtain data subset for specific symbol (i.e. prior knowledge concept) and return it.

Parameters
----------
symbol : string
    symbol to return data subset for

Returns
-------
pkcDS : :class:`~kdvs.fw.DataSet.DataSet`
    data subset for specific symbol
        """
        # obtain DataSet instance for given symbol (in this context symbol is PKC ID)
        _, pkc_ds = self.pkdm.getSubset(symbol, forSamples=self.samples, get_ssinfo=False, get_dataset=True)
        return pkc_ds
