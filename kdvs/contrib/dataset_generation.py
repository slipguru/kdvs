# Adapted for KDVS by Grzegorz Zycinski <grzegorz.zycinski@unige.it>
# Statistical Learning and Image Processing Genoa University Research Group
# Via Dodecaneso, 35 - 16146 Genova, ITALY.

# This code is written by Salvatore Masecchia <salvatore.masecchia@unige.it>
# and Annalisa Barla <annalisa.barla@unige.it>
# Copyright (C) 2010 SlipGURU -
# Statistical Learning and Image Processing Genoa University Research Group
# Via Dodecaneso, 35 - 16146 Genova, ITALY.
#
# This file is part of L1L2Py.
#
# L1L2Py is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# L1L2Py is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with L1L2Py. If not, see <http://www.gnu.org/licenses/>.

from optparse import OptionParser
import numpy as np
import os

def correlated_dataset(num_samples, num_variables, groups, weights,
                       variables_stdev=1.0,
                       correlations_stdev=1e-2,
                       labels_stdev=1e-2):
    r"""Random supervised dataset generation with correlated variables.

    The function returns a supervised training set with ``num_samples``
    examples with ``num_variables`` variables.

    Parameters
    ----------
    num_samples : int
        Number of samples.
    num_variables : int
        Number of variables.
    groups : tuple of int
        For each group of relevant variables indicates the group cardinality.
    weights : array_like of sum(groups) float
        True regression model.
    variables_stdev : float, optional (default is `1.0`)
        Standard deviation of the zero-mean Gaussian distribution generating
        variables column vectors.
    correlations_stdev : float, optional (default is `1e-2`)
        Standard deviation of the zero-mean Gaussian distribution generating
        errors between variables which belong to the same group
    labels_stdev : float, optional (default is `1e-2`)
        Standard deviation of the zero-mean Gaussian distribution generating
        regression errors.

    Returns
    -------
    X : (``num_samples``, ``num_variables``) ndarray
        Data matrix.
    Y : (``num_samples``, 1) ndarray
        Regression output.

    Notes
    -----
    The data will have ``len(groups)`` correlated groups of variables, where
    for each one the function generates a column vector :math:`\mathbf{x}` of
    ``num_samples`` values drawn from a zero-mean Gaussian distribution
    with standard deviation equal to ``variables_stdev``.

    For each variable of the group associated with the :math:`\mathbf{x}`
    vector, the function generates the  values as

    .. math:: \mathbf{x}^j = \mathbf{x} + \epsilon_x,

    where :math:`\epsilon_x` is additive noise drawn from a zero-mean Gaussian
    distribution with standard deviation equal to ``correlations_stdev``.

    The regression values will be generated as

    .. math::
        \mathbf{Y} = \mathbf{\tilde{X}}\boldsymbol{\tilde{\beta}} + \epsilon_y,

    where :math:`\boldsymbol{\tilde{\beta}}` is the ``weights`` parameter, a
    list of ``sum(groups)`` coefficients of the relevant variables,
    :math:`\mathbf{\tilde{X}}` is the submatrix containing only the column
    related to the relevant variables and :math:`\epsilon_y` is additive noise drawn
    from a zero-mean Gaussian distribution with standard deviation equal to
    ``labels_stdev``.

    At the end the function returns the matrices
    :math:`\mathbf{X}` and :math:`\mathbf{Y}` where

    .. math:: \mathbf{X} = [\mathbf{\tilde{X}}; \mathbf{X_N}]

    is the concatenation of the matrix :math:`\mathbf{\tilde{X}}` with the
    relevant variables with ``num_variables - sum(groups)`` noisy variables
    generated indipendently using values drawn from a zero-mean Gaussian
    distribution with standard deviation equal to ``variables_stdev``.

    Examples
    --------
    >>> X, Y = correlated_dataset(30, 40, (5, 5, 5), [3.0]*15)
    >>> X.shape
    (30, 40)
    >>> Y.shape
    (30, 1)

    """

    num_relevants = sum(groups)
    num_noisy = num_variables - num_relevants

    X = np.empty((num_samples, num_variables))
    weights = np.asarray(weights).reshape(-1, 1)

    # For each group generates the correlated variables
    var_idx = 0
    for g in groups:
        x = np.random.normal(scale=variables_stdev, size=(num_samples, 1))
        err_x = np.random.normal(scale=correlations_stdev, size=(num_samples, g))
        X[:, var_idx:var_idx + g] = x + err_x
        var_idx += g

    # Generates the outcomes
    err_y = np.random.normal(scale=labels_stdev, size=(num_samples, 1))
    Y = np.dot(X[:, :num_relevants], weights) + err_y

    # Add noisy variables
    X[:, num_relevants:] = np.random.normal(scale=variables_stdev,
                                            size=(num_samples, num_noisy))

    return X, Y

