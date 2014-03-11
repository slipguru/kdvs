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
Provides concrete implementation of statistical techniques that use
`l1l2py <http://slipguru.disi.unige.it/Software/L1L2Py/>`_ library.
"""

from kdvs.core.dep import verifyDepModule
from kdvs.core.error import Error, Warn
from kdvs.core.util import isListOrTuple, importComponent
from kdvs.fw.Job import Job, NOTPRODUCED
from kdvs.fw.Stat import Technique, DEFAULT_CLASSIFICATION_RESULTS, \
    calculateConfusionMatrix, calculateMCC, Results, DEFAULT_GLOBAL_PARAMETERS, \
    RESULTS_PLOTS_ID_KEY, DEFAULT_SELECTION_RESULTS, DEFAULT_RESULTS, \
    RESULTS_RUNTIME_KEY
from kdvs.fw.impl.stat.Plot import MATPLOTLIB_GRAPH_BACKEND_PDF, MatplotlibPlot
import itertools
import l1l2py
import numpy
import os


# ---- L1L2_OLS classifier

def l1l2_ols_job_wrapper(*args):
    r"""
Wrapper job function for :func:`l1l2py.algorithms.ridge_regression`. This function
transposes data subset if the dimensions do not match with labels vector, performs
the call, and calculates classification error with supplied error function. See
`l1l2py documentation <http://slipguru.disi.unige.it/Software/L1L2Py/algorithms.html#regularization-algorithms>`__
for more details.

Parameters
----------
data : :class:`numpy.ndarray`
    data subset to be processed

labels : :class:`numpy.ndarray`
    associated label information to be processed

error_func : callable
    callable used as error function

Returns
-------
beta : :class:`numpy.ndarray`
    solution of ridge regression

error : float
    classification error

labels : :class:`numpy.ndarray`
    original labels

labels_predicted : :class:`numpy.ndarray`
    labels predicted with the obtained solution
    """
    data, labels, error_func = args
    # try to transpose if dimensions do not match
    if data.shape[0] != labels.shape[0]:
        data = data.T
    # calculate beta
    beta = l1l2py.algorithms.ridge_regression(data, labels)
    # calculate error
    labels_predicted = numpy.dot(data, beta)
    error = error_func(labels, labels_predicted)
    return (beta, error, labels, labels_predicted)


class L1L2_OLS(Technique):
    r"""
Classifier based on :func:`l1l2py.algorithms.ridge_regression` (called with mu=0.0).
It uses l1l2py v1.0.5. It can be configured with the following parameters:

    * 'error_func' (callable) -- callable used as error function
    * 'return_predictions' (boolean) -- if predictions shall be returned

The configuration parameters are interpreted once, during initialization. This
technique uses single virtual degree of freedom (DOF). The following
:class:`~kdvs.fw.Stat.Results` elements are produced:

    * 'Classification Error' (float) -- classification error
    * 'Beta' (:class:`numpy.ndarray`) -- solution obtained from ridge regression
    * 'CM MCC' (tuple: (int, int, int, int, float)) -- the number of: true positives, true negatives, false positives, false negatives, and Matthews Correlation Coefficient,
    * 'Predictions' (dict) -- if 'return_predictions' was True, it contains the dictionary:
        {
        'orig_labels' : iterable of original labels in numerical format (:data:`numpy.sign`),
        'pred_labels' : iterable of predicted labels in numerical format (:data:`numpy.sign`),
        'orig_samples' : iterable of original samples
        }

This technique creates empty 'Selection' Results element. This technique produces
single Job instance. This technique does not generate any plots.

See Also
--------
l1l2_ols_job_wrapper
    """
    _version = '1.0.5'
    _ols_parameters = ('error_func', 'return_predictions')
    _global_parameters = DEFAULT_GLOBAL_PARAMETERS
    _l1l2_ols_result_elements = ('Beta', 'CM MCC')

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    keyworded parameters to configure this technique; the following parameters
    are currently used: 'error_func', 'return_predictions'

Raises
------
Error
    if l1l2py library is not present, or a wrong version of l1l2py is present
        """
        verifyDepModule('l1l2py')
        if self._verify_version():
            super(L1L2_OLS, self).__init__(list(itertools.chain(self._ols_parameters, self._global_parameters)), **kwargs)
        else:
            raise Error('L1L2Py version "%s" must be provided to use this class!' % self._version)
        self.results_elements.extend(DEFAULT_RESULTS)
        self.results_elements.extend(DEFAULT_CLASSIFICATION_RESULTS)
        self.results_elements.extend(DEFAULT_SELECTION_RESULTS)
        if self.parameters['return_predictions']:
            self.results_elements.append('Predictions')
        self.results_elements.extend(self._l1l2_ols_result_elements)

    def createJob(self, ssname, data, labels, additionalJobData={}):
        r"""
Create single :class:`~kdvs.fw.Job.Job` that wraps :func:`l1l2_ols_job_wrapper`
call together with proper arguments and associated additional data.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

data : :class:`numpy.ndarray`
    data subset to be processed

labels : :class:`numpy.ndarray`
    associated label information to be processed

additionalJobData : dict
    any additional information that will be associated with each job produced;
    empty dictionary by default

Returns
-------
(jID, job) : string, :class:`~kdvs.fw.Job.Job`
    tuple of the following: custom job ID (ssname in this case), and Job instance to be executed

Notes
-----
Proper order of data and labels must be ensured in order for the technique to work.
Typically, subsets are generated according to samples order specified within the
primary data set; labels must be in the same order. By definition, KDVS does not
check this.
        """
        super(L1L2_OLS, self).createJob(ssname, data, labels)
        call_args = (data, labels, self.parameters['error_func'])
        jobData = {
            'depfuncs' : (),
            'modules' : ('l1l2py', 'numpy', 'os'),
            }
        jobData.update(additionalJobData)
        job = Job(call_func=l1l2_ols_job_wrapper, call_args=call_args, additional_data=jobData)
        # yield always pair (customID, job)
        yield (ssname, job)

    def produceResults(self, ssname, jobs, runtime_data):
        r"""
Produce :class:`~kdvs.fw.Stat.Results` instance for exactly one job result.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

jobs : iterable of :class:`~kdvs.fw.Job.Job`
    executed job(s) that contain(s) raw results

runtime_data : dict
    data collected in runtime that shall be included in the final Results instance

Returns
-------
final_results : :class:`~kdvs.fw.Stat.Results`
    Results instance that contains final results of the technique

Raises
------
Error
    if more than one jobs were specified
        """
        # we expect single job here
        if len(jobs) > 1:
            raise Error('%s can produce results for single job only!' % self.__class__)
        return self._createResults(ssname, jobs[0].result, jobs[0].additional_data, runtime_data)

    def _verify_version(self):
        return l1l2py.__version__ == self._version

    def _createResults(self, ssname, jobResult, additionalJobData, runtime_data):
        beta, error, labels, labels_predicted = jobResult
        results = Results(ssID=ssname, elements=self.results_elements)
        # get single degree of freedom
        dof0 = self.parameters['global_degrees_of_freedom'][0]
        # write single error value
        results['Classification Error'] = dict()
        results['Classification Error'][dof0] = error
        if self.parameters['return_predictions']:
            # ---- calculate confusion matrix elements for OLS job
            orig = [numpy.sign(l) for l in labels]
            pred = [numpy.sign(l) for l in labels_predicted]
            tp, tn, fp, fn = calculateConfusionMatrix(orig, pred)
            # ---- calculate average confusion matrix elements and MCC for OLS job
            mcc = calculateMCC(tp, tn, fp, fn)
            results['CM MCC'] = dict()
            results['CM MCC'][dof0] = (tp, tn, fp, fn, mcc)
            #
            samples = additionalJobData['samples']
            #
            results['Predictions'] = dict()
            results['Predictions'][dof0] = dict()
            results['Predictions'][dof0]['orig_labels'] = [numpy.sign(l) for l in labels]
            results['Predictions'][dof0]['pred_labels'] = [numpy.sign(l)[0] for l in labels_predicted]
            results['Predictions'][dof0]['orig_samples'] = samples
        # store model
        results['Beta'] = beta
        # prepare space for selection results
        results['Selection'] = dict()
        # store selected runtime information
        results[RESULTS_RUNTIME_KEY]['techID'] = runtime_data['techID']
        # we generate no plots here
        return results


# ---- L1L2_RLS classifier

