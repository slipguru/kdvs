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
Provides concrete implementation of reporters that are associated with statistical
techniques which utilize `l1l2py <http://slipguru.disi.unige.it/Software/L1L2Py/>`_
library and all associated functionalities such as selectors. Refer to
individual reporters for more details. IMPORTANT NOTE: the functionality of those
reporters was devised for 'experiment' application, therefore LOTS OF details
are hard--coded.
"""

from kdvs.core.error import Error
from kdvs.core.util import pairwise
from kdvs.fw.Report import Reporter, DEFAULT_REPORTER_PARAMETERS
from kdvs.fw.Stat import RESULTS_RUNTIME_KEY, SELECTIONERROR, SELECTED, \
    NOTSELECTED, RESULTS_SUBSET_ID_KEY
import collections
import itertools
import operator

class L1L2_VarFreq_Reporter(Reporter):
    r"""
This local reporter, for each :class:`~kdvs.fw.Stat.Results` instance, produces
single report that contains a list of 'properly selected variables', sorted
according to descending frequencies (see literature about L1L2 implementation
for technical details). It recognizes the following Results elements:

    * ':data:`~kdvs.fw.Stat.RESULTS_SUBSET_ID_KEY`'
    * 'Selection'->'inner'

Since it focuses on variable selection (called 'inner selection' in KDVS
terminology), will produce valid report only if inner selection was done with
one of the following inner selectors:

    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_AllVars`
    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq`
    
This reporter accepts no specific parameters. It re--implements :meth:`initialize`
method to get `em2annotation` mapping that must be provided in `additionalData`
dictionary. In 'experiment' application, this reporter processes Results instances
only for those subsets that were 'selected' in the terms of 'outer selection',
based on classfication error.

See Also
--------
kdvs.fw.Annotation.get_em2annotation
    """
    specific_parameters = ()
    global_parameters = DEFAULT_REPORTER_PARAMETERS

    def __init__(self, **kwargs):
        r"""
        """
        super(L1L2_VarFreq_Reporter, self).__init__(list(itertools.chain(self.specific_parameters, self.global_parameters)), **kwargs)

    def initialize(self, storageManager, subsets_results_location, additionalData):
        r"""
Parameters
----------
storageManager : :class:`~kdvs.fw.StorageManager.StorageManager`
    instance of storage manager that will govern the production of physical files

subsets_results_location : string
    identifier of standard location used to store KDVS results

additionalData : object
    any additional data used by the reporter; the instance must contain `em2annotation`
    mapping

Raises
------
Error
    if `em2annotation` mapping was not found in `additionalData`
        """
        # we need to overload this method since we need to check if some
        # additional data are provided
        super(L1L2_VarFreq_Reporter, self).initialize(storageManager, subsets_results_location, additionalData)
        if 'em2annotation' not in self.getAdditionalData():
            raise Error('em2annotation mapping was not provided for this reporter!')
        else:
            self.em2annotation = self.getAdditionalData()['em2annotation']

    def produce(self, resultsIter):
        r"""
Produce single report with frequencies of variables, selection information, and
all bioinformatic annotations, for each Results instance. Refer to the comments
how 'selection' of individual variables is reported.

