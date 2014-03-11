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
Provides concrete implementations for various standard selectors. Selectors
are closely tied to statistical techniques and reporters. Selectors implemented
here were designed to work with techniques that use
`l1l2py <http://slipguru.disi.unige.it/Software/L1L2Py/>`_ library, but can be
adapted for other purposes with some care. NOTE: this part of API has only been
sketched, the selectors implemented here are not freely portable and many details
are still hard--coded.
"""

from kdvs.fw.Stat import Selector, SELECTIONERROR, SELECTED, NOTSELECTED
from kdvs.core.error import Warn

class OuterSelector(Selector):
    r"""
Base class for 'outer selectors'. The 'outer selection' refers to the prior
knowledge concepts that can be 'selected' if they pass certain criteria. For
instance, if concrete statistical technique performs classification on data subset,
the associated prior knowledge concept can be 'selected' by passing certain
criteria related to classification error. Or, if individual classification
error for that data subset is below median classification error computed across
all considered data subsets, it may be marked as 'selected', etc. The concrete
implementation accepts iterable of :class:`~kdvs.fw.Stat.Results` instances,
and can compute whatever passing criteria it sees fit. It must fill Results
element 'Selection', subdictionary 'outer', for reporting; later, the associated
Reporter must interpret it correctly. Very often, outer selector is closely tied
to inner selector.
    """
    def __init__(self, parameters, **kwargs):
        super(OuterSelector, self).__init__(parameters, **kwargs)

    def perform(self, indResultIter):
        r"""
Perform 'outer selection', based on the input :class:`~kdvs.fw.Stat.Results`
instances. The individual prior knowledge concepts (for which Results were produced),
can be marked as :data:`~kdvs.fw.Stat.SELECTED` or :data:`~kdvs.fw.Stat.NOTSELECTED`
(:data:`~kdvs.fw.Stat.SELECTIONERROR` may be used in dubious cases). The typical
way to mark 'selection' is to fill standard Results element 'Selection',
subdictionary 'outer', with details understood for associated
:class:`~kdvs.fw.Report.Reporter`. Also, the implementation shall return the
iterable of objects that contain individual selection markings stored in
'Selection'->'outer' Results element. By default, this method does nothing.

Parameters
----------
indResultIter : iterable of :class:`~kdvs.fw.Stat.Results`
    iterable of Results instances; depending on the needs, they may come from
    single category or multiple categories (e.g. from all categories of certain
    categorizer)
        """
        pass

class InnerSelector(Selector):
    r"""
Base class for 'inner selectors'. The 'inner selection' refers to the individual
variables of data subset that can be 'selected' if they pass certain criteria.
For instance, if concrete statistical technique performs variable selection
(in machine learning sense) on data subset, selected variables can be simply
marked by the selector as 'selected' (in KDVS sense). Or, if the technique uses
more complicated scheme, such as counting frequencies of selected variables across
all splits (as some l1l2py--related techniques do), the selector can mark certain
variables as 'selected' depending on some frequency threshold, etc. The concrete
implementation accepts the following:

    * results of outer selection
    * iterable of individual :class:`~kdvs.fw.Stat.Results` instances
    * information about data subsets (to retrieve specific variables)
    
and can compute whatever passing criteria it sees fit. It mus fill Results element
'Selection', subdictionary 'inner', for reporting; later, the associated Reporter
must interpret it correctly. Very often, inner selector is closely tied to outer
selector.
    """
    def __init__(self, parameters, **kwargs):
        super(InnerSelector, self).__init__(parameters, **kwargs)

    def perform(self, outerSelectionResults, ssIndResults, subsetsDict):
        r"""