def l1l2_rls_job_wrapper(*args):
    r"""
Wrapper job function for :func:`l1l2py.algorithms.ridge_regression`. This function
transposes data subset if the dimensions do not match with labels vector, creates
training and test splits based on supplied index sets, performs the call for each
value of lambda parameter, calculates errors on training and test splits with
supplied error function. See
`l1l2py documentation <http://slipguru.disi.unige.it/Software/L1L2Py/algorithms.html#regularization-algorithms>`__
for more details.

Parameters
----------
data : :class:`numpy.ndarray`
    data subset to be processed

labels : :class:`numpy.ndarray`
    associated label information to be processed

calls : dict
    dictionary that contains the information necessary for each call:
        'splits'->i->'train_idxs' (tuple)
            index set for training part of split 'i', obtained either from 'ext_split_sets' technique parameter or generated
        'splits'->i->'test_idxs'
            index set for test part of split 'i', obtained either from 'ext_split_sets' technique parameter or generated
        'error_func' (callable)
            callable used as error function
        'data_normalizer' (callable)
            callable used to normalize data subset
        'labels_normalizer' (callable)
            callable used to normalize label values
        'return_predictions' (boolean)
            if predictions shall be returned
        'lambda_range' (tuple of float)
            range of values of lambda parameter calculated from input technique parameters

Returns
-------
results : dict
    dictionary of unformatted results:
        i->'beta' (tuple of float)
            solution of ridge regression for split 'i', for each lambda value
        i->'error_ts' (tuple of float)
            error calculated on test part of split 'i', for each lambda value
        i->'error_tr' (tuple of float)
            error calculated on training part of split 'i', for each lambda value
        i->'pred' (tuple of :class:`numpy.ndarray`)
            labels predicted with the obtained solution for split 'i', for each lambda value
        i->'min_err_ts'
            minimum value of error in 'error_ts'
        i->'min_err_ts_pred'
            predicted labels associated with 'min_err_ts'
    """
    data, labels, calls = args
    # try to transpose if dimensions do not match
    if data.shape[0] != labels.shape[0]:
        data = data.T
    lambda_range = calls['lambda_range']
    error_func = calls['error_func']
    data_normalizer = calls['data_normalizer']
    labels_normalizer = calls['labels_normalizer']
    results = dict()
    for i, sdata in calls['splits'].iteritems():
        train_idxs = sdata['train_idxs']
        test_idxs = sdata['test_idxs']
        Xtr, Ytr = data[train_idxs, :], labels[train_idxs, :]
        Xts, Yts = data[test_idxs, :], labels[test_idxs, :]
        if not data_normalizer is None:
            Xtr, Xts = data_normalizer(Xtr, Xts)
        if not labels_normalizer is None:
            Ytr, Yts = labels_normalizer(Ytr, Yts)
        results[i] = dict()
        results[i]['beta'] = list()
        results[i]['error_ts'] = list()
        results[i]['error_tr'] = list()
        results[i]['pred'] = list()

        for lambda_ in lambda_range:
            # calculate beta
            beta = l1l2py.algorithms.ridge_regression(Xtr, Ytr, lambda_)
            results[i]['beta'].append(beta)
            # calculate error on test set
            labels_predicted_ts = numpy.dot(Xts, beta)
            error_ts = error_func(Yts, labels_predicted_ts)
            labels_predicted_tr = numpy.dot(Xtr, beta)
            error_tr = error_func(Ytr, labels_predicted_tr)

            error_tr = error_func(Ytr, labels_predicted_ts)

            results[i]['error_ts'].append(error_ts)
            results[i]['error_tr'].append(error_tr)
            results[i]['pred'].append(labels_predicted_ts)

        # collect all errors to find a minimum
        errs = numpy.array(results[i]['error_ts'])
        # identify all minimum values
        # NOTE: from this call we obtain at least one value
        imins = numpy.where(errs == errs.min())[0]

        # NOTE: the following code will be cleaned after unit testing is completed
#        if len(imins) > 1:
#            # multiple minimum errors found
#            # collect all predictions associated with multiple minimum errors
#            # and check if they are equal
#            tpred = [list(results[i]['pred'][idx].ravel()) for idx in imins]
#
#            # we will write consensus prediction vector here, together with
#            # information if component was randomized, as vector of tuples
#            # (sign, randomized?)
#            consensus_pred = [None] * len(tpred[0])
#
#            # in each "vertical slice" of tpred we see predicted label sign for each
#            # sample; we select dominant sign as consensus
#            for cidx in range(len(tpred[0])):
#                vs = list(numpy.sign([tpred[ridx][cidx] for ridx in range(len(tpred))]))
#                # count signs as they appear in vertical slice
#                c = collections.defaultdict(int)
#                for s in vs:
#                    c[s] += 1
#                # construct table of counts for -1 and 1
#                counts = [0, 0]
#                try:
#                    counts[0] = c[float(-1)]
#                except KeyError:
#                    pass
#                try:
#                    counts[1] = c[float(1)]
#                except KeyError:
#                    pass
#                # do we randomize sign choice at the end?
#                randomized = False
#                # determine which sign value is dominant
#                if counts[0] > counts[1]:
#                    # -1
#                    choice = -1.0
#                elif counts[0] < counts[1]:
#                    # 1
#                    choice = 1.0
#                else:
#                    # equal counts, randomize choice and mark this fact
#                    choice = random.choice((-1.0, 1.0))
#                    randomized = True
#                # store consensus information
#                consensus_pred[cidx] = (choice, randomized)
#            # obtain final consensus prediction
#            prediction = [p[0] for p in consensus_pred]
#        else:
#            # here we have only one prediction
#            min_err_ts_idx = imins[0]
#            pr = results[i]['pred'][min_err_ts_idx]
#            # there was no need for actual consensus, mark it with None
#            consensus_pred = [(float(p), None) for p in pr]
#            # store prediction itself
#            prediction = [float(p) for p in pr]

#        # store single minimum error value
#        results[i]['min_err_ts'] = next(iter(set(imins)))
#        # store predictions associated with minimum error
#        results[i]['min_err_ts_pred'] = prediction
#        # store also consensus information if applicable
#        results[i]['min_err_ts_consensus_pred'] = consensus_pred

        # take leftmost error value (i.e. produced for smallest lambda value)
        # NOTE: we traverse lambda range in increasing order so this is safe
        # NOTE: from previous call we obtain at least one value so this is safe
        min_err_ts_idx = imins[0]
        # store error value itself
        results[i]['min_err_ts'] = errs[min_err_ts_idx]
        # store associated prediction vector
        results[i]['min_err_ts_pred'] = [float(l) for l in results[i]['pred'][min_err_ts_idx]]

    return results

class L1L2_RLS(Technique):
    r"""
Classifier based on :func:`l1l2py.algorithms.ridge_regression`, called with range
of `mu` values (also dubbed 'lambda' here). It uses l1l2py v1.0.5. This technique
produces training and test splits. It can be configured with the following parameters:

    * 'error_func' (callable) -- callable used as error function
    * 'return_predictions' (boolean) -- if predictions shall be returned
    * 'external_k' (int) -- number of splits to make
    * 'lambda_min' (float) -- minimum value of lambda parameter range
    * 'lambda_max' (float) -- maximum value of lambda parameter range
    * 'lambda_number' (int) -- number of values of lambda parameter range
    * 'lambda_range_type' (string) -- type of lambda parameter range to generate
        ('geometric'/'linear')
    * 'lambda_range' (iterable of float) -- custom lambda parameter values to use
        (None if not used)
    * 'data_normalizer' (callable) -- callable used to normalize data subset
    * 'labels_normalizer' (callable) -- callable used to normalize label values
    * 'ext_split_sets' (None) -- placeholder parameter for pre--computed splits (if any)

The configuration parameters are interpreted once, during initialization. This
technique uses single virtual degree of freedom (DOF). The following
:class:`~kdvs.fw.Stat.Results` elements are produced:

    * 'Classification Error' (float) -- classification error for all DOFs (based on 'Avg Err TS')
    * 'Avg Err TS' (:class:`numpy.ndarray`) -- mean of error obtained on test splits
    * 'Std Err TS' (:class:`numpy.ndarray`) -- standard deviation of error obtained on test splits
    * 'Med Err TS' (:class:`numpy.ndarray`) -- median of error obtained on test splits
    * 'Var Err TS' (:class:`numpy.ndarray`) -- variance of error obtained on test splits
    * 'Avg Err TR' (:class:`numpy.ndarray`) -- mean of error obtained on training splits
    * 'Std Err TR' (:class:`numpy.ndarray`) -- standard deviation of error obtained on training splits
    * 'Med Err TR' (:class:`numpy.ndarray`) -- median of error obtained on training splits
    * 'Var Err TR' (:class:`numpy.ndarray`) -- variance of error obtained on training splits
    * 'Err TS' (:class:`numpy.ndarray`) -- individual errors obtained for all test splits
    * 'Err TR' (:class:`numpy.ndarray`) -- individual errors obtained for all training splits
    * 'CM MCC' (tuple: (int, int, int, int, float)) -- the number of: true positives, true negatives, false positives, false negatives, and Matthews Correlation Coefficient,
    * 'DofExt' (dict) -- many result bits depending of individual DOF, including:
        predictions, model, numbers of: true positives, true negatives, false positives, false negatives,
        Matthews Correlation Coefficient (some of them are exposed separately)
    * 'Predictions' (dict) -- if 'return_predictions' was True, the dictionary:

        { DOF_name: {
        'orig_labels' : iterable of original labels in numerical format (:data:`numpy.sign`),
        'pred_labels' : iterable of predicted labels in numerical format (:data:`numpy.sign`),
        'orig_samples' : iterable of original samples
        } }

This technique creates empty 'Selection' Results element. This technique produces
single :class:`~kdvs.fw.Job.Job` instance. This technique generates two boxplot
error plots (via :class:`L1L2ErrorBoxplotMuGraph`) for training and test splits.

See Also
--------
l1l2_rls_job_wrapper
    """
    _version = '1.0.5'
    _rls_parameters = (
        #
        'error_func', 'return_predictions', 'external_k',
        # lambda min, max, number, range
        'lambda_min', 'lambda_max', 'lambda_number', 'lambda_range_type',
        # specific lambda range if desired, None otherwise
        'lambda_range',
        # normalizers
        'data_normalizer', 'labels_normalizer',
        # placeholder for external splits
        'ext_split_sets',
        )
    _global_parameters = DEFAULT_GLOBAL_PARAMETERS
    _l1l2_rls_result_elements = (
        'Avg Err TS', 'Std Err TS', 'Med Err TS', 'Var Err TS',
        'Avg Err TR', 'Std Err TR', 'Med Err TR', 'Var Err TR',
        'Err TS', 'Err TR',
        'CM MCC', 'DofExt',
        )
    _LOG_PREFIX = '[L1L2_RLS]'

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    keyworder parameters to configure this technique; refer to the documentation for
    extensive list

