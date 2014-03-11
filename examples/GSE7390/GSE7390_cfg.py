# example configuration file

# ---- import section

import l1l2py

# ---- content section

# ---- 1. job container definition

# ---- simple job container that does not use any parallelization and just
# ---- executes all jobs in given order
# ---- slowest but requires no external libraries or environments
job_container_type = 'kdvs.fw.impl.job.SimpleJob.SimpleJobContainer'
job_container_cfg = {}

# ---- this job container can be used if PPlus is installed
# job_container_type = 'kdvs.fw.impl.job.PPlusJob.PPlusJobContainer'

# ---- configuration for PPlus job container
# job_container_cfg = {
# ---- run jobs locally? (if PPlkus installed on single machine)
#    'debug' : True,
# ---- run jobs in parallel? (if PPlus installed in P2P environment)
#    'debug' : False,
# ---- number of processors dedicated to executing jobs (if on single machine)
# ---- number of machines accessible in P2P environment  (if in P2P)
#    'local_workers_number' : 6,
#    }

# ---- 2. experiment profile definition

# ---- instance of experiment profile
experiment_profile = 'kdvs.fw.impl.app.Profile.MA_GO_PROFILE'

# ---- experiment profile configuration
experiment_profile_inst = {
    # ---- data section
    'annotation_file' : {
        'path' : 'examples/GSE7390/GPL96.txt.bz2',
        'metadata' : {
            'delimiter' : '\t',
            'comment' : '#',
        },
        'indexes' : ('ID', 'Representative Public ID', 'Gene Symbol'),
    },
    'gedm_file' : {
        'path' : 'examples/GSE7390/GSE7390.txt.bz2',
        'metadata' : {
            'delimiter' : None,
            'comment' : '#',
        },
        # special value -- index only by ID column
        'indexes' : None,
    },
    'labels_file' : {
        # NOTE: labels file can be omitted entirely (e.g. for regression experiments)
        # by providing None as a path
        'path' : 'examples/GSE7390/GSE7390_labels.csv.txt',
        'metadata' : {
            'delimiter' : None,
            'comment' : '#',
        },
        'indexes' : (),
    },

    # ---- GO section
    'go_domain' : 'MF',

    # ---- instances section
    'subset_categorizers' : {
        'SCNull' : {
            'kdvs.fw.impl.data.Null.NullCategorizer' : {
                'ID' : 'NC',
                'null_category' : '__all__',
            },
        },
        'SCSizeThreshold' : {
            'kdvs.fw.impl.data.SubsetSize.SubsetSizeCategorizer' : {
                'ID' : 'SSC32',
                'size_lesser_category' : '<=',
                'size_greater_category' : '>',
                'size_threshold' : 32,
            },
        },
    },

    'subset_orderers' : {
        'SONull' : {
            'kdvs.fw.impl.data.Null.NullOrderer' : {
            },
        },
        'SOSizeDecreasing' : {
            'kdvs.fw.impl.data.SubsetSize.SubsetSizeOrderer' : {
                'descending' : True,
            },
        },
    },

    'statistical_techniques' : {
        'L1L2_OLS' : {
            'kdvs.fw.impl.stat.L1L2.L1L2_OLS' : {
                # ---- individual parameters
                'error_func' : l1l2py.tools.balanced_classification_error,
                'return_predictions' : True,
                # ---- global parameters
                # use null DOF
                'global_degrees_of_freedom' : None,
                # ---- job related parameters
                # is job importable for remote job containers?
                'job_importable' : False,
            },
        },
        'L1L2_L1L2' : {
            'kdvs.fw.impl.stat.L1L2.L1L2_L1L2' : {
                # ---- individual parameters
                # external splits
                'external_k' : 4,
                # internal splits
                'internal_k' : 3,
                # tau min, max, number, range
                'tau_min_scale' : 1. / 3,
                'tau_max_scale' : 1. / 8,
                'tau_number' : 10,
                'tau_range_type' : 'geometric',
                 # mu min, max, number, range
                'mu_scaling_factor_min' : 0.005,
                'mu_scaling_factor_max' : 1,
                'mu_number' : 3,
                'mu_range_type' : 'geometric',
                 # lambda min, max, number, range
                'lambda_min' : 1e-1,
                'lambda_max' : 1e4,
                'lambda_range_type' : 'geometric',
                'lambda_number' : 15,
                 # specific lambda range if desired, None otherwise
                'lambda_range' : None,
                # error functions
                'error_func' : l1l2py.tools.balanced_classification_error,
                'cv_error_func' : l1l2py.tools.balanced_classification_error,
                # sparse/regularized solution (mutually exclusive)
                'sparse' : True,
                'regularized' : False,
                # normalizers
                'data_normalizer' : l1l2py.tools.center,
                'labels_normalizer' : None,
                # return predictions?
                'return_predictions' : True,
                # ---- global parameters
                # here to use mu_number value
                'global_degrees_of_freedom' : tuple(['mu%d' % i for i in range(3)]),
                # placeholder for external splits
                'ext_split_sets' : None,
                # ---- job related parameters
                # is job importable for remote job containers?
#                'job_importable' : True,
                'job_importable' : False,
            },
        },
        'L1L2_RLS' : {
            'kdvs.fw.impl.stat.L1L2.L1L2_RLS' : {
                # ---- individual parameters
                # external splits
                'external_k' : 4,
                 # lambda min, max, number, range
                'lambda_min' : 1e-1,
                'lambda_max' : 1e4,
                'lambda_range_type' : 'geometric',
                'lambda_number' : 15,
                 # specific lambda range if desired, None otherwise
                'lambda_range' : None,
                # error function(s)
                'error_func' : l1l2py.tools.balanced_classification_error,
                # normalizers
                'data_normalizer' : l1l2py.tools.center,
                'labels_normalizer' : None,
                # return predictions?
                'return_predictions' : True,
                # ---- global parameters
                # use null DOF
                'global_degrees_of_freedom' : None,
                # placeholder for external splits
                'ext_split_sets' : None,
                # ---- job related parameters
                # is job importable for remote job containers?
#                'job_importable' : True,
                'job_importable' : False,
            },
        },
    },

    'subset_outer_selectors' : {
        'PKCSelector_ClsErrThr' : {
            'kdvs.fw.impl.stat.PKCSelector.OuterSelector_ClassificationErrorThreshold' : {
                'error_threshold' : 0.3,
            },
        },
    },

    'subset_inner_selectors' : {
        'VarSelector_ClsErrThr_AllVars' : {
            'kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_AllVars' : {
            },
        },
        'VarSelector_ClsErrThr_L1L2_VarsFreqThr' : {
            'kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_L1L2_VarsFreq' : {
                'frequency_threshold' : 0.0,
                # set to False for compatibility with KDVS v1.0 reports
                'pass_variables_for_nonselected_pkcs' : True,
            }
        }
    },

    'reporters' : {
        'L1L2_VarFreq_Reporter' : {
            'kdvs.fw.impl.report.L1L2.L1L2_VarFreq_Reporter' : {
            }
        },
        'L1L2_PKC_Reporter' : {
            'kdvs.fw.impl.report.L1L2.L1L2_PKC_Reporter' : {
            }
        },
        'L1L2_PKC_UTL_Reporter' : {
            'kdvs.fw.impl.report.L1L2.L1L2_PKC_UTL_Reporter' : {
            }
        },
        'L1L2_VarCount_Reporter' : {
            'kdvs.fw.impl.report.L1L2.L1L2_VarCount_Reporter' : {
            }
        },
    },

    'envops' : {
        'L1L2_UniformExtSplitProvider_SCNull' : {
            'kdvs.fw.impl.envop.L1L2.L1L2_UniformExtSplitProvider' : {
                'enclosingCategorizerID' : 'SCNull',
                'extSplitParamName' : 'external_k',
                'extSplitPlaceholderParam' : 'ext_split_sets',
            }
        },
    },


    # ---- operations section
    'subset_hierarchy_categorizers_chain' : (
        'SCNull',
        'SCSizeThreshold'
    ),

    'subset_hierarchy_components_map' : {
        'SCNull' : {
            '__all__' : {
                'orderer' : 'SOSizeDecreasing',
                'technique' : None,
                'outer_selector' : None,
                'inner_selector' : None,
                'reporter' : ['L1L2_PKC_UTL_Reporter'],
                'preenvop' : ['L1L2_UniformExtSplitProvider_SCNull'],
#                'preenvop' : [],
                'postenvop' : [],
                'misc' : {
                },
            },
        },
        'SCSizeThreshold' : {
            '<=' : {
                'orderer' : 'SONull',
#                'technique' : 'L1L2_OLS',
                'technique' : 'L1L2_RLS',
                'outer_selector' : 'PKCSelector_ClsErrThr',
                'inner_selector' : 'VarSelector_ClsErrThr_AllVars',
                'reporter' : ['L1L2_VarFreq_Reporter', 'L1L2_VarCount_Reporter', 'L1L2_PKC_Reporter'],
                'preenvop' : [],
                'postenvop' : [],
                'misc' : {
                    # number of test elements to consider
                    'test_mode_elems' : 1,
                    # test elements: take first/take last
                    'test_mode_elems_order' : 'first',
                },
            },
            '>' : {
                'orderer' : 'SONull',
                'technique' : 'L1L2_L1L2',
                'outer_selector' : 'PKCSelector_ClsErrThr',
                'inner_selector' : 'VarSelector_ClsErrThr_L1L2_VarsFreqThr',
                'reporter' : ['L1L2_VarFreq_Reporter', 'L1L2_VarCount_Reporter', 'L1L2_PKC_Reporter'],
                'preenvop' : [],
                'postenvop' : [],
                'misc' : {
                    # number of test elements to consider
                    'test_mode_elems' : 1,
#                    'test_mode_elems' : 30,
                    # test elements: take first/take last
                    'test_mode_elems_order' : 'last',
                },
            },
        },
    },

}

# ---- 3. mapping definitions

# ---- map between prior knowledge concepts and measurement IDs
pkcidmap_type = 'kdvs.fw.impl.map.PKCID.GPL.PKCIDMapGOGPL'

# ---- map between gene symbols and expression measurements IDs

# ---- simplest map that follows only annotations
# geneidmap_type = 'kdvs.fw.impl.map.GeneID.GPL.GeneIDMapGPL'
# ---- map that follows original protocol implemented in KDVS v 1.0
geneidmap_type = 'kdvs.fw.impl.map.GeneID.HGNC_GPL.GeneIDMapHGNCGPL'