Perform 'inner selection' based on the input :class:`~kdvs.fw.Stat.Results`
instances and information already produced by some outer selection. Very often,
only variables that come from 'properly selected' data subsets can be considered
'properly selected' in KDVS sense. The additional information about subsets is
used to retrieve specific variables for reporting. The individual variables can
be marked as :data:`~kdvs.fw.Stat.SELECTED` or :data:`~kdvs.fw.Stat.NOTSELECTED`
(:data:`~kdvs.fw.Stat.SELECTIONERROR` may be used in dubious cases). The typical way
to mark 'selection' is to fill standard Results element 'Selection', subdictionary
'inner', with details understood for associated :class:`~kdvs.fw.Report.Reporter`.
Also, the implementation shall return the dictionary of objects that contain
individual selection markings stored in 'Selection'->'inner' Results element
(keyed by subset ID). By default, this method does nothing.

Parameters
----------
outerSelectionResults : object
    results of outer selection produced by one of :class:`OuterSelector`

ssIndResults : dict of :class:`~kdvs.fw.Stat.Results`
    dictionary that contains Results instances, keyed by subset ID

subsetsDict : dict
    technical mapping produced so far only in 'experiment' application

        * {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}
        """
        pass


class OuterSelector_ClassificationErrorThreshold(OuterSelector):
    r"""
Outer selector that marks PKC as 'selected' if associated classification error
(that must be present in :class:`~kdvs.fw.Stat.Results` instance as
'Classification Error') is below (<) the configurable threshold. The error
threshold is specified during initialization and interpreted once.
    """
    _parameters = ('error_threshold',)

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    parameters to configure this outer selector; the following parameters are used:
        * 'error_threshold' (float) -- error threshold that this instance will use
        """
        super(OuterSelector_ClassificationErrorThreshold, self).__init__(self._parameters, **kwargs)

    def perform(self, indResultIter):
        r"""
Mark each individual :class:`~kdvs.fw.Stat.Results` instance as
:data:`~kdvs.fw.Stat.SELECTED` or :data:`~kdvs.fw.Stat.NOTSELECTED`, depending on
the classification error. The value of classification error is compared to
error threshold; if it is smaller (<), then PKC is marked as
:data:`~kdvs.fw.Stat.SELECTED`, and as :data:`~kdvs.fw.Stat.NOTSELECTED` otherwise.
Note that for technique that uses not--null multiple degrees of freedom (DOFs),
each DOF can be associated with different classification error; this is often the
case when the statistical technique is regularized and certain parameter values
can drastically alter the results it produces. It uses the following selection
marking for single Results instance: a dictionary

    * {DOF : selection_status}

It fills 'Selection'->'outer' Results element that must be present (may be empty).

Parameters
----------
indResultIter : iterable of :class:`~kdvs.fw.Stat.Results`
    iterable of Results instances that should come from single category

Returns
-------
cres : iterable of dict
    iterable of selection markings as dictionary {DOF : selection_status}
        """
        super(OuterSelector_ClassificationErrorThreshold, self).perform(indResultIter)
        err_res = { None : SELECTIONERROR }
        cres = list()
        try:
            cerr_thr = self.parameters['error_threshold']
            for indResult in indResultIter:
                try:
                    class_err = indResult['Classification Error']
                    result = dict([(dof, SELECTED if err < cerr_thr else NOTSELECTED) for (dof, err) in class_err.iteritems()])
                    indResult['Selection']['outer'] = result
                except KeyError:
                    result = err_res
                cres.append(result)
            return cres
        except KeyError:
            cres.append(err_res)
            return cres

class InnerSelector_ClassificationErrorThreshold_AllVars(InnerSelector):
    r"""
Inner selector that marks all variables coming from 'properly selected' data subsets
(by outer selection) as 'properly selected'. IMPORTANT NOTE: when the variable
comes from 'not selected' data subset, it is marked as 'not selected' regardless
of any proper variable selection scheme used; this ignores any variable selection
(in machine learning sense) performed for such data subset. This selector accepts
no configuration parameters. NOTE: currently, this selector produces only selection
markings, and does not use selection constants.
    """
    _parameters = ()

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    parameters to configure this inner selector; currently no parameters are used
        """
        super(InnerSelector_ClassificationErrorThreshold_AllVars, self).__init__(self._parameters, **kwargs)

    def perform(self, outerSelectionResults, ssIndResults, subsetsDict):
        r"""