Parameters
----------
resultsIter : iterable of :class:`~kdvs.fw.Stat.Results`
    iterable of results obtained across single category
        """
        for result in resultsIter:
            ssname = result[RESULTS_SUBSET_ID_KEY]
            inner = result['Selection']['inner']
            for dof, idata in inner.iteritems():
                # obtain report location
                fname = '%s_%s_%s' % (ssname, dof, '_vars_freqs.txt')
                rloc = '%s%s%s' % (ssname, self.locsep, fname)
                # header
                header = ['Variable Name', 'Frequency (%)', 'Selected?', 'Gene Symbols(s)',
                          'Representative Public ID', 'GenBank Accession #',
                          'Entrez Gene ID(s)', 'Ensembl Gene ID(s)',
                          'RefSeq ID(s)']
                # go through frequencies
                freqs = list()
                selected = set()
                for svar, svdata in idata['sel_vars'].iteritems():
                    try:
                        freq = svdata['freq']
                        freq = int(float(freq) * 100.0)
                    except:
                        freq = 100
                    rec = list()
                    rec.append(svar)
                    rec.append(freq)
                    # NOTE: Criterion for variable selection marked here:
                    # 1) the enclosing subset must be selected, in outer selection sense
                    # 2) the variable must be reported as selected by technique;
                    #    for L1L2, as byproduct of frequency calculation,
                    #    variables with non-zero frequency are selected
                    # 3) frequency must be above frequency threshold specified
                    if svdata['pass']:
                        rec.append('Y')
                        selected.add(svar)
                    else:
                        rec.append('N')
                    for sa in self.em2annotation[svar]:
                        rec.append(sa)
                    freqs.append(rec)
                for nsvar, nsvdata in idata['nsel_vars'].iteritems():
                    try:
                        nfreq = nsvdata['freq']
                        nfreq = int(float(nfreq) * 100.0)
                    except:
                        nfreq = 100
                    rec = list()
                    rec.append(nsvar)
                    rec.append(nfreq)
                    rec.append('N')
#                    if nsvdata['pass']:
#                        rec.append('Y')
#                    else:
#                        rec.append('N')
                    for sa in self.em2annotation[nsvar]:
                        rec.append(sa)
                    freqs.append(rec)
                # sort according to frequencies
                freqs.sort(key=operator.itemgetter(1), reverse=True)
                # produce report content
                rcontent = list()
                rcontent.append('# Vars: %d, Selected: %d\n' % (len(freqs), len(selected)))
                rcontent.append('%s\n' % ('\t'.join(header)))
                for rec in freqs:
                    rcontent.append('%s\n' % ('\t'.join([str(r) for r in rec])))
                # store report
                self.openReport(rloc, rcontent)


class L1L2_VarCount_Reporter(Reporter):
    r"""
This local reporter produces counts of selected and non selected variables across
specific individual results. For each variable, it lists its count across all
observed :class:`~kdvs.fw.Stat.Results` instances, and all available bioinformatic
annotations. It produces two reports (for selected and non selected variables)
for each degree of freedom (DOF) associated with the technique. For instance,
if technique has 3 DOFs associated:

    * D1, D2, D3

6 reports will be produced in total:

    * sel_D1, sel_D2, sel_D3
    * nsel_D1, nsel_D2, nsel_D3

(exact names may vary).
Because of that, any technique that uses this reporter must properly separate raw
results for each DOF (i.e. properly fill `DOF` Results element, see individual
techniques for details). It recognizes the following Results elements:

    * ':data:`~kdvs.fw.Stat.RESULTS_RUNTIME_KEY`'->'techID'
    * 'Selection'->'inner'

Since it focuses on variable selection (called 'inner selection' in KDVS terminology),
it will produce valid report only if inner selection was done with one of the
following inner selectors:

    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_AllVars`
    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq`

