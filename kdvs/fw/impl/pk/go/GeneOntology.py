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
Provides concrete implementation of `Gene Ontology <http://www.geneontology.org/>`_
(GO) manager that manages individual GO terms as prior knowledge concepts. Also
provides various constants specific for GO.
"""

from datetime import datetime
from kdvs.core.error import Error, Warn
from kdvs.core.provider import RECOGNIZED_FILE_PROVIDERS
from kdvs.core.util import quote
from kdvs.fw.Map import SetBDMap
from kdvs.fw.PK import PKCManager, PriorKnowledgeConcept
import collections
import re

try:
    from xml.etree.cElementTree import iterparse
except ImportError:
    from xml.etree.ElementTree import iterparse

# ---- Gene Ontology content miscellanea

GO_BP_DS = 'BP'
r"""
Internal KDVS symbol that refers to Biological Process (BP) domain of GO.
"""

GO_MF_DS = 'MF'
r"""
Internal KDVS symbol that refers to Molecular Function (MF) domain of GO.
"""

GO_CC_DS = 'CC'
r"""
Internal KDVS symbol that refers to Cellular Component (CC) domain of GO.
"""

GO_DOMAINS = {
    'BP' : 'biological_process',
    'CC' : 'cellular_component',
    'MF' : 'molecular_function',
}
r"""
Descriptive identifiers for GO domains.
"""

GO_DS = GO_DOMAINS.keys()
r"""
Symbols of GO domains recognized by KDVS.
"""

GO_ROOT_TERMS = {
    'BP' : 'GO:0008150',
    'CC' : 'GO:0005575',
    'MF' : 'GO:0003674',
}
r"""
Root terms of GO domains.
"""

GO_EVIDENCE_CODES = {
    # experiment evidence codes
    'EXP' : 'inferred from experiment',
    'IDA' : 'inferred from direct assay',
    'IPI' : 'inferred from physical interaction',
    'IMP' : 'inferred from mutant phenotype',
    'IGI' : 'inferred from genetic interaction',
    'IEP' : 'inferred from expression pattern',
    # computational analysis evidence codes
    'ISS' : 'inferred from sequence or structural similarity',
    'ISO' : 'inferred from sequence orthology',
    'ISA' : 'inferred from sequence',
    'ISM' : 'inferred from sequence model',
    'IGC' : 'inferred from genomic context',
    'RCA' : 'inferred from reviewed computational analysis',
    # author statement codes
    'TAS' : 'traceable author statement',
    'NAS' : 'non-traceable author statement',
    # curatiorial statement evidence codes
    'IC' : 'inferred by curator',
    'ND' : 'no biological data available',
    # auto-assigned evidence codes
    'IEA' : 'inferred from electronic annotation',
    # obsolete evidence codes
    'NR' : 'not recorded'
}
r"""
Mapping of recognized GO evidence codes: {code : description}.
"""

GO_INV_EVIDENCE_CODES = {
    # experiment evidence codes
    'inferred from experiment' : 'EXP',
    'inferred from direct assay' : 'IDA',
    'inferred from physical interaction' : 'IPI',
    'inferred from mutant phenotype' : 'IMP',
    'inferred from genetic interaction' : 'IGI',
    'inferred from expression pattern' : 'IEP',
    # computational analysis evidence codes
    'inferred from sequence or structural similarity' : 'ISS',
    'inferred from sequence orthology' : 'ISO',
    'inferred from sequence' : 'ISA',
    'inferred from sequence model' : 'ISM',
    'inferred from genomic context' : 'IGC',
    'inferred from reviewed computational analysis' : 'RCA',
    # author statement codes
    'traceable author statement' : 'TAS',
    'non-traceable author statement' : 'NAS',
    # curatiorial statement evidence codes
    'inferred by curator' : 'IC',
    'no biological data available' : 'ND',
    # auto-assigned evidence codes
    'inferred from electronic annotation' : 'IEA',
    # obsolete evidence codes
    'not recorded' : 'NR'
}
r"""
Inverted mapping of recognized GO evidence codes: {description : code}.
"""

GO_UNKNOWN_EV_CODE = 'UNK'
r"""
KDVS--specific artificial 'unknown evidence code' used when non recognized
evidence code is encountered.
"""

# ---- Gene Ontology parse technical data

# recognized relations
GO_DEF_RECOGNIZED_RELATIONS = ['is_a', 'part_of', 'regulates', 'positively_regulates', 'negatively_regulates']
r"""
Default inter--term relation recognized by KDVS.
"""

# root tag
GO_OBOXML_ROOT_TAG = 'obo'
r"""
Standard root tag of GO release encoded as OBO-XML file.
"""

# ---- Gene Ontology ID resolvance

_goid_num_length = 7
_goid_num_patt = re.compile('\d{%s}' % _goid_num_length)
_goid_idprefix = 'GO:'
_goid_patt = re.compile('%s(?P<num>\d{%s})' % (_goid_idprefix, _goid_num_length))
_goid_num_img = '%%0%ds' % _goid_num_length

def isGOID(goid):
    r"""
