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
Provides abstract functionality for handling annotations.
"""

from kdvs.core.error import Warn
from kdvs.fw.DBTable import DBTemplate
import collections

# NOTE: please do not modify this table!
# NOTE: this general table utilize multifield 'pkc_data' of the following format:
# 'feature1=value1,...,featureN=valueN', where 'feature' is the property specific
# for PK source, and 'value' is the value of this property for specified PKC.
# Typical features of PK may be: PKC name, PKC description, higher level grouping
# of PKCs, e.g. into domains, etc.
# NOTE: it is advisable to create and use more specific tables tailored for
# specificity of individual PK sources, due to limited querying power of this
# table and potentially high cost of parsing the multifield
PKC2EM_TMPL = DBTemplate({
    'name' : 'pkc2em',
    'columns' : ('pkc_id', 'em_id', 'pkc_data'),
    'id_column' : 'pkc_id',
    'indexes' : ('pkc_id',),
    })
r"""
Database table template for storing mapping between prior knowledge concepts and
measurements (PKC->M). It defines the name 'pkc2em' and columns 'pkc_id', 'em_id',
'pkc_data'. The ID column 'pkc_id' is also indexed. This general table utilizes
multifield 'pkc_data' of the following format:

    * 'feature1=value1,...,featureN=valueN',

where 'feature' is the property specific for PK source, and 'value' is the value
of this property for specified PKC. Typical features of PK may be: PKC name,
PKC description, higher level grouping of PKCs, e.g. into domains, etc.
NOTE: it is advisable to create and use more specific tables tailored for
specificity of individual PK sources, due to limited querying power of this
table and potentially high computational cost of parsing the multifield.
"""

# NOTE: please do not modify this table!
# NOTE: this general table contains selected set of annotations for given EM;
# this selection is arbitrary and may not reflect all needs of the user; in that
# case it is advised to use different, more specific table
EM2ANNOTATION_TMPL = DBTemplate({
    'name' : 'em2annotation',
    'columns' : ('em_id', 'gene_symbol', 'repr_id', 'gb_acc', 'entrez_gene_id', 'ensembl_id', 'refseq_id'),
    'id_column' : 'em_id',
    'indexes' : ('em_id',),
    })
r"""
Database table template that provides annotations for measurements. This template
is tailored specifically for Gene Ontology. It defines the name 'em2annotation' and
columns 'em_id', 'gene_symbol', 'repr_id', 'gb_acc', 'entrez_gene_id', 'ensembl_id', 'refseq_id'.
The ID column 'em_id' is also indexed. This table contains selected set of
annotations for given measurement (i.e. probeset for microarray, gene for RNASeq etc).
The selection is arbitrary and may not reflect all needs of the user; in that case
it is advisable to use different, more specific table.
"""

MULTIFIELD_SEP = ';'
r"""
Default separator for the multifield 'pkc_data' used in generic annotation
database template.
"""

def get_em2annotation(em2annotation_dt):
    r"""
Obtain the dictionary with mapping between measurements and annotations,
stored in specified DBTable instance.

Parameters
----------
em2annotation_dt : :class:`~kdvs.fw.DBTable.DBTable`
    wrapped content of 'em2annotation' database table

Returns
-------
em2a : collections.defaultdict
    mapping between measurements and annotations
    """
    em2a_s = collections.defaultdict(list)
    query_em2a_columns = '*'
    em2a_cs = em2annotation_dt.get(columns=query_em2a_columns)
    for em2a_row in em2a_cs:
        em2a_strs = [str(r) for r in em2a_row]
        em_id = em2a_strs[0]
        anno_data = em2a_strs[1:]
        em2a_s[em_id].append(anno_data)
    em2a_cs.close()
    em2a = dict()
    for emid, d in em2a_s.iteritems():
        # data from table shall be unique across emids, so we take first record
        em2a[emid] = d[0]
        # should not happen but to be safe
        if len(d) != 1:
            raise Warn('%s annotated with more than 1 record!' % emid)
    return em2a