Raises
------
Error
    if l1l2py library is not present, or a wrong version of l1l2py is present
        """
        verifyDepModule('l1l2py')
        if self._verify_version():
            super(L1L2_RLS, self).__init__(list(itertools.chain(self._rls_parameters, self._global_parameters)), **kwargs)
        else:
            raise Error('L1L2Py version "%s" must be provided to use this class!' % self._version)
        self.results_elements.extend(DEFAULT_RESULTS)
        self.results_elements.extend(DEFAULT_CLASSIFICATION_RESULTS)
        self.results_elements.extend(DEFAULT_SELECTION_RESULTS)
        if self.parameters['return_predictions']:
            self.results_elements.append('Predictions')
        self.results_elements.extend(self._l1l2_rls_result_elements)

    def createJob(self, ssname, data, labels, additionalJobData={}):
        r"""
Create single :class:`~kdvs.fw.Job.Job` instance. Splits are created during job
execution. The number of splits is taken from the value of the parameter 'external_k'.
If value of the parameter 'ext_split_sets' is not None, index sets specified
there will be used across all splits. Otherwise, new index sets will be generated
for each split with :func:`l1l2py.tools.stratified_kfold_splits`.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

data : :class:`numpy.ndarray`
    data subset to be processed

labels : :class:`numpy.ndarray`
    associated label information to be processed

additionalJobData : dict
    any additional information that will be associated with each job produced;
    empty dictionary by default

Returns
-------
(jID, job) : string, :class:`~kdvs.fw.Job.Job`
    tuple of the following: custom job ID (ssname in this case), and Job instance to be executed

Notes
-----
Proper order of data and labels must be ensured in order for the technique to work.
Typically, subsets are generated according to samples order specified within the
primary data set; labels must be in the same order. By definition, KDVS does not
check this.
        """
        super(L1L2_RLS, self).createJob(ssname, data, labels)
        calls = self._prepareRLScall(data, labels)
        external_k = self.parameters['external_k']
        ext_split_sets = self.parameters['ext_split_sets']
        jobData = {
            'depfuncs' : (),
            'modules' : ('l1l2py', 'numpy', 'os'),
            'external_k' : external_k,
            'ext_split_sets' : ext_split_sets,
            'ssname' : ssname,
            'calls' : calls,
            'data_shape' : data.shape,
            'labels' : labels,
        }
        jobData.update(additionalJobData)
        job = Job(call_func=l1l2_rls_job_wrapper, call_args=(data, labels, calls), additional_data=jobData)
        # make custom ID
        customID = '%s' % (ssname)
        # yield always pair (customID, job)
        yield (customID, job)

    def produceResults(self, ssname, jobs, runtime_data):
        r"""
Produce :class:`~kdvs.fw.Stat.Results` instance for exactly one job result.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

jobs : iterable of :class:`~kdvs.fw.Job.Job`
    executed job(s) that contain(s) raw results

runtime_data : dict
    data collected in runtime that shall be included in the final Results instance

Returns
-------
final_results : :class:`~kdvs.fw.Stat.Results`
    Results instance that contains final results of the technique

