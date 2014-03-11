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
Provides concrete implementation of :class:`~kdvs.fw.Map.PKCIDMap` builder that
uses `Gene Ontology <http://www.geneontology.org/>`_ as prior knowledge source
for data subsets generation.
It uses Affymetrix annotations shipped with specified microarray; those
annotations shall contain mapping between the individual probe(set)s and Gene
Ontology terms (i.e. prior knowledge concepts). The currently implemented builder
is tailored for processing of Affymetrix annotations.
See `Affymetrix annotations <http://www.affymetrix.com/support/technical/annotationfilesmain.affx>`_
for more details. The mapping is based solely on the annotations, i.e. it utilizes
GO terms present at the time when annotations were constructed. KDVS provides
concrete manager (:class:`~kdvs.fw.impl.pk.go.GeneOntology.GOManager`) that
offers more control over Gene Ontology content.
"""

from kdvs.core.error import Error
from kdvs.core.util import quote
from kdvs.fw.DBTable import DBTable, DBTemplate
from kdvs.fw.DSV import DSV
from kdvs.fw.Map import SetBDMap, PKCIDMap
from kdvs.fw.impl.pk.go.GeneOntology import GO_INV_EVIDENCE_CODES, \
    GO_UNKNOWN_EV_CODE, GO_num2id, GO_DS, GO_BP_DS, GO_MF_DS, GO_CC_DS

# this custom table uses specific features of GO such as evidence codes and term domain
GOTERM2EM_TMPL = DBTemplate({
    'name' : 'goterm2em',
    'columns' : ('term_id', 'em_id', 'term_evc', 'term_name', 'term_domain'),
    'id_column' : 'term_id',
    'indexes' : ('term_id',),
    })
r"""
Custom database template that hold querying data used in fast construction of
GO--based :class:`~kdvs.fw.Map.PKCIDMap`. It defines the name 'goterm2em' and
columns 'term_id', 'em_id', 'term_evc', 'term_name', 'term_domain'. The ID column
'term_id' is indexed. The application 'experiment' utilizes this table. See
:data:`~kdvs.fw.Annotation.PKC2EM_TMPL` for detailed discussion.
"""

class PKCIDMapGOGPL(PKCIDMap):
    r"""
PKCIDMap builder that uses Affymetrix annotations available at `Gene Expression
Omnibus <http://www.ncbi.nlm.nih.gov/geo/>`_. Annotations must already be loaded
"as--is" into KDVS DB and wrapped into :class:`~kdvs.fw.DSV.DSV` instance.
The mapping table follows custom template :data:`GOTERM2EM_TMPL`. This builder
constructs two mappings:

    * (1) domain--unaware one that does not group individual terms according to domains,
    * (2) domain--aware one that groups individual terms according to domains

The domain--aware mapping is stored in public attribute :attr:`domains_map`.
    """
    _SEQ_TYPE_COL = 'Sequence Type'
    _GO_BP_COL = 'Gene Ontology Biological Process'
    _GO_MF_COL = 'Gene Ontology Molecular Function'
    _GO_CC_COL = 'Gene Ontology Cellular Component'
    _CTRL_SEQUENCE_TAG = 'Control sequence'
    _TERMS_MISSING = ''
    _TERM_SEPARATOR = '///'
    _TERM_INTER_SEPARATOR = '//'

    def __init__(self):
        super(PKCIDMapGOGPL, self).__init__()
        self.domains_map = dict([(d, SetBDMap()) for d in GO_DS])
        self.dbt = None
        self.built = False

    def getMapForDomain(self, domain):
        r"""
Return part of PKCIDMap referring to specific GO domain.

Parameters
----------
domain : string
    GO domain name, one of: 'BP', 'MF', 'CC'

Returns
-------
domain_part_map : :class:`~kdvs.fw.Map.SetBDMap`
    part of :class:`~kdvs.fw.Map.PKCIDMap` the refers to specific GO domain

