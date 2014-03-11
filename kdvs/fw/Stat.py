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
Provides high--level functionality for statistical techniques. Statistical technique
accepts data subset and processes it as it sees fit. Technique shall produce
Results object that is stored physically and may be used later to generate reports.
Typically, each technique has its own specific Reporter associated.
"""

from kdvs.core.error import Error
from kdvs.core.util import quote, Parametrizable, Constant
from kdvs.fw.DBTable import DBTable
from numpy import ndarray
import math
import numpy

# ---- wrapper for labels functionality

class Labels(object):

    r"""
Provides uniform information about labels. In supervised machine learning, when
the algorithms learn generalities from incoming known samples, the samples are
of different types (typically two, sometimes more), and each type has a label
associated to it. This information is present only when statistical technique
uses supervised classification; in that case, the label information shall be
supplied as an additional input file and load into :class:`~kdvs.fw.DBTable.DBTable`
instance. Typically, in the scenario with two classes of samples, first class
has label '1' associated, and second class has label '-1' associated. See 'example_experiment'
directory for an example of labels file.
    """

    def __init__(self, source, unused_sample_label=0):
        r"""
Parameters
----------
source : :class:`~kdvs.fw.DBTable.DBTable`
    DBTable instance that contains label information

unused_sample_label : integer
    if this label is specified in label information, the related samples are skipped
    from processing entirely; 0 by default

Raises
------
Error
    if source is incorrectly specified
        """
        if not isinstance(source, DBTable):
            raise Error('%s instance expected! (got %s)' % (DBTable, source.__class__))
        else:
            self.source = source
        self.labels = dict()
        self.unused_sample_label = str(unused_sample_label)
        self._create_labels_dict()

    def _create_labels_dict(self):
        lbs = self.source.getAll(as_dict=True, dict_on_rows=True)
        try:
            self.labels.update([(str(k), str(v[0])) for k, v in lbs.iteritems() if str(v[0]) != self.unused_sample_label])
        except Exception, e:
            raise Error('Could not create labels dictionary! (Reason: %s)' % e)

    def getLabels(self, samples_order, as_array=False):
        r"""
Return labels in samples order, as read from input label information. When
primary data set is read, samples are in specific order, e.g.

    * S1, S2, ..., S40

However, label information specified in separated input file can have different
sample order, e.g.

    * S32, S33, ..., S40, S1, S2, S3, ..., S31

Here it is ensured that labels are ordered according to specified sample order.

Parameters
----------
sample_order : iterable
    iterable of sample names; returned labels will be ordered according to the
    order of samples

as_array : boolean
    return labels as numpy.array of floats; False by default

Returns
-------
lbsord : iterable
    labels ordered according to specified samples order; labels are returned as
    plain text or as numerical numpy.array if requested
        """
        # get labels according to order of presented samples
        # possible to replace with similar:
        # [v for s in samples_order for k, v in self.labels.iteritems() if k==s]
        lbsord = list()
        for sord in samples_order:
            try:
                lb = self.labels[sord]
                lbsord.append(lb)
            except KeyError:
#                raise Error('Label for sample %s not found!'%quote(sord))
                pass
        if as_array:
            return numpy.array([float(l) for l in lbsord])
        else:
            return lbsord

    def getSamples(self, samples_order):
        r"""
Return used samples in samples order, as read from input label information.
Useful when reordering samples according to specific order, and skipping unused
samples (that have 'unused_sample_label' associated).

Parameters
----------
samples_order : iterable
    iterable of sample names; returned used samples will be ordered according to
    this order

Returns
-------
smpord : iterable
    used samples ordered according to specified order
        """
        # get valid samples according to presented order
        # valid samples are samples associated with used labels
        smpord = list()
        for sord in samples_order:
            if sord in self.labels:
                smpord.append(sord)
        return smpord

# ---- wrapper for numerical results

NOTPRESENT = Constant('NotPresent')
r"""
Constant that represents element that has not been present among :class:`~kdvs.fw.Stat.Results`.
"""

DEFAULT_RESULTS = ()
r"""
Default empty content of :class:`~kdvs.fw.Stat.Results` wrapper object.
"""

RESULTS_SUBSET_ID_KEY = 'SubsetID'
r"""
Standard :class:`~kdvs.fw.Stat.Results` element that refers to ID of data subset processed; typically,
equivalent to associated prior knowledge concept identifier.
"""

RESULTS_PLOTS_ID_KEY = 'Plots'
r"""
Standard :class:`~kdvs.fw.Stat.Results` element that refers to dictionary of plots associated with the
result. Plots are produced with :class:`~kdvs.fw.Stat.Plot` according to specification.
"""

RESULTS_RUNTIME_KEY = 'Runtime'
r"""
Standard :class:`~kdvs.fw.Stat.Results` element that refers to any information available in runtime,
that needs to be included with the result itself.
"""

class Results(object):
    r"""
