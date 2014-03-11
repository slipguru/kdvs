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
Provides specification for actions executed by execution environment.
"""

from kdvs.core.error import Error
import types
from kdvs.core.util import isListOrTuple

class ActionSpec(object):

    r"""
Creates new action to be submitted to execution environment.
Action specification encapsulates arbitrary Python callable and its arguments.
In addition, if requested, execution environment can check if certain variables
have been present and/or produced before and after the execution.
    """

    def __init__(self, input_vars, output_vars, func, args, kwargs):
        r"""
Parameters
----------
input_vars : list/tuple
    names of the variables that shall be present in the environment before
    the execution of the action

output_vars : list/tuple
    names of the variables that shall be present in the environment after
    the execution of the action

func : callable
    function to be executed

args : iterable
    any additional positional arguments passed to function

kwargs : dict
    any additional keyworded arguments passed to function
        """

        if isinstance(input_vars, types.ListType) or isinstance(input_vars, types.TupleType):
            self.input_vars = input_vars
        else:
            raise Error('List or tuple expected! Got \"%s\"' % input_vars.__class__)
        if isListOrTuple(output_vars):
            self.output_vars = output_vars
        else:
            raise Error('List or tuple expected! Got \"%s\"' % output_vars.__class__)
#        if isinstance(func, types.FunctionType):
        if callable(func):
            self.func = func
        else:
            raise Error('Callable expected! Got \"%s\"' % func.__class__)
        if isListOrTuple(args):
            self.args = args
        else:
            raise Error('List or tuple expected! Got \"%s\"' % args.__class__)
        if isinstance(kwargs, types.DictType):
            self.kwargs = kwargs
        else:
            raise Error('Dictionary expected! Got \"%s\"' % kwargs.__class__)

    def __str__(self):
        return ','.join((str(self.input_vars), str(self.output_vars),
                         '"' + self.func.__name__ + '"', str(self.args), str(self.kwargs)))

    def as_tuple(self):
        r"""
Return all the elements of action specification as tuple:
(input_vars, output_vars, func, args, kwargs)
        """
        return (self.input_vars, self.output_vars, self.func, self.args, self.kwargs)
