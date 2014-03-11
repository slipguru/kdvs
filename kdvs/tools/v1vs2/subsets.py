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
Check that all generated subset information is the same.
"""
from kdvs.core.util import deserializeObj
import os

dir10_root = '/home/grzegorz/KDVS2.0-1vs2/1.0/feb465c2b89611e2bf935cf9dd7722c1_disk_data/'
dir10_subsets_dir = dir10_root

# submatrix dictionary keys:
# __kdvs__go_namespace - Gene Ontology domain that contain associated GO term
# __kdvs__go_term - short identifier of GO term (i.e. 0000001, not GO:0000001)
# __kdvs__samples - list of all samples, as loaded from GEDM (see get_GEDM_samples for more details)
# __kdvs__matrix - specific submatrix data, as dictionary of rows of expression values, keyed by probeset names (see get_GEDM_rows for more details)

dir20_root = '/home/grzegorz/KDVS2.0/KDVS_output'
dir20_subsets_dict = '/home/grzegorz/KDVS2.0/KDVS_output/debug/SUBSETS'
# 'GO:0000009'-> 'mat': '0000009', 'shape': (1, 72), 'vars': ['218444_at']

# deserialization from V1.0
def _pzp_deserialize_obj(encoded_object):
    import zlib
    import cPickle
    # unpickle, unzip, unpickle
    pass1 = cPickle.loads(encoded_object)
    pass2 = zlib.decompress(pass1)
    pass3 = cPickle.loads(pass2)
    return pass3

def _pzp_deserialize(obj_path):
    with open(obj_path, 'rb') as ifo:
        decoded_obj = _pzp_deserialize_obj(ifo.read())
    return decoded_obj

def main():

    # get v20 dictionary of subsets
    with open(dir20_subsets_dict, 'rb') as f:
        subsets_v20 = deserializeObj(f)

    for subm in subsets_v20.values():
        v20_mat = subm['mat']
        v20_vars = subm['vars']
        v10_id = '%s__' % v20_mat
        v10_subm_path = os.path.join(dir10_root, v10_id)
        v10_subm_metaobj = _pzp_deserialize(v10_subm_path)
        # check ID
        assert v10_subm_metaobj['__kdvs__go_term'] == v20_mat
        # check samples length
        assert len(v10_subm_metaobj['__kdvs__samples']) == subm['shape'][1]
        # check variables
        v10_vars = v10_subm_metaobj['__kdvs__matrix'].keys()
        assert len(v10_vars) == len(v20_vars)
        assert set(v10_vars) == set(v20_vars)
        assert sorted(v10_vars) == sorted(v20_vars)
        assert sorted(v10_vars) == v20_vars


if __name__ == '__main__':
    main()
