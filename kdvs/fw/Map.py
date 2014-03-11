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
Provides high--level functionality for mappings constructed by KDVS.
"""

from kdvs.core.error import Error
from kdvs.core.util import Constant
import collections

NOTMAPPED = Constant('NotMapped')
r"""
Constant used to signal that entity is not mapped.
"""

# ----- general maps -----

class ChainMap(object):
    r"""
This map uses dictionaries of interlinked partial single mappings to derive final
mapping. For instance, for single mappings

    * {'a' : 1, 'b' : 2, 'c' : 3}
    * {1 : 'baa', 2 : 'boo', 3 : 'bee'}
    * {'baa' : 'x', 'boo' : 'y', 'bee' : 'z'}

the derived final mapping has the form

    * {'a' : 'x', 'b' : 'y', 'c' : 'z'}

Each single partial mapping is wrapped into an instance of this class, and
deriving is done with class--wide static method. This class exposes partial
:class:`dict` API and re--implements methods `__setitem__` and `__getitem__`.
NOTE: for this map, order of derivation, and therefore, order of single partial
mappings processed, is important.
    """
    def __init__(self, initial_dict=None):
        r"""
Parameters
----------
initial_dict : dict/None
    dictionary that contains the partial mapping, or None if to be constructed
    partially (this class implements subset of dictionary methods to do so); None
    by default

Raises
------
Error
    if mapping could not be initiated from initial dictionary
        """
        self.map = dict()
        if initial_dict is not None:
            try:
                self.map.update(initial_dict)
            except Exception, e:
                raise Error('Could not initialize map with defaults %s! (Reason: %s)' % (initial_dict, e))

    def __str__(self):
        return self.map.__str__()

    def __getitem__(self, key):
        r"""
For partial single mapping already present, return value for given key. When the
key--value pair is not present, return NOTMAPPED.

Parameters
----------
key : object
    lookup key

Returns
-------
value : object
    lookup value, or NOTMAPPED if lookup pair was not present
        """
        try:
            return self.map.__getitem__(key)
        except KeyError:
            return NOTMAPPED

    def __setitem__(self, key, val, replace=True):
        r"""
Add new key--value pair to partial single mapping, with possible replacement.

Parameters
----------
key : object
    key of new key--value pair to be added

value : object
    value of new key--value pair to be added

replace : boolean
    if True, if key already exists, replace existing key--value pair with given
    key--value pair; if False, raise Error; True by default

Raises
------
Error
    if replacement was not requested and key--value pair is already present
        """
        if replace is False and key in self.map:
            raise Error('"%s" already present in map!' % key)
        else:
            self.map.__setitem__(key, val)

    def getMap(self):
        r"""
Return partial single mapping as a dictionary.
        """
        return self.map

    def update(self, map_dict, replace=True):
        r"""
Update partial single mapping with all key--value pairs at once from given
dictionary, with possible replacement.

Parameters
----------
map_dict : dict
    dictionary that contains all key--value pairs to be added

replace : boolean
    if True, if any key from given dictionary already exists in the partial
    mapping, replace existing key--value pair with given
    key--value pair; if False, raise Error; True by default

Raises
------
Error
    if replacement was not requested and any key--value pair is already present
        """
        for key, val in map_dict.iteritems():
            self.__setitem__(key, val, replace)

    @staticmethod
    def deriveMap(key, maps):
        r"""
Derive single final value for given single key, computed across all given partial
single mappings.

Parameters
----------
key : object
    key for which the final value will be derived

maps : iterable of :class:`ChainMap`
    all single partial mappings, wrapped in ChainMap instance, that will be used
    for deriving the final value, in given order

Returns
-------
key, interms, value : object/NOTMAPPED, list of object, object/None
    the tuple with the following elements: lookup key or NOTMAPPED if at any stage
    of derivation NOTMAPPED was encountered; all intermediate values encountered
    during derivation; final derived value or None if not found