Perform 'inner selection' on the individual variables according to
:class:`~kdvs.fw.Stat.Results` instances. Inner selection is based `solely` on
outer selection results. If data subset was marked during outer selection as
:data:`~kdvs.fw.Stat.SELECTED`, all its variables are marked as 'selected' as well,
and as 'not selected' otherwise. Currently, it understands outer selection
results produced by :class:`OuterSelector_ClassificationErrorThreshold`.
It fills 'Selection'->'inner' Results element that must be present (may be empty).

Parameters
----------
outerSelectionResults : object
    results of outer selection; must conform to the format used by
    :class:`OuterSelector_ClassificationErrorThreshold`

ssIndResults : dict of :class:`~kdvs.fw.Stat.Results`
    dictionary that contains Results instances, keyed by subset ID

subsetsDict : dict
    technical mapping produced so far only in 'experiment' application
        * {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}

Returns
-------
vres : dict of dict
    dictionary of the following selection markings:
        * {PKC_ID : {DOF : {'sel_vars'/'nsel_vars' : {variable_name : {'pass' : True/False}}}}}
        """
        super(InnerSelector_ClassificationErrorThreshold_AllVars, self).perform(outerSelectionResults, ssIndResults, subsetsDict)
        vres = dict()
        for pkcid, osdata in outerSelectionResults.iteritems():
            ssdata = subsetsDict[pkcid]
            svars = ssdata['vars']
            ssname = ssdata['mat']
            vres[pkcid] = dict()
            # for this inner selector we do not need individual results
            for dof, selresult in osdata.iteritems():
                vres[pkcid][dof] = dict()
                vres[pkcid][dof]['sel_vars'] = dict()
                vres[pkcid][dof]['nsel_vars'] = dict()
                if selresult == SELECTED:
                    for svar in svars:
                        vres[pkcid][dof]['sel_vars'][svar] = dict()
                        vres[pkcid][dof]['sel_vars'][svar]['pass'] = True
                elif selresult == NOTSELECTED:
                    vres[pkcid][dof]['sel_vars'] = dict()
                    vres[pkcid][dof]['nsel_vars'] = dict()
                    for svar in svars:
                        vres[pkcid][dof]['nsel_vars'][svar] = dict()
                        vres[pkcid][dof]['nsel_vars'][svar]['pass'] = True
                else:
                    pass
            ssIndResults[ssname]['Selection']['inner'] = vres[pkcid]
        return vres

class InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq(InnerSelector):
    r"""
Inner selector closely tied with techniques that use
`l1l2py <http://slipguru.disi.unige.it/Software/L1L2Py/>`_ library, that marks
variables coming from 'properly selected' data subsets (by outer selection) as
'properly selected', if they appeared frequently enough among selected variables
(in variable selection sense) across test splits. This selector accepts the following
configuration parameters:

    * 'frequency_threshold' (float) -- the threshold on the frequency of appearance across splits
    * 'pass_variables_for_nonselected_pkcs' (boolean) -- for compatibility with KDVS v1.0;
        if True, the variables that come from 'not selected' data subsets will
        be counted as 'not selected' (as expected, introduced in KDVS v2.0);
        if False, such variables will be ignored and not counted anywhere
        (replicating the behavior of KDVS v1.0)

