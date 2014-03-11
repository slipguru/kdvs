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
Provides various utility classes and functions.
"""

from kdvs import ROOT_IMPORT_PATH
from kdvs.core.error import Error
import cPickle
import inspect
import itertools
import os
import sys
import types
import uuid
import pprint

def quote(s, quote="\""):
    r"""
Surrounds requested string with given "quote" strings.

Parameters
----------
s : string
    string to quote

quote : string
    string to be appended to the beginning and the end of requested string

Returns
-------
quoted_str : string
    quote + s + quote
    """
    return ''.join([quote, str(s), quote])

def CommentSkipper(seq, comment=None):
    r"""
Generator that discards strings prefixed with given comment string.

Parameters
----------
seq : iterable
    sequence of strings

comment : string/None
    comment prefix; if None, do not perform any discarding at all

Returns
-------
ncomseq : iterable
    filtered input sequence of strings without commented ones
    """
    # skip lines from sequence that starts with comment
    if comment is not None:
        for s in seq:
            if not s.startswith(comment):
                yield s
    else:
        for s in seq:
            yield s

def isListOrTuple(obj):
    r"""
Return True if given object is an instance of list or tuple, and False otherwise.
    """
    return isinstance(obj, types.ListType) or isinstance(obj, types.TupleType)

def isTuple(obj):
    r"""
Return True if given object is an instance of tuple, and False otherwise.
    """
    return isinstance(obj, types.TupleType)

def isIntegralNumber(obj):
    r"""
Return True if given object is an instance of integer number, and False otherwise.
    """
    # since boolean is technically an integral type, we need to handle this case explicitly
    if isinstance(obj, types.BooleanType):
        return False
    else:
        return isinstance(obj, types.IntType) or isinstance(obj, types.LongType)

def className(obj):
    r"""
Return class name of the object.
    """
    return obj.__class__.__name__

def emptyGenerator():
    r"""
Generator that yields nothing.
    """
    return
    yield

def emptyCall():
    r"""
Empty callable.
    """
    pass

def revIndices(sliceobj):
    r"""
Internal function. Revert given slice object.
    """
#    print sliceobj
    step = sliceobj.step if sliceobj.step is not None else 1
    start = sliceobj.start if sliceobj.start is not None else 0
#    print start, sliceobj.stop, step
    return range(start, sliceobj.stop, step)

class NPGenFromTxtWrapper(object):
    r"""
Wraps DBResult instance into a generator that can be passed to :func:`numpy.loadtxt` family
of functions. It exposes appropriate methods accepted by :func:`numpy.loadtxt` depending
on the numpy version: 'readline' (for numpy < 1.6.0), 'next' (for numpy >= 1.6.0).
    """
    def __init__(self, dbresult, delim=' ', id_col_idx=None):
        r"""
Parameters
----------
dbresult : :class:`~kdvs.fw.DBResult.DBResult`
    DBResult object to be wrapped

delim : string
    requested delimiter for 'loadtxt'--type function, space by default

id_col_idx : integer/None
    index of column that contains ID; if not None, the content of that column
    will be discarded by the generator

See Also
--------
numpy.genfromtxt
        """
        # whitespace is default delimiter for numpy.genfromtxt/numpy.loadtxt
        def _get_row(dbresult, delim):
            results = dbresult.get()
            for res in results:
                rcols = [str(r) for r in res]
                if id_col_idx is not None:
                    rcols.pop(id_col_idx)
                yield delim.join(rcols)
        self.dbresult = dbresult
        self.delim = delim
        self.gen = _get_row(self.dbresult, self.delim)
    def __iter__(self):
        # from 1.6.0, numpy uses iterator for data input
        return self
    def next(self):
        # from 1.6.0, numpy uses iterator for data input
        return self.gen.next()
    def readline(self):
        # prior to 1.6.0, numpy uses getline() for data input
        return self.gen.next()

def getSerializableContent(obj):
    r"""
Produce representation of the object that is as serializable as possible (in the
sense of :mod:`pickle`).

Parameters
----------
obj : object
    object to be serialized