Raises
------
Error
    if iterable of partial single maps is incorrectly specified
        """
        interm = []
        if not all(isinstance(m, ChainMap) for m in maps):
            raise Error('Iterable of %s expected! (got %s)' % (ChainMap.__class__, maps))
        worklist = []
        worklist.extend(maps)
        worklist.insert(0, key)
        while len(worklist) > 1:
            interm_key = worklist.pop(0)
            interm_map = worklist.pop(0)
            val_interm_key = interm_map[interm_key]
            if val_interm_key == NOTMAPPED:
                return (NOTMAPPED, interm, interm_map)
            interm.append(val_interm_key)
            worklist.insert(0, val_interm_key)
        return (worklist[0], interm, None)

    @staticmethod
    def buildDerivedMap(keys, maps):
        r"""
Build mapping of key--value pairs that come from deriving of final values for
specified keys.

Parameters
----------
keys : iterable of object
    keys for which the final values will be derived and final map will be built

maps : iterable of :class:`ChainMap`
    all single partial mappings, wrapped in ChainMap instance, that will be used
    for deriving the final values, in given order

Returns
-------
dmap, interms : dict, iterable of object
    the tuple with the following elements: dictionary that contains derived final
    mapping for specified keys (may contain NOTMAPPED and None as values if some
    keys were not mapped correctly); all intermediate values encountered
    during derivation

Raises
------
Error
    if iterable of partial single maps is incorrectly specified

See Also
--------
deriveMap
        """
        dmap = ChainMap()
        interms = []
        for key in keys:
            derived_res = ChainMap.deriveMap(key, maps)
            dmap[key] = derived_res[0]
            interms.append(derived_res[1])
        return (dmap, interms)


class BDMap(object):
    r"""
This map stores bi--directional mappings. For such map, values can repeat. To
reflect that, values in both direction (forward and backward) will be binned. For
instance, for given initial mapping

    * {'a' : 1, 'b' : 1, 'c' : 2, 'd' : 3}

the following forward mapping will be constructed

    * {'a' : [1], 'b' : [1], 'c' : [2], 'd' : [3]}

and the following backward mapping will be constructed as well

    * {1 : ['a','b'], 2 : ['c'], 3 : ['d']}

The exact underlying data structure that hold binned values ("binning container")
depends on the specific map subtype. This class exposes partial
:class:`dict` API and re--implements methods `__setitem__`, `__getitem__`, and
`__delitem__`.

See Also
--------
collections.defaultdict
    """
    def __init__(self, factory_obj, add_op_name, initial_map=None):
        r"""
Parameters
----------
factory_obj : callable
    callable that returns new empty data structure for binning of repeated values,
    e.g. list(), set(), etc.

add_op_name : string
    name of the function that appends repeated value to binning container, e.g.
    "append" for list, "add" for set, etc.

initial_map : dict/None
    initial key--value pairs to add to bi--directional mapping, or None if nothing
    is to be added initially (this class implements subset of dictionary methods
    to add key--value pairs later); None by default
        """
        self.factory_obj = factory_obj
        self.add_op_name = add_op_name
        self.fwd_map = collections.defaultdict(factory_obj)
        self.bwd_map = collections.defaultdict(factory_obj)
        if initial_map is not None:
            for k, v in initial_map.iteritems():
                self.__setitem__(k, v)

    def _addto_bwd_map(self, key, val):
        # update backward map silently
        try:
            addop = getattr(self.bwd_map[val], self.add_op_name)
            addop(key)
        except:
            pass

    def _delfrom_bwd_map(self, delkey):
        # update backward map silently
        for revvals in self.bwd_map.values():
            try:
                # remove all occurences of delkey
                self._remove_occurences(revvals, delkey)
            except:
                pass
        for revkey in self.bwd_map.keys():
            if len(self.bwd_map[revkey]) == 0:
                del self.bwd_map[revkey]

    def _remove_occurences(self, it, key):
        raise NotImplementedError('Must be implemented in a subclass!')

    def __getitem__(self, key):
        r"""
Return value from forward mapping for given key.
        """
        return self.fwd_map[key]

    def __setitem__(self, key, val):
        r"""