Raises
------
Error
    if more than one jobs were specified
        """
        # we expect single job here
        if len(jobs) > 1:
            raise Error('%s can produce results for single job only!' % self.__class__)
        results = self._createResults(ssname, jobs[0].result, jobs[0].additional_data, runtime_data)
        self._producePlots(ssname, jobs[0].result, jobs[0].additional_data, results)
        return results

    def _createResults(self, ssname, jobResult, additionalJobData, runtime_data):
        calls = additionalJobData['calls']
        samples = additionalJobData['samples']
        labels = additionalJobData['labels']
        data_shape = additionalJobData['data_shape']
        #
        results = Results(ssID=ssname, elements=self.results_elements)
        external_k = self.parameters['external_k']
        assert range(external_k) == sorted(jobResult.keys())
        dofs = self.parameters['global_degrees_of_freedom']
        nof_dofs = len(dofs)
        err_ts_l = list()
        err_tr_l = list()
        # get error values for all splits
        for i, sdata in jobResult.iteritems():
            error_ts = sdata['error_ts']
            error_tr = sdata['error_tr']
            err_ts_l.append(error_ts)
            err_tr_l.append(error_tr)
        err_ts_l = numpy.asarray(err_ts_l)
        err_tr_l = numpy.asarray(err_tr_l)
        results['Err TS'] = err_ts_l
        results['Err TR'] = err_tr_l
        # ---- calculate statistics
        # NOTE: in all of the cases below we end up with single value for single
        # null DOF, and some shape adjustments are being made to reflect this;
        # this should help the design of proper reporters as similar to
        # L1L2_L1L2 ones (or even using the same ones)
        # 1. mean
        m_avg_err_ts = numpy.mean(err_ts_l, axis=1)
        avg_err_ts = numpy.mean(m_avg_err_ts, keepdims=True)
        m_avg_err_tr = numpy.mean(err_tr_l, axis=1)
        avg_err_tr = numpy.mean(m_avg_err_tr, keepdims=True)
        # 2. standard deviation
        m_std_err_ts = numpy.std(err_ts_l, axis=1)
        std_err_ts = numpy.std(m_std_err_ts, keepdims=True)
        m_std_err_tr = numpy.std(err_tr_l, axis=1)
        std_err_tr = numpy.std(m_std_err_tr, keepdims=True)
        # 3. median error
        m_med_err_ts = numpy.median(err_ts_l, axis=1)
        med_err_ts = numpy.array(numpy.median(m_med_err_ts), ndmin=1)
        m_med_err_tr = numpy.median(err_tr_l, axis=1)
        med_err_tr = numpy.array(numpy.median(m_med_err_tr), ndmin=1)
        # 4. variation
        m_var_err_ts = numpy.var(err_ts_l, axis=1)
        var_err_ts = numpy.var(m_var_err_ts, keepdims=True)
        m_var_err_tr = numpy.var(err_tr_l, axis=1)
        var_err_tr = numpy.var(m_var_err_tr, keepdims=True)
        # store statistics
        results['Avg Err TS'] = avg_err_ts
        results['Std Err TS'] = std_err_ts
        results['Med Err TS'] = med_err_ts
        results['Var Err TS'] = var_err_ts
        results['Avg Err TR'] = avg_err_tr
        results['Std Err TR'] = std_err_tr
        results['Med Err TR'] = med_err_tr
        results['Var Err TR'] = var_err_tr
        # store classification error
        results['Classification Error'] = dict(zip(dofs, list(avg_err_ts)))
#        # ---- data orientation: (variables, samples)
#        numof_vars = data_shape[0]
        numof_samples = data_shape[1]
        dofext = dict()
        for dof_idx in range(nof_dofs):
            dofext[dof_idx] = dict()
            tp = tn = fp = fn = 0
            for i, cdata in calls['splits'].iteritems():
                output = jobResult[i]
                dofext[dof_idx][i] = dict()
                if self.parameters['return_predictions']:
                    try:
                        test_idxs = cdata['test_idxs']
                        origLabels = labels
                        origSamples = [samples[ti] for ti in test_idxs]
                        orig = list(numpy.sign([l for l in origLabels[test_idxs, :]]))
                        pred = list(numpy.sign([l for l in output['min_err_ts_pred']]))
                        ttp, ttn, tfp, tfn = calculateConfusionMatrix(orig, pred)
                        tp += ttp
                        tn += ttn
                        fp += tfp
                        fn += tfn
                        dofext[dof_idx][i]['orig_samples'] = origSamples
                        dofext[dof_idx][i]['orig_labels'] = orig
                        dofext[dof_idx][i]['pred_labels'] = pred
                    except KeyError:
                        pass
                # ---- store model for external split
                dofext[dof_idx][i]['model'] = output['beta']
            if self.parameters['return_predictions']:
                # ---- calculate average confusion matrix elements and MCC for each dof
                mcc = calculateMCC(tp, tn, fp, fn)
                dofext[dof_idx]['cm_mcc'] = (tp, tn, fp, fn, mcc)
        # ---- store DofExt results
        results['DofExt'] = dofext
        # ---- store predictions
        if self.parameters['return_predictions']:
            predictions = dict()
            for dof_idx in range(nof_dofs):
                dof = dofs[dof_idx]
                predictions[dof] = dict()
                predictions[dof]['orig_labels'] = [None] * numof_samples
                predictions[dof]['pred_labels'] = [None] * numof_samples
                predictions[dof]['orig_samples'] = [None] * numof_samples
                for i, cdata in calls['splits'].iteritems():
                    test_idxs = cdata['test_idxs']
                    for ti, ui in enumerate(test_idxs):
                        predictions[dof]['orig_labels'][ui] = dofext[dof_idx][i]['orig_labels'][ti]
                        predictions[dof]['pred_labels'][ui] = dofext[dof_idx][i]['pred_labels'][ti]
                        predictions[dof]['orig_samples'][ui] = dofext[dof_idx][i]['orig_samples'][ti]
                # make sure that indexing reconstruction was correct
                assert list(predictions[dof]['orig_samples']) == list(samples)
                assert list(predictions[dof]['orig_labels']) == list(labels)
            results['Predictions'] = predictions
        # ---- store MCC related information
        cm_mcc = dict()
        for dof_idx in range(nof_dofs):
            cm_mcc[dofs[dof_idx]] = dofext[dof_idx]['cm_mcc']
        results['CM MCC'] = cm_mcc
        # ---- store calls data
        # TODO: store calls here or only with jobs themselves?
#        result['Calls'] = calls
        # ---- prepare space for selection results
        results['Selection'] = dict()
        # store selected runtime information
        results[RESULTS_RUNTIME_KEY]['techID'] = runtime_data['techID']
        return results

    def _producePlots(self, ssname, jobResult, additionalJobData, resultInst):
#        calls = additionalJobData['calls']
#        lambda_range = calls['lambda_range']
        # we store generated plots here
        plots = resultInst[RESULTS_PLOTS_ID_KEY]
        # ---- prediction error on TS
        err_ts = resultInst['Err TS']
        # create file name
        pred_error_ts_plot_name = '%s_prediction_error_ts' % ssname
        pred_error_ts_plot_full_name = '%s%s%s' % (pred_error_ts_plot_name, os.path.extsep, MATPLOTLIB_GRAPH_BACKEND_PDF['format'])
        # create physical plot
        pred_error_ts_plot = L1L2ErrorBoxplotMuGraph()
        pred_error_ts_plot.configure(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        pred_error_ts_plot.create(**{
            'errors' : err_ts,
            # NOTE: null DOF here given as 1 so log10 yields 0
            'mu_range' : (1,),
            'plot_title' : 'TEST ERROR',
            })
        pred_error_ts_plot_content = pred_error_ts_plot.plot(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        # add to plots
        plots[pred_error_ts_plot_full_name] = pred_error_ts_plot_content
        # ---- prediction error on TR
        err_tr = resultInst['Err TR']
        # create file name
        pred_error_tr_plot_name = '%s_prediction_error_tr' % ssname
        pred_error_tr_plot_full_name = '%s%s%s' % (pred_error_tr_plot_name, os.path.extsep, MATPLOTLIB_GRAPH_BACKEND_PDF['format'])
        # create physical plot
        pred_error_tr_plot = L1L2ErrorBoxplotMuGraph()
        pred_error_tr_plot.configure(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        pred_error_tr_plot.create(**{
            'errors' : err_tr,
            # NOTE: null DOF here given as 1 so log10 yields 0
            'mu_range' : (1,),
            'plot_title' : 'TRAINING ERROR',
            })
        pred_error_tr_plot_content = pred_error_tr_plot.plot(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        # add to plots
        plots[pred_error_tr_plot_full_name] = pred_error_tr_plot_content

    def _prepareRLScall(self, data, labels):
        # try to transpose if dimensions do not match
        if data.shape[0] != labels.shape[0]:
            data = data.T
        calls = dict()
        # obtain lambda range
        lambda_range = self._determine_lambda_range()
        # prepare external splits
        ext_split_sets = self.parameters['ext_split_sets']
        if ext_split_sets is None:
            ext_split_sets = l1l2py.tools.stratified_kfold_splits(labels, self.parameters['external_k'])
        calls['splits'] = dict()
        for i, (train_idxs, test_idxs) in enumerate(ext_split_sets):
            calls['splits'][i] = dict()
            calls['splits'][i]['train_idxs'] = train_idxs
            calls['splits'][i]['test_idxs'] = test_idxs
        calls['error_func'] = self.parameters['error_func']
        calls['data_normalizer'] = self.parameters['data_normalizer']
        calls['labels_normalizer'] = self.parameters['labels_normalizer']
        calls['return_predictions'] = self.parameters['return_predictions']
        calls['lambda_range'] = lambda_range
        return calls

    def _determine_lambda_range(self):
        # determine lambda parameter range
        # it is common for all submatrices; we can also specify custom one
        lr = self.parameters['lambda_range']
        if lr is None:
            lambda_min = self.parameters['lambda_min']
            lambda_max = self.parameters['lambda_max']
            lambda_number = self.parameters['lambda_number']
            lambda_range_type = self.parameters['lambda_range_type']
            if lambda_range_type == 'geometric':
                rf = l1l2py.tools.geometric_range
            elif lambda_range_type == 'linear':
                rf = l1l2py.tools.linear_range
            lambda_range = rf(lambda_min, lambda_max, lambda_number)
            return lambda_range
        else:
            if not isListOrTuple(lr):
                raise Error('List or tuple expected! (got %s)' % lr.__class__)
            return lr

    def _verify_version(self):
        return l1l2py.__version__ == self._version



# ---- L1L2_L1L2 classifier/feature selector

def l1l2_l1l2_job_wrapper(*args):
    r"""
Wrapper job function for :func:`l1l2py.model_selection`. This function passes
all properly prepared arguments directly to the call. See
`l1l2py documentation <http://slipguru.disi.unige.it/Software/L1L2Py/core.html#complete-model-selection>`__
for more details.
    """
    return l1l2py.model_selection(*args)


class L1L2_L1L2(Technique):
    r"""
Classifier and variable selector that enforces model sparsity, based on
:func:`l1l2py.model_selection`, that utilizes three ranges of parameters: 'tau', 'lambda',
and 'mu'. 'Tau' and 'lambda' parameters are used internally to control selection
of best statistical model. 'Tau' and 'mu' values are not specified directly (they must be
found computationally), but user has the control of how they scale across the requested
range. 'Lambda' values may be specified directly. Values of 'mu' parameter are
degrees of freedom (DOF) for this technique (the actual DOF identifiers used are
configurable). It uses l1l2py v1.0.5. This technique produces two layers of
training and test splits: internal ones (hidden), and external ones
(managed by this technique directly).

