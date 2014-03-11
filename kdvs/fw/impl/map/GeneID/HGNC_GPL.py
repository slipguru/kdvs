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
Provides concrete implementation of GeneIDMap builder that uses annotations
shipped with specified microarray; those annotations shall contain mapping
between the individual probe(set)s and gene symbols. The currently implemented
builder is tailored for processing of Affymetrix annotations.
See `Affymetrix annotations <http://www.affymetrix.com/support/technical/annotationfilesmain.affx>`_
for more details. The mapping is based both on the annotations and HGNC data,
i.e. it tries to resolve obsolete or synonymous gene symbols into more usable ones.
"""

from kdvs.core.error import Error
from kdvs.core.util import quote
from kdvs.fw.Annotation import EM2ANNOTATION_TMPL, MULTIFIELD_SEP
from kdvs.fw.DBTable import DBTable
from kdvs.fw.DSV import DSV
from kdvs.fw.Map import GeneIDMap

class GeneIDMapHGNCGPL(GeneIDMap):
    r"""
GeneIDMap builder that uses Affymetrix annotations available at `Gene Expression
Omnibus <http://www.ncbi.nlm.nih.gov/geo/>`_. Annotations must already be loaded
"as--is" into KDVS DB and wrapped into DSV instance. HGNC data must be loaded
and wrapped in DSV as well. The mapping table follows
:data:`~kdvs.fw.Annotation.EM2ANNOTATION_TMPL` template.
    """
    _ANNO_REPR_PUBLIC_ID_COL = 'Representative Public ID'
    _ANNO_SEQ_SOURCE_COL = 'Sequence Source'
    _ANNO_GENE_SYMBOL_COL = 'Gene Symbol'
    _ANNO_EGENE_ID_COL = 'ENTREZ_GENE_ID'
    _ANNO_GB_ACC_COL = 'GB_ACC'
    _ANNO_SEQSRC_ABBRS = {
        'GenBank' : 'GB',
        'Affymetrix Proprietary Database' : 'AFFX',
    }
    _ANNO_MULTIFIELD_SEP = '///'
    _HGNC_APPROVED_SYMBOL_COL = 'Approved Symbol'
    _HGNC_LOCUS_TYPE_COL = 'Locus Type'
    _HGNC_EGENE_ID_COL = 'Entrez Gene ID'
    _HGNC_ENSEMBL_ID_COL = 'Ensembl Gene ID'
    _HGNC_REFSEQ_ID_COL = 'RefSeq IDs'
    _HGNC_VALID_GENE_TYPES = ['gene with protein product']
    _HGNC_MULTIFIELD_SEP = ','

    def __init__(self):
        r"""
        """
        super(GeneIDMapHGNCGPL, self).__init__()
        self.built = False
        self.dbt = None

    def build(self, anno_dsv, hgnc_dsv, map_db_key):
        r"""
Construct the mapping using resources already present in KDVS DB (via
:class:`~kdvs.core.db.DBManager`) and wrapped in :class:`~kdvs.fw.DSV.DSV`
instances. The mapping is built as database table and wrapped into
:class:`~kdvs.fw.DBTable.DBTable` instance; it is stored in public attribute :attr:`dbt`
of this instance. After the build is finished, the public attribute :attr:`built`
is set to True. This builder requires both Affymetrix annotations data and HGNC
data already loaded in KDVS DB and wrapped in DSV instances. Refer to the
comments for resolvancy protocol used.

Parameters
----------
anno_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains Affymetrix annotations data

hgnc_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains HGNC data

map_db_key : string
    ID of the database that will hold mapping table

Raises
------
Error
    if DSV containing Affymetrix annotation data is incorrectly specified, is
    not created, or is empty