# callback for varargs; adapted from optparse
def _callback(option, opt_str, value, parser):
    if value is not None:
        raise RuntimeError('Vararg callback: storage variable must be None!')
    value = list()

    def _floatable(strn):
        try:
            float(strn)
            return True
        except ValueError:
            return False

    for arg in parser.rargs:
        # stop on --foo like options
        if arg[:2] == "--" and len(arg) > 2:
            break
        # stop on -a, but not on -3 or -3.0
        if arg[:1] == "-" and len(arg) > 1 and not _floatable(arg):
            break
        value.append(arg)

    del parser.rargs[:len(value)]
    setattr(parser.values, option.dest, value)


def main():

    r"""
Generates one or more randomized datasets with correlated variables. Use -h
command line options for more details.
    """

    # default "fmt" for savetxt
    # NOTE: copied directly from npyio.py
    np_default_fmt = "%.18e"

    # default delimiter to use for datasets
    default_delimiter = '\t'

    # default number of variables generated
    var_num_thr = 9

    desc = 'Knowledge Driven Variable Selection: dataset generation (companion application)'
    parser = OptionParser(description=desc)
    parser.add_option("-o", "--output-dir", action="store", dest="output_dir",
        help="store output files in ODIR; default: current directory", metavar="ODIR", default=None)
    parser.add_option("-s", "--numof-samples", action="store", dest="numof_samples",
        help="number of samples in generated dataset(s)", metavar="NS")
    parser.add_option("-v", "--numof-variables", action="store", dest="numof_vars", default=var_num_thr,
        help="number of variables in generated dataset(s)", metavar="NV")
    parser.add_option("-g", action="callback", dest="groups", callback=_callback,
        help="cardinality of groups of correlated variables (in subsequent arguments, e.g. -g 5 5 5 for 3 groups)", metavar="GR")
    parser.add_option("-w", action="callback", dest="weights", callback=_callback, default=None,
        help="weights of regression model for each significant variable (in subsequent arguments, e.g. -w 1.0 1.0 1.0 for 3 variables)", metavar="WT")
    parser.add_option("--variables-stddev", action="store", dest="variables_stddev", default=1.0,
        help="standard deviation of the zero-mean Gaussian distribution generating variables column vectors", metavar="VS")
    parser.add_option("--correlations-stddev", action="store", dest="correlations_stddev", default=1e-2,
        help="standard deviation of the zero-mean Gaussian distribution generating errors between variables which belong to the same group", metavar="CS")
    parser.add_option("--labels-stddev", action="store", dest="labels_stddev", default=1e-2,
        help="standard deviation of the zero-mean Gaussian distribution generating regression errors", metavar="LS")
    parser.add_option("-n", "--numof-datasets", action="store", dest="numof_datasets",
        help="number of datasets generated at once", metavar="ND", default=1)
    parser.add_option("-f", "--number-format", action="store", dest="number_format",
        help="format string for numeric output, default: %s" % np_default_fmt, metavar="FS", default=np_default_fmt)
    parser.add_option("-d", "--delimiter", action="store", dest="delimiter",
        help="delimiter for numeric output, default: %s" % '\\t', metavar="DS", default=default_delimiter)

    options = parser.parse_args()[0]

    output_dir = options.output_dir
    if output_dir is None:
        output_dir = os.getcwd()
    numof_samples = int(options.numof_samples)
    numof_variables = int(options.numof_vars)
    numof_datasets = int(options.numof_datasets)

    # get groups
    groups = [int(gs) for gs in options.groups]
    if len(groups) < 1:
        raise RuntimeError('At least one group must be specified!')

    if options.weights is None:
        # default weights
        weights = [1.0] * sum(groups)
    else:
        # get weights
        weights = [float(ws) for ws in options.weights]

    # get variables_stddev
    variables_stddev = options.variables_stddev

    # get correlations_stddev
    correlations_stddev = options.correlations_stddev

    # get labels_stddev
    labels_stddev = options.labels_stddev

    delimiter = options.delimiter
    fmt = options.number_format

    if numof_variables < var_num_thr:
        raise RuntimeError('At least %d variables must be generated!' % (var_num_thr))

    # for multiple datasets we can generate one big multiset and split it in parts

    total_numof_variables = numof_variables * numof_datasets

    msg = 'Started generating %d dataset(s) of %d samples with %d variables in %s' % (
            numof_datasets, numof_samples, numof_variables, output_dir)
    print msg

    print 'Cardinalities of correlated variable groups:', groups

    print 'Variables stddev:', variables_stddev

    print 'Correlations stddev:', correlations_stddev

    print 'Labels stddev:', labels_stddev

    X, Y = correlated_dataset(num_samples=numof_samples,
                              num_variables=total_numof_variables,
                              groups=groups,
                              weights=weights,
                              variables_stdev=variables_stddev,
                              correlations_stdev=correlations_stddev,
                              labels_stdev=labels_stddev)

    # switch to row orientation used by KDVS
    X = X.T

    # calculate indexes for datasets obtained from multiset
    datasets_rows_idxs = [range(i * numof_variables, (i + 1) * numof_variables - 1 + 1) for i in range(numof_datasets)]

    # reconstruct individual datasets
    XS = [X[didxs, :] for didxs in datasets_rows_idxs]

    # enumerate all columns (samples) and create headers for dataset(s) and labelset
    X_header = ['S%d' % i for i in range(1, Y.shape[0] + 1)]
    X_header_for_labels = list(X_header)
    X_header.insert(0, 'ID')
    X_header_str = delimiter.join(X_header)

    for i, X in enumerate(XS):

        print 'Generating individual dataset %d...' % (i + 1),

        # enumerate all rows (measurements)
        X_id_col = np.arange(1, X.shape[0] + 1)

        # include measurement IDs into generated dataset
        # create empty array with one more column
        Xtemp = np.empty((X.shape[0], X.shape[1] + 1))
        # fill first column with measurement indexes
        Xtemp[:, 0] = X_id_col
        # copy rest of the array
        Xtemp[:, 1:] = X

        # our format string to use
        fmt_used = delimiter.join(["M%i"] + [fmt] * X.shape[1])

        # ---- save data information
        data_subset_path = os.path.abspath(os.path.join(output_dir, 'data%d.txt' % (i + 1)))
        with open(data_subset_path, 'wb') as f:
            f.write(X_header_str + '\n')
            np.savetxt(f, Xtemp, fmt=fmt_used, delimiter=delimiter)

        print 'done'

    # enumerate all labels and generate label information
    Y_header = "%s%s%s\n" % ('Samples', delimiter, 'Labels')
    Y_labels = ["%s%s%s\n" % (X_header_for_labels[i - 1], delimiter, Y[i - 1][0]) for i in range(1, Y.shape[0] + 1)]

    print 'Generating labels...',

    labels_path = os.path.abspath(os.path.join(output_dir, 'labels.txt'))

    # ---- save labels information
    with open(labels_path, 'wb') as f:
        f.write(Y_header)
        f.writelines(Y_labels)

    print 'done'

    print 'All Done'

if __name__ == '__main__':
    main()