It can be configured with the following parameters:
    * 'external_k' (int) -- number of external splits to make (within the control of the technique)
    * 'internal_k' (int) -- number of internal splits to make (beyond the control of the technique, implemented in l1l2py)
    * 'tau_min_scale' (float) -- minimum scaling factor for the tau parameter range
    * 'tau_max_scale' (float) -- maximum scaling factor for the tau parameter range
    * 'tau_number' (int) -- number of values of tau parameter range
    * 'tau_range_type' (string) -- type of tau parameter range to generate
        ('geometric'/'linear')
    * 'mu_scaling_factor_min' (float) -- minimum scaling factor for the mu parameter range
    * 'mu_scaling_factor_max' (float) -- maximum scaling factor for the mu parameter range
    * 'mu_number' (int) -- number of values of mu parameter range
    * 'mu_range_type' (string) -- type of mu parameter range to generate
        ('geometric'/'linear')
    * 'lambda_min' (float) -- minimum value of lambda parameter range
    * 'lambda_max' (float) -- maximum value of lambda parameter range
    * 'lambda_number' (int) -- number of values of lambda parameter range
    * 'lambda_range_type' (string) -- type of lambda parameter range to generate
        ('geometric'/'linear')
    * 'lambda_range' (iterable of float) -- custom lambda parameter values to use
        (None if not used)
    * 'error_func' (callable) -- callable used as error function for external splits
    * 'cv_error_func' (callable) -- callable used as error function for internal splits
    * 'sparse' (boolean) -- if most sparsed solution shall be enforced (exclusive with 'regularized')
    * 'regularized' (boolean) -- if most regularized solution shall be enforced (exclusive with 'sparse')
    * 'return_predictions' (boolean) -- if predictions shall be returned
    * 'data_normalizer' (callable) -- callable used to normalize data subset
    * 'labels_normalizer' (callable) -- callable used to normalize label values
    * 'ext_split_sets' (None) -- placeholder parameter for pre--computed splits (if any)

The configuration parameters are interpreted once, during initialization.

The following :class:`~kdvs.fw.Stat.Results` elements are produced:

    * 'Classification Error' (float) -- classification error for all DOFs (i.e. 'mu' values) (based on 'Avg Err TS')
    * 'Avg Err TS' (numpy.ndarray) -- mean of error obtained on external test splits
    * 'Std Err TS' (numpy.ndarray) -- standard deviation of error obtained on external test splits
    * 'Med Err TS' (numpy.ndarray) -- median of error obtained on external test splits
    * 'Var Err TS' (numpy.ndarray) -- variance of error obtained on external test splits
    * 'Avg Err TR' (numpy.ndarray) -- mean of error obtained on external training splits
    * 'Std Err TR' (numpy.ndarray) -- standard deviation of error obtained on external training splits
    * 'Err TS' (numpy.ndarray) -- all individual errors obtained for all external and internal test splits
    * 'Err TR' (numpy.ndarray) -- all individual errors obtained for all external and internal training splits
    * 'MuExt' (dict) -- many result bits depending of individual DOF (i.e. 'mu' value)
        and external split, including: predictions, model, numbers of: true positives, true negatives,
        false positives, false negatives, Matthews Correlation Coefficient (some of them
        are exposed separately)
    * 'Calls' (dict) -- all information used to prepare individual l1l2py calls
        (exposed for debug purpose)
    * 'Avg Kfold Err TS' (numpy.ndarray) -- mean of errors obtained for internal test splits
    * 'Avg Kfold Err TR' (numpy.ndarray) -- mean of errors obtained for internal training splits
    * 'Max Tau' (int) -- index of 'tau' value in tau parameter range that was used to produce the best solution
    * 'CM MCC' (tuple: (int, int, int, int, float)) -- the number of: true positives, true negatives, false positives, false negatives, and Matthews Correlation Coefficient
    * 'Predictions' (dict) -- if 'return_predictions' was True, the dictionary:

        { DOF_name: {
        'orig_labels' : iterable of original labels in numerical format (:data:`numpy.sign`),
        'pred_labels' : iterable of predicted labels in numerical format (:data:`numpy.sign`),
        'orig_samples' : iterable of original samples
        } }

This technique creates empty 'Selection' Results element. This technique produces
as many Job instances as the number of external splits (each external split is
processed in separate Job).

This technique generates the following plots:

    * for each DOF (i.e. 'mu' value), surface of error for external test splits in (tau,lambda) parameter space
        (via :class:`L1L2KfoldErrorsGraph`)
    * single surface of average error across all external and internal test splits in (tau,lambda) parameter space
        (via :class:`L1L2KfoldErrorsGraph`)
    * single boxplot of error obtained on external test splits for all 'mu' values
        (via :class:`L1L2ErrorBoxplotMuGraph`)
    * single boxplot of error obtained on external training splits for all 'mu' values
        (via :class:`L1L2ErrorBoxplotMuGraph`)