Returns
-------
ser_obj : object
    serialized object (in terms of `pickle`) or serializable surrogate that identifies
    the origin of the original object.
    """
    # return serializable surrogate that can identify origin of original object
    if inspect.ismodule(obj):
        return ('Module', obj.__name__, obj.__file__)
    elif isinstance(obj, types.FileType):
        return ('File', obj.name)
    elif inspect.isroutine(obj):
        return ('Executable', obj.func_name, inspect.getsourcefile(obj))
    elif inspect.isclass(obj):
        return ('Class', obj.__name__, inspect.getsourcefile(obj))
    else:
        try:
            cPickle.dumps(obj)
            return obj
        except:
            return '<Not serializable: %s.%s>' % (obj.__class__.__module__, obj.__class__.__name__)

# ---- utils for serializing objects in various ways (self contained, can be used as depfuncs)

def serializeObj(obj, out_fh, protocol=None):
    r"""
Serialize given input object to opened file--like handle. Self--contained function,
can be used as depfunc with :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`.

Parameters
----------
obj : object
    object to be serialized

out_fh : file-like
    file-like object that accepts serialized object

protocol : integer/None
    protocol used by :mod:`pickle`/:mod:`cPickle` in serialization of the input object; if None,
    the highest possible is used
    """
    import cPickle
    import gzip
    if protocol is None:
        proto = cPickle.HIGHEST_PROTOCOL
#        proto = 0
    else:
        proto = protocol
    wrapped_out_fh = gzip.GzipFile(fileobj=out_fh)
#    cPickle.Pickler(out_fh, protocol=proto).dump(obj)
    cPickle.Pickler(wrapped_out_fh, protocol=proto).dump(obj)

def deserializeObj(in_fh):
    r"""
Deserialize object from opened file--like handle. Self--contained function,
can be used as depfunc with :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`.

Parameters
----------
in_fh : file-like
    file-like object that contains serialized object

Returns
-------
obj : object
    deserialized object

See Also
--------
pickle
cPickle
    """
    import cPickle
    import gzip
    wrapped_in_fh = gzip.GzipFile(fileobj=in_fh)
#    return cPickle.Unpickler(in_fh).load()
    return cPickle.Unpickler(wrapped_in_fh).load()

def serializeTxt(lines, out_fh):
    r"""
Serialize given lines of text to opened file--like handle. Self--contained function,
can be used as depfunc with :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`.

Parameters
----------
lines : iterable
    lines of text to be serialized

out_fh : file-like
    file-like object that accepts serialized object

Notes
-----
Currently it just writes text lines with 'writelines'. Override for more detailed
control.
    """
    out_fh.writelines(lines)

def pprintObj(obj, out_fh, indent=2):
    r"""
Pretty prints in sense of :func:`pprint.pprint`, the represenation of given input object,
to opened file--like handle. Self--contained function, can be used as depfunc
with :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`.

Parameters
----------
obj : object
    object to be pretty printed

out_fh : file-like
    file-like object that accepts pretty printed object

indent : integer
    indentation used by pretty printer; 2 spaces by default
    """
    import pprint
    pprint.pprint(obj, out_fh, indent=indent)

def writeObj(obj, out_fh):
    r"""