Return True if goid is valid GO term ID, False othwerwise.
    """
    return _goid_patt.match(goid) != None

def GO_num2id(num):
    r"""
Resolve numerical part of GO term ID into full GO term ID.

Parameters
----------
num : integer/string
    supposed numerical part of GO term ID

Returns
-------
termID : string
    full GO term ID

Raises
------
Error
    if numerical part does not resolve to valid GO term ID
    """
    err = Error('Unrecognized numeric part of GO ID! (got %s)' % quote(str(num)))
    if isinstance(num, int):
        fmt = "%%0%dd" % _goid_num_length
        num = fmt % num
    elif isinstance(num, basestring):
        if _goid_num_patt.match(num) is None:
            raise err
    else:
        raise err
    return _goid_idprefix + num

def GO_id2num(goid, numint=True):
    r"""
Extract numerical part of full GO term ID.

Parameters
----------
goid : string
    full GO term ID

numint : boolean
    if True, return numerical part converted to integer; if False, return numerical
    part as string; True by default

Returns
-------
num : integer/string
    numerical part of full GO term ID
    """
    num = _goid_patt.match(goid).groupdict()['num']
    if numint:
        return int(num)
    else:
        return _goid_num_img % num

# ---- Gene Ontology parser and manager

class GOManager(PKCManager):
    r"""
Concrete prior knowledge manager that parses GO release encoded in
`OBO-XML <http://www.geneontology.org/GO.format.shtml#OBO-XML>`_ file
and keeps track of all individual GO terms (i.e. prior knowledge concepts).
The following content is exposed through public attributes after :meth:`load`
method finishes successfully:

    * :attr:`terms` -- dictionary of individual term data
    * :attr:`synonyms` -- :class:`~kdvs.fw.Map.SetBDMap` of synonymous terms
    * :attr:`termsPlainHierarchy` -- :class:`~kdvs.fw.Map.SetBDMap` of term hierarchy {parent : children} independent of relations
    * :attr:`termsRelationsHierarchy` -- {relation_name : :class:`~kdvs.fw.Map.setBDMap`} mapping of term hierarchies grouped by recognized relations
    * :attr:`obsolete_terms` -- iterable of obsolete terms IDs
    * :attr:`valid_terms` -- iterable of valid terms names IDs
    * :attr:`domain2validTerms` -- valid terms grouped by domains
    """
    def __init__(self):
        super(GOManager, self).__init__()

    def configure(self, domains=None, recognized_relations=None):
        r"""
Configure this manager.

Parameters
----------
domains : iterable of string/None
    iterable of GO domains that this manager will recognize; if None, all domains
    are recognized; None by default

