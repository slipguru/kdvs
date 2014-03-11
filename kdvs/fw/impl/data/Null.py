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
Provides functionality for 'null' data--driven activities. Null activities are
neutral against their arguments, simply passing them.
"""

from kdvs.fw.Categorizer import Categorizer, Orderer

class NullCategorizer(Categorizer):
    r"""
Null categorizer that uses single virtual 'category' that passes the data
subset without checking it and marks it with that category. Useful as
placeholder and on the top of categorizers hierarchy, where more specialized work
is done with more specialized categorizers.
    """
    def __init__(self, ID='NullCategorizer', null_category='__all__'):
        r"""
Parameters
----------
ID : string
    identifier of this categorizer; can be skipped to use default name

null_category : string
    name of single virtual category that null categorizer marks all subsets with; can be
    skipped to use default name
        """
        self.NULL = null_category
        funcTable = {
            null_category : self._null,
        }
        super(NullCategorizer, self).__init__(ID, funcTable)

    def _null(self, dataset_inst):
        # all datasets categorized equally
        return self.NULL


class NullOrderer(Orderer):
    r"""
Null orderer that simply returns given iterable without actually ordering it.
Useful as placeholder and on lower levels of categorizers hierarchy, when the
ordering has already been performed upstream.
    """
    def __init__(self):
        r"""
        """
        super(NullOrderer, self).__init__()

    def build(self, iterable):
        r"""
'Build' the order by simply keeping the input iterable as is.
        """
        self.ordering = iterable

    def order(self):
        r"""
Return the order by simply returning an input iterable.
        """
        return super(NullOrderer, self).order()
