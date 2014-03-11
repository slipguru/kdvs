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
Provides specific functionality for handling HUGO Gene Nomenclature Committee
(HGNC) annotation data (http://www.genenames.org/). KDVS uses HGNC annotation
data to resolve gene naming problems that may arise from using old microarray
annotations. HGNC data refer to gene names as 'symbols'. The data contain all
history of approval of individual symbols; some symbols are withdrawn according
to the current knowledge of the genes. HGNC data are downloaded in the form of
DSV file; see README in 'data' directory for more details. Typically, HGNC data
are loaded into KDVS DB and wrapped in :class:`~kdvs.fw.DSV.DSV` instance;
'experimert' application does it automatically.
"""

from kdvs.core.util import quote
from kdvs.fw.DBTable import DBTemplate, DBTable

HGNC_APPROVED_SYMBOL_COL = 'Approved Symbol'
r"""
Column in HGNC data that contains approved symbol(s).
"""

HGNC_STATUS_COL = 'Status'
r"""
Column in HGNC data that contains status of specific gene symbol.
"""

HGNC_LOCUS_TYPE_COL = 'Locus Type'
r"""
Column in HGNC data that contains type of genetic locus that the symbol describes;
it could be valid protein products, tRNA gene, etc.
"""

HGNC_PREVIOUS_SYMBOLS_COL = 'Previous Symbols'
r"""
Column in HGNC data that contains previously approved symbols.
"""

HGNC_SYNONYMS_COL = 'Synonyms'
r"""
Column in HGNC data that contains valid synonyms for specific symbol; some
synonyms, although not official, are still widely used in different research
environments and must be accounted for when resolving any gene name.
"""

HGNC_EGENE_ID_COL = 'Entrez Gene ID'
r"""
Column in HGNC data that contains Entrez Gene ID for specific symbol; although
it is regularly updated, the user should pay attention for its accuracy.
"""

HGNC_ENSEMBL_ID_COL = 'Ensembl Gene ID'
r"""
Column in HGNC data that contains Ensembl Gene ID for specific symbol; although
it is regularly updated, the user should pay attention for its accuracy.
"""

HGNC_REFSEQ_ID_COL = 'RefSeq IDs'
r"""
Column in HGNC data that contains (possibly many) RefSeq IDs for specific symbol;
although it is regularly updated, the user should pay attention for its accuracy.
"""

HGNC_FIELDS_SEP = ','
r"""
Default DSV separator for the HGNC data file.
"""

HGNC_STATUS_APPROVED = 'Approved'
r"""
Value in 'Status' column referring to the fact that the specific symbol has
approved status (i.e. is considered official at this moment).
"""

HGNC_STATUS_WITHDRAWN = ['Entry Withdrawn', 'Symbol Withdrawn']
r"""
Values in 'Status' column referring to the fact that the specific symbol has been
withdrawn (i.e. is no longer considered valid); however, it may still be
encountered among very old data.
"""

HGNC_WITHDRAWN_GS_PART = '~withdrawn'
r"""
Suffix that is appended to each withdrawn symbol; KDVS removes it to fasten the
querying.
"""

HGNC_FIELD_EMPTY = ""
r"""
Refers to empty value in any column of HGNC data.
"""

HGNCSYNONYMS_TMPL = DBTemplate({
    'name' : 'hgnc_synonyms',
    'columns' : ('synonym', 'approved'),
    'id_column' : 'synonym',
    'indexes' : '*',
    })
r"""
Database template used by KDVS to create fast query table for resolving synonyms.
It defines the name 'hgnc_synonyms' and columns 'synonym', 'approved'. The ID
column is 'synonym'. All columns are indexed. With it, user obtains approved
symbol given the synonym.
"""

HGNCPREVIOUS_TMPL = DBTemplate({
    'name' : 'hgnc_previous',
    'columns' : ('previous', 'approved'),
    'id_column' : 'previous',
    'indexes' : '*',
    })
r"""
Database template used by KDVS to create fast query table for resolving previous
symbols. It defines the name 'hgnc_previous' and columns 'previous', 'approved'.
The ID column is 'previous'. All columns are indexed. With it, user obtains
approved symbol given the previous symbol.
"""

def correctHGNCApprovedSymbols(hgnc_dsv):
    r"""
Manually correct HGNC data after loading into DB and wrapping into :class:`~kdvs.fw.DSV.DSV`
instance. It removes suffix (defined in :data:`HGNC_WITHDRAWN_GS_PART`)
from withdrawn symbols in order to fasten further querying. This call must be
used in the application that uses HGNC data, and must be made after HGNC data
has been loaded and wrapped into DSV instance.

Parameters
----------
hgnc_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains HGNC data
    """
    # Approved Symbol column in HGNC DSV data contains symbols with textual
    # suffix when symbol is withdrawn; to unify querying, we need to get
    # rid of the suffix
    # NOTE: in this exceptional case we use low level access to database
    # table in order to perform specific modification
    db = hgnc_dsv.db
    c = db.cursor()
    #    c.execute('update or ignore %s '
    #               'set "Approved Symbol"=rtrim("Approved Symbol","~withdrawn") '
    #               'where "Approved Symbol" like "%~withdrawn"'%(hgnc_table_name))
    st = 'update or ignore %s ' \
               'set %s=rtrim(%s,%s) ' \
               'where %s like %s' % (
                    hgnc_dsv.name, quote(HGNC_APPROVED_SYMBOL_COL),
                    quote(HGNC_APPROVED_SYMBOL_COL),
                    quote(HGNC_WITHDRAWN_GS_PART),
                    quote(HGNC_APPROVED_SYMBOL_COL),
                    quote('%' + HGNC_WITHDRAWN_GS_PART))
    c.execute(st)
    db.commit()
    c.close()

def generateHGNCPreviousSymbols(hgnc_dsv, map_db_key):
    r"""
Create helper table that eases resolving of previous gene symbols with HGNC data.
The helper table may be created in different subordinated database than original
HGNC data. The table is specified via template.

Parameters
----------
hgnc_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains HGNC data

map_db_key : string
    ID of the database that will hold helper table

Returns
-------
previousDT : :class:`~kdvs.fw.DBTable.DBTable`
    wrapper for newly created helper table

See Also
--------
kdvs.fw.DBTable.DBTemplate
    """
    previous_dt = DBTable.fromTemplate(hgnc_dsv.dbm, map_db_key, HGNCPREVIOUS_TMPL)
    previous_dt.create(indexed_columns=HGNCPREVIOUS_TMPL['indexes'])
    pr_columns = (HGNC_APPROVED_SYMBOL_COL, HGNC_PREVIOUS_SYMBOLS_COL)
    pr_filter = "%s not like %s" % (quote(HGNC_PREVIOUS_SYMBOLS_COL), quote(HGNC_FIELD_EMPTY))
    hgnc_cs = hgnc_dsv.get(columns=pr_columns, filter_clause=pr_filter)
    def _gen():
        for pr_row in hgnc_cs:
            approved, rawprevs = [str(r) for r in pr_row]
            # parse previous symbols
            if len(rawprevs) > 0:
                # parse previous
                prevs = [s.strip() for s in rawprevs.split(HGNC_FIELDS_SEP)]
            else:
                # no previous, make approved its own previous
                prevs = [approved]
            for prev in prevs:
                yield (prev, approved)
    previous_dt.load(_gen())
    hgnc_cs.close()
    return previous_dt

def generateHGNCSynonyms(hgnc_dsv, map_db_key):
    r"""
Create helper table that eases resolving of synonymic gene symbols with HGNC data.
The helper table may be created in different subordinated database than original
HGNC data. The table is specified via template.

Parameters
----------
hgnc_dsv : :class:`~kdvs.fw.DSV.DSV`
    valid instance of DSV that contains HGNC data

map_db_key : string
    ID of the database that will hold helper table

Returns
-------
synonymsDT : :class:`~kdvs.fw.DBTable.DBTable`
    DBTable wrapper for newly created helper table

See Also
--------
kdvs.fw.DBTable.DBTemplate
    """
    synonyms_dt = DBTable.fromTemplate(hgnc_dsv.dbm, map_db_key, HGNCSYNONYMS_TMPL)
    synonyms_dt.create(indexed_columns=HGNCSYNONYMS_TMPL['indexes'])
    syn_columns = (HGNC_APPROVED_SYMBOL_COL, HGNC_SYNONYMS_COL)
    syn_filter = "%s not like %s" % (quote(HGNC_SYNONYMS_COL), quote(HGNC_FIELD_EMPTY))
    hgnc_cs = hgnc_dsv.get(columns=syn_columns, filter_clause=syn_filter)
    def _gen():
        for syn_row in hgnc_cs:
            approved, rawsyns = [str(r) for r in syn_row]
            # parse synonyms
            if len(rawsyns) > 0:
                # parse synoyms
                syns = [s.strip() for s in rawsyns.split(HGNC_FIELDS_SEP)]
            else:
                # no synonyms, make approved its own synonym
                syns = [approved]
            for syn in syns:
                yield (syn, approved)
    synonyms_dt.load(_gen())
    hgnc_cs.close()
    return synonyms_dt