recognized_relations : iterable of string/None
    iterable of inter--term relations that this manager will recognize; if None,
    default relations will be recognized (:data:`GO_DEF_RECOGNIZED_RELATIONS`); None by default
        """
        # resolve recognized relations
        if recognized_relations is None:
            self.recognizedRelations = list(GO_DEF_RECOGNIZED_RELATIONS)
        else:
            self.recognizedRelations = recognized_relations
        # constant iterable of PK recognized domains
        if domains is None:
            self.domains = tuple(GO_DS)
        else:
            self.domains = tuple(domains)
        # direct dictionary of term data
        self.terms = dict()
        # additional map of synonym GO terms
        self.synonyms = SetBDMap()
        # additional map of terms grouped according to recognized relations
        self.termsRelationsHierarchy = dict([(r, SetBDMap()) for r in self.recognizedRelations])
        # additional map of term hierarchy (parent->child independently of relations)
        self.termsPlainHierarchy = SetBDMap()
        # configuration is finished
        self.configured = True

    def load(self, fh, root_tag=None):
        r"""
Read GO release from OBO-XML file and build all data structures. XML parsing is
done with :mod:`xml.etree.ElementTree` (:mod:`xml.etree.cElementTree` if possible).

Parameters
----------
fh : file--like
    opened file handle of the OBO-XML file that contains encoded GO release;
    file handle must come from any recognized KDVS file provider

root_tag : string/None
    root XML tag of OBO-XML file that will be accepted; if None, default root
    tag (:data:`GO_OBOXML_ROOT_TAG`) will be used; None by default

Raises
------
Error
    if requested root tag has not been found
Error
    if file handle comes from unrecognized file provider
Error
    if parsing of OBO-XML is interrupted with an error (re--raised ElementTree exception)

See Also
--------
kdvs.core.provider.fileProvider
        """
        super(GOManager, self).load(fh)
        # technical parsing data
        self._format = None
        self._release_date = None
        # resolve root xml tag
        if root_tag is None:
            self.root_tag = GO_OBOXML_ROOT_TAG
        else:
            self.root_tag = root_tag
        # resolve file type
        if not fh.__class__ in RECOGNIZED_FILE_PROVIDERS:
            raise Error('File provider instance expected! (got %s)' % (fh.__class__))
        # do parsing
        try:
            self._parse(fh)
#        except ParseError, e:
        except Exception, e:
            raise Error('Error during parsing! (Reason: %s)' % e)
        # obtain obsolete terms
        self.obsolete_terms = [k for k, v in self.terms.iteritems() if v['obsolete'] is True]
        # obtain valid (non-obsolete terms)
        self.valid_terms = [k for k, v in self.terms.iteritems() if v['obsolete'] is False]
        # domains of valid terms
        self.domain2validTerms = dict()
        self._build_valid_terms_by_domain()

    def getPKC(self, conceptID):
        r"""
Get PKC instance for specified concept ID (i.e. GO term ID). This method resolves
synonymous GO terms.

Parameters
----------
conceptID : string
    full GO term ID for valid (i.e. not obsolete) term

Returns
-------
pkc : :class:`~kdvs.fw.PK.PriorKnowledgeConcept` / None
    PKC instance that corresponds to specified GO term, or None if the conceptID
    has not been found

Raises
------
Warn
    if synonymic term resolves into more than one direct terms
        """
        try:
            syn = self.synonyms.getBwdMap()[conceptID]
            if len(syn) == 1:
                # we should have only one resolving ID here
                conceptID = next(iter(syn))
            elif len(syn) > 1:
                # should not happen but to be safe
                raise Warn('More than one synonym resolution found! (%s)' % syn)
            else:
                pass
        except:
            pass
        # create PKC instance on the fly
        try:
            term = self.terms[conceptID]
            domainID = tuple(self.domain2concepts.getBwdMap()[conceptID])
            addInfo = dict()
            addInfo['obsolete'] = term['obsolete']
            pkc = PriorKnowledgeConcept(conceptID, term['name'], domainID, term['desc'], addInfo)
            return pkc
        except KeyError:
            return None

    def dump(self):
        r"""
