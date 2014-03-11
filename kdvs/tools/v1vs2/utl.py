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
Check if UTL (unified term lists) for :class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2`
and :class:`~kdvs.fw.impl.stat.L1L2.L1L2_OLS` are reported in the same way.
See :class:`~kdvs.fw.impl.report.L1L2.L1L2_PKC_UTL_Reporter` for more details.
NOTE: there is known discrepancy due to different versions of Gene Ontology
release; this has been addressed by printing those differences and manual
verification.
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

utl10_names = ['unified_term_list_SIZE_ABOVE_%d_SIZE_BELOW_0.txt' % m for m in range(mu_number)]
utl10_paths = [os.path.join(dir10_data, fn) for fn in utl10_names]
utl20_names = ['UTL_L1L2_L1L2_mu%d_%d_L1L2_OLS_NullDOF_0.txt' % (m, m) for m in range(mu_number)]
utl20_paths = [os.path.join(dir20_data, fn) for fn in utl20_names]

u10 = 'GO term ID    GO term name    Tot vars    Sel vars    Error estimate    #TP    #TN    #FP    #FN    MCC'
u20 = 'PKC ID    Subset Name    Selected?    PKC Name    Total Vars    Selected Vars    Error Estimate    #TP    #TN    #FP    #FN    MCC'

u10k = 'GO term ID'
u20k = 'PKC ID'

u10_to_u20 = {
    'GO term ID' : 'PKC ID',
    'GO term name' : 'PKC Name',
    'Tot vars' : 'Total Vars',
    'Sel vars' : 'Selected Vars',
    'Error estimate' : 'Error Estimate',
    '#TP' : '#TP',
    '#TN' : '#TN',
    '#FP' : '#FP',
    '#FN' : '#FN',
    'MCC' : 'MCC',
}

def _compareUTL(utl10_path, utl20_path, mu_idx):

    utl10_file = open(utl10_path, 'rb')
    utl20_file = open(utl20_path, 'rb')

    # skip comment lines
    for _ in range(3):
        utl20_file.next()

    utl10_csv = csv.DictReader(utl10_file, dialect='excel-tab')
    utl20_csv = csv.DictReader(utl20_file, dialect='excel-tab')

    u10dat = dict()

    for u10rec in utl10_csv:
        u10key = u10rec[u10k]
        u10dat[u10key] = dict()
        for u10term, u20term in u10_to_u20.iteritems():
            common_term = u10term
            u10dat[u10key][common_term] = u10rec[u10term]
        # u10 reports only selected terms without hacking
        u10dat[u10key]['Selected?'] = 'Y'

    u20dat = dict()

    for u20rec in utl20_csv:
        u20key = u20rec[u20k]
        u20dat[u20key] = dict()
        for u10term, u20term in u10_to_u20.iteritems():
            common_term = u10term
#            u10dat[u10key][common_term] = u10rec[u10term]
            u20dat[u20key][common_term] = u20rec[u20term]
        u20dat[u20key]['Selected?'] = u20rec['Selected?']

    # u10 contains only selected terms; does u20 reports all selected ones too?
    u10sel = sorted([k for k in u10dat.keys() if u10dat[k]['Selected?'] == 'Y'])
    u20sel = sorted([k for k in u20dat.keys() if u20dat[k]['Selected?'] == 'Y'])
    assert u10sel == u20sel

    u10set = set([k for k in u10dat.keys()])
    u20set = set([k for k in u20dat.keys()])

    # does u10 contain something more than u20? it should not
    u10_minus_u20 = u10set - u20set
    assert len(u10_minus_u20) == 0

    # does u20 reports remaining ones as not selected?
    # NOTE: we do not check directly for N since technique may generate SELECTIONERROR
    u20_minus_u10 = u20set - u10set
    statuses = set([u20dat[k]['Selected?'] for k in u20_minus_u10])
    assert 'Y' not in statuses

    # does any record differ between u10 and u20 selected terms?
    for u10key, u20key in zip(u10sel, u20sel):
        u10_inddat = u10dat[u10key]
        u20_inddat = u20dat[u20key]
        if u10_inddat != u20_inddat:
            print 'DIFF (', u10key, u20key, ')'
            for u10r in u10_inddat.keys():
                if u10_inddat[u10r] != u20_inddat[u10r]:
                    print '\t', u10r, ':', u10_inddat[u10r], '<>', u20_inddat[u10r]

    # write temporary info for further reference if needed
    with open('utl_diff_%d.txt' % mu_idx, 'wb') as f:
        u = {'u10' : u10dat, 'u20' : u20dat}
        pprint.pprint(u, f, indent=2)

    utl10_file.close()
    utl20_file.close()


def main():

    for i, u1, u2 in zip(range(mu_number), utl10_paths, utl20_paths):
        _compareUTL(u1, u2, i)

if __name__ == '__main__':
    main()
