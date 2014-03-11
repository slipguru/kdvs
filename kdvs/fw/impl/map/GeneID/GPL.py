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
Provides concrete implementation of :class:`~kdvs.fw.Map.GeneIDMap` builder
that uses annotations shipped with specified microarray; those annotations shall
contain mapping between the individual probe(set)s and gene symbols. The currently
implemented builder is tailored for processing of Affymetrix annotations.
See `Affymetrix annotations <http://www.affymetrix.com/support/technical/annotationfilesmain.affx>`_
for more details. The mapping is based solely on the annotations, i.e. it does
not check for obsolete or synonymous gene symbols in HGNC data.
See :mod:`~kdvs.fw.impl.map.GeneID.HGNC_GPL` for the builder that provides this functionality.
"""

from kdvs.core.error import Error
from kdvs.core.util import quote
from kdvs.fw.Annotation import EM2ANNOTATION_TMPL, MULTIFIELD_SEP
from kdvs.fw.DBTable import DBTable
from kdvs.fw.DSV import DSV
from kdvs.fw.Map import GeneIDMap

class GeneIDMapGPL(GeneIDMap):
    r"""
GeneIDMap builder that uses Affymetrix annotations available at `Gene Expression
Omnibus <http://www.ncbi.nlm.nih.gov/geo/>`_. Annotations must already be loaded
"as--is" into KDVS DB and wrapped into DSV instance. The mapping table follows
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

    def __init__(self):
        super(GeneIDMapGPL, self).__init__()
        self.built = False
        self.dbt = None

    def build(self, anno_dsv, hgnc_dsv, map_db_key):
        r"""
Construct the mapping using resources already present in KDVS DB (via
:class:`~kdvs.core.db.DBManager`) and wrapped in :class:`~kdvs.fw.DSV.DSV`
instances. The mapping is built as database table and wrapped
into :class:`~kdvs.fw.DBTable.DBTable` instance; it is stored in public attribute
:attr:`dbt` of this instance. After the build is finished, the public attribute
:attr:`built` is set to True. This builder requires Affymetrix annotations data
already loaded in KDVS DB and wrapped in DSV instance.

Parameters
----------
anno_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains Affymetrix annotations data

hgnc_dsv : :class:`~kdvs.fw.DSV.DSV`
    currently unused, added for compatibility

map_db_key : string
    ID of the database that will hold mapping table

Raises
------
Error
    if DSV containing Affymetrix annotation data is incorrectly specified, is
    not created, or is empty
        """
        #
        # NOTE: in this map, we follow strictly the information from annotations,
        # without resolving symbols in HGNC data
        #
        # ---- check conditions for ANNO
        if not isinstance(anno_dsv, DSV):
            raise Error('%s instance expected! (got %s)' % (DSV.__class__, anno_dsv.__class__))
        if not anno_dsv.isCreated():
            raise Error('Helper data table %s must be created first!' % quote(anno_dsv.name))
        if anno_dsv.isEmpty():
            raise Error('Helper data table %s must not be empty!' % quote(anno_dsv.name))
        # ---- create em2annotation
        em2annotation_dt = DBTable.fromTemplate(anno_dsv.dbm, map_db_key, EM2ANNOTATION_TMPL)
        em2annotation_dt.create(indexed_columns=EM2ANNOTATION_TMPL['indexes'])
        # query ANNO for basic annotations: probeset ID, representative public ID,
        # gene symbol, Entrez Gene ID, GB accession
        # NOTE: we need cursor due to sheer quantity of data
        query_anno_columns = (anno_dsv.id_column, self._ANNO_REPR_PUBLIC_ID_COL,
                              self._ANNO_SEQ_SOURCE_COL, self._ANNO_GENE_SYMBOL_COL,
                              self._ANNO_EGENE_ID_COL, self._ANNO_GB_ACC_COL)
        anno_cs = anno_dsv.get(columns=query_anno_columns)
        # build em2annotation
        def _gen():
            for arow in anno_cs:
                probeset_id, repr_pub_id, seqsrc, gss, egeneids, gbacc = [str(ar) for ar in arow]
                # reconstruct correct public ID
                pubid = '%s:%s' % (self._ANNO_SEQSRC_ABBRS[seqsrc], repr_pub_id)
                # NOTE: multifields "Gene Symbol" and "ENTREZ_GENE_ID" in
                # Affymetrix annotations are known not to be ordered accordingly;
                # therefore we simply unify multifield separator and report the
                # order as-is; it is up to the user to reconstruct correct
                # pairing when querying manually in Entrez Gene afterwards
                gs = MULTIFIELD_SEP.join([s.strip() for s in gss.split(self._ANNO_MULTIFIELD_SEP)])
                egeneid = MULTIFIELD_SEP.join([s.strip() for s in egeneids.split(self._ANNO_MULTIFIELD_SEP)])
                yield (probeset_id, gs, pubid, gbacc, egeneid, '', '')
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