Raises
------
Error
    if domain name is incorrectly specified
        """
        if domain not in GO_DS:
            raise Error('Gene Ontology domain symbol (%s) expected! (got %s)' % (','.join(GO_DS), domain))
        else:
            return self.domains_map[domain]

    def build(self, anno_dsv, map_db_key):
        r"""
Construct the mapping using resources already present in KDVS DB (via
:class:`~kdvs.core.db.DBManager`) and wrapped in :class:`~kdvs.fw.DSV.DSV`
instances. The mapping is built as database table and wrapped into
:class:`~kdvs.fw.DBTable.DBTable` instance; it is stored in public attribute
:attr:`dbt` of this instance. After the build is finished, the public attribute
:attr:`built` is set to True. This builder requires Affymetrix annotations data
already loaded in KDVS DB and wrapped in DSV instance.

Parameters
----------
anno_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains Affymetrix annotations data

map_db_key : string
    ID of the database that will hold mapping table

Raises
------
Error
    if DSV containing Affymetrix annotation data is incorrectly specified, is
    not created, or is empty
        """
        # NOTE: this map utilizes GO as prior knowledge sources and uses specific
        # features of this source, such as evidence codes

        # ---- check conditions
        if not isinstance(anno_dsv, DSV):
            raise Error('%s instance expected! (got %s)' % (DSV.__class__, anno_dsv.__class__))
        if not anno_dsv.isCreated():
            raise Error('Helper data table %s must be created first!' % quote(anno_dsv.name))
        if anno_dsv.isEmpty():
            raise Error('Helper data table %s must not be empty!' % quote(anno_dsv.name))
        # ---- create goterm2em
        goterm2em_dt = DBTable.fromTemplate(anno_dsv.dbm, map_db_key, GOTERM2EM_TMPL)
        goterm2em_dt.create(indexed_columns=GOTERM2EM_TMPL['indexes'])
        # ---- specify data subset from ANNO
        query_domain_columns = (anno_dsv.id_column, self._SEQ_TYPE_COL, self._GO_BP_COL, self._GO_MF_COL,
                                self._GO_CC_COL)
        ctrl_seq_tag = self._CTRL_SEQUENCE_TAG
        terms_missing = self._TERMS_MISSING
        term_separator = self._TERM_SEPARATOR
        term_part_separator = self._TERM_INTER_SEPARATOR
        # ---- query data subset and build term2probeset
        res = anno_dsv.getAll(columns=query_domain_columns, as_dict=False)
        def _build_map():
            for r in res:
                msid, seq_type, bp_s, mf_s, cc_s = [str(pr) for pr in r]
                if seq_type != ctrl_seq_tag:
                    for ns, terms_s in ((GO_BP_DS, bp_s), (GO_MF_DS, mf_s), (GO_CC_DS, cc_s)):
                        if terms_s != terms_missing:
                            for term in terms_s.split(term_separator):
                                tid, term_desc, ev_long = [x.strip() for x in term.split(term_part_separator)]
                                try:
                                    term_ev_code = GO_INV_EVIDENCE_CODES[ev_long]
                                except KeyError:
                                    term_ev_code = GO_UNKNOWN_EV_CODE
                                term_id = GO_num2id(tid)
                                yield term_id, msid, term_ev_code, term_desc, ns
        goterm2em_dt.load(_build_map())
        # ---- query term2probeset
        query_t2em_columns = (goterm2em_dt.id_column, 'em_id', 'term_domain')
        res = goterm2em_dt.getAll(columns=query_t2em_columns, as_dict=False)
        # build final map
        for r in res:
            tid, msid, dom = [str(pr) for pr in r]
            # update domain-unaware map
            self.pkc2emid[tid] = msid
            # update domain-aware map
            self.domains_map[dom][tid] = msid
        self.built = True
        self.dbt = goterm2em_dt
