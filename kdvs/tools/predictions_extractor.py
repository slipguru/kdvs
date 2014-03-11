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
Extracts predictions from results of finished experiment. See 'predictions_extractor.py -h' for help.
"""

from kdvs.core.util import deserializeObj
import optparse
import os

def main():

    # output file name of this script
    output_file_name = 'predictions.txt'

    # for autodiscovery, configuration file to be found in KDVS output directory
    cfg_name = 'CFG'
    # vars to be looked for during autodiscovery
    vars_to_find = {
        # results location to be resolved in full parh inside KDVS output directory
        'subsets_results_location' : None,
        # mapping of subsets to techniques used
        'technique2ssname_key' : None,
        # suffix added to subset ID when serializing subsets results
        'subset_results_suffix' : None,
    }

    # custom epilog formatting
    optparse.OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = optparse.OptionParser(description=
                                   "Extracts predictions from results of finished experiment. "
                                   "INPUT: Root directory with experiment results specified with -d option. "
                                   "OUTPUT: Writes '%s' file to directory specified with -o option. "
                                   "Default output directory: '%s'."
                                   ""
                                    % (
                                        output_file_name,
                                        os.getcwd()
                                        ),
                                   epilog=
                                   "\n"
                                   "'%s' contains the predictions for each processed data subset in linear manner; \n"
                                   "for each data subset the following information is written (without '>'):\n"
                                   "> subset_ID (technique_ID) \n"
                                   "> DOF_1 (outer_selection_status) \n"
                                   "> sample1,sample2,...,sampleN \n"
                                   "> original_label1,original_label2,...,original_labelN \n"
                                   "> predicted_label1,predicted_label2,...,predicted_labelN \n"
                                   "> DOF_2 (outer_selection_status) \n"
                                   "> sample1,sample2,...,sampleN \n"
                                   "> original_label1,original_label2,...,original_labelN \n"
                                   "> predicted_label1,predicted_label2,...,predicted_labelN \n"
                                   "> ...\n"
                                   "> DOF_P (outer_selection_status) \n"
                                   "> sample1,sample2,...,sampleN \n"
                                   "> original_label1,original_label2,...,original_labelN \n"
                                   "> predicted_label1,predicted_label2,...,predicted_labelN \n"
                                   ""
                                    % (
                                        output_file_name,
                                        )
                                  )
    parser.add_option("-d", "--kdvs-output-dir", dest="kdvs_output_dir",
                  help="input root KDVS output directory", metavar="DIR")
    parser.add_option("-o", "--output-dir", dest="output_dir",
                  help="write result files into directory ODIR", metavar="ODIR", default=None)

    options = parser.parse_args()[0]

    kdvs_output_dir = options.kdvs_output_dir
    output_dir = options.output_dir
    if output_dir is None:
        output_dir = os.path.abspath(os.getcwd())

    kdvs_output_dir = os.path.abspath(kdvs_output_dir)
    if not os.path.exists(kdvs_output_dir):
        raise Exception('KDVS output directory "%s" not found!' % kdvs_output_dir)

    cfg_path = os.path.join(kdvs_output_dir, cfg_name)
    if not os.path.exists(cfg_path):
        raise Exception('Configuration file "%s" not found!' % cfg_path)

    with open(cfg_path, 'rb') as f:
        cfg = deserializeObj(f)

    for var in vars_to_find.keys():
        try:
            val = cfg[var]
            vars_to_find[var] = val
        except KeyError:
            raise Exception('Variable "%s"not found in %s!' % (var, cfg_name))

    tech2ss_path = os.path.join(kdvs_output_dir, vars_to_find['subsets_results_location'], vars_to_find['technique2ssname_key'])
    with open(tech2ss_path, 'rb') as f:
        tech2ss = deserializeObj(f)

    # reverse tech2ss mapping quickly
    ss2tech = dict()
    for tech, ss_s in tech2ss.iteritems():
        for ss_ in ss_s:
            ss2tech[ss_] = tech

    print 'Extracting predictions...',

    output_file_path = os.path.join(output_dir, output_file_name)

    output_file = open(output_file_path, 'wb')

    for ss, tech in ss2tech.iteritems():
        ss_results_path = os.path.join(kdvs_output_dir, vars_to_find['subsets_results_location'], ss, '%s%s' % (ss, vars_to_find['subset_results_suffix']))

        if not os.path.exists(ss_results_path):
            raise Exception('Results for %s ("%s") not found!' % (ss, ss_results_path))

        with open(ss_results_path, 'rb') as f:
            ss_results = deserializeObj(f)

        output_file.write('%s (%s)\n' % (ss, tech))

        predictions = ss_results['Predictions']
        outersels = ss_results['Selection']['outer']
        # both dictionaries contain same keys, we need one instance
        dofs = outersels.keys()
        for dof in sorted(dofs):
            outer_selection_status = outersels[dof]
            output_file.write('%s (%s)\n' % (dof, outer_selection_status))
            osamples = ','.join([str(l) for l in predictions[dof]['orig_samples']])
            output_file.write('%s\n' % osamples)
            olabels = ','.join([str(l) for l in predictions[dof]['orig_labels']])
            output_file.write('%s\n' % olabels)
            plabels = ','.join([str(l) for l in predictions[dof]['pred_labels']])
            output_file.write('%s\n' % plabels)

    output_file.close()

    print 'done'
    print '%s written' % (output_file_path)
    print 'All Done'

if __name__ == '__main__':
    main()