Add given key--value pair to bi--directional mapping. The underlying forward
and backward partial mappings will be updated automatically.
        """
        addop = getattr(self.fwd_map[key], self.add_op_name)
        addop(val)
        self._addto_bwd_map(key, val)

    def __delitem__(self, key):
        r"""
Remove key--value pair (specified by lookup key) from bi--directional mapping.
The underlying forward and backward partial mappings will be updated automatically.
        """
        del self.fwd_map[key]
        self._delfrom_bwd_map(key)

    def clear(self):
        r"""
Clear bi--directional mapping. The underlying forward and backward mappings will be
cleared.
        """
        self.fwd_map.clear()
        self.bwd_map.clear()

    def keyIsMissing(self):
        r"""
Perform specific activity when given key is missing in the map during construction
of bi--directional mapping. By default, it creates new binning container by
calling factory_obj().

See Also
--------
collections.defaultdict.__missing__
        """
        return self.factory_obj()

    def getFwdMap(self):
        r"""
Return forward mapping as an instance of collections.defaultdict.
        """
        return self.fwd_map

    def getBwdMap(self):
        r"""
Return backward mapping as an instance of collections.defaultdict.
        """
        return self.bwd_map

    def getMap(self):
        r"""
Return forward mapping as an instance of collections.defaultdict.
        """
        return self.getFwdMap()

    def dumpFwdMap(self):
        r"""
Return forward mapping as a dictionary. NOTE: the resulting dictionary may not
be suitable for printing, depending on the type of underlying binning container.
        """
        return dict(self.fwd_map)

    def dumpBwdMap(self):
        r"""
Return backward mapping as a dictionary. NOTE: the resulting dictionary may not
be suitable for printing, depending on the type of underlying binning container.
        """
        return dict(self.bwd_map)


class ListBDMap(BDMap):
    r"""
Specialized BDMap that uses lists as binning containers. Repeated values are
added to binning container with :meth:`append` method. NOTE: all specialized
behavior incl. exceptions raised, depends on list type. Refer to documentation
of list type for more details.

See Also
--------
list
    """
    def __init__(self, initial_map=None):
        super(ListBDMap, self).__init__(list, 'append', initial_map)
    def _remove_occurences(self, it, key):
        it[:] = (rv for rv in it if rv != key)

class SetBDMap(BDMap):
    r"""
Specialized BDMap that uses sets as binning containers. Repeated values are
added to binning container with :meth:`add` method. NOTE: all specialized
behavior incl. exceptions raised, depends on set type. Refer to documentation
of set type for more details.

See Also
--------
set
    """
    def __init__(self, initial_map=None):
        super(SetBDMap, self).__init__(set, 'add', initial_map)
    def _remove_occurences(self, it, key):
        it.remove(key)

# ----- specific maps -----

# map between prior knowledge concepts and expression measurements IDs

class PKCIDMap(object):
    r"""
Abstract bi--directional mapping (binned in sets) between prior knowledge
concepts and individual measurements. The concrete implementation must implement
the "build" method, where the mapping is built and :class:`SetBDMap` instance of
`self.pkc2emid` is filled with it.
    """
    def __init__(self):
        self.pkc2emid = SetBDMap()
    def build(self, *args, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')

# map between prior knowledge concepts and gene symbols

class PKCGeneMap(object):
    r"""
Abstract bi--directional mapping (binned in sets) between prior knowledge
concepts and gene symbols. Used for gene expression data analysis, may not be
present in all KDVS applications. The concrete implementation must implement
the "build" method, where the mapping is built and :class:`SetBDMap` instance of
`self.pkc2gene` is filled with it.
    """
    def __init__(self):
        self.pkc2gene = SetBDMap()
    def build(self, *args, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')

# map between gene symbols and expression measurements IDs

class GeneIDMap(object):
    r"""
Abstract bi--directional mapping (binned in sets) between gene symbols and
individual measurements. Used for gene expression data analysis, may not be
present in all KDVS applications. The concrete implementation must implement
the "build" method, where the mapping is built and :class:`SetBDMap` instance of
`self.gene2emid` is filled with it.
    """
    def __init__(self):
        self.gene2emid = SetBDMap()
    def build(self, *args, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')
