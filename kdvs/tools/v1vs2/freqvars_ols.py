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
Check if all frequencies for variables are calculated correctly for
:class:`~kdvs.fw.impl.stat.L1L2.L1L2_OLS`. NOTE: there is known discrepancy
due to relative order of variables that share the same frequency; this has been
addressed by comparing in sets.
"""
from kdvs.core.util import deserializeObj
import csv
import glob
import os
import pprint

dir10_root = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/'
dir10_data = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/postprocessing_results'
dir20_root = '/home/grzegorz/KDVS2.0/KDVS_output'
dir20_data = '/home/grzegorz/KDVS2.0/KDVS_output/ss_results'

dir10_ols_vars_glob = os.path.join(dir10_data, 'size_below/*__vars.txt')

f10 = 'Variable Name   Gene Symbols(s)   Entrez Gene ID(s)  GenBank Accession #'
f20 = 'Variable Name    Frequency (%)    Gene Symbols(s)    Representative Public ID    GenBank Accession #    Entrez Gene ID(s)    Ensembl Gene ID(s)    RefSeq ID(s)'

f10k = 'Variable Name'
f20k = 'Variable Name'

f10_fields = ['Variable Name', 'Gene Symbols(s)', 'Entrez Gene ID(s)', 'GenBank Accession #']

f10_to_f20 = {
    'Variable Name' : 'Variable Name',
    'Gene Symbols(s)' : 'Gene Symbols(s)',
    'Entrez Gene ID(s)' : 'Entrez Gene ID(s)',
    'GenBank Accession #' : 'GenBank Accession #',
}


def main():

    # if all equalities are satisfied there should be no output from the script
    # for any inequality AssertionError is thrown

    dir10_ols_vars_p = [(p, os.path.basename(p)) for p in glob.glob(dir10_ols_vars_glob)]

    dir10_ols_vars_paths = [p[0] for p in dir10_ols_vars_p]
    dir10_ss = [p[1].split('__')[0] for p in dir10_ols_vars_p]

    dir10_ols_vars_paths = dict([(ss, p) for ss, p in zip(dir10_ss, dir10_ols_vars_paths)])

    tech2ss_path = os.path.join(dir20_data, 'TECH2SS')
    with open(tech2ss_path, 'rb') as f:
        tech2ss = deserializeObj(f)
    dir20_ss = tech2ss['L1L2_OLS']
    dir20_ols_vars_paths = dict([(ss, os.path.join(dir20_data, ss, '%s_NullDOF__vars_freqs.txt' % ss)) for ss in dir20_ss])

    dir10set = set(dir10_ss)
    dir20set = set(dir20_ss)
    common_ss = dir10set & dir20set

    # all terms reported in 10 are selected
    assert len(dir10set - common_ss) == 0

    dir20_notsel = dir20set - common_ss

    # check common terms first
    for ss in common_ss:

        dir10_path = dir10_ols_vars_paths[ss]
        dir20_path = dir20_ols_vars_paths[ss]

        f10dat = dict()

        with open(dir10_path, 'rb') as f10_file:
            f10_csv = csv.DictReader(f10_file, fieldnames=f10_fields, dialect='excel-tab')

            for f10rec in f10_csv:
                f10key = f10rec[f10k]
                f10dat[f10key] = dict()
                for f10term, f20term in f10_to_f20.iteritems():
                    common_term = f10term
                    f10dat[f10key][common_term] = f10rec[f10term]
                f10dat[f10key]['Selected?'] = 'Y'
                f10dat[f10key]['Frequency (%)'] = '100'

        f20dat = dict()

        with open(dir20_path, 'rb') as f20_file:
            # skip comment
            f20_file.next()
            f20_csv = csv.DictReader(f20_file, dialect='excel-tab')

            for f20rec in f20_csv:
                f20key = f20rec[f20k]
                f20dat[f20key] = dict()
                for f10term, f20term in f10_to_f20.iteritems():
                    common_term = f10term
                    f20dat[f20key][common_term] = f20rec[f20term]
                f20dat[f20key]['Selected?'] = f20rec['Selected?']
                f20dat[f20key]['Frequency (%)'] = f20rec['Frequency (%)']

        # f10 contains only selected variables; does f20 reports all selected ones too?
        f10sel = sorted([k for k in f10dat.keys() if (f10dat[k]['Selected?'] == 'Y')])
        f20sel = sorted([k for k in f20dat.keys() if (f20dat[k]['Selected?'] == 'Y')])
        assert f10sel == f20sel

        f10set = set(f10sel)
        f20set = set(f20sel)

        f_common = f10set & f20set
        # f10 and f20 shall contain exactly the same variables
        assert len(f10set - f_common) == 0
        assert len(f20set - f_common) == 0

        # f10 and f20 variables shall contain exactly the same frequencies
        f_eq_freqs = set([f for f in f_common if f10dat[f]['Frequency (%)'] == f20dat[f]['Frequency (%)']])
        assert f_common == f_eq_freqs

#        # write temporary info for further reference if needed
#        with open('freqvars_%s_OLS.txt' % ss, 'wb') as f:
#            fdict = {'f10' : f10dat, 'f20' : f20dat}
#            pprint.pprint(fdict, f, indent=2)

    # check remaining terms reported in 20
    for ss in dir20_notsel:

        dir20_path = dir20_ols_vars_paths[ss]

        f20dat = dict()

        with open(dir20_path, 'rb') as f20_file:
            # skip comment
            f20_file.next()
            f20_csv = csv.DictReader(f20_file, dialect='excel-tab')

            for f20rec in f20_csv:
                f20key = f20rec[f20k]
                f20dat[f20key] = dict()
                for f10term, f20term in f10_to_f20.iteritems():
                    common_term = f10term
                    f20dat[f20key][common_term] = f20rec[f20term]
                f20dat[f20key]['Selected?'] = f20rec['Selected?']
                f20dat[f20key]['Frequency (%)'] = f20rec['Frequency (%)']

        # shall contain only not selected variables
        f20sel = sorted([k for k in f20dat.keys() if (f20dat[k]['Selected?'] == 'Y')])

        assert len(f20sel) == 0

#        # write temporary info for further reference if needed
#        with open('freqvars_%s_OLS.txt' % ss, 'wb') as f:
#            fdict = {'f10' : {}, 'f20' : f20dat}
#            pprint.pprint(fdict, f, indent=2)


if __name__ == '__main__':
    main()