NOTE: currently, this selector produces only selection markings, and does not use selection constants.
    """
    _parameters = ('frequency_threshold', 'pass_variables_for_nonselected_pkcs')

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    parameters to configure this inner selector; the following parameters are used:
        * 'frequency_threshold' (float) -- the threshold on the frequency of appearance across splits
        * 'pass_variables_for_nonselected_pkcs' (boolean) -- for compatibility with KDVS v1.0
        """
        super(InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq, self).__init__(self._parameters, **kwargs)

    def perform(self, outerSelectionResults, ssIndResults, subsetsDict):
        r"""
Perform 'inner selection' on the individual variables according to
:class:`~kdvs.fw.Stat.Results` instances. Inner selection results are based on
outer selection results, as well as raw results from statistical technique that
uses l1l2 regularization (see l1l2py documentation for more details). If data
subset was marked during outer selection as :data:`~kdvs.fw.Stat.SELECTED`,
the selector scans frequencies (stored in 'MuExt' Results element) and marks
individual variables if they 'pass' the frequency threshold criterion (freq > thr).
Currently, it understands outer selection results produced by
:class:`OuterSelector_ClassificationErrorThreshold`. It fills 'Selection'->'inner'
Results element that must be present (may be empty).

Parameters
----------
outerSelectionResults : object
    results of outer selection; must conform to the format used by
    :class:`OuterSelector_ClassificationErrorThreshold`

ssIndResults : dict of :class:`~kdvs.fw.Stat.Results`
    dictionary that contains Results instances, keyed by subset ID

subsetsDict : dict
    technical mapping produced so far only in 'experiment' application
        * {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]},

Returns
-------
vres : dict of dict
    dictionary of the following selection markings:
        * {PKC_ID : {DOF : {'sel_vars'/'nsel_vars' : {variable_name : {'freq' : frequency_value, 'pass' : True/False}}}}}
        """
        super(InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq, self).perform(outerSelectionResults, ssIndResults, subsetsDict)
        vres = dict()
        freq_thr = self.parameters['frequency_threshold']
        for pkcid, osdata in outerSelectionResults.iteritems():
            ssdata = subsetsDict[pkcid]
            svars = ssdata['vars']
            ssname = ssdata['mat']
            vres[pkcid] = dict()
            indResult = ssIndResults[ssname]
            for dof, selresult in osdata.iteritems():
                vres[pkcid][dof] = dict()
                vres[pkcid][dof]['sel_vars'] = dict()
                vres[pkcid][dof]['nsel_vars'] = dict()
                # reconstruct mu index X from DOF: "muX"
                mu = int(dof.split('mu')[1])
                # get frequencies for dof
                freqs_mu = indResult['MuExt']['freqs'][mu]
                # walk all variables and check the frequency
                if selresult == SELECTED:
                    # KDVS rule: if PKC is selected (in outer sense) we can look
                    # for variables selected (in inner sense)
                    for varind, svar in enumerate(svars):
                        if freqs_mu[varind] > 0.0:
                            # L1L2 rule: variable associated with non-zero frequency is selected (in inner sense)
                            vres[pkcid][dof]['sel_vars'][svar] = dict()
                            vres[pkcid][dof]['sel_vars'][svar]['freq'] = freqs_mu[varind]
                            # KDVS rule: final decision to mark variable as selected
                            # depends also on frequency threshold!
                            vpass = True if freqs_mu[varind] > freq_thr else False
                            vres[pkcid][dof]['sel_vars'][svar]['pass'] = vpass
                        else:
                            # L1L2 rule: variable associated with zero frequency is NOT selected (in inner sense)
                            vres[pkcid][dof]['nsel_vars'][svar] = dict()
                            vres[pkcid][dof]['nsel_vars'][svar]['freq'] = freqs_mu[varind]
                            vres[pkcid][dof]['nsel_vars'][svar]['pass'] = True
                elif selresult == NOTSELECTED:
                    # KDVS rule: each variable in not selected PKC
                    # (in outer sense) is NOT selected (in inner sense)
                    for svar in svars:
                        vres[pkcid][dof]['nsel_vars'][svar] = dict()
                        pass_nonsel = self.parameters['pass_variables_for_nonselected_pkcs']
                        if pass_nonsel is True:
                            # this condition, introduced in KDVS v2.0, reports
                            # all variables associated with _not selected_
                            # L1L2-processed PKC as 'not selected'
                            # (also they will be counted as 'not selected')
                            vres[pkcid][dof]['nsel_vars'][svar]['pass'] = True
                        else:
                            # this condition replicates behavior of KDVS v1.0
                            # where variables associated with _not selected_
                            # L1L2-processed PKCs are NOT reported as not selected
                            # (in fact they are not counted at all anywhere)
                            vres[pkcid][dof]['nsel_vars'][svar]['pass'] = False
                else:
                    pass
            ssIndResults[ssname]['Selection']['inner'] = vres[pkcid]
        return vres

