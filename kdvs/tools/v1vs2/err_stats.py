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
Check if all statistical details of :class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2`
are reported in the same way (up to those elements that are present in both v1 and v2).
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

utl10_names = ['SIZE_ABOVE_stats_mu%d.txt' % m for m in range(mu_number)]
utl10_paths = [os.path.join(dir10_data, fn) for fn in utl10_names]
utl20_names = ['L1L2_L1L2_mu%d_err_stats.txt' % (m) for m in range(mu_number)]
utl20_paths = [os.path.join(dir20_data, fn) for fn in utl20_names]

u10 = 'GO term ID,Mu,Mean TS,Std TS,Mean TR,Std TR,Med TS,Tot vars,Sel vars'
u20 = 'PKC ID    Subset Name    Selected?    Avg Error TS    Avg Error TR    Std Error TS    Std Error TR    Var Error TS    Med Error TS    Total Vars    Selected Vars'

u10k = 'GO term ID'
u20k = 'PKC ID'

u10_to_u20 = {
    'GO term ID' : 'PKC ID',
    'Mean TS' : 'Avg Error TS',
    'Std TS' : 'Std Error TS',
    'Mean TR' : 'Avg Error TR',
    'Std TR' : 'Std Error TR',
    'Med TS' : 'Med Error TS',
    'Tot vars' : 'Total Vars',
    'Sel vars' : 'Selected Vars',
}


def _compareStats(utl10_path, utl20_path, mu_idx):

    utl10_file = open(utl10_path, 'rb')
    utl20_file = open(utl20_path, 'rb')

    utl10_csv = csv.DictReader(utl10_file, dialect='excel')
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
            u10dat[u10key][common_term] = u10rec[u10term]
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
        assert u10_inddat == u20_inddat

    # write temporary info for further reference if needed
    with open('stats_diff_%d.txt' % mu_idx, 'wb') as f:
        u = {'u10' : u10dat, 'u20' : u20dat}
        pprint.pprint(u, f, indent=2)

    utl10_file.close()
    utl20_file.close()


def main():

    # if all equalities are satisfied there should be no output from the script
    # for any inequality AssertionError is thrown

    for i, u1, u2 in zip(range(mu_number), utl10_paths, utl20_paths):
        _compareStats(u1, u2, i)

if __name__ == '__main__':
    main()