Write given input object to opened file--like handle. Self--contained function,
can be used as depfunc with :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`.

Parameters
----------
obj : object
    object to be written

out_fh : file-like
    file-like object that accepts written object

Notes
-----
Currently it just writes object with 'write'. The exact behavior depends on the
given input object and file-like object. The function does not check for any error.
Override for more detailed control.
    """
    out_fh.write(obj)

# ----

def isDirWritable(directory):
    r"""
Return True if given directory is writable, and False otherwise.
    """
    # check if directory is writable by creating dummy temporary file in it
    tmpf = uuid.uuid1().hex + os.path.extsep + 'tmp'
    tmpname = os.path.join(directory, tmpf)
    try:
        t = open(tmpname, 'wb')
        t.close()
        os.remove(tmpname)
        return True
    except:
        return False

def importComponent(qualified_name, qualifier='.'):
    r"""
Dynamically import given module.

Parameters
----------
qualified_name : string
    fully qualified module path as resolvable by Python, e.g. 'kdvs.core.util.importComponent'.

qualifier : string
    qualifier symbol used in given module path; dot ('.') by default

Returns
-------
module : module
    imported module instance, as leaf (not root) in Python module hierarchy;
    see :func:`__import__` for more details

Notes
-----
Importing is done relatively to :data:`~kdvs.__init__.ROOT_IMPORT_PATH` only. This function is used
for detailed dynamic imports from within KDVS.
    """
    if ROOT_IMPORT_PATH not in sys.path:
        sys.path.append(ROOT_IMPORT_PATH)
    module, _, inst = qualified_name.rpartition(qualifier)
    mod = __import__(module, fromlist=[inst])
    return getattr(mod, inst)

def getFileNameComponent(path):
    r"""
Return filename component of given file path.
    """
    return os.path.basename(path).partition('.')[0]

def resolveIndexes(dsv, indexes_info):
    r"""
Internal helper function. Return correct indexes for given :class:`~kdvs.fw.DSV.DSV` instance.
    """
    return (dsv.id_column,) if indexes_info is None else indexes_info

# s -> (s0,s1), (s1,s2), (s2, s3), ...
def pairwise(iterable):
    r"""
Taken from :mod:`itertools` receipts. Split given iterable of elements into overlapping
pairs of elements as follows: (s0,s1,s2,s3,...) -> (s0,s1),(s1,s2),(s2, s3),...
    """
    a, b = itertools.tee(iterable)
    next(b, None)
    return itertools.izip(a, b)

class Parametrizable(object):
    r"""
Abstract class that can be parametrized. During instantiation, given parameters
can be compared to reference ones, and Error is thrown when they do not match.
    """

    def __init__(self, ref_parameters=(), **kwargs):
        r"""
Parameters
----------
ref_parameters : iterable
    reference parameters to be checked against during instantiation; empty tuple by default

kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones

Raises
------
Error
    if some supplied parameters are not on the reference list
        """
        self.parameters = None
        # we report any parameter not in reference iterable
        missing_params = set(ref_parameters) ^ set(kwargs.keys())
        if len(missing_params) > 0:
            refps = ','.join([quote(rp) for rp in ref_parameters])
            mps = ','.join([quote(mp) for mp in missing_params])
            raise Error('Some parameters are not on reference list! (reflist=%s, missing/extra=%s)' % (refps, mps))
        else:
            self.parameters = dict(kwargs)

class Configurable(object):
    r"""
Abstract class that can be configured. During instantiation, given configuration
can be compared to reference one, and Error is thrown when they do not match.
Expected configuration is a dictionary of objects {'par1' : partype1obj,
'par2' : partype2obj, ...}, where partypeXobj is the example object of expected
type. For instance, if partypeXobj is {}, it will be checked if the parameter
value is a dictionary. Object types are checked with :func:`isinstance`.
    """

    def __init__(self, expected_cfg={}, actual_cfg={}):
        r"""
Parameters
----------

expected_cfg : dict
    expected configuration; empty dictionary by default

actual_cfg : dict
    actual supplied configuration; empty dictionary by default

Raises
------
Error
    if any element is missing from expected configuration
Error
    if expected type of any element is wrong
        """
        self._cfg = dict()
        self._preconfigure(expected_cfg, actual_cfg)

    def __getitem__(self, key):
        return self._cfg.__getitem__(key)

    def keys(self):
        r"""
Return all keys of actual supplied configuration.
        """
        return self._cfg.keys()

    def _preconfigure(self, expected_cfg, actual_cfg):
        for exp_elem in expected_cfg.keys():
            if not exp_elem in actual_cfg:
                raise Error('%s element missing in configuration!' % quote(exp_elem))
            else:
                inst = actual_cfg[exp_elem]
                exp_inst = expected_cfg[exp_elem]
                if not isinstance(inst, exp_inst.__class__):
                    raise Error('Instance of %s expected! (got %s)' % (exp_inst.__class__, inst.__class__))
                else:
                    self._cfg[exp_elem] = inst

class Constant(object):
    r"""
Class that represents string constants.
    """
    def __init__(self, srepr):
        r"""
Parameters
----------
srepr : object
    Textual representation of string constant.

Notes
-----
In current implementation, it represents 'text' with '<text>'.
        """
        self.srepr = '<%s>' % srepr
    def __str__(self):
        return self.srepr
    def __repr__(self):
        return self.__str__()