This reporter accepts no specific parameters. It re--implements :meth:`initialize`
method to get `em2annotation` and `technique2DOF` mappings that must be provided
in `additionalData` dictionary. 'Technique2DOF' is a technical mapping

    * {techniqueID : { 'DOFS_IDXS': (0, 1, ..., n), 'DOFs': (name_DOF0, name_DOF1, ..., name_DOFn)}

that is produced so far only in 'experiment' application. IMPORTANT: this reporter
assumes that the input Results instances originate from single category.

See Also
--------
kdvs.fw.Annotation.get_em2annotation
    """

    # NOTE: this reporter is designed to report results obtained from single
    # technique; since 'produce' is executed usually for single category, and
    # technique is so far (that is, without hacking) unique across category,
    # there should be no problem with that

    specific_parameters = ()
    global_parameters = DEFAULT_REPORTER_PARAMETERS

    def __init__(self, **kwargs):
        r"""
        """
        super(L1L2_VarCount_Reporter, self).__init__(list(itertools.chain(self.specific_parameters, self.global_parameters)), **kwargs)

    def initialize(self, storageManager, subsets_results_location, additionalData):
        r"""
Parameters
----------
storageManager : :class:`~kdvs.fw.StorageManager.StorageManager`
    instance of storage manager that will govern the production of physical files

subsets_results_location : string
    identifier of standard location used to store KDVS results

additionalData : object
    any additional data used by the reporter; the instance must contain `em2annotation`
    and `technique2DOF` mappings

Raises
------
Error
    if `em2annotation` or `technique2DOF` mapping was not found in `additionalData`
        """
        super(L1L2_VarCount_Reporter, self).initialize(storageManager, subsets_results_location, additionalData)
        if 'em2annotation' not in self.getAdditionalData():
            raise Error('em2annotation mapping was not provided for this reporter!')
        else:
            self.em2annotation = self.getAdditionalData()['em2annotation']
        if 'technique2DOF' not in self.getAdditionalData():
            raise Error('technique2DOF mapping was not provided for this reporter!')
        else:
            self.technique2DOF = self.getAdditionalData()['technique2DOF']

    def produce(self, resultsIter):
        r"""
For input :class:`~kdvs.fw.Stat.Results` instances, identify their common technique
(via runtime standard Results element :attr:`techID`), along with associated DOFs
(via `technique2DOF`). For each DOF, count all selected and non selected variables
across all Results instances, and produce two report files (for selected and not
selected variables), where for each variable a count is reported, along with all
bioinformatic annotations.

Parameters
----------
resultsIter : iterable of :class:`~kdvs.fw.Stat.Results`
    iterable of results obtained across single category

Raises
------
Error
    if more than one technique was detected across Results instances
        """
        # determine common technique across results
        tech = set()
        for result in resultsIter:
            tech.add(result[RESULTS_RUNTIME_KEY]['techID'])
        if len(tech) > 1:
            # should not be seen but to be safe
            raise Error('Reporter %s: more than one technique detected across results!' % self.__class__.__name__)
        else:
            techID = next(iter(tech))
        dofs = self.technique2DOF[techID]['DOFs']
        # prepare counting facility
        hist = dict()
        for dof in dofs:
            hist[dof] = dict()
            hist[dof]['sel'] = collections.defaultdict(int)
            hist[dof]['nsel'] = collections.defaultdict(int)
        # perform counting
        for result in resultsIter:
            inner = result['Selection']['inner']
            for dof, idata in inner.iteritems():
                selvars = idata['sel_vars']
                nselvars = idata['nsel_vars']
                for svar in selvars.keys():
                    if selvars[svar]['pass']:
                        hist[dof]['sel'][svar] += 1
                for nsvar in nselvars.keys():
                    if nselvars[nsvar]['pass']:
                        hist[dof]['nsel'][nsvar] += 1
        # finish by sorting according to counter values
        cnt = dict()
        for dof in dofs:
            cnt[dof] = dict()
            cnt[dof]['sel'] = [(v, c) for v, c in hist[dof]['sel'].iteritems()]
            cnt[dof]['sel'].sort(key=operator.itemgetter(1), reverse=True)
            cnt[dof]['nsel'] = [(v, c) for v, c in hist[dof]['nsel'].iteritems()]
            cnt[dof]['nsel'].sort(key=operator.itemgetter(1), reverse=True)

        header_sel = ['Variable Name', '# Times Selected', 'Gene Symbols(s)',
                  'Representative Public ID', 'GenBank Accession #',
                  'Entrez Gene ID(s)', 'Ensembl Gene ID(s)',
                  'RefSeq ID(s)']
        header_nsel = ['Variable Name', '# Times Not Selected', 'Gene Symbols(s)',
                  'Representative Public ID', 'GenBank Accession #',
                  'Entrez Gene ID(s)', 'Ensembl Gene ID(s)',
                  'RefSeq ID(s)']

        for dof, cdata in cnt.iteritems():

            # ---- do selected count

            # obtain report location
            fname_sel = '%s_%s_%s' % (techID, dof, 'vars_count_sel.txt')
            rloc_sel = '%s' % (fname_sel)
            # gather records
            r_sel = list()
            for var, count in cdata['sel']:
                rec_sel = list()
                rec_sel.append(var)
                rec_sel.append(count)
                for va in self.em2annotation[var]:
                    rec_sel.append(va)
                r_sel.append(rec_sel)
            # write content
            rcontent_sel = list()
            rcontent_sel.append('%s\n' % ('\t'.join(header_sel)))
            for rs in r_sel:
                rcontent_sel.append('%s\n' % ('\t'.join([str(r) for r in rs])))
            self.openReport(rloc_sel, rcontent_sel)

            # ---- do not selected count

            # obtain report location
            fname_nsel = '%s_%s_%s' % (techID, dof, 'vars_count_nsel.txt')
            rloc_nsel = '%s' % (fname_nsel)
            # gather records
            r_nsel = list()
            for var, count in cdata['nsel']:
                rec_nsel = list()
                rec_nsel.append(var)
                rec_nsel.append(count)
                for va in self.em2annotation[var]:
                    rec_nsel.append(va)
                r_nsel.append(rec_nsel)
            # write content
            rcontent_nsel = list()
            rcontent_nsel.append('%s\n' % ('\t'.join(header_nsel)))
            for rns in r_nsel:
                rcontent_nsel.append('%s\n' % ('\t'.join([str(r) for r in rns])))
            self.openReport(rloc_nsel, rcontent_nsel)


class L1L2_PKC_Reporter(Reporter):
    r"""
This local reporter produces reports that contain detailed information regarding
'outer selection', that is, results of classification performed by statistical
technique on given data subset (classification is possible since data subset
contains data points from two, or more, classes of samples); data subset is in
turn associated to specific :class:`~kdvs.fw.PK.PriorKnowledgeConcept` (PKC).
The following details are reported for each PKC:

    * selection status (in 'outer selection' sense)
    * average error obtained on test splits
    * average error obtained on training splits
    * standard deviation of the error obtained on test splits
    * standard deviation of the error obtained on training splits
    * variance of the error obtained on test splits
    * median error obtained on test splits
    * total number of variables in the subset
    * total number of 'properly selected' variables ('inner selection' in KDVS sense)

It produces single report for each degree of freedom (DOF) associated with the
technique. For instance, if technique has 3 DOFs associated:

    * D1, D2, D3

3 reports will be produced in total:

    * err_D1, err_D2, err_D3

(exact names may vary). The technique must expose the following properly filled
Results elements:

    * ':data:`~kdvs.fw.Stat.RESULTS_SUBSET_ID_KEY`'
    * 'Selection'->'outer'
    * 'Selection'->'inner'
    * 'Avg Error TS'
    * 'Avg Error TR'
    * 'Std Error TS'
    * 'Std Error TR'
    * 'Var Error TS'
    * 'Med Error TS'

NOTE: all 'Error'--like elements will be reported "as-is".

It will produce valid report only if outer selection was done with the following:

    * :class:`~kdvs.fw.impl.stat.PKCSelector.OuterSelector_ClassificationErrorThreshold`

and only if inner selection was done with one of the following:

    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_AllVars`
    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq`

This reporter accepts no specific parameters. It re--implements :meth:`initialize`
method to get the following mappings:

    * `subsets`
    * `pkcid2ssname`
    * `technique2DOF`

that must be provided in `additionalData` dictionary. The `subsets` is a technical
mapping:

    * {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}

produced so far only in 'experiment' application. The `pkcid2ssname` is a technical
mapping

    * {PKC_ID : subsetID}

produced so far only in 'experiment' application. `Technique2DOF` is a technical
mapping:

    * {techniqueID : { 'DOFS_IDXS': (0, 1, ..., n), 'DOFs': (name_DOF0, name_DOF1, ..., name_DOFn)}

produced so far only in 'experiment' application. IMPORTANT: this reporter assumes
that the input Results instances originate from single category.
    """

    # NOTE: this reporter is designed to report results obtained from single
    # technique; since 'produce' is executed usually for single category, and
    # technique is so far (that is, without hacking) unique across category,
    # there should be no problem with that

    specific_parameters = ()
    global_parameters = DEFAULT_REPORTER_PARAMETERS

    def __init__(self, **kwargs):
        r"""
        """
        super(L1L2_PKC_Reporter, self).__init__(list(itertools.chain(self.specific_parameters, self.global_parameters)), **kwargs)

    def initialize(self, storageManager, subsets_results_location, additionalData):
        r"""
Parameters
----------
storageManager : :class:`~kdvs.fw.StorageManager.StorageManager`
    instance of storage manager that will govern the production of physical files

subsets_results_location : string
    identifier of standard location used to store KDVS results

additionalData : object
    any additional data used by the reporter; the instance must contain `subsets`,
    `pkcid2ssname`, `technique2DOF` mappings

Raises
------
Error
    if `subsets`, `pkcid2ssname` or `technique2DOF` mapping was not found in
    `additionalData`
        """
        super(L1L2_PKC_Reporter, self).initialize(storageManager, subsets_results_location, additionalData)
        if 'subsets' not in self.getAdditionalData():
            raise Error('Subsets dictionary was not provided for this reporter!')
        else:
            self.subsets = self.getAdditionalData()['subsets']
        if 'pkcid2ssname' not in self.getAdditionalData():
            raise Error('pkcid2ssname mapping was not provided for this reporter!')
        else:
            self.pkcid2ssname = self.getAdditionalData()['pkcid2ssname']
        if 'technique2DOF' not in self.getAdditionalData():
            raise Error('technique2DOF mapping was not provided for this reporter!')
        else:
            self.technique2DOF = self.getAdditionalData()['technique2DOF']

    def produce(self, resultsIter):
        r"""
For input :class:`~kdvs.fw.Stat.Results` instances, identify their common technique
(via runtime standard Results element :attr:`techID`), along with associated DOFs
(via `technique2DOF`). For each DOF, scan all Results instances to gather all
required information, and produce single report file, where for each PKC,
relevant statistical information is listed.

Parameters
----------
resultsIter : iterable of :class:`~kdvs.fw.Stat.Results`
    iterable of results obtained across single category

Raises
------
Error
    if more than one technique was detected across Results instances
        """
        # determine common technique across results
        tech = set()
        for result in resultsIter:
            tech.add(result[RESULTS_RUNTIME_KEY]['techID'])
        if len(tech) > 1:
            # should not be seen but to be safe
            raise Error('Reporter %s: more than one technique detected across results!' % self.__class__.__name__)
        else:
            techID = next(iter(tech))
        dofs = self.technique2DOF[techID]['DOFs']
        dofs_idxs = self.technique2DOF[techID]['DOFS_IDXS']
        # for each DOF we report separately
        for dof, dof_idx in zip(dofs, dofs_idxs):
            stats = list()
            header = ['PKC ID', 'Subset Name', 'Selected?', 'Avg Error TS', 'Avg Error TR',
                      'Std Error TS', 'Std Error TR', 'Var Error TS', 'Med Error TS',
                      'Total Vars', 'Selected Vars']
            # obtain report location
            fname = '%s_%s_%s' % (techID, dof, 'err_stats.txt')
            rloc = '%s' % (fname)
            # in each result there are multiple partial results for each DOF
            for result in resultsIter:
                ssname = result[RESULTS_SUBSET_ID_KEY]
                pkcID = self.pkcid2ssname['bwd'][ssname]
                # obtain data
                avg_err_ts = result['Avg Err TS'][dof_idx]
                avg_err_tr = result['Avg Err TR'][dof_idx]
                std_err_ts = result['Std Err TS'][dof_idx]
                std_err_tr = result['Std Err TR'][dof_idx]
                var_err_ts = result['Var Err TS'][dof_idx]
                med_err_ts = result['Med Err TS'][dof_idx]
                total_vars = len(self.subsets[pkcID]['vars'])
                inner = result['Selection']['inner']
                if inner[dof]['sel_vars'] == SELECTIONERROR:
                    selected_vars = -1
                else:
                    all_sel_vars = [svar for svar in inner[dof]['sel_vars'].keys() if inner[dof]['sel_vars'][svar]['pass']]
                    selected_vars = len(all_sel_vars)
#                selected_vars = len(inner[dof]['sel_vars'])
                outer = result['Selection']['outer']
                selected = outer[dof]
                if selected == SELECTED:
                    vsel = 'Y'
                elif selected == NOTSELECTED:
                    vsel = 'N'
                elif selected == SELECTIONERROR:
                    vsel = 'ERR'
                else:
                    vsel = '?'
                # prepare record
                rec = list()
                rec.append(pkcID)
                rec.append(ssname)
                rec.append(vsel)
                rec.append(avg_err_ts)
                rec.append(avg_err_tr)
                rec.append(std_err_ts)
                rec.append(std_err_tr)
                rec.append(var_err_ts)
                rec.append(med_err_ts)
                rec.append(total_vars)
                rec.append(selected_vars)
                # store record
                stats.append(rec)

# TODO: check if this is redundant!
#            # sort records according to subset size (i.e. total vars)
#            stats.sort(key=operator.itemgetter(8), reverse=True)

            # produce report content
            rcontent = list()
            rcontent.append('%s\n' % ('\t'.join(header)))
            for rec in stats:
                rcontent.append('%s\n' % ('\t'.join([str(r) for r in rec])))
            # store report
            self.openReport(rloc, rcontent)


class L1L2_PKC_UTL_Reporter(Reporter):
    r"""
This global reporter produces unified term list (UTL) for each single combination
of DOFs coming from statistical techniques employed on selected categorizer hierarchy.
For instance, if technique *T1* with DOFs

    * a1, a2, a3

was used in category *A* of categorizer *C*, and technique *T2* with DOFs

    * b1, b2, b3

was used in category *B* of the same categorizer *C*, the following combinations
will be generated:

    * a1_b1, a1_b2, a1_b3
    * a2_b1, a2_b2, a2_b3
    * a3_b1, a3_b2, a3_b3

and in total 9 UTLs will be produced. UTL contains series of information specific
for prior knowledge concepts (PKCs), including:

    * selection status (in 'outer selection' sense)
    * identifier of associated data subset
    * full name of prior knowledge concept (as given by PKC manager)
    * total number of variables in data subset
    * total number of 'properly selected' variables ('inner selection' in KDVS sense)
    * 'error estimate', i.e. average error obtained on test splits
        (must be exposed by the technique as Results element `Classification Error`)
    * number of true positives
    * number of true negatives
    * number of false positives
    * number of false negatives
    * Matthews Correlation Coefficient

All this information is associated with classification process performed by
the statistical technique (classification is possible since data subset contains
data points from two, or more, classes of samples). The technique must expose
the following properly filled Results elements:

    * 'Selection'->'outer'
    * 'Selection'->'inner'
    * 'Classification Error'
        (produced for all DOFs separately, see individual techniques for details)
    * 'CM MCC'
        (as tuple with TP, TN, FP, FN, MCC values)

It will produce valid report only if outer selection was done with the following:

    * :class:`~kdvs.fw.impl.stat.PKCSelector.OuterSelector_ClassificationErrorThreshold`

and only if inner selection was done with one of the following:

    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_AllVars`
    * :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq`

This reporter accepts no specific parameters. It re--implements :meth:`initialize`
method to get the following mappings/instances:

    * `subsets`
    * `pkcid2ssname`
    * `technique2DOF`
    * `operations_map_img`
    * `categories_map`
    * `cchain`
    * `submission_order`
    * `pkc_manager`

that must be provided in `additionalData` dictionary.
The following mappings/instances are produced so far only inside 'experiment' application:

    * `subsets`
        {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}
    * `pkcid2ssname` 
        {PKC_ID : subsetID}
    * `technique2DOF`
        {techniqueID : { 'DOFS_IDXS': (0, 1, ..., n), 'DOFs': (name_DOF0, name_DOF1, ..., name_DOFn)}
    * `operations_map_img`
        (textual representation of internal mapping `operations_map`)
    * `categories_map`
        {categorizerID : [categories]}
    * `cchain`
        i.e. categorizers chain, comes directly from :data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE` application profile (element 'subset_hierarchy_categorizers_chain')
    * `submission_order`
        an iterable of PKC IDs sorted in order of submission of their jobs
    * `pkc_manager`
        a concrete instance of :class:`~kdvs.fw.PK.PKCManager` that governs all PKCs generated

IMPORTANT: this reporter assumes that, across each category of the considered
categorizer, all Results instances originated from single statistical technique.
See comments for the algorithm details.
    """
    # NOTE: this reporter produces report similar to 'unified term list' in KDVS v 1.0

    specific_parameters = ()
    global_parameters = DEFAULT_REPORTER_PARAMETERS

    def __init__(self, **kwargs):
        r"""
        """
        super(L1L2_PKC_UTL_Reporter, self).__init__(list(itertools.chain(self.specific_parameters, self.global_parameters)), **kwargs)

    def initialize(self, storageManager, subsets_results_location, additionalData):
        r"""
Parameters
----------
storageManager : :class:`~kdvs.fw.StorageManager.StorageManager`
    instance of storage manager that will govern the production of physical files

subsets_results_location : string
    identifier of standard location used to store KDVS results

additionalData : object
    any additional data used by the reporter; the instance must contain the following
    mappings/instances: `subsets`, `pkcid2ssname`, `technique2DOF`, `operations_map_img`,
    `categories_map`, `cchain`, `submission_order`, `pkc_manager`

Raises
------
Error
    if any of the following was not found in `additionalData`: `subsets`, `pkcid2ssname`,
    `technique2DOF`, `operations_map_img`, `categories_map`, `cchain`, `submission_order`,
    `pkc_manager`
        """
        super(L1L2_PKC_UTL_Reporter, self).initialize(storageManager, subsets_results_location, additionalData)
#        if 'em2annotation' not in self.getAdditionalData():
#            raise Error('em2annotation mapping was not provided for this reporter!')
#        else:
#            self.em2annotation = self.getAdditionalData()['em2annotation']
        if 'subsets' not in self.getAdditionalData():
            raise Error('Subsets dictionary was not provided for this reporter!')
        else:
            self.subsets = self.getAdditionalData()['subsets']
        if 'pkcid2ssname' not in self.getAdditionalData():
            raise Error('pkcid2ssname mapping was not provided for this reporter!')
        else:
            self.pkcid2ssname = self.getAdditionalData()['pkcid2ssname']
        if 'technique2DOF' not in self.getAdditionalData():
            raise Error('technique2DOF mapping was not provided for this reporter!')
        else:
            self.technique2DOF = self.getAdditionalData()['technique2DOF']
        if 'operations_map_img' not in self.getAdditionalData():
            raise Error('operations_map_img mapping was not provided for this reporter!')
        else:
            self.operationsMap = self.getAdditionalData()['operations_map_img']
        if 'categories_map' not in self.getAdditionalData():
            raise Error('categories_map mapping was not provided for this reporter!')
        else:
            self.categoriesMap = self.getAdditionalData()['categories_map']
        if 'cchain' not in self.getAdditionalData():
            raise Error('cchain was not provided for this reporter!')
        else:
            self.cchain = self.getAdditionalData()['cchain']
        if 'submission_order' not in self.getAdditionalData():
            raise Error('submission_order mapping was not provided for this reporter!')
        else:
            self.submission_order = self.getAdditionalData()['submission_order']
        if 'pkc_manager' not in self.getAdditionalData():
            raise Error('pkc_manager was not provided for this reporter!')
        else:
            self.pkcManager = self.getAdditionalData()['pkc_manager']

    def produceForHierarchy(self, subsetHierarchy, ssIndResults, currentCategorizerID, currentCategoryID):
        r"""
Having current categorizer, get one below in the chain (if possible), along with
all its categories. For each category, make sure that all relevant
:class:`~kdvs.fw.Stat.Results` instances come from the same technique, and
identify it, along with associated DOFs. Having series of DOFs for categories,
permute them as explained above, and for each permutation, scan associated Results
instances, gather requested information, and produce single report file.
See comments for more technical details.

Parameters
----------
subsetHierarchy : :class:`~kdvs.fw.SubsetHierarchy.SubsetHierarchy`
    concrete current hierarchy of subsets that contains whole category tree

ssIndResults : dict of iterable of :class:`~kdvs.fw.Stat.Results`
    iterables of Results obtained for all categories at once

currentCategorizerID : string
    identifier of :class:`~kdvs.fw.Categorizer.Categorizer` from which the reporter will start work

currentCategoryID : string
    optionally, identifier of category the reporter shall start with

Raises
------
Error
    if more than one technique was detected across any category

See Also
--------
itertools.product
        """

        # in this report we are working across categories of single categorizer
        # one level below of the current one (dubbed nextCategorizer)

        # we collect all DOFs from techniques used across its categories and we
        # permute them (formally, we do cartesian product); based on those
        # permutations, we go through results, collect relevant entries and
        # report them

        # NOTE: this reporter works on premise that technique is unique across
        # category; otherwise the number of possible DOF permutations explodes
        # and reporting that is non feasible

        # NOTE: this reporter ignores current category

        # first we need to identify next immediate categorizer in the chain
        # to do this we split categorizer chain in pairs
        nextCategorizerID = None
        for currentID, nextID in pairwise(iter(self.cchain)):
            if currentID == currentCategorizerID:
                # next found finish looping
                nextCategorizerID = nextID
                break
        # if current categorizer was LAST in chain, we obviously cannot find the
        # next one; we report nothing and exit now
        if nextCategorizerID is None:
            return

        # we will permute DOFs across these categories
        permutable_categories = self.categoriesMap[nextCategorizerID]

        # we will also store submission order produced for this categorizer
        subm_order = self.submission_order[nextCategorizerID]

        # first we quickly gather all DOFs across categories
        dofs_across_categories = list()

        for category in permutable_categories:

            operations = self.operationsMap[category]

            # retrieve PKC IDs for this category and store it for further querying
            pkcids = [k for k in operations.keys() if not k.startswith('__') and not k.endswith('__')]

            # determine common technique across subsets
            tech = set()
            for pkcid in pkcids:
                tech.add(operations[pkcid]['__technique__'])
            if len(tech) > 1:
                # should not be seen but to be safe
                raise Error('Reporter %s: more than one technique detected across category!' % self.__class__.__name__)
            else:
                techID = next(iter(tech))

            cat_dofs = self.technique2DOF[techID]['DOFs']
            cat_dofs_idxs = self.technique2DOF[techID]['DOFS_IDXS']
            dofentry = tuple([(d, i) for d, i in zip(cat_dofs, cat_dofs_idxs)])
            dofs_across_categories.append((category, techID, dofentry, len(dofentry)))

        # sort based on number of DOFs (we begin permuting with longer DOF lists)
        dofs_across_categories.sort(key=operator.itemgetter(3), reverse=True)

        # re--index gathered information to facilitate generating permutation IDs later
        dofs_records = list()
        for dac in dofs_across_categories:
            techrec = list()
            category, techID, dofentry, _ = dac
            for dofidx in dofentry:
                techrec.append((category, techID, dofidx))
            dofs_records.append(techrec)

        # we generate cartesian product between all DOFs of all techniques
        # used across respective categories
        dof_permutations = list(itertools.product(*dofs_records))

        for dof_permutation in dof_permutations:

            # report for this permutation

            rec1, rec2 = dof_permutation

            cat1, tech1, (dof1, idx1) = rec1
            cat2, tech2, (dof2, idx2) = rec2

            cat1_subm_order = subm_order[cat1]
            cat2_subm_order = subm_order[cat2]

            full1ID = '%s_%s_%s_%s' % (cat1, tech1, dof1, idx1)
            name1ID = '%s_%s_%s' % (tech1, dof1, idx1)

            full2ID = '%s_%s_%s_%s' % (cat2, tech2, dof2, idx2)
            name2ID = '%s_%s_%s' % (tech2, dof2, idx2)

            permutationFullID = '%s_%s' % (full1ID, full2ID)
            permutationID = '%s_%s' % (name1ID, name2ID)

            # obtain report location
            fname = '%s_%s%s' % ('UTL', permutationID, '.txt')
            rloc = '%s' % (fname)

            # gather required information

            # now dof1 and dof2 will be merged; we gathered this information so far:
            # - we have two categories cat1 and cat2, that hold techniques that
            #   respective DOFs belong to
            # - we have two submission order sequences for cat1 and cat2
            # - we have two techniques tech1 and tech2, that enclose respective DOFs
            # - we have two indexes of dof1 and dof2, idx1 and idx2, to be used
            #   in querying information from results

            # we need to go through merged submission order sequences, reconstruct
            # subset names (with the help of pkcid2ssname), and get individual
            # results from ssIndResults
            full_subm_order = list(itertools.chain(cat1_subm_order, cat2_subm_order))
            full_ss = [self.pkcid2ssname['fwd'][pkcid] for pkcid in full_subm_order]
            full_results = [ssIndResults[ss] for ss in full_ss]

            # we also need quick iterable of DOFs and indexes for merged submission
            # order sequences
            full_dofs = list(itertools.chain([dof1 for _ in cat1_subm_order], [dof2 for _ in cat2_subm_order]))
            full_dof_idxs = list(itertools.chain([idx1 for _ in cat1_subm_order], [idx2 for _ in cat2_subm_order]))

            # gather all needed information
            records = list()
            for pkcID, ssname, result, dof, idx in zip(full_subm_order, full_ss, full_results, full_dofs, full_dof_idxs):
                try:
                    pkcname = self.pkcManager.getPKC(pkcID)['conceptName']
                except:
                    pkcname = "There shall be PKC name!"
                tp = tn = fp = fn = mcc = None
                try:
                    tp, tn, fp, fn, mcc = result['CM MCC'][dof]
                except KeyError:
                    pass
                inner = result['Selection']['inner']
                total_vars = len(self.subsets[pkcID]['vars'])

                if inner[dof]['sel_vars'] == SELECTIONERROR:
                    selected_vars = -1
                else:
                    all_sel_vars = [svar for svar in inner[dof]['sel_vars'].keys() if inner[dof]['sel_vars'][svar]['pass']]
                    selected_vars = len(all_sel_vars)
#                selected_vars = len(inner[dof]['sel_vars'])
                err_estimate = result['Classification Error'][dof]

                outer = result['Selection']['outer']
                selected = outer[dof]
                if selected == SELECTED:
                    vsel = 'Y'
                elif selected == NOTSELECTED:
                    vsel = 'N'
                elif selected == SELECTIONERROR:
                    vsel = 'ERR'
                else:
                    vsel = '?'

                # fill record
                record = list()
                record.append(pkcID)
                record.append(ssname)
                record.append(vsel)
                record.append(pkcname)
                record.append(total_vars)
                record.append(selected_vars)
                record.append(err_estimate)
                record.append(tp)
                record.append(tn)
                record.append(fp)
                record.append(fn)
                record.append(mcc)
                records.append(record)

            header = ['PKC ID', 'Subset Name', 'Selected?', 'PKC Name', 'Total Vars',
                      'Selected Vars', 'Error Estimate', '#TP', '#TN', '#FP', '#FN', 'MCC']
            rcontent = list()
            # write comments
            rcontent.append('# Full DOF Permutation ID: %s\n' % permutationFullID)
            rcontent.append('# "Error Estimate" = "Classification Error"\n')
            rcontent.append('#\n')
            # write the rest
            rcontent.append('%s\n' % ('\t'.join(header)))
            for rec in records:
                rcontent.append('%s\n' % ('\t'.join([str(r) for r in rec])))

            self.openReport(rloc, rcontent)