Wrapper for results obtained from statistical technique. Result is typically
composed of various elements produced by the technique. The element can be any
object of any valid Python/numpy type. Elements are referred to by their `names`,
and Results instance works like a dictionary. If an element is a dictionary
itself, it can contain nested dictionaries, so the following syntax also works:

    * Results['element_name']['subelement_name1']...['subelement_nameN']

In the documentation, this is represented as:

    * 'element_name'->'subelement_name1'->...->'subelement_nameN'

Each valid statistical technique shall produce exactly one instance of Results
for exactly one data subset. This class exposes partial :class:`dict` API and
implements `__getitem__` and `__setitem__` methods.
    """
    def __init__(self, ssID, elements=None):
        r"""
Parameters
----------
ssID : string
    identifier of data subset processed; this identifier will be referred later
    as the content of :data:`RESULTS_SUBSET_ID_KEY` element

elements : iterable of string
    elements that will be present in the instance; by default, each element
    is NOTPRESENT
        """
        self._results = dict()
        self._elements = list()
        if elements is not None:
            self._elements.extend(elements)
        self._elements.extend(DEFAULT_RESULTS)
        self._results.update([el, NOTPRESENT] for el in self._elements)
        self._results[RESULTS_SUBSET_ID_KEY] = ssID
        self._results[RESULTS_PLOTS_ID_KEY] = dict()
        self._results[RESULTS_RUNTIME_KEY] = dict()

    def __getitem__(self, key):
        return self._results[key]

    def __setitem__(self, key, value):
        r"""
Raises
------
Error
    if element is not associated with this instance, i.e. is not one of standard
    elements, and was not present during initialization
        """
        if key not in self._elements:
            raise Error('Element %s not associated with this instance!' % quote(key))
        else:
            self._results[key] = value

    def keys(self):
        r"""
Return all element names.
        """
        return self._results.keys()

    def __str__(self):
        return self._results.__str__()

    def __repr__(self):
        return self.__str__()


# ---- wrappers for numerical computation activities

DEFAULT_CLASSIFICATION_RESULTS = (
    'Classification Error',
    )
r"""
Default Results element that shall always be produced by techniques that incorporate
classification.
"""

DEFAULT_SELECTION_RESULTS = (
    'Selection',
    )
r"""
Default Results element that shall always be produced by techniques that incorporate
some kind of 'selection' (including variable selection).
"""

DEFAULT_GLOBAL_PARAMETERS = (
    'global_degrees_of_freedom', 'job_importable',
    )
r"""
Default statistical technique parameters that shall always be present.
"""

class Technique(Parametrizable):
    r"""
Abstract statistical technique that processes data subsets one at a time. Technique
is parametrizable and is initialized during instance creation. Technique processes
data subset by creating one or more jobs to be executed by specified job container.
After job(s) are finished, the technique produces single :class:`~kdvs.fw.Stat.Results`
instance. This split of functionalities was introduced to ease implementation of techniques
that use cross validation extensively. Concrete implementation must implement
:meth:`produceResults` and reimplement :meth:`createJob` methods. In the simplest case,
single job that wraps single function call may be generated. More complicated
implementations may require generation of cross validation splits, processing
them in separated jobs, and merging partial results into single one.
    """
    def __init__(self, ref_parameters, **kwargs):
        r"""
Parameters
----------
ref_parameters : iterable
    reference parameters to be checked against during instantiation; empty tuple
    by default

kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones
        """
        super(Technique, self).__init__(ref_parameters, **kwargs)
        self.results_elements = list(DEFAULT_RESULTS)
        self.techdata = dict()

    # needs to be overriden by subclass
    # if properly subclassed, yields pair(s) of (jname, j)
    #   jname is custom ID for produced job
    #   j is an instance of Job
    # jname may be None
    # if not subclassed, returns None
    def createJob(self, ssname, data, labels=None, additionalJobData={}):
        r"""
This method must be reimplemented as a generator that yields jobs to be executed.
By default, it only checks if input data are correctly specified.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

data : :class:`numpy.ndarray`
    data to be processed; could be whole data subset or its part (e.g. training or test split)

labels : :class:`numpy.ndarray`/None
    associated label information to be processed; used when technique incorporates
    supervised classification; None if not needed

additionalJobData : dict
    any additional information that will be associated with each job produced;
    empty dictionary by default

Returns
-------
(jID, job) : string, :class:`~kdvs.fw.Job.Job`
    tuple of the following: custom job ID, and Job instance to be executed

Notes
-----
Proper order of data and labels must be ensured in order for the technique to work.
Typically, subsets are generated according to samples order specified within the
primary data set; labels must be in the same order. By definition, it is not checked
during job execution.
        """
        self._check_input(ssname, data, labels)

    def produceResults(self, ssname, jobs, runtime_data):
        r"""
Must be implemented in subclass. It returns single :class:`~kdvs.fw.Stat.Results` instance.

Parameters
----------
ssname : string
    identifier of data subset being processed; typically, equivalent to associated
    prior knowledge concept

jobs : iterable of :class:`~kdvs.fw.Job.Job`
    executed job(s) that contain(s) raw results

runtime_data : dict
    data collected in runtime that shall be included in the final :class:`~kdvs.fw.Stat.Results` instance

Returns
-------
final_results : :class:`~kdvs.fw.Stat.Results`
    Results instance that contains final results of the technique
        """
        # implemented by subclasses, takes job(s) and produces Result object
        # runtime data are miscellaneous runtime information useful for reporting
        # results, not obtainable easily otherwise;  so far, include:
        # techID,...
        raise NotImplementedError('Must be implemented in subclass!')

    def _check_input(self, ssname, data, labels):
        if data is not None and not isinstance(data, (numpy.ndarray, ndarray)):
            raise Error('(%s) %s expected! (got %s)' % (ssname, 'numpy.ndarray', data.__class__))
        if labels is not None and not isinstance(labels, (numpy.ndarray, ndarray)):
            raise Error('(%s) %s expected! (got %s)' % (ssname, 'numpy.ndarray', labels.__class__))


# ---- wrappers for selection activities

NOTSELECTED = Constant('NotSelected')
r"""
Constant that refers to entity being not selected.
"""

SELECTED = Constant('Selected')
r"""
Constant that refers to entity being selected.
"""

SELECTIONERROR = Constant('SelectionError')
r"""
Constant that refers to error encountered during selection process.
"""

class Selector(Parametrizable):
    r"""
Abstract parametrizable wrapper for selection activity. Generally, for KDVS
'selection' is understood in much wider context than in machine learning community.
Both prior knowledge concepts and variables from data subsets can be 'selected'.
Some statistical techniques incorporate variable selection (in machine learning
sense), some do not. In order to unify the concept, KDVS introduced 'selection
activity' that marks specified entities as 'properly selected'. For example, if
the technique incorporates proper variable selection, concrete Selector instance
will simply recognize it and mark selected variables as 'properly selected'.
If the technique does not involve variable selection, concrete Selector instance
may simply declare some variables as 'properly selected' or not, depending on the
needs. If some prior knowledge concepts could be 'selected' in any sense, another
concrete Selector can accomplish this as well. Selectors produce 'selection markings'
that can be saved later and reported. The concrete subclass must implement
:meth:`perform` method. Selectors are closely tied with techniques and reporters.
    """
    def __init__(self, parameters, **kwargs):
        r"""
Parameters
----------
parameters : iterable
    reference parameters to be checked against during instantiation; empty tuple
    by default

kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones
        """
        super(Selector, self).__init__(parameters, **kwargs)

    def perform(self, *args, **kwargs):
        r"""
