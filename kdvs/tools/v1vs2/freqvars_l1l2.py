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
:class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2`. NOTE: there is known discrepancy
due to relative order of variables that share the same frequency; this has been
addressed by comparing in sets.
"""
import csv
import os
import pprint

dir10_root = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/'
dir10_data = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/postprocessing_results'
dir20_root = '/home/grzegorz/KDVS2.0/KDVS_output'
dir20_data = '/home/grzegorz/KDVS2.0/KDVS_output/ss_results'

# NOTE: copied directly from configuration file
mu_number = 3

# NOTE: list of common terms was compiled manually
common_terms = [
    '0000166', '0000287', '0003677', '0003682', '0003697', '0003702', '0003705',
    '0003714', '0003723', '0003725', '0003743', '0003746', '0003824', '0003924',
    '0004197', '0004386', '0004601', '0004672', '0004674', '0004812', '0004866',
    '0004867', '0004930', '0005083', '0005085', '0005089', '0005488', '0005515',
    '0005518', '0008233', '0008565', '0015293', '0016301', '0016563', '0016773',
    '0016787', '0016829', '0016831', '0016874', '0017124', '0020037', '0030145',
    '0030674', '0030955', '0042393', '0042802', '0042803', '0043565', '0046872',
    '0046982', '0046983', '0050662', '0051082', '0051087', '0051536'
]

f10_names = [('%s__freqs_mu%d.txt' % (t, m), t, m) for t in common_terms for m in range(mu_number)]
f10_paths = [(os.path.join(dir10_data, '%s__' % t, fn), t, m) for fn, t, m in f10_names]
f20_names = [('%s_mu%d__vars_freqs.txt' % (t, m), t, m) for t in common_terms for m in range(mu_number)]
f20_paths = [(os.path.join(dir20_data, '%s' % t, fn), t, m) for fn, t, m in f20_names]

f10 = 'Variable Name   Gene Symbols(s)   Entrez Gene ID(s)  GenBank Accession #   Frequency (%)'
f20 = 'Variable Name    Frequency (%)    Gene Symbols(s)    Representative Public ID    GenBank Accession #    Entrez Gene ID(s)    Ensembl Gene ID(s)    RefSeq ID(s)'

f10k = 'Variable Name'
f20k = 'Variable Name'

f10_fields = ['Variable Name', 'Gene Symbols(s)', 'Entrez Gene ID(s)', 'GenBank Accession #', 'Frequency (%)']

f10_to_f20 = {
    'Variable Name' : 'Variable Name',
    'Gene Symbols(s)' : 'Gene Symbols(s)',
    'Entrez Gene ID(s)' : 'Entrez Gene ID(s)',
    'GenBank Accession #' : 'GenBank Accession #',
    'Frequency (%)' : 'Frequency (%)',
}

def _compareFreqs(f10_path, f10_term, f10_mu_idx, f20_path, f20_term, f20_mu_idx):

    assert f10_term==f20_term
    assert f10_mu_idx==f20_mu_idx

    try:
        f10_file = open(f10_path, 'rb')
    except:
        return
    try:
        f20_file = open(f20_path, 'rb')
    except:
        return

    # skip utility/comment line
    f10_file.next()
    f20_file.next()

    f10_csv = csv.DictReader(f10_file, fieldnames=f10_fields, dialect='excel-tab')
    f20_csv = csv.DictReader(f20_file, dialect='excel-tab')

    f10dat = dict()

    for f10rec in f10_csv:
        f10key = f10rec[f10k]
        f10dat[f10key] = dict()
        for f10term, f20term in f10_to_f20.iteritems():
            common_term = f10term
            f10dat[f10key][common_term] = f10rec[f10term]
        f10dat[f10key]['Selected?'] = 'Y'

    f20dat = dict()

    for f20rec in f20_csv:
        f20key = f20rec[f20k]
        f20dat[f20key] = dict()
        for f10term, f20term in f10_to_f20.iteritems():
            common_term = f10term
            f20dat[f20key][common_term] = f20rec[f20term]
        f20dat[f20key]['Selected?'] = f20rec['Selected?']


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

    # write temporary info for further reference if needed
#    with open('freqvars_%s_%d.txt' % (f10_term, f10_mu_idx), 'wb') as f:
#        fdict = {'f10' : f10dat, 'f20' : f20dat}
#        pprint.pprint(fdict, f, indent=2)

    f10_file.close()
    f20_file.close()



def main():

    # if all equalities are satisfied there should be no output from the script
    # for any inequality AssertionError is thrown

    for (f1, t1, m1), (f2, t2, m2) in zip(f10_paths, f20_paths):
        _compareFreqs(f1, t1, m1, f2, t2, m2)

if __name__ == '__main__':
    main()