See Also
--------
l1l2py.algorithms.l1_bound
    """
    _version = '1.0.5'
    _global_parameters = DEFAULT_GLOBAL_PARAMETERS
    _l1l2_parameters = ('external_k', 'internal_k',
                     # tau min, max, number, range
                     'tau_min_scale', 'tau_max_scale', 'tau_number', 'tau_range_type',
                     # mu min, max, number, range
                     'mu_scaling_factor_min', 'mu_scaling_factor_max', 'mu_number', 'mu_range_type',
                     # lambda min, max, number, range
                     'lambda_min', 'lambda_max', 'lambda_number', 'lambda_range_type',
                     # specific lambda range if desired, None otherwise
                     'lambda_range',
                     #
                     'error_func', 'cv_error_func', 'sparse', 'regularized',
                     'return_predictions', 'data_normalizer', 'labels_normalizer',
                     'ext_split_sets')
    _l1l2_result_elements = (
        'Avg Err TS', 'Avg Err TR', 'Std Err TS', 'Std Err TR', 'Med Err TS',
        'Var Err TS', 'MuExt', 'Calls',
        'Err TR', 'Err TS', 'Avg Kfold Err TS', 'Avg Kfold Err TR', 'Max Tau',
        'CM MCC',
        )
    _LOG_PREFIX = '[L1L2_L1L2]'

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    keyworded parameters to configure this technique; refer to the documentation for
    extensive list

Raises
------
Error
    if l1l2py library is not present, or a wrong version of l1l2py is present
        """
        verifyDepModule('l1l2py')
        if self._verify_version():
            super(L1L2_L1L2, self).__init__(list(itertools.chain(self._l1l2_parameters, self._global_parameters)), **kwargs)
        else:
            raise Error('L1L2Py %s must be provided to use this class!' % self._version)
        self.results_elements.extend(DEFAULT_RESULTS)
        self.results_elements.extend(DEFAULT_CLASSIFICATION_RESULTS)
        self.results_elements.extend(DEFAULT_SELECTION_RESULTS)
        if self.parameters['return_predictions']:
            self.results_elements.append('Predictions')
        self.results_elements.extend(self._l1l2_result_elements)

    def createJob(self, ssname, data, labels, additionalJobData={}):
        r"""
Create as many :class:`~kdvs.fw.Job.Job` instances as the number of external
splits (each external split is processed in separated Job). Internal splits are
created from external splits during job execution. The number of external splits
is taken from the value of the parameter 'external_k'. If value of the parameter
'ext_split_sets' is not None, index sets specified there will be used across all
splits. Otherwise, new index sets will be generated for each split with
:func:`l1l2py.tools.stratified_kfold_splits`. All Job instances produced here may be
associated together as 'job group' managed by :class:`~kdvs.fw.Job.JobGroupManager`;
this approach is used in 'experiment' application to keep splits together.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

data : :class:`numpy.ndarray`
    data subset to be processed

labels : :class:`numpy.ndarray`
    associated label information to be processed

additionalJobData : dict
    any additional information that will be associated with each job produced;
    empty dictionary by default

Returns
-------
(jID, job) : string, :class:`~kdvs.fw.Job.Job`
    tuple of the following: custom job ID (in this case, the ID reflect ssname
    and the numerical identifier of external split), and Job instance to be executed

Notes
-----
Proper order of data and labels must be ensured in order for the technique to work.
Typically, subsets are generated according to samples order specified within the
primary data set; labels must be in the same order. By definition, KDVS does not
check this.
        """
        super(L1L2_L1L2, self).createJob(ssname, data, labels)
        calls = self._prepareL1L2call(data, labels)
        external_k = self.parameters['external_k']
        for i in range(external_k):
            jobData = {
                'depfuncs' : (),
                'modules' : ('l1l2py', 'numpy', 'os'),
                'ext_split' : i,
                'ssname' : ssname,
                'calls' : calls,
                'data_shape' : data.shape,
                'labels' : labels,
                }
            jobData.update(additionalJobData)
            job = Job(call_func=l1l2_l1l2_job_wrapper, call_args=calls[i]['call_args'], additional_data=jobData)
            # make custom ID
            customID = '%s_split%d' % (ssname, i)
            # yield always pair (customID, job)
            yield (customID, job)

    def produceResults(self, ssname, jobs, runtime_data):
        r"""
Produce single :class:`~kdvs.fw.Stat.Results` instance for job results coming from
all external splits performed on the same data subset. To produce the final Results
instance, all job results must be completed correctly; sometimes this may not be
the case (see l1l2py documentation for more details).

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

jobs : iterable of :class:`~kdvs.fw.Job.Job`
    executed job(s) that contain(s) raw results

runtime_data : dict
    data collected in runtime that shall be included in the final Results instance

Returns
-------
final_results : :class:`~kdvs.fw.Stat.Results`
    Results instance that contains final results of the technique

Raises
------
Error
    if job results were generated for more than one data subset
Error
    if multiple preparatory data instances ('calls') were detected across jobs
Error
    if mutiple shapes of split matrices were detected across jobs
Warn
    if some jobs finished with an error (on l1l2py side)
Warn
    if the result has not been produced for some jobs (other reasons) 
        """
        # ---- we expect that partial results for all external splits are produced
        external_k = self.parameters['external_k']
        ext_splits = range(external_k)
        commonSSName = set()
        splits = set()
        refSplits = set(ext_splits)
        for job in jobs:
            commonSSName.add(job.additional_data['ssname'])
            splits.add(job.additional_data['ext_split'])
        # process stopping criterions
        if len(commonSSName) > 1:
            raise Error('%s Jobs for %s are generated for different subsets! (%s)' % (self._LOG_PREFIX, ssname, list(commonSSName)))
        else:
            ssname = next(iter(commonSSName))
        # ---- verify that 'calls' instances are identical
        calls = None
        all_calls = [j.additional_data['calls'] for j in jobs]
        group_calls = [g for g, _ in itertools.groupby(all_calls)]
        if len(group_calls) == 1:
            calls = group_calls[0]
        else:
            raise Error('%s Multiple L1L2 preparatory data instances found for %s! Make sure that exactly one instance is distributed with each job!' % (self._LOG_PREFIX, ssname))
        # ---- verify that data shapes are identical
        data_shape = None
        all_ds = set([j.additional_data['data_shape'] for j in jobs])
        if len(all_ds) == 1:
            data_shape = next(iter(all_ds))
        else:
            raise Error('%s Multiple data shapes found for %s! Make sure that exactly one instance is distributed with each job!' % (self._LOG_PREFIX, ssname))
        # process non-stopping criterions
        remSplits = refSplits - splits
        if len(remSplits) > 0:
            raise Warn('%s Not all jobs for %s (external splits) were generated! (missing: %s). Check for possible job exceptions!' % (self._LOG_PREFIX, ssname, sorted(list(remSplits))))
        not_produced = [j.additional_data['ext_split'] for j in jobs if j.result == NOTPRODUCED]
        if len(not_produced) > 0:
            raise Warn('%s Not all jobs for %s (external splits) produced raw results! (missing: %s). Check for possible job exceptions!' % (self._LOG_PREFIX, sorted(not_produced)))
        # obtain samples instance (single one is sufficient)
        samples = jobs[0].additional_data['samples']
        # obtain labels instance (single one is sufficient)
        labels = jobs[0].additional_data['labels']
        # proceed with generating Results
        resultsInst = Results(ssID=ssname, elements=self.results_elements)
        # ---- sort jobs according to splits
        splitJobs = list()
        for i in ext_splits:
            for j in jobs:
                if i == j.additional_data['ext_split']:
                    splitJobs.append(j)
        # ---- get raw output for each job
        outputs = [j.result for j in splitJobs]
        # ---- postprocess external splits
        self._postprocessExtSplits(splitJobs, outputs, calls, data_shape, samples, labels, resultsInst)
        # ---- produce plots
        self._produceExtSplitsPlots(ssname, outputs, calls, resultsInst)
        # ---- store selected runtime information
        resultsInst[RESULTS_RUNTIME_KEY]['techID'] = runtime_data['techID']
        return resultsInst

    def _postprocessExtSplits(self, splitJobs, outputs, calls, data_shape, samples, labels, result):
        external_k = self.parameters['external_k']
        ext_splits = range(external_k)
        # ---- obtain average results from raw outputs
        lambda_range = calls['lambda_range']
        tau_range = calls['tau_range']
        mu_range = calls['mu_range']
        mu_number = len(mu_range)
        max_tau = len(tau_range)
        kfold_err_ts = list()
        kfold_err_tr = list()
        err_ts = list()
        err_tr = list()
        for out in outputs:
            valid_tau = out['kcv_err_ts'].shape[0]
            max_tau = numpy.min((valid_tau, max_tau))
            kfold_err_ts.append(out['kcv_err_ts'])
            kfold_err_tr.append(out['kcv_err_tr'])
            err_ts.append(out['err_ts_list'])
            err_tr.append(out['err_tr_list'])
        # collect avg errors
        avg_kfold_err_ts = numpy.empty((len(kfold_err_ts), max_tau, len(lambda_range)))
        avg_kfold_err_tr = numpy.empty((len(kfold_err_tr), max_tau, len(lambda_range)))
        for i, (tmp_ts, tmp_tr) in enumerate(zip(kfold_err_ts, kfold_err_tr)):
            avg_kfold_err_ts[i] = tmp_ts[:max_tau, :]
            avg_kfold_err_tr[i] = tmp_tr[:max_tau, :]
        avg_kfold_err_ts = avg_kfold_err_ts.mean(axis=0)
        avg_kfold_err_tr = avg_kfold_err_tr.mean(axis=0)
        # retrieve errors for mu range
        m_err_tr = numpy.asarray(err_tr)
        m_err_ts = numpy.asarray(err_ts)
        # ---- calculate statistics
        # 1. mean
        avg_err_ts = m_err_ts.mean(axis=0)
        avg_err_tr = m_err_tr.mean(axis=0)
        # 2. standard deviation
        std_err_ts = m_err_ts.std(axis=0)
        std_err_tr = m_err_tr.std(axis=0)
        # 3. median error
        med_err_ts = numpy.median(m_err_ts, axis=0)
        # 4. variation
        var_err_ts = m_err_ts.var(axis=0)
        #
        result['Avg Err TS'] = avg_err_ts
        result['Avg Err TR'] = avg_err_tr
        result['Std Err TS'] = std_err_ts
        result['Std Err TR'] = std_err_tr
        result['Med Err TS'] = med_err_ts
        result['Var Err TS'] = var_err_ts
        #
        result['Err TS'] = err_ts
        result['Err TR'] = err_tr
        result['Avg Kfold Err TS'] = avg_kfold_err_ts
        result['Avg Kfold Err TR'] = avg_kfold_err_tr
        result['Max Tau'] = max_tau
        # ---- our 'classification error' value
#        result['Classification Error']=avg_err_ts
#        result['Classification Error']=list(avg_err_ts)
        dofs = self.parameters['global_degrees_of_freedom']
        result['Classification Error'] = dict(zip(dofs, list(avg_err_ts)))
        # ---- obtain additional results
        # ---- data orientation: (variables, samples)
        numof_vars = data_shape[0]
        numof_samples = data_shape[1]
        # ---- produce MuExt results
        # ---- obtain predictions, confusion matrix, MCC value, and frequencies
        # ---- NOTE: some of those are possible to obtain only when predictions
        # ----       are returned from l1l2py.model_selection!
        add_result = dict()
        tfreqs = numpy.zeros((mu_number, numof_vars), dtype=numpy.float)
        for mu in range(mu_number):
            add_result[mu] = dict()
            tp = tn = fp = fn = 0
            for i in ext_splits:
                add_result[mu][i] = dict()
                if self.parameters['return_predictions']:
                    # ---- calculate confusion matrix elements for external split
                    try:
                        test_idxs = calls[i]['ext_cv_test_idxs']
                        origLabels = labels