Perform selection activity. Typically, Selector accepts :class:`~kdvs.fw.Stat.Results`
instance and, depending on the needs, may go through individual variables of the
data subset marking them as 'properly selected' or not, or may mark whole data
subset (that has associated prior knowledge concept) as 'selected'. In dubious
cases, the selector can use constant value 'selection error'. The associated
:class:`~kdvs.fw.Report.Reporter` instance shall recognize properly selected
prior knowledge concepts and/or variables, and report them accordingly. This
method must also return 'selection markings' in the format understandable for Reporter.
        """
        raise NotImplementedError('Must be implemented in subclass!')


# ---- wrapper for drawing activities

class Plot(object):
    r"""
Abstract wrapper for plot. Concrete implementation must implement :meth:`configure`,
:meth:`create`, and :meth:`plot` methods. When using the plotter, the following
sequence of calls shall be issued: :meth:`configure`, :meth:`create`, :meth:`plot`.
    """
    def __init__(self):
        # driver that does all the drawing
        self.driver = None
        # "canvas" of the drawing
        self.backend = None
        # Python modules identified before as useful in drawing
        self.components = dict()

    def configure(self, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')

    def create(self, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')

    def plot(self, **kwargs):
        raise NotImplementedError('Must be implemented in subclass!')


# ---- various statistical utilities

def calculateConfusionMatrix(original_labels, predicted_labels, positive_label=1, negative_label= -1):
    r"""
Calculate confusion matrix for original and predicted labels. It is used when
labels reflect two classes, and one class is referred to as 'cases' (that has positive
label associated), and second class is referred to as 'control' (that has negative
label associated).

Parameters
----------
original_labels : iterable of integer
    original labels as integers

predicted_labels : iterable of integer
    predicted labels as integers

positive_label : integer
    label that refers to 'cases' class; 1 by default (hence positive label)

negative_label : integer
    label that refers to 'control' class; -1 by default (hence negative label)

Returns
-------
(tp, tn, fp, fn) : tuple of integer
    tuple of the following: number of true positives, number of true negatives,
    number of false positives, number of false negatives

Raises
------
Error
    if number of original and predicted variables differ
Error
    if labels have different values than 'positive' or 'negative'
    """
    if len(original_labels) != len(predicted_labels):
        raise Error('Numbers of original/predicted labels differ! (%d vs %d)' % (len(original_labels), len(predicted_labels)))
    tp = 0
    tn = 0
    fp = 0
    fn = 0
    for ol, pl in zip(original_labels, predicted_labels):
#        ol=np.sign(olb)
#        pl=np.sign(plb)
        if ol == positive_label and pl == positive_label:
            # true positive
            tp += 1
        elif ol == negative_label and pl == negative_label:
            # true negative
            tn += 1
        elif ol == negative_label and pl == positive_label:
            # false positive
            fp += 1
        elif ol == positive_label and pl == negative_label:
            # false negative
            fn += 1
        else:
            raise Error('Unexpected label values! (%s, %s)' % (str(ol), str(pl)))
    return tp, tn, fp, fn

def calculateMCC(tp, tn, fp, fn):
    r"""
Calculate Matthews Correlation Coefficient for given confusion matrix.

Parameters
----------
tp : integer
    number of true positives

tn : integer
    number of true negatives

fp : integer
    number of false positives

fn : integer
    number of false negatives

Returns
-------
mcc : float
    `Matthews Correlation Coefficient <http://en.wikipedia.org/wiki/Matthews_correlation_coefficient>`_
    """
    if tp == 0 and tn == 0 and fp == 0 and fn == 0:
        return None
    # calculate Matthews Correlation Coefficient
    # A = TP*TN - FP*FN
    # P1 = TP+FP, P2 = TP+FN, P3 = TN+FP, P4 = TN+FN
    # B = sqrt(P1*P2*P3*P4)
    # MCC = A / B
    # 1. calculate A
    a = float(tp * tn) - float(fp * fn)
    # 2. calculate P1, P2, P3, P4
    p1 = tp + fp
    p2 = tp + fn
    p3 = tn + fp
    p4 = tn + fn
    # 3. calculate B
    if p1 == 0 or p2 == 0 or p3 == 0 or p4 == 0:
        # if any of Px is zero, then B is 1
        b = 1.
    else:
        b = math.sqrt(float(p1) * float(p2) * float(p3) * float(p4))
    # 4. calculate MCC
    mcc = a / b
    return mcc
