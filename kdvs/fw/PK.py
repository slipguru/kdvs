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
Provides high--level functionality for entities related to prior knowledge,
such as prior knowledge concepts, prior knowledge managers, etc.
"""

from kdvs.core.error import Error
from kdvs.fw.Map import SetBDMap

PKC_DETAIL_ELEMENTS = ['conceptID', 'conceptName', 'domainID', 'description', 'additionalInfo']
r"""
Default elements of each prior knowledge concept recognized by KDVS.

See Also
--------
PriorKnowledgeConcept
"""

class PriorKnowledgeConcept(object):
    r"""
The general representation of prior knowledge concept. Specific details depend
on the knowledge itself. For example, in gene expression data analysis, genes
may be grouped into functional classes, and each class may be represented by
single prior knowledge concept. Prior knowledge concepts may be additionally
grouped in domains if necessary; the concept of domain is used by prior knowledge
manager to expose selected "subset" of knowledge, without the need of exposing
all of it. The concept is thinly wrapped in a dictionary.
    """
    def __init__(self, conceptid, name, domain_id=None, description=None, additionalInfo={}):
        r"""
Parameters
----------
conceptid : string
    unique identifier of the concept across the whole knowledge

name : string
    name of the concept

domain_id : string/None
    unique identifier of the domain the concept is associated with, or None
    if the knowledge spans no domains

description : string/None
    optional textual description of the concept

additionalInfo : dict
    optional additional information associated with the concept; empty dictionary
    by default
        """
        self._pkc = dict()
        self._pkc['conceptID'] = conceptid
        self._pkc['conceptName'] = name
        self._pkc['domainID'] = domain_id
        self._pkc['description'] = description
        self._pkc['additionalInfo'] = dict(additionalInfo)

    def __getitem__(self, key):
        return self._pkc.__getitem__(key)

    def keys(self):
        r"""
Return all keys of the associated dictionary that holds the elements of the concept.
        """
        return self._pkc.keys()

class PKCManager(object):
    r"""
Abstract prior knowledge manager. The role of prior knowledge manager in KDVS
is to read any specific representation of the knowledge, memorize the individual
prior knowledge concepts, optionally map concepts to domains if necessary, and
expose individual concepts through its API. The concrete implementation must
implement the :meth:`configure`, :meth:`getPKC`, and :meth:`dump` methods,
and re--implement :meth:`load` method. The manager must be configured before
knowledge can be loaded. Concrete implementation may cache instances of
:class:`PriorKnowledgeConcept` or create them on the fly. Dump must be in
serializable format, and should be human readable if possible. Mapping between
concepts and domains by default is bi--directional (via :class:`~kdvs.fw.Map.SetBDMap`).
    """
    def __init__(self):
        # all considered prior knowledge domains (separated groups of concepts, e.g. thematic)
        self.domains = tuple()
        # concept IDs grouped according to domains
        self.domain2concepts = SetBDMap()
        self.configured = False

    def configure(self, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')

    def isConfigured(self):
        r"""
Return True if manager has been configured, False otherwise.
        """
        return self.configured

    def load(self, fh, **kwargs):
        r"""
By default, this method raises Error if manager has not been configured yet.
        """
        if not self.isConfigured():
            raise Error('PKC Manager must be configured before proceeding with load!')

    def getPKC(self, conceptID):
        # subclass may pre-cache PKC instances or create them on the fly
        raise NotImplementedError('Must be implemented in subclass!')

    def dump(self):
        # dump must be in serializable format
        raise NotImplementedError('Must be implemented in subclass!')