#                        origLabels = splitJobs[i].additional_data['labels']
#                        origSamples = samples[test_idxs, :]
                        origSamples = [samples[ti] for ti in test_idxs]
                        orig = [numpy.sign(l) for l in origLabels[test_idxs, :]]
                        pred = [numpy.sign(l)[0] for l in outputs[i]['prediction_ts_list'][mu]]
                        ttp, ttn, tfp, tfn = calculateConfusionMatrix(orig, pred)
                        tp += ttp
                        tn += ttn
                        fp += tfp
                        fn += tfn
                        add_result[mu][i]['orig_samples'] = origSamples
                        add_result[mu][i]['orig_labels'] = orig
                        add_result[mu][i]['pred_labels'] = pred
                    except KeyError:
                        pass
                # ---- store frequencies for external split
                tfreqs[mu] += numpy.asarray(outputs[i]['selected_list'][mu], dtype=numpy.int)
                # ---- store model for external split
                add_result[mu][i]['model'] = outputs[i]['beta_list'][mu]
            if self.parameters['return_predictions']:
                # ---- calculate average confusion matrix elements and MCC for each mu
                mcc = calculateMCC(tp, tn, fp, fn)
                add_result[mu]['cm_mcc'] = (tp, tn, fp, fn, mcc)
        # ---- normalize frequencies
        freqs = tfreqs / float(external_k)
        add_result['freqs'] = freqs
        # ---- store MuExt results
        result['MuExt'] = add_result
        # ---- store predictions
        if self.parameters['return_predictions']:
            predictions = dict()
            for mu in range(mu_number):
                dof = dofs[mu]
                predictions[dof] = dict()
                predictions[dof]['orig_labels'] = [None] * numof_samples
                predictions[dof]['pred_labels'] = [None] * numof_samples
                predictions[dof]['orig_samples'] = [None] * numof_samples
                for i in ext_splits:
                    test_idxs = calls[i]['ext_cv_test_idxs']
                    for ti, ui in enumerate(test_idxs):
                        predictions[dof]['orig_labels'][ui] = add_result[mu][i]['orig_labels'][ti]
                        predictions[dof]['pred_labels'][ui] = add_result[mu][i]['pred_labels'][ti]
                        predictions[dof]['orig_samples'][ui] = add_result[mu][i]['orig_samples'][ti]
                # make sure that indexing reconstruction was correct
                assert list(predictions[dof]['orig_samples']) == list(samples)
                assert list(predictions[dof]['orig_labels']) == list(labels)
            result['Predictions'] = predictions
        # ---- store MCC related information
        cm_mcc = dict()
        for mu in range(mu_number):
            cm_mcc[dofs[mu]] = add_result[mu]['cm_mcc']
        result['CM MCC'] = cm_mcc
        # ---- store calls data
        # TODO: store calls here or only with jobs themselves?
#        result['Calls'] = calls
        # ---- prepare space for selection results
        result['Selection'] = dict()

    def _produceExtSplitsPlots(self, ssname, outputs, calls, result):