Error
    if DSV containing HGNC data is incorrectly specified,
    is not created, or is empty
        """
        #
        # NOTE: this map follows resolvancy protocol implemented originally in
        # KDVS v 1.0.
        #
        # NOTE: in this map, we apply the following resolvancy protocol:
        # 1. get gene symbol(s) from annotations
        # 2. resolve them in HGNC data as follows:
        #    - if the symbol is approved and refers to gene, retain it
        #    - if the symbol is not approved, discard it
        # 3. for not discarded symbol(s) obtained in (2), get the following
        #    element(s) from HGNC data: Entrez Gene ID, Ensembl Gene ID, RefSeq IDs
        # 4. for not discarded symbol(s) obtained in (2), get the following
        #    element(s) from annotations: GB accession
        #
        # NOTE: in this map, we rely on annotations as the source of external
        # IDs; we still retain sequence public ID from annotations; gene symbols
        # are only verified if approved (i.e. the approval history is not followed)
        #
        # ---- check conditions for ANNO
        if not isinstance(anno_dsv, DSV):
            raise Error('%s instance expected! (got %s)' % (DSV.__class__, anno_dsv.__class__))
        if not anno_dsv.isCreated():
            raise Error('Helper data table %s must be created first!' % quote(anno_dsv.name))
        if anno_dsv.isEmpty():
            raise Error('Helper data table %s must not be empty!' % quote(anno_dsv.name))
        # ---- check conditions for HGNC
        if not isinstance(hgnc_dsv, DSV):
            raise Error('%s instance expected! (got %s)' % (DSV.__class__, hgnc_dsv.__class__))
        if not hgnc_dsv.isCreated():
            raise Error('Helper data table %s must be created first!' % quote(hgnc_dsv.name))
        if hgnc_dsv.isEmpty():
            raise Error('Helper data table %s must not be empty!' % quote(hgnc_dsv.name))
        # ---- create em2annotation
        em2annotation_dt = DBTable.fromTemplate(anno_dsv.dbm, map_db_key, EM2ANNOTATION_TMPL)
        em2annotation_dt.create(indexed_columns=EM2ANNOTATION_TMPL['indexes'])
        # pre-query data from HGNC: approved symbol, Entrez Gene ID,
        # Ensembl Gene ID, RefSeq IDs; filter non-gene entries
        # NOTE: we need cursor due to sheer quantity of data
        hgnc_data = dict()
        only_genes_filter = "%s in (%s)" % (quote(self._HGNC_LOCUS_TYPE_COL),
                                            ','.join([quote(t) for t in self._HGNC_VALID_GENE_TYPES]))
        query_hgnc_columns = (self._HGNC_APPROVED_SYMBOL_COL, self._HGNC_EGENE_ID_COL,
                              self._HGNC_ENSEMBL_ID_COL, self._HGNC_REFSEQ_ID_COL)
        hgnc_cs = hgnc_dsv.get(columns=query_hgnc_columns, filter_clause=only_genes_filter)
        for hgnc_row in hgnc_cs:
            approved, egeneid, ensembl, refseq = [str(r) for r in hgnc_row]
            hgnc_data[approved] = (egeneid, ensembl, refseq)
        hgnc_cs.close()
        # query ANNO for basic annotations: probeset ID, representative public ID,
        # gene symbol, GB accession
        # NOTE: we need cursor due to sheer quantity of data
        query_anno_columns = (anno_dsv.id_column, self._ANNO_REPR_PUBLIC_ID_COL,
                              self._ANNO_SEQ_SOURCE_COL, self._ANNO_GENE_SYMBOL_COL,
                              self._ANNO_GB_ACC_COL)
        anno_cs = anno_dsv.get(columns=query_anno_columns)
        def _gen():
            for arow in anno_cs:
                probeset_id, repr_pub_id, seqsrc, gss_str, gbacc = [str(ar) for ar in arow]
                # reconstruct correct public ID
                pubid = '%s:%s' % (self._ANNO_SEQSRC_ABBRS[seqsrc], repr_pub_id)
                # separate gene symbols
                gss = [s.strip() for s in gss_str.split(self._ANNO_MULTIFIELD_SEP)]
                gs_rec = list()
                egeneid_rec = list()
                ensembl_rec = list()
                refseq_rec = list()
                for gs in gss:
                    if gs in hgnc_data:
                        # gene symbol is approved
                        gs_rec.append(gs)
                        egeneid, ensembl, refseq = hgnc_data[gs]
                        egeneid_rec.append(egeneid)
                        ensembl_rec.append(ensembl)
                        refseq_rec.append(refseq)
                gs_s = MULTIFIELD_SEP.join(gs_rec)
                egeneid_s = MULTIFIELD_SEP.join(egeneid_rec) if len(egeneid_rec) > 0 else ''
                ensembl_s = MULTIFIELD_SEP.join(ensembl_rec) if len(ensembl_rec) > 0 else ''
                refseq_s = MULTIFIELD_SEP.join(refseq_rec) if len(refseq_rec) > 0 else ''
                yield (probeset_id, gs_s, pubid, gbacc, egeneid_s, ensembl_s, refseq_s)
        em2annotation_dt.load(_gen())
        # ---- query em2annotation and build map
        # NOTE: we need cursor due to sheer quantity of data
        query_em2a_columns = (em2annotation_dt.id_column, 'gene_symbol')
        em2a_cs = em2annotation_dt.get(columns=query_em2a_columns)
        for em2a_row in em2a_cs:
            pr_id, gs = [str(r) for r in em2a_row]
            self.gene2emid[gs] = pr_id
        em2a_cs.close()
        self.built = True
        self.dbt = em2annotation_dt