Build dictionary dump of all the information produced by this manager, if possible in
textual format, and return it. The dump dictionary contains representations of
data structures keyed by the names of relevant public attributes. For bi--directional
mappings, forward and backward parts are separated into 'fwd' and 'bwd' subkeyed
parts.
        """
        dump = dict()
        dump['domains'] = self.domains
        dump['recognized_relations'] = self.recognizedRelations
        dump['terms'] = self.terms
        dump['synonyms'] = dict()
        dump['synonyms']['fwd'] = self.synonyms.getFwdMap()
        dump['synonyms']['bwd'] = self.synonyms.getBwdMap()
        tpl = dict()
        tpl['fwd'] = self.termsPlainHierarchy.getFwdMap()
        tpl['bwd'] = self.termsPlainHierarchy.getBwdMap()
        dump['termsPlainHierarchy'] = tpl
        trh = dict()
        for k, v in self.termsRelationsHierarchy.iteritems():
            trh[k] = dict()
            trh[k]['fwd'] = v.getFwdMap()
            trh[k]['bwd'] = v.getBwdMap()
        dump['termsRelationsHierarchy'] = trh
        return dump

    def getSynonyms(self, termID):
        r"""
Get recognized synonymous term IDs for specified GO term ID.

Parameters
----------
termID : string
    full GO term ID

Returns
-------
synonyms : iterable of string / None
    iterable of synonymous full GO term IDs, or None if not found
        """
        synonyms = self.synonyms.dumpFwdMap()
        try:
            return synonyms[termID]
        except KeyError:
            return None

    def getDescendants(self, parentTermID, depth=False):
        r"""
Follow term hierarchy and return descendant terms for specified GO term ID.
Optionally, return numerical depth information.

Parameters
----------
parentTermID : string
    full GO term ID

depth : boolean
    if True, return descendant terms with additional depth information; if False,
    return only descendant terms without depth information; False by default

Returns
-------
descendants : iterable of string
    if 'depth' is False; iterable of full GO term IDs of descendant terms; parent
    term is included at the beginning

descendants_with_depth : iterable of (string, int) tuples
    if 'depth' is True; iterable of the following tuples: (full GO term ID of descendant
    term, level of depth as integer relative to the parent); parent term is
    included at the beginning with depth 0; subsequent depths are positive integers
        """
        hierarchy = self.termsPlainHierarchy.dumpFwdMap()
        descendants = set()
        term_queue = collections.deque(((parentTermID, 0),))
        # do until term queue is empty
        while len(term_queue) > 0:
            # get leftmost element from the queue
            parent, lvl = term_queue.popleft()
            # get children from flat hierarchy
            try:
                for child in hierarchy[parent]:
                    # add child to the queue
                    term_queue.append((child, lvl + 1))
                    # add child to descendants
                    descendants.add((child, lvl + 1))
            except KeyError:
                pass
        if depth is True:
            return descendants
        else:
            return set(t[0] for t in descendants)

    def getAncestors(self, childTermID, depth=False):
        r"""
Follow term hierarchy and return ancestor terms for specified GO term ID.
Optionally, return numerical depth information.

Parameters
----------
childTermID : string
    full GO term ID

depth : boolean
    if True, return ancestor terms with additional depth information; if False,
    return only ancestor terms without depth information; False by default

Returns
-------
ancestors : iterable of string
    if 'depth' is False; iterable of full GO term IDs of ancestor terms; child
    term is included at the beginning

