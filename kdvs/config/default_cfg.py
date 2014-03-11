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

# default configuration file

from kdvs.core.config import getDefaultDataRootPath
from kdvs.core.log import Logger

default_config_loaded = True

# ---- dynamic components

log_name = 'kdvs'
log_file = 'kdvs.log'
log_type_def_std = 'kdvs.core.log.StreamLogger'
log_type_def_file = 'kdvs.core.log.RotatingFileLogger'

experiment_profile = 'kdvs.fw.impl.app.Profile.NULL_PROFILE'
experiment_profile_inst = {
    }

job_container_type = 'kdvs.fw.impl.job.SimpleJob.SimpleJobContainer'
job_container_cfg = {
    }
storage_manager_type = 'kdvs.fw.StorageManager.StorageManager'
execution_environment_type = 'kdvs.core.env.LoggedExecutionEnvironment'
# execution_environment_exp_cfg = {
#    'logger' : 'kdvs.core.log.Logger',
#    }
execution_environment_exp_cfg = {
    'logger' : Logger(),
    }

job_group_manager_type = 'kdvs.fw.Job.JobGroupManager'
job_group_manager_cfg = {
    }

# ---- default storage identifiers

# default tablespace name where all data tables will be stored
data_db_id = 'DATA'
# default tablespace name where all mapping tables will be stored
map_db_id = 'MAPS'
# default tablespace name where all miscellaneous tables will be stored
misc_db_id = 'MISC'

# ---- default file entity keys

cfg_key = 'CFG'
ts_start_key = 'TS_START'
ts_end_key = 'TS_END'
pkcidmap_key = 'PKCIDMAP'
geneidmap_key = 'GENEIDMAP'
subsets_key = 'SUBSETS'
subsets_results_key = 'SUBSETS_RESULTS'
subset_hierarchy_key = 'SUBSET_HIERARCHY'
operations_map_key = 'OP_MAP'
jobID_map_key = 'JOBID_MAP'
submission_order_key = 'SUBMISSION_ORDER'
jobs_exceptions_key = 'JEXC'
jobs_misc_data_key = 'JC_MISC_DATA'
group_completion_key = 'GRCOMP'
technique2dof_key = 'TECH2DOF'
technique2ssname_key = 'TECH2SS'
outer_selection_key = 'OUTER_SELECTION'
inner_selection_key = 'INNER_SELECTION'
em2annotation_key = 'EM2ANNOTATION'
pkcid2ssname_key = 'PKCID2SS'

# job_group_callbacks_exceptions_key = 'GREXC'

misc_view_key = 'MISC'

# ---- default locations

dbm_location = 'db'
debug_output_location = 'debug'
jobs_location = 'jobs'
subsets_location = 'ss'
subsets_results_location = 'ss_results'
plots_sublocation = 'plots'

# ---- default statistical artefacts
unused_sample_label = 0
null_dof = 'NullDOF'

# ---- miscellaneous entities

pk_manager_dump_suffix = '_DUMP'
subset_results_suffix = '_RES'
subset_ds_suffix = '_DS'
jobs_raw_output_suffix = '_RAW_OUT'
txt_suffix = '.txt'
subset_submission_all_symbol = '__all__'
test_submission_listing_thr = 5

# ---- static data files
def_data_path = getDefaultDataRootPath()

# specification follows file name matching as interpreted by 'glob'
static_data_files = {
    # HGNC file contains naming information of genes
    'hgnc_file' : {
        'DBID' : 'HGNC',
        'spec' : ('HGNC', 'HGNC*.tsv*'),
        'path' : None,
        'fh' : None,
        'type' : 'DSV',
        'metadata' : {
            'delimiter' : '\t',
            'comment' : '#',
        },
        'loadToDB' : True,
        'indexes' : ('Approved Symbol', 'Previous Symbols', 'Synonyms'),
        'manager' : None,
    },
    # GO file contains graph of GO terms
    'go_file' : {
        'DBID' : 'GO',
        'spec' : ('GO', 'go_termdb*.obo-xml*'),
        'path' : None,
        'fh' : None,
        'type' : 'XML',
        'metadata' : None,
        'loadToDB' : False,
        'indexes' : (),
        'manager' : {
            'kdvs.fw.impl.pk.go.GeneOntology.GOManager' : {
                'configure' : {
                    'domains' : None,
                    'recognized_relations' : None,
                },
                'load' : {
                    'root_tag' : None,
                }
            }
        }
    }
}
