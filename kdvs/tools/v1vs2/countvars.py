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
Check if variables are counted in exactly the same way for both
:class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2` and :class:`~kdvs.fw.impl.stat.L1L2.L1L2_OLS`.
NOTE: there is known discrepancy between v1 and v2 regarding how variables coming
from 'not selected' data subsets are counted.
See :mod:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq`
for more details.
"""
import cPickle
import csv
import os
import pprint

dir10_root = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/'
dir10_data = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/postprocessing_results'
dir20_root = '/home/grzegorz/KDVS2.0/KDVS_output'
dir20_data = '/home/grzegorz/KDVS2.0/KDVS_output/ss_results'

# NOTE: copied directly from configuration file
mu_number = 3

sel10_l1l2_names = ['selected_vars_hist_SIZE_ABOVE_%d.txt' % (m) for m in range(mu_number)]
sel10_l1l2_paths = [os.path.join(dir10_data, fn) for fn in sel10_l1l2_names]
sel20_l1l2_names = ['L1L2_L1L2_mu%d_vars_count_sel.txt' % (m) for m in range(mu_number)]
sel20_l1l2_paths = [os.path.join(dir20_data, fn) for fn in sel20_l1l2_names]

nsel10_l1l2_names = ['not_selected_vars_hist_SIZE_ABOVE_%d.txt' % (m) for m in range(mu_number)]
nsel10_l1l2_paths = [os.path.join(dir10_data, fn) for fn in nsel10_l1l2_names]
nsel20_l1l2_names = ['L1L2_L1L2_mu%d_vars_count_nsel.txt' % (m) for m in range(mu_number)]
nsel20_l1l2_paths = [os.path.join(dir20_data, fn) for fn in nsel20_l1l2_names]

sel10_ols_name = 'selected_vars_hist_SIZE_BELOW_0.txt'
sel10_ols_path = os.path.join(dir10_data, sel10_ols_name)
sel20_ols_name = 'L1L2_OLS_NullDOF_vars_count_sel.txt'
sel20_ols_path = os.path.join(dir20_data, sel20_ols_name)

nsel20_ols_name = 'L1L2_OLS_NullDOF_vars_count_nsel.txt'
nsel20_ols_path = os.path.join(dir20_data, nsel20_ols_name)


# selected, l1l2
sel10_l1l2_fields = ['Variable Name', 'Gene Symbols(s)', '# Times Selected']
sel20_l1l2_header = 'Variable Name    # Times Selected    Gene Symbols(s)    Representative Public ID    GenBank Accession #    Entrez Gene ID(s)    Ensembl Gene ID(s)    RefSeq ID(s)'
sel10_l1l2_to_sel20_l1l2 = {
    'Variable Name' : 'Variable Name',
    'Gene Symbols(s)' : 'Gene Symbols(s)',
    '# Times Selected' : '# Times Selected',
}
sel10_l1l2_k = 'Variable Name'
sel20_l1l2_k = 'Variable Name'


# not selected, l1l2
nsel10_l1l2_fields = ['Variable Name', 'Gene Symbols(s)', '# Times Not Selected']
nsel20_l1l2_header = 'Variable Name    # Times Not Selected    Gene Symbols(s)    Representative Public ID    GenBank Accession #    Entrez Gene ID(s)    Ensembl Gene ID(s)    RefSeq ID(s)'
nsel10_l1l2_to_nsel20_l1l2 = {
    'Variable Name' : 'Variable Name',
    'Gene Symbols(s)' : 'Gene Symbols(s)',
    '# Times Not Selected' : '# Times Not Selected',
}
nsel10_l1l2_k = 'Variable Name'
nsel20_l1l2_k = 'Variable Name'



def _compare_l1l2_sel(sel10_path, sel20_path, mu_idx):

    sel10_file = open(sel10_path, 'rb')
    sel20_file = open(sel20_path, 'rb')

    # skip header/comment lines
    sel10_file.next()

    sel10_csv = csv.DictReader(sel10_file, fieldnames=sel10_l1l2_fields, dialect='excel-tab')
    sel20_csv = csv.DictReader(sel20_file, dialect='excel-tab')

    sel10dat = dict()

    for sel10rec in sel10_csv:
        sel10key = sel10rec[sel10_l1l2_k]
        sel10dat[sel10key] = dict()
        for sel10term, sel20term in sel10_l1l2_to_sel20_l1l2.iteritems():
            common_term = sel10term
            sel10dat[sel10key][common_term] = sel10rec[sel10term]

    sel20dat = dict()

    for sel20rec in sel20_csv:
        sel20key = sel20rec[sel20_l1l2_k]
        sel20dat[sel20key] = dict()
        for sel10term, sel20term in sel10_l1l2_to_sel20_l1l2.iteritems():
            common_term = sel10term
            sel20dat[sel20key][common_term] = sel20rec[sel20term]

    # do we count exactly the same variables?
    sel10_vars = sorted(sel10dat.keys())
    sel20_vars = sorted(sel20dat.keys())
    assert sel10_vars == sel20_vars

    # do we have exactly the same counts?
    sel10_counts = [sel10dat[v]['# Times Selected'] for v in sel10_vars]
    sel20_counts = [sel20dat[v]['# Times Selected'] for v in sel20_vars]
    assert sel10_counts == sel20_counts

    # do we report exactly the same gene symbols?
    sel10_gss = [sorted(sel10dat[v]['Gene Symbols(s)'].split('/')) for v in sel10_vars]
    sel20_gss = [sorted(sel20dat[v]['Gene Symbols(s)'].split(';')) for v in sel20_vars]

    # TODO: known discrepancies between HGNC versions used in v10 and v20

#    for v10, v20, gss10, gss20 in zip(sel10_vars, sel20_vars, sel10_gss, sel20_gss):
#        if gss10 != gss20:
#            print mu_idx, v10, v20, gss10, gss20

    # write temporary info for further reference if needed
#    with open('sel_l1l2_diff_%d.txt' % mu_idx, 'wb') as f:
#        u = {'sel10' : sel10dat, 'sel20' : sel20dat}
#        pprint.pprint(u, f, indent=2)

    sel10_file.close()
    sel20_file.close()


def _compare_l1l2_notsel(nsel10_path, nsel20_path, mu_idx):

    nsel10_file = open(nsel10_path, 'rb')
    nsel20_file = open(nsel20_path, 'rb')

    # skip header/comment lines
    nsel10_file.next()

    nsel10_csv = csv.DictReader(nsel10_file, fieldnames=nsel10_l1l2_fields, dialect='excel-tab')
    nsel20_csv = csv.DictReader(nsel20_file, dialect='excel-tab')

    nsel10dat = dict()

    for nsel10rec in nsel10_csv:
        nsel10key = nsel10rec[nsel10_l1l2_k]
        nsel10dat[nsel10key] = dict()
        for nsel10term, nsel20term in nsel10_l1l2_to_nsel20_l1l2.iteritems():
            common_term = nsel10term
            nsel10dat[nsel10key][common_term] = nsel10rec[nsel10term]

    nsel20dat = dict()

    for nsel20rec in nsel20_csv:
        nsel20key = nsel20rec[nsel20_l1l2_k]
        nsel20dat[nsel20key] = dict()
        for nsel10term, nsel20term in nsel10_l1l2_to_nsel20_l1l2.iteritems():
            common_term = nsel10term
            nsel20dat[nsel20key][common_term] = nsel20rec[nsel20term]

    # do we not count exactly the same variables?
    nsel10_vars = sorted(nsel10dat.keys())
    nsel20_vars = sorted(nsel20dat.keys())

    # IMPORTANT NOTE!
    # this part of tests may fail if behavior of L1L2-related inner selector
    # has been modified to reflect old counting algorithm used in KDVS v1.0
    # see kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq
    # for more details

# debug code
#    print len(nsel10_vars), len(nsel20_vars)
#    nsel10set = set(nsel10_vars)
#    nsel20set = set(nsel20_vars)
#    nsel_common = nsel10set & nsel20set
#    print len(nsel_common), len(nsel10set - nsel_common), len(nsel20set - nsel_common)
# debug code

    assert nsel10_vars == nsel20_vars

    # do we have exactly the same counts?
    nsel10_counts = [nsel10dat[v]['# Times Not Selected'] for v in nsel10_vars]
    nsel20_counts = [nsel20dat[v]['# Times Not Selected'] for v in nsel20_vars]
    assert nsel10_counts == nsel20_counts

    # write temporary info for further reference if needed
#    with open('nsel_l1l2_diff_%d.txt' % mu_idx, 'wb') as f:
#        u = {'nsel10' : nsel10dat, 'nsel20' : nsel20dat}
#        pprint.pprint(u, f, indent=2)

    nsel10_file.close()
    nsel20_file.close()


def _compare_ols_sel(sel10_path, sel20_path):

    sel10_file = open(sel10_path, 'rb')
    sel20_file = open(sel20_path, 'rb')

    # skip header/comment lines
    sel10_file.next()

    sel10_csv = csv.DictReader(sel10_file, fieldnames=sel10_l1l2_fields, dialect='excel-tab')
    sel20_csv = csv.DictReader(sel20_file, dialect='excel-tab')

    sel10dat = dict()

    for sel10rec in sel10_csv:
        sel10key = sel10rec[sel10_l1l2_k]
        sel10dat[sel10key] = dict()
        for sel10term, sel20term in sel10_l1l2_to_sel20_l1l2.iteritems():
            common_term = sel10term
            sel10dat[sel10key][common_term] = sel10rec[sel10term]

    sel20dat = dict()

    for sel20rec in sel20_csv:
        sel20key = sel20rec[sel20_l1l2_k]
        sel20dat[sel20key] = dict()
        for sel10term, sel20term in sel10_l1l2_to_sel20_l1l2.iteritems():
            common_term = sel10term
            sel20dat[sel20key][common_term] = sel20rec[sel20term]

    # do we count exactly the same variables?
    sel10_vars = sorted(sel10dat.keys())
    sel20_vars = sorted(sel20dat.keys())
    assert sel10_vars == sel20_vars

    # do we have exactly the same counts?
    sel10_counts = [sel10dat[v]['# Times Selected'] for v in sel10_vars]
    sel20_counts = [sel20dat[v]['# Times Selected'] for v in sel20_vars]
    assert sel10_counts == sel20_counts

    # do we report exactly the same gene symbols?
    sel10_gss = [sorted(sel10dat[v]['Gene Symbols(s)'].split('/')) for v in sel10_vars]
    sel20_gss = [sorted(sel20dat[v]['Gene Symbols(s)'].split(';')) for v in sel20_vars]

    # TODO: known discrepancies between HGNC versions used in v10 and v20

#    for v10, v20, gss10, gss20 in zip(sel10_vars, sel20_vars, sel10_gss, sel20_gss):
#        if gss10 != gss20:
#            print v10, v20, gss10, gss20

    # write temporary info for further reference if needed
#    with open('sel_l1l2_diff_%d.txt' % mu_idx, 'wb') as f:
#        u = {'sel10' : sel10dat, 'sel20' : sel20dat}
#        pprint.pprint(u, f, indent=2)

    sel10_file.close()
    sel20_file.close()


# deserialization from V1.0
def _pzp_deserialize_obj(encoded_object):
    import zlib
    # unpickle, unzip, unpickle
    pass1 = cPickle.loads(encoded_object)
    pass2 = zlib.decompress(pass1)
    pass3 = cPickle.loads(pass2)
    return pass3

def _pzp_deserialize(obj_path):
    with open(obj_path, 'rb') as ifo:
        decoded_obj = _pzp_deserialize_obj(ifo.read())
    return decoded_obj

def _compare_ols_notsel(nsel20_path):

    # NOTE: since we do not report not selected OLS variables, this part requires:
    # obtaining variables from all not selected subsets in v10, computing not
    # selected variables manually, and computing histogram manually

    v10_ols_stats_path = os.path.join(dir10_data, 'SIZE_BELOW_stats')
    v10_ols_stats_file = open(v10_ols_stats_path, 'rb')
    v10_ols_stats = cPickle.load(v10_ols_stats_file)
    v10_ols_stats_file.close()

#    v10_global_stat_path = os.path.join(dir10_data, 'global_stat')
#    v10_global_stat_file = open(v10_global_stat_path, 'rb')
#    v10_global_stat = cPickle.load(v10_global_stat_file)
#    v10_global_stat_file.close()

    v10_nps = [v10np.split('__')[0] for v10np in v10_ols_stats['nodes_not_passing_thr_err']]
    v10vars = dict()
    for v10_np in v10_nps:
        v10_subm_path = os.path.join(dir10_root, '%s__' % v10_np)
        v10_subm_metaobj = _pzp_deserialize(v10_subm_path)
        v10_vars = v10_subm_metaobj['__kdvs__matrix'].keys()
        v10vars[v10_np] = v10_vars

    v10dat = dict()
    # simulate counting of not selected variables similar to used in v10
    for vv in v10vars.values():
        for v in vv:
            if v not in v10dat:
                v10dat[v] = dict()
                v10dat[v]['Variable Name'] = v
                v10dat[v]['# Times Not Selected'] = 1
                v10dat[v]['Gene Symbols(s)'] = ''
            else:
                v10dat[v]['# Times Not Selected'] += 1
    for v10v in v10dat.values():
        v10v['# Times Not Selected'] = str(v10v['# Times Not Selected'])

    v20_file = open(nsel20_path, 'rb')
    v20_csv = csv.DictReader(v20_file, dialect='excel-tab')

    v20dat = dict()

    for v20rec in v20_csv:
        v20key = v20rec[nsel20_l1l2_k]
        v20dat[v20key] = dict()
        for v10term, v20term in nsel10_l1l2_to_nsel20_l1l2.iteritems():
            common_term = v10term
            v20dat[v20key][common_term] = v20rec[v20term]

    # do we not count exactly the same variables?
    v10_vars = sorted(v10dat.keys())
    v20_vars = sorted(v20dat.keys())
    assert v10_vars == v20_vars

    # do we have exactly the same "not counts"?
    v10_ncounts = [v10dat[v]['# Times Not Selected'] for v in v10_vars]
    v20_ncounts = [v20dat[v]['# Times Not Selected'] for v in v20_vars]
    assert v10_ncounts == v20_ncounts

    # write temporary info for further reference if needed
#    with open('nsel_ols_diff.txt', 'wb') as f:
#        v = {'v10' : v10dat, 'v20' : v20dat}
#        pprint.pprint(v, f, indent=2)

    v20_file.close()


def main():

    # if all equalities are satisfied there should be no output from the script
    # for any inequality AssertionError is thrown

    # NOTE: "compare_l1l2_notsel" may fail depending on if and how inner selector
    # has been tweaked; see note inside

    # OK
    for i, s1, s2 in zip(range(mu_number), sel10_l1l2_paths, sel20_l1l2_paths):
        _compare_l1l2_sel(s1, s2, i)

    # OK
    _compare_ols_sel(sel10_ols_path, sel20_ols_path)

    # OK
    for i, s1, s2 in zip(range(mu_number), nsel10_l1l2_paths, nsel20_l1l2_paths):
        _compare_l1l2_notsel(s1, s2, i)

    # OK
    _compare_ols_notsel(nsel20_ols_path)


if __name__ == '__main__':
    main()