ancestors_with_depth : iterable of (string, int) tuples
    if 'depth' is True; iterable of the following tuples: (full GO term ID of
    ancestor term, level of depth as integer relative to the child); child term is
    included at the beginning with depth 0; subsequent depths are negative integers
        """
        hierarchy = self.termsPlainHierarchy.dumpBwdMap()
        ancestors = set()
        term_queue = collections.deque(((childTermID, 0),))
        # do until term queue is empty
        while len(term_queue) > 0:
            # get leftmost element from the queue
            child, lvl = term_queue.popleft()
            # get parents from flat hierarchy and
            try:
                for parent in hierarchy[child]:
                    # add parent to the queue
                    term_queue.append((parent, lvl - 1))
                    # add parent to ancestors
                    ancestors.add((parent, lvl - 1))
            except KeyError:
                pass
        if depth is True:
            return ancestors
        else:
            return set(t[0] for t in ancestors)

    def _parse(self, xml_fh):
        # used pattern for parsing large files, as documented in:
        # http://effbot.org/zone/element-iterparse.htm
        #
        # ---- get context iterator
        context = iter(iterparse(xml_fh, events=('start', 'end')))
        # ---- get root element
        event, root = context.next()
        # ---- check root tag
        root_tag = root.tag
        if root_tag != self.root_tag:
            raise Error('Could not recognize XML dialect of the release! (got root tag: %s, should be: %s)' % (quote(root_tag), quote(self.root_tag)))
        # ---- process other elements
        for event, item in context:
            # ---- process header
            if event == 'end' and item.tag.endswith('header'):
                # ---- get format ID
                self._format = self._findSingleChildText(item, 'format-version')
                # ---- get release date
                rel_date = self._findSingleChildText(item, 'date')
                self._release_date = datetime.strptime(rel_date, "%d:%m:%Y %H:%M")
                item.clear()
                root.clear()
            # ---- process individual terms
            if event == 'end' and item.tag.endswith('term'):
                # ---- get term acc
                term = self._findSingleChildText(item, 'id')
                self.terms[term] = dict()
                # ---- get term name
                name = self._findSingleChildText(item, 'name')
                self.terms[term]['name'] = name
                # ---- get term namespace
                namespace = self._findSingleChildText(item, 'namespace')
                self.domain2concepts[namespace] = term
                # ---- get term description
                desc = self._findSingleChildText(item, 'def/defstr')
                self.terms[term]['desc'] = desc
                # ---- get obsolence
                obs_el = item.find('is_obsolete')
                if obs_el is not None and obs_el.text == '1':
                    self.terms[term]['obsolete'] = True
                    is_obsolete = 1
                    obs_el.clear()
                else:
                    self.terms[term]['obsolete'] = False
                    is_obsolete = 0
                # ---- process further if term not obsolete
                if is_obsolete == 0:
                    # ---- get alt ids
                    alt_id_els = item.findall('alt_id')
                    for alt_id_el in alt_id_els:
                        alt_id = alt_id_el.text
                        self.synonyms[term] = alt_id
                        alt_id_el.clear()
                    # ---- get relationships
                    # is_a
                    is_a_els = item.findall('is_a')
                    for is_a_el in is_a_els:
                        parent = is_a_el.text
                        if 'is_a' in self.recognizedRelations:
                            self.termsRelationsHierarchy['is_a'][parent] = term
                            self.termsPlainHierarchy[parent] = term
                        is_a_el.clear()
                    # other relationships
                    rel_els = item.findall('relationship')
                    for rel_el in rel_els:
                        rel_type = self._findSingleChildText(rel_el, 'type')
                        rel_dst = self._findSingleChildText(rel_el, 'to')
                        if rel_type in self.recognizedRelations:
                            self.termsRelationsHierarchy[rel_type][term] = rel_dst
                            self.termsPlainHierarchy[term] = rel_dst
                        rel_el.clear()
                item.clear()
                root.clear()

    def _findSingleChildText(self, xmlitem, elid):
        ch_el = xmlitem.find(elid)
        content = ch_el.text
        ch_el.clear()
        return content

    def _build_valid_terms_by_domain(self):
        obsolete_terms = set(self.obsolete_terms)
        for domain, domain_terms in self.domain2concepts.getBwdMap().iteritems():
            valid_terms = domain_terms - obsolete_terms
            self.domain2validTerms[domain] = list(valid_terms)