#        calls = result['Calls']
        lambda_range = calls['lambda_range']
        tau_range = calls['tau_range']
        mu_range = calls['mu_range']
        # we store generated plots here
        plots = result[RESULTS_PLOTS_ID_KEY]
        # ---- produce plots for external splits
        # ---- error surface for all individual external splits
        for i, out in enumerate(outputs):
            valid_tau = out['kcv_err_ts'].shape[0]
            # create file name
            plot_name = '%s_avg_kcv_err_%d' % (ssname, i)
            plot_full_name = '%s%s%s' % (plot_name, os.path.extsep, MATPLOTLIB_GRAPH_BACKEND_PDF['format'])
            # create physical plot
            plot = L1L2KfoldErrorsGraph()
            plot.configure(**MATPLOTLIB_GRAPH_BACKEND_PDF)
            plot.create(**{
                'ranges' : (numpy.log10(tau_range[:valid_tau]), numpy.log10(lambda_range)),
                'labels' : ('$log_{10}(\\tau)$', '$log_{10}(\lambda)$'),
                'ts_errors' : out['kcv_err_ts'],
                'tr_errors' : out['kcv_err_tr'],
                'plot_title' : 'EXT. SPLIT %d KCV ERROR vs. TAU, LAMBDA' % i,
                })
            plot_content = plot.plot(**MATPLOTLIB_GRAPH_BACKEND_PDF)
            # add to plots
            plots[plot_full_name] = plot_content
        # ---- avg error surfaces for all external splits
        max_tau = result['Max Tau']
        avg_kfold_err_ts = result['Avg Kfold Err TS']
        avg_kfold_err_tr = result['Avg Kfold Err TR']
        # create file name
        avgplot_name = '%s_avg_kcv_err' % ssname
        avgplot_full_name = '%s%s%s' % (avgplot_name, os.path.extsep, MATPLOTLIB_GRAPH_BACKEND_PDF['format'])
        # create physical plot
        avgplot = L1L2KfoldErrorsGraph()
        avgplot.configure(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        avgplot.create(**{
            'ranges' : (numpy.log10(tau_range[:max_tau]), numpy.log10(lambda_range)),
            'labels' : ('$log_{10}(\\tau)$', '$log_{10}(\lambda)$'),
            'ts_errors' : avg_kfold_err_ts,
            'tr_errors' : avg_kfold_err_tr,
            'plot_title' : 'AVG KCV ERROR vs. TAU, LAMBDA',
            })
        avgplot_content = avgplot.plot(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        # add to plots
        plots[avgplot_full_name] = avgplot_content

        # ---- prediction error on TS
        err_ts = result['Err TS']
        # create file name
        pred_error_ts_plot_name = '%s_prediction_error_ts' % ssname
        pred_error_ts_plot_full_name = '%s%s%s' % (pred_error_ts_plot_name, os.path.extsep, MATPLOTLIB_GRAPH_BACKEND_PDF['format'])
        # create physical plot
        pred_error_ts_plot = L1L2ErrorBoxplotMuGraph()
        pred_error_ts_plot.configure(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        pred_error_ts_plot.create(**{
            'errors' : err_ts,
            'mu_range' : mu_range,
            'plot_title' : 'TEST ERROR vs. MU',
            })
        pred_error_ts_plot_content = pred_error_ts_plot.plot(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        # add to plots
        plots[pred_error_ts_plot_full_name] = pred_error_ts_plot_content

        # ---- prediction error on TR
        err_tr = result['Err TR']
        # create file name
        pred_error_tr_plot_name = '%s_prediction_error_tr' % ssname
        pred_error_tr_plot_full_name = '%s%s%s' % (pred_error_tr_plot_name, os.path.extsep, MATPLOTLIB_GRAPH_BACKEND_PDF['format'])
        # create physical plot
        pred_error_tr_plot = L1L2ErrorBoxplotMuGraph()
        pred_error_tr_plot.configure(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        pred_error_tr_plot.create(**{
            'errors' : err_tr,
            'mu_range' : mu_range,
            'plot_title' : 'TRAINING ERROR vs. MU',
            })
        pred_error_tr_plot_content = pred_error_tr_plot.plot(**MATPLOTLIB_GRAPH_BACKEND_PDF)
        # add to plots
        plots[pred_error_tr_plot_full_name] = pred_error_tr_plot_content

    def _prepareL1L2call(self, data, labels):
        # try to transpose if dimensions do not match
        if data.shape[0] != labels.shape[0]:
            data = data.T
        calls = dict()
        # obtain lambda range
        lambda_range = self._determine_lambda_range()
        # obtain correct tau range
        tau_range = self._calculate_tau_range(data, labels)
        # obtain correct mu range
        mu_range = self._calculate_mu_range(data)
        # prepare external splits
#        ext_cv_sets = l1l2py.tools.stratified_kfold_splits(labels, self.parameters['external_k'])
        ext_split_sets = self.parameters['ext_split_sets']
        if ext_split_sets is None:
            ext_split_sets = l1l2py.tools.stratified_kfold_splits(labels, self.parameters['external_k'])
        # prepare internal splits
#        for i, (train_idxs, test_idxs) in enumerate(ext_cv_sets):
        for i, (train_idxs, test_idxs) in enumerate(ext_split_sets):
            Xtr, Ytr = data[train_idxs, :], labels[train_idxs, :]
            Xts, Yts = data[test_idxs, :], labels[test_idxs, :]
            int_cv_splits = l1l2py.tools.stratified_kfold_splits(Ytr, self.parameters['internal_k'])
            # get call arguments
            call_args = (
                Xtr, Ytr, Xts, Yts,
                mu_range, tau_range, lambda_range,
                int_cv_splits,
                self.parameters['error_func'], self.parameters['cv_error_func'],
                self.parameters['data_normalizer'], self.parameters['labels_normalizer'],
                self.parameters['sparse'], self.parameters['regularized'],
                self.parameters['return_predictions']
                )
            calls[i] = dict()
            calls[i]['ext_cv_train_idxs'] = train_idxs
            calls[i]['ext_cv_test_idxs'] = test_idxs
            calls[i]['call_args'] = call_args
        calls['lambda_range'] = lambda_range
        calls['tau_range'] = tau_range
        calls['mu_range'] = mu_range
        return calls

    def _calculate_tau_range(self, data, labels):
        # determine tau parameter range
        # normalize data if requested
        data_normalizer = self.parameters['data_normalizer']
        labels_normalizer = self.parameters['labels_normalizer']
        if data_normalizer is not None:
            data = data_normalizer(data)
        if labels_normalizer is not None:
            labels = labels_normalizer(labels)
        # get scaling factors and determine min and max
        upper_bound_tau = l1l2py.algorithms.l1_bound(data, labels)
        tau_min_scale = self.parameters['tau_min_scale']
        tau_max_scale = self.parameters['tau_max_scale']
        tau_max = upper_bound_tau * tau_max_scale
        tau_min = upper_bound_tau * tau_min_scale
        tau_number = self.parameters['tau_number']
        ttype = self.parameters['tau_range_type']
        if ttype == 'geometric':
            rf = l1l2py.tools.geometric_range
        elif ttype == 'linear':
            rf = l1l2py.tools.linear_range
        tau_range = rf(tau_min, tau_max, tau_number)
        return tau_range

    def _calculate_mu_range(self, data):
        # determine mu parameter range
        # normalize data if requested
        data_normalizer = self.parameters['data_normalizer']
        if data_normalizer:
            data = data_normalizer(data)
        # determine mu range
        mu_fact = self._mu_scaling_factor(data)
        mu_min = mu_fact * self.parameters['mu_scaling_factor_min']
        mu_max = mu_fact * self.parameters['mu_scaling_factor_max']
        mtype = self.parameters['mu_range_type']
        if mtype == 'geometric':
            rf = l1l2py.tools.geometric_range
        elif mtype == 'linear':
            rf = l1l2py.tools.linear_range
        mu_number = self.parameters['mu_number']
        mu_range = rf(mu_min, mu_max, mu_number)
        return mu_range

    def _mu_scaling_factor(self, data):
        n, d = data.shape
        if d > n:
            tmp = numpy.dot(data, data.T)
            num = numpy.linalg.eigvalsh(tmp).max()
        else:
            tmp = numpy.dot(data.T, data)
            evals = numpy.linalg.eigvalsh(tmp)
            num = evals.max() + evals.min()
        return (num / (2.*n))

    def _determine_lambda_range(self):
        # determine lambda parameter range
        # it is common for all submatrices; we can also specify custom one
        lr = self.parameters['lambda_range']
        if lr is None:
            lambda_min = self.parameters['lambda_min']
            lambda_max = self.parameters['lambda_max']
            lambda_number = self.parameters['lambda_number']
            lambda_range_type = self.parameters['lambda_range_type']
            if lambda_range_type == 'geometric':
                rf = l1l2py.tools.geometric_range
            elif lambda_range_type == 'linear':
                rf = l1l2py.tools.linear_range
            lambda_range = rf(lambda_min, lambda_max, lambda_number)
            return lambda_range
        else:
            if not isListOrTuple(lr):
                raise Error('List or tuple expected! (got %s)' % lr.__class__)
            return lr

    def _verify_version(self):
        return l1l2py.__version__ == self._version


# ---- L1L2_L1L2 specific graphs

class L1L2KfoldErrorsGraph(MatplotlibPlot):
    r"""
Specialized subclass that plots surface of selected errors in (tau,lambda)
parameter space. The exact values to plot are configurable. This plotter is
tailored for l1l2py--related techniques that use splits. This plotter
accepts no additional configuration parameters.

See Also
--------
mpl_toolkits.mplot3d.axes3d.Axes3D
    """
    def __init__(self):
        super(L1L2KfoldErrorsGraph, self).__init__()

    def configure(self, **kwargs):
        r"""
Configure this plotter. The following configuration options can be used:

    * 'backend' (string) -- physical matplotlib backend
    * 'driver' (string) -- physical matplotlib driver

Refer to `matplotlib documentation <http://matplotlib.org/contents.html>`__
for more details. In addition, initialize proper plotting toolkits
(:mod:`matplotlib.cm` for color management,
:class:`mpl_toolkits.mplot3d.axes3d.Axes3D` for 3D plotting).

Parameters
----------
kwargs : dict
    configuration parameters of this plotter
        """
        super(L1L2KfoldErrorsGraph, self).configure(**kwargs)
        # resolve some detailed components
        self.components['cm'] = importComponent('matplotlib.cm')
        verifyDepModule('mpl_toolkits')
        self.components['Axes3D'] = importComponent('mpl_toolkits.mplot3d.Axes3D')

    def create(self, **kwargs):
        r"""
Create plot environment and set all necessary parameters according to content
parameters provided. The following content parameters are available:

    * 'ranges' (tuple of :class:`numpy.ndarray`) -- data ranges to be used
    * 'labels' (tuple of string) -- label ranges to be plotted
    * 'ts_errors' (tuple of :class:`numpy.ndarray`) -- test errors to be plotted
    * 'tr_errors' (tuple of :class:`numpy.ndarray`) -- training errors to be plotted
    * 'plot_title' (string) -- tile of this plot

Parameters
----------
kwargs : dict
    content parameters of this plotter
        """
        super(L1L2KfoldErrorsGraph, self).create(**kwargs)
        # get components
        plt = self.driver
        Axes3D = self.components['Axes3D']
        cm = self.components['cm']
        # get data
        try:
            ranges = kwargs['ranges']
            labels = kwargs['labels']
            ts_errors = kwargs['ts_errors']
            tr_errors = kwargs['tr_errors']
            title = kwargs['plot_title']
        except KeyError, ke:
            raise Error('Necessary data element missed! (%s)' % ke)
        # create plot (with default matplotlib autoincrement)
        fig = plt.figure(None)
        if len(ranges[0]) > 1:
            ax = Axes3D(fig)
            x_vals, y_vals = numpy.meshgrid(*ranges)
            x_idxs, y_idxs = numpy.meshgrid(*(numpy.arange(len(x)) for x in ranges))
            ax.set_xlabel(labels[0])
            ax.set_ylabel(labels[1])
            ax.set_zlabel('$error$')
            ax.plot_surface(x_vals, y_vals, ts_errors[x_idxs, y_idxs],
                                rstride=1, cstride=1, cmap=cm.Blues)
            if not tr_errors is None:
                ax.plot_surface(x_vals, y_vals, tr_errors[x_idxs, y_idxs],
                                rstride=1, cstride=1, cmap=cm.Reds)
        else:
            plt.plot(ranges[1], ts_errors.T, 'bo-',
                     label='%s=%f' % (labels[0], ranges[0][0]))
            if not tr_errors is None:
                plt.plot(ranges[1], tr_errors.T, 'ro-',
                     label='%s=%f' % (labels[0], ranges[0][0]))
            plt.xlabel(labels[1])
            plt.ylabel('$error$')
            plt.legend()
        plt.suptitle(title)

    def plot(self, **kwargs):
        r"""
Produce actual plot and return its content.
        """
        return super(L1L2KfoldErrorsGraph, self).plot(**kwargs)


class L1L2ErrorBoxplotMuGraph(MatplotlibPlot):
    r"""
Specialized subclass that produces boxplots of requested data for all given
parameter values (i.e. DOF values). The exact values to plot are configurable.
This plotter is tailored for l1l2py--related techniques that use splits and DOFs.
This plotter accepts no additional configuration parameters.

See Also
--------
matplotlib.pyplot.boxplot
    """
    def __init__(self):
        super(L1L2ErrorBoxplotMuGraph, self).__init__()

    def configure(self, **kwargs):
        r"""
Configure this plotter. The following configuration options can be used:

    * 'backend' (string) -- physical matplotlib backend
    * 'driver' (string) -- physical matplotlib driver

Refer to `matplotlib documentation <http://matplotlib.org/contents.html>`__
for more details.

Parameters
----------
kwargs : dict
    configuration parameters of this plotter
        """
        super(L1L2ErrorBoxplotMuGraph, self).configure(**kwargs)

    def create(self, **kwargs):
        r"""
Create plot environment and set all necessary parameters according to content
parameters provided. The following content parameters are available:

    * 'errors' (tuple of :class:`numpy.ndarray`) -- data to be plotted
    * 'mu_range' (tuple of float) -- range of values of 'mu' parameter,
    * 'plot_title' (string) -- tile of this plot

Parameters
----------
kwargs : dict
    content parameters of this plotter
        """
        super(L1L2ErrorBoxplotMuGraph, self).create(**kwargs)
        # get components
        plt = self.driver
        # get data
        try:
            errors = kwargs['errors']
            mu_range = kwargs['mu_range']
            title = kwargs['plot_title']
        except KeyError, ke:
            raise Error('Necessary data element missed! (%s)' % ke)
        # create plot (with default matplotlib autoincrement)
        plt.figure(None)
        plt.boxplot(errors, positions=numpy.log10(mu_range))
        plt.suptitle(title)
        plt.xlabel('$log_{10}(\\mu)$')
        plt.ylabel('$error$')

    def plot(self, **kwargs):
        r"""
Produce actual plot and return its content.
        """
        return super(L1L2ErrorBoxplotMuGraph, self).plot(**kwargs)

