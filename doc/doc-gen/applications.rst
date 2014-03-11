.. _applications:

:tocdepth: 5

KDVS applications
*****************

This section describes the concrete KDVS applications.

.. _applications_experiment:

experiment.py
-------------

The application 'experiment.py' performs performs prior–knowledge–guided feature
selection and re–annotation, according to specified configuration. The feature
selection utilizes statistical techniques based on
`l1l2py <http://slipguru.disi.unige.it/Software/L1L2Py/>`__ library. It uses `Gene
Ontology <http://www.geneontology.org>`__ as prior knowledge source and
microarray gene expression as measured data. It is located in subdirectory
'**kdvs/bin**'.

The 'experiment.py' application has been built as a concrete subclass
:class:`~kdvs.bin.experiment.MA_GO_Experiment_App` of :class:`~kdvs.fw.impl.app.CmdLineApp.CmdLineApp`
class, that adds series of actions to :class:`~kdvs.core.env.LoggedExecutionEnvironment`
instance. For complete list of actions and description of each action refer to
API documentation.

.. _applications_componentinitializers:

Component initializers
++++++++++++++++++++++

The 'experiment.py' application uses the concept of `dynamic instantiation` of
certain components.

Many KDVS components are `parametrizable` (when subclasses of
:class:`~kdvs.core.util.Parametrizable`) or `configurable` (when subclasses of
:class:`~kdvs.core.util.Configurable`). This is needed when a class expects
many input parameters that may be given only at runtime and not in the class
definition itself.

When instance of :class:`~kdvs.core.util.Parametrizable` is created, the given
list of parameters is checked against the reference list. If they do not match
(i.e. some parameter is missing or is not present at the reference list), the
object will not be created. Here, `only parameters names` are checked.
When instance of :class:`~kdvs.core.util.Configurable` is created, the given
list of parameters is again checked against the reference list. However, not only
the parameters names are checked, but `types of values` as well. Refer to API
documentation for individual abstract classes.

The "`component initializer`" is a Python dictionary that has the following general
format::

    'class_import_path' : {
        'param1' : param1_val,
        'param2' : param2_val,
        # ...
        'paramN' : paramN_val,
    }

where '`class_import_path`' is the full import package path. For instance, to
instantiate one of reference statistical techniques inside the application,
such as :class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2`, the '`class_import_path`'
must be specified as follows::

    'kdvs.fw.impl.stat.L1L2.L1L2_L1L2'

and the example `component initializer` will be specified as follows (refer to
the API documentation for complete list of parameters)::

    'kdvs.fw.impl.stat.L1L2.L1L2_L1L2' : {
        'external_k' : 4,
        'internal_k' : 3,
        # ...
        # other parameters
        # ...
     }

This is interpreted as follows:

    * get string 'kdvs.fw.impl.stat.L1L2.L1L2_L1L2'
    * dynamically import class 'kdvs.fw.impl.stat.L1L2.L1L2_L1L2'
    * get all parameters from related dictionary
    * pass them according to the initialization rules for :class:`~kdvs.core.util.Parametrizable`/:class:`~kdvs.core.util.Configurable` instance

Many KDVS components used in 'experiment.py' application were built as
`parametrizable`/`configurable`, and `application profile` used by this application
utilizes `component initializers` frequently. Refer to API documentation for each
individual subclass for more details.

.. note::

    Unless otherwise stated, once the component instances are created, they `cannot`
    be altered. It is necessary to re--create the instance from scratch with new
    parameters. Currently, KDVS **does not** provide support for dynamic modification
    of parametrizable/configurable instances.

Application profile
+++++++++++++++++++

'experiment.py' interprets the profile dictionary specified in
:data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE` instance::

    MA_GO_PROFILE = {

        # ---- data section
        'annotation_file' : {},
        'gedm_file' : {},
        'labels_file' : {},

        # ---- GO section
        'go_domain' : '',

        # ---- subsets section

        # ---- initializers for all individual components
        'subset_categorizers' : {},
        'subset_orderers' : {},
        'statistical_techniques' : {},
        'subset_outer_selectors' : {},
        'subset_inner_selectors' : {},
        'reporters' : {},
        'envops' : {},

        # ---- subset hierarchy categorizer tree (as a linear iterable of categorizers)
        'subset_hierarchy_categorizers_chain' : (),

        # ---- fully expanded assignments of individual operations
        'subset_hierarchy_components_map' : {},

    }

As specified in API documentation, the :data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE`
contains `prototypes` of profile variables. That is, if section 'annotation_file'
refers to empty dictionary, then 'annotation_file' section of `full` profile
specified in configuration file must contain properly filled dictionary that
contains information about annotation file.

The fully specified profile of this type is available in the following location::

    examples/GSE7390/GSE7390_cfg.py

annotation_file
===============

This section specifies file that contains annotations (see :ref:`background_annotationmatrix`).
The file must come in DSV format. The section must contain the following elements:

    * 'path' (string) -- file path of annotation file `relative` to the configuration file
    * 'metadata' (dict) -- dictionary of metadata that describe selected structural
      details of annotation file; currently, two metadata elements are recognized:

        * 'delimiter' (string) -- delimiter that separates values in each line
        * 'comment' (string/None) -- comment prefix; each commented line is discarded; None if not used

    * 'indexes' (tuple/None) -- tuple of the column names that shall be `indexed` when
      loaded into KDVS database backend; indexing speeds up information querying
      from these columns, but increases the overall size of database, therefore
      only crucial columns should be indexed; None if the only index shall be created
      for ID column (see also :class:`~kdvs.fw.DBTable.DBTable` and :class:`~kdvs.fw.DSV.DSV`
      API documentation); empty tuple for creating no indexes at all

An example of 'annotation_file' section from example configuration file::

    {
    # ...
        'annotation_file' : {
            'path' : 'GPL96.txt.bz2',
            'metadata' : {
                'delimiter' : '\t',
                'comment' : '#',
            },
            'indexes' : ('ID', 'Representative Public ID', 'Gene Symbol'),
        },
    # ...
    }

gedm_file
=========

This section specifies file that contains measurements (see :ref:`background_measurementdatamatrix`).
The name refers historically to Gene Expression Data Matrix (GEDM). The file must
come in DSV format. The section must contain the following elements:

    * 'path' (string) -- file path of measurements file `relative` to the configuration file
    * 'metadata' (dict) -- dictionary of metadata that describe selected structural
      details of measurements file; currently, two metadata elements are recognized:

        * 'delimiter' (string) -- delimiter that separates values in each line
        * 'comment' (string/None) -- comment prefix; each commented line is discarded; None if not used

    * 'indexes' (tuple/None) -- tuple of the column names that shall be `indexed` when
      loaded into KDVS database backend; indexing speeds up information querying
      from that columns, but increases the overall size of database, therefore
      only crucial columns should be indexed; None if the only index shall be created
      for ID column (see also :class:`~kdvs.fw.DBTable.DBTable` and :class:`~kdvs.fw.DSV.DSV`
      API documentation); empty tuple for creating no indexes at all

.. note::

    Typically, for measurements files, 'indexes' element has value None,
    since querying is performed according to measurement ID only, and the index
    for ID column -- typically the first one in DSV file -- will be created
    automatically by KDVS database backend in that case

An example of 'gedm_file' section from example configuration file::

    {
    # ...
        'gedm_file' : {
            'path' : 'GSE7390.txt.bz2',
            'metadata' : {
                'delimiter' : None,
                'comment' : '#',
            },
            # special value -- index only by ID column
            'indexes' : None,
        },
    # ...
    }

labels_file
===========

This section specifies file that contains label information (see :ref:`background_labelinformation`).
Note that for some statistical techniques (see :ref:`framework_statisticaltechniques`) the label information
is `not needed`, therefore this file may not be always present. If present, the
file must come in DSV format. The section must contain the following elements:

    * 'path' (string/None) -- file path of labels file `relative` to the configuration file;
      None if not present
    * 'metadata' (dict) -- dictionary of metadata that describe selected structural
      details of labels file; currently, two metadata elements are recognized:

        * 'delimiter' (string) -- delimiter that separates values in each line
        * 'comment' (string/None) -- comment prefix; each commented line is discarded; None if not used

    * 'indexes' (tuple/None) -- tuple of the column names that shall be `indexed` when
      loaded into KDVS database backend; indexing speeds up information querying
      from that columns, but increases the overall size of database, therefore
      only crucial columns should be indexed; None if the only index shall be created
      for ID column (see also :class:`~kdvs.fw.DBTable.DBTable` and :class:`~kdvs.fw.DSV.DSV`
      API documentation); empty tuple for creating no indexes at all

.. note::

    Labels file may not be present; this is reflected by 'path' element having value None

.. note::

    Due to non-intensive querying, indexes are typically not needed for label information;
    this is reflected by 'indexes' element having value of empty tuple

An example of 'labels_file' section from example configuration file::

    {
    # ...
        'labels_file' : {
            # NOTE: labels file can be omitted entirely (e.g. for regression experiments)
            # by providing None as a path
            'path' : 'GSE7390_labels.csv.txt',
            'metadata' : {
                'delimiter' : None,
                'comment' : '#',
            },
            'indexes' : (),
        },
    # ...
    }

go_domain
=========

This element specifies Gene Ontology domain the KDVS shall focus on when processing
prior knowledge concepts (see also :ref:`background_priorknowledge`). This element
has only one string value. The possible values are:

    * 'BP' -- for `Biological Process <http://www.geneontology.org/GO.process.guidelines.shtml>`__
    * 'MF' -- for `Molecular Function <http://www.geneontology.org/GO.function.guidelines.shtml>`__
    * 'CC' -- for `Cellular Component <http://www.geneontology.org/GO.component.guidelines.shtml>`__

An example of 'go_domain' element from example configuration file::

    {
    # ...
        # ---- GO section
        'go_domain' : 'MF',
    # ...
    }

Initializers
============

The 'experiment.py' application specifies initializers for many components
(see `Component initializers`_) in many sections of application profile. General
format of each of such section is as follows::

    {
    # ...
        'section_name' : {
            'instance_name1' : {
                'instance_import_path' : {
                    'param1' : param1_val,
                    'param2' : param2_val,
                    # ...
                },
            },
            'instance_name2' : {
                'instance_import_path' : {
                    'param1' : param1_val,
                    'param2' : param2_val,
                    # ...
                },
            },
            # ...
            'instance_nameK' : {
                'instance_import_path' : {
                    'param1' : param1_val,
                    'param2' : param2_val,
                    # ...
                },
            }
        }
    # ...
    }

All details for all section names are specified below.

subset_categorizers
~~~~~~~~~~~~~~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any categorizers the application is using (see :ref:`framework_subsethierarchy`
and :class:`~kdvs.fw.Categorizer.Categorizer`
API documentation for more details). The specification for each individual object
is read and `single instance` of each object is created. The instances are
referred to by their `names`.

An example of 'subset_categorizers' section from example configuration file::

    {
    # ...
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
    # ...
    }

Here, two instances are created: the instance of :class:`~kdvs.fw.impl.data.Null.NullCategorizer`
with the name 'SCNull', and the instance of :class:`~kdvs.fw.impl.data.SubsetSize.SubsetSizeCategorizer`,
known as 'SCSizeThreshold'. Each instance has some parameters specified. During
instantiation, the parameters will be verified, so for instance, skipping one
parameter will generate an error. The instances can be referred to by their names
`later` in the configuration file (i.e. they must be instantiated first to be
referred to later).

subset_orderers
~~~~~~~~~~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any orderers the application is using (see :ref:`framework_subsetordering`
and :class:`~kdvs.fw.Categorizer.Orderer`
API documentation for more details). The specification for each individual object
is read and `single instance` of each object is created. The instances are
referred to by their `names`.

An example of 'subset_orderers' section from example configuration file::

    {
    # ...
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
    # ...
    }

Here, two instances are created: the instance of :class:`~kdvs.fw.impl.data.Null.NullOrderer`
with the name 'SONull', and the instance of :class:`~kdvs.fw.impl.data.SubsetSize.SubsetSizeOrderer`,
with the name 'SOSizeDecreasing'. The first one has no parameters, the second one
has one parameter specified. During instantiation, the parameters will be
verified, so for instance, skipping the parameter (or specifying anything for
null orderer) will generate an error. The instances can be referred to by their
names `later` in the configuration file (i.e. they must be instantiated first to be
referred to later).

statistical_techniques
~~~~~~~~~~~~~~~~~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any statistical techniques the application is using (see :ref:`framework_statisticaltechniques`
and :class:`~kdvs.fw.Stat.Technique`
API documentation for more details). The specification for each individual object
is read and `single instance` of each object is created. The instances are
referred to by their `names`.

.. note::

    Each technique must define some `global` parameters to be properly executed;
    see :ref:`annex_globaltechniqueparameters` for more details.

An example of 'statistical_techniques' section from example configuration file
(some parameters were omitted for clarity; refer to individual techniques for
complete parameter list)::

    {
    # ...
        'statistical_techniques' : {
            'L1L2_OLS' : {
                'kdvs.fw.impl.stat.L1L2.L1L2_OLS' : {
                    'error_func' : l1l2py.tools.balanced_classification_error,
                    'return_predictions' : True,
                    'global_degrees_of_freedom' : None,
                    'job_importable' : False,
                },
            },
            'L1L2_L1L2' : {
                'kdvs.fw.impl.stat.L1L2.L1L2_L1L2' : {
                    'external_k' : 4,
                    'internal_k' : 3,
                    'tau_min_scale' : 1. / 3,
                    'tau_max_scale' : 1. / 8,
                    # more parameters to follow...
                }
            },
            'L1L2_RLS' : {
                'kdvs.fw.impl.stat.L1L2.L1L2_RLS' : {
                    'external_k' : 4,
                    'lambda_min' : 1e-1,
                    'lambda_max' : 1e4,
                    'lambda_range_type' : 'geometric',
                    # more parameters to follow...
                }
            },
        }
    # ...
    }

Note that parameter value can be of `any Python type`. For instance, the parameter
'error_func' of 'L1L2_OLS' instance has the value of Python callable (i.e.
Python function; see also :ref:`calls`); in this case, during the interpretation of the configuration
file, at least the Python module containing the function must be imported::

    import l1l2py

see `Configuration file`_ for more details about configuration file structure
and interpretation.

subset_outer_selectors
~~~~~~~~~~~~~~~~~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any "`outer selectors`" the application is using (see :ref:`framework_selecting`
and :class:`~kdvs.fw.impl.stat.PKCSelector.OuterSelector`
API documentation for more details). The specification for each individual object
is read and `single instance` of each object is created. The instances are
referred to by their `names`.

An example of 'subset_outer_selectors' section from example configuration file::

    {
    # ...
        'subset_outer_selectors' : {
            'PKCSelector_ClsErrThr' : {
                'kdvs.fw.impl.stat.PKCSelector.OuterSelector_ClassificationErrorThreshold' : {
                    'error_threshold' : 0.3,
                },
            },
        },
    # ...
    }

subset_inner_selectors
~~~~~~~~~~~~~~~~~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any "`inner selectors`" the application is using (see :ref:`framework_selecting`
and :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector`
API documentation for more details). The specification for each individual object
is read and `single instance` of each object is created. The instances are
referred to by their `names`.

An example of 'subset_inner_selectors' section from example configuration file::

    {
    # ...
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
    # ...
    }

reporters
~~~~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any `reporters` the application is using (see :ref:`framework_reporting`
and :class:`~kdvs.fw.Report.Reporter`
API documentation for more details). The specification for each individual object
is read and `single instance` of each object is created. The instances are
referred to by their `names`.

An example of 'reporters' section from example configuration file::

    {
    # ...
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
    # ...
    }

envops
~~~~~~

This section specifies component initializers (see `Component initializers`_)
for any "`envops`" the application is using (see :class:`~kdvs.fw.EnvOp.EnvOp`
API documentation and comments in the :mod:`~kdvs.fw.EnvOp` module for more details).
The specification for each individual object is read and `single instance` of
each object is created. The instances are referred to by their `names`.

An example of 'envops' section from example configuration file::

    {
    # ...
        'envops' : {
            'L1L2_UniformExtSplitProvider_SCNull' : {
                'kdvs.fw.impl.envop.L1L2.L1L2_UniformExtSplitProvider' : {
                    'enclosingCategorizerID' : 'SCNull',
                    'extSplitParamName' : 'external_k',
                    'extSplitPlaceholderParam' : 'ext_split_sets',
                }
            },
        },
    # ...
    }

subset_hierarchy_categorizers_chain
===================================

This element specifies `categorizer chain`, i.e. a nesting of categories for
data subsets. See :ref:`framework_subsethierarchy`, especially :ref:`Figure 5 <framework-fig5>`
(bottom leftmost part), for more details. This element has value of a tuple of
strings, i.e. `names` of the `categorizers` defined before (see `Component initializers`_).

An example of 'subset_hierarchy_categorizers_chain' section from example configuration file::

    {
    # ...
        'subset_hierarchy_categorizers_chain' : (
            'SCNull',
            'SCSizeThreshold'
        ),
    # ...
    }

Both 'SCNull' and 'SCSizeThreshold' names refer to instances of `categorizers`
specified earlier; see `subset_categorizers`_.

subset_hierarchy_components_map
===============================

This element specifies whole `category tree` and all the operations that will be
executed on subsets. See :ref:`framework_subsethierarchy`, especially
:ref:`Figure 5 <framework-fig5>` (bottom middle part) for more details.

Here, all the components declared previously (see `Component initializers`_) are
used. It is done by assigning series of components to each category, thus
specifying "`operations map`". Since the `categorizer chain` has been specified
before, (see `subset_hierarchy_categorizers_chain`_), the application knows
the order in which the operations will be executed.

The general format of this element is as follows::

    {
    # ...
        'subset_hierarchy_components_map' : {
            'categorizer_name1' : {
                'category_name1' : {
                    # "operations map" 1
                },
                'category_name2' : {
                    # "operations map" 2
                },
                # ...
                'category_nameK1' : {
                    # "operations map" K1
                }
            },
            'categorizer_name2' : {
                'category_name1' : {
                    # "operations map" 1
                },
                'category_name2' : {
                    # "operations map" 2
                },
                # ...
                'category_nameK2' : {
                    # "operations map" K2
                }
            },
            # ...
            'categorizer_nameP' : {
                'category_name1' : {
                    # "operations map" 1
                },
                'category_name2' : {
                    # "operations map" 2
                },
                # ...
                'category_nameKP' : {
                    # "operations map" KP
                }
            }
        }
    # ...
    }

where 'categorizer_nameX' are `names` of instances of categorizers specified in
`subset_categorizers`_, and 'category_nameX' is the non-uniquified name of the
category offered by the categorizer.

.. note::

    Some categories may be `not specified` here at all; in that case all the
    subsets categorized with each such category will be `skipped` from further
    processing. The same applies for whole categorizers; if one is not specified
    here, `all his associated categories` will be treated as `skipped`.

Operations map
~~~~~~~~~~~~~~

Individual operations map specifies all operations to be executed on the level of
the category. Some of those operations will be executed for each subset tagged
with this category; some operations will be executed once before processing
of all subsets takes place; finally some operations will be executed once after
processing of all subsets has been finished. The details depend on individual
operations.

Operations are defined simply as an `operation ID` mapped to single `component ID`::

    {
    # ...
        'technique' : 'L1L2_RLS',
    # ...
    }

or to an iterable of `component IDs`::

    {
    # ...
        'reporter' : ['L1L2_VarFreq_Reporter', 'L1L2_VarCount_Reporter', 'L1L2_PKC_Reporter'],
    # ...
    }

All operation IDs interpreted by 'experiment.py' application are explained below.

orderer
^^^^^^^
This operation defines an :class:`~kdvs.fw.Categorizer.Orderer` instance to be used
for this category. The ordering is executed once, before processing of all subsets.
For instance, the orderer 'SONull' that does 'null' ordering for '__all__' category of
'SCNull' categorizer may be specified like this::

    {
    # ...
        # define categorizer(s)
        'subset_categorizers' : {
            'SCNull' : {
                'kdvs.fw.impl.data.Null.NullCategorizer' : {
                    'ID' : 'NC',
                    'null_category' : '__all__',
                },
            },
            # ...
        },
        # ...
        # define orderer(s)
        'subset_orderers' : {
            'SONull' : {
                'kdvs.fw.impl.data.Null.NullOrderer' : {
                },
            },
            # ...
         },
         # ...
         # use orderer in component map
        'subset_hierarchy_components_map' : {
            'SCNull' : {
                '__all__' : {
                    'orderer' : 'SONull',
                    # ...
                }
            },
            # ...
        }
    # ...
    }

.. note::

    An orderer must be specified for each category of each categorizer in
    component map. If no real ordering is required, use an instance of
    :class:`~kdvs.fw.impl.data.Null.NullOrderer`.

technique
^^^^^^^^^
This operation defines a :class:`~kdvs.fw.Stat.Technique` instance to be used
across this category. The technique is executed once for each subset tagged with
this category. For instance, the technique 'L1L2_OLS' will be executed for each
subset tagged with '<=' category of 'SCSizeThreshold' categorizer::

    {
    # ...
        # define categorizer(s)
        'subset_categorizers' : {
            'SCSizeThreshold' : {
                'kdvs.fw.impl.data.SubsetSize.SubsetSizeCategorizer' : {
                    'ID' : 'SSC32',
                    'size_lesser_category' : '<=',
                    'size_greater_category' : '>',
                    'size_threshold' : 32,
                },
            },
            # ...
        },
        # ...
        # define technique(s)
        'statistical_techniques' : {
            'L1L2_OLS' : {
                'kdvs.fw.impl.stat.L1L2.L1L2_OLS' : {
                    'error_func' : l1l2py.tools.balanced_classification_error,
                    'return_predictions' : True,
                    'global_degrees_of_freedom' : None,
                    'job_importable' : False,
                },
            },
            # ...
        },
        # ...
        # use technique in component map
        'subset_hierarchy_components_map' : {
            'SCSizeThreshold' : {
                '<=' : {
                    'technique' : 'L1L2_OLS',
                    # ...
                },
                # ...
            },
            #...
        }
    # ...
    }

.. note::

    The technique may be specified as None. In that case, the subset processing
    will be skipped. It is useful for general top--level categories in deep category
    trees, when there is no need to process subset there (it is too early), a
    good example being 'null' category from :class:`~kdvs.fw.impl.data.Null.NullCategorizer`.
    This trick saves computational time as well::

        {
        # ...
            'subset_categorizers' : {
                'SCNull' : {
                    'kdvs.fw.impl.data.Null.NullCategorizer' : {
                        'ID' : 'NC',
                        'null_category' : '__all__',
                    },
                },
                # ...
            },
            # ...
            'subset_hierarchy_components_map' : {
                'SCNull' : {
                    '__all__' : {
                        'technique' : None,
                        # ...
                    }
                },
                # ...
            }
        # ...
        }

outer_selector
^^^^^^^^^^^^^^
This operation defines an :class:`~kdvs.fw.impl.stat.PKCSelector.OuterSelector`
instance to be used for this category. The outer selection is performed once
after the processing of all subsets has been completed, and before `inner selection`.
For instance, we would like to perform outer selection based on classification
error threshold on each subset from '<=' category::

    {
    # ...
        # define categorizer(s)
        'subset_categorizers' : {
            'SCSizeThreshold' : {
                'kdvs.fw.impl.data.SubsetSize.SubsetSizeCategorizer' : {
                    'ID' : 'SSC32',
                    'size_lesser_category' : '<=',
                    'size_greater_category' : '>',
                    'size_threshold' : 32,
                },
            },
            # ...
        },
        # ...
        # define outer selector(s)
        'subset_outer_selectors' : {
            'PKCSelector_ClsErrThr' : {
                'kdvs.fw.impl.stat.PKCSelector.OuterSelector_ClassificationErrorThreshold' : {
                    'error_threshold' : 0.3,
                },
            },
        },
        # ...
        # use outer selector in component map
        'subset_hierarchy_components_map' : {
            'SCSizeThreshold' : {
                '<=' : {
                    'outer_selector' : 'PKCSelector_ClsErrThr',
                    # ...
                },
                # ...
            },
            #...
        }
    # ...
    }

.. note::

    As for the technique, the outer selector may be specified as None. In that
    case, the outer selection is simply not performed, in line with 'None'
    technique, because simply there are no :class:`~kdvs.fw.Stat.Results` instances
    produced yet. Again, good example is a 'null' category from
    :class:`~kdvs.fw.impl.data.Null.NullCategorizer`::

        {
        # ...
            'subset_categorizers' : {
                'SCNull' : {
                    'kdvs.fw.impl.data.Null.NullCategorizer' : {
                        'ID' : 'NC',
                        'null_category' : '__all__',
                    },
                },
                # ...
            },
            # ...
            'subset_hierarchy_components_map' : {
                'SCNull' : {
                    '__all__' : {
                        'outer_selector' : None,
                        # ...
                    }
                },
                # ...
            }
        # ...
        }

inner_selector
^^^^^^^^^^^^^^
This operation defines an :class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector`
instance to be used for this category. The inner selection is performed once
after the processing of all subsets has been completed, and after `outer selection`.
For instance, we would like to perform inner selection, that selects `all` variables
based on classification error threshold, on each subset from '<=' category::

    {
    # ...
        # define categorizer(s)
        'subset_categorizers' : {
            'SCSizeThreshold' : {
                'kdvs.fw.impl.data.SubsetSize.SubsetSizeCategorizer' : {
                    'ID' : 'SSC32',
                    'size_lesser_category' : '<=',
                    'size_greater_category' : '>',
                    'size_threshold' : 32,
                },
            },
            # ...
        },
        # ...
        # define inner selector(s)
        'subset_inner_selectors' : {
            'VarSelector_ClsErrThr_AllVars' : {
                'kdvs.fw.impl.stat.PKCSelector.InnerSelector_ClassificationErrorThreshold_AllVars' : {
                },
            },
            # ...
        },
        # ...
        # use inner selector in component map
        'subset_hierarchy_components_map' : {
            'SCSizeThreshold' : {
                '<=' : {
                    'inner_selector' : 'VarSelector_ClsErrThr_AllVars',
                    # ...
                },
                # ...
            },
            #...
        }
    # ...
    }

.. note::

    As for the technique, the inner selector may be specified as None. In that
    case, the inner selection is simply not performed, in line with 'None'
    technique, because simply there are no :class:`~kdvs.fw.Stat.Results` instances
    produced yet. Again, good example is a 'null' category from
    :class:`~kdvs.fw.impl.data.Null.NullCategorizer`::

        {
        # ...
            'subset_categorizers' : {
                'SCNull' : {
                    'kdvs.fw.impl.data.Null.NullCategorizer' : {
                        'ID' : 'NC',
                        'null_category' : '__all__',
                    },
                },
                # ...
            },
            # ...
            'subset_hierarchy_components_map' : {
                'SCNull' : {
                    '__all__' : {
                        'inner_selector' : None,
                        # ...
                    }
                },
                # ...
            }
        # ...
        }

reporter
^^^^^^^^
This operation defines an iterable of all :class:`~kdvs.fw.Report.Reporter`
instance(s) to be used for this category.

The crucial thing here is to remember that there are `two` modes of reporting.
In 'local' mode, the reporter typically goes through all
:class:`~kdvs.fw.Stat.Results` instances `from single category` and produces its
reports. In 'global' mode, the reporter can accept `whole category tree` and go
through :class:`~kdvs.fw.Stat.Results` instances `from more that one category`.
See :ref:`framework_reporting` and :ref:`framework_subsethierarchy` for more details.

This behavior is reflected when reporters are specified in component map. Typically,
'local' reporters are specified simply for the category they need to scan.
'Global' reporters, though, may be specified for example, `some level(s) higher/lower`
than the categories they are scanning; this way, they can collect all the information
they need.

For instance, having the following categorizers::

    {
    # ...
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
    # ...
    }

that form the following categorizers chain ('SCNull' is above 'SCSizeThreshold'
in hierarchy)::

    {
    # ...
        'subset_hierarchy_categorizers_chain' : (
            'SCNull',
            'SCSizeThreshold'
        ),
    # ...
    }


and having the following reporters declared::

    {
    # ...
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
    # ...
    }

we can use three 'local' reporters, that simply scan the single category, and
one 'global' reporter that collects summary information from all categories
`one level below`::

    {
    # ...
        'subset_hierarchy_components_map' : {
            'SCNull' : {
                '__all__' : {
                    # 'global' reporter
                    'reporter' : ['L1L2_PKC_UTL_Reporter'],
                    # ...
                }
            },
            'SCSizeThreshold' : {
                '<=' : {
                    # 'local' reporter(s)
                    'reporter' : ['L1L2_VarFreq_Reporter', 'L1L2_VarCount_Reporter', 'L1L2_PKC_Reporter'],
                    # ...
                },
                '>' : {
                    # 'local' reporter(s)
                    'reporter' : ['L1L2_VarFreq_Reporter', 'L1L2_VarCount_Reporter', 'L1L2_PKC_Reporter'],
                    # ...
                }
            },
            # ...
        }
    # ...
    }

.. note::

    It may seem counter-intuitive, but 'global' reporters do not depend on the
    reports produced by 'local' reporters, and 'local' reporters do not depend on
    each other as well. Since reporters are scanning :class:`~kdvs.fw.Stat.Results`
    instances exclusively, when all Results instances are produced, reporters may
    be executed `in any order`.

preenvop/postenvop
^^^^^^^^^^^^^^^^^^

These operations specify the iterables of instance(s) of :class:`~kdvs.fw.EnvOp.EnvOp`
that will be use for this category.

Each 'preenvop' is executed once, before all subset processing starts.

Each 'postenvop' is executed once, after all subset processing has been finished,
and after all the following: outer selection, inner selection, and before reporters.

The "envops" may be not specified at all, in which case the empty iterable is used.

For instance, to use single "envop" at the top of hierarchy::

    {
    # ...
        # define categorizer(s)
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
        # ...
        # define envop(s)
        'envops' : {
            'L1L2_UniformExtSplitProvider_SCNull' : {
                'kdvs.fw.impl.envop.L1L2.L1L2_UniformExtSplitProvider' : {
                    'enclosingCategorizerID' : 'SCNull',
                    'extSplitParamName' : 'external_k',
                    'extSplitPlaceholderParam' : 'ext_split_sets',
                }
            },
        },
        # ...
        # use envop(s) in component map
        'subset_hierarchy_components_map' : {
            'SCNull' : {
                '__all__' : {
                    # one envop executed at the top of hierarchy before subset processing
                    'preenvop' : ['L1L2_UniformExtSplitProvider_SCNull'],
                    'postenvop' : [],
                    # ...
                }
            },
            'SCSizeThreshold' : {
                '<=' : {
                    'preenvop' : [],
                    'postenvop' : [],
                    # ...
                },
                '>' : {
                    'preenvop' : [],
                    'postenvop' : [],
                    # ...
                }
            },
            # ...
        }
    # ...
    }

misc
^^^^

This "operation" specifies all additional parameter(s) needed for the processing
of the category. For instance, if we need to skip some parts of subset processing
for each category during development to save time, it can be done with recognition
of certain 'misc' parameters by the application.

The 'experiment.py' application uses 'misc' operation to specify the parameters
that describe "test mode", where certain amount of subsets are entirely `skipped`
from processing, independently from techniques used, results produced, and selections
performed. For instance, instead of processing ~2000 subsets each time during
development of a new technique, one can process only 5 subsets and discard the
rest. Of course, when the implementation of the technique is finished and validated,
"test mode" needs to be switched off.

Currently, 'experiment.py' application recognizes the following parameters:

    * 'test_mode_elems' (integer) -- number of subsets to retain during test mode
    * 'test_mode_elems_order' (string) -- if 'first' is specified, then certain
      amount of first subsets from the submission order is retained during test
      mode; if 'last' is specified, then certain amount of last subsets from the
      submission order is retained during test mode

The "submission order" is the order of subsets within single category that is
used by subset processing. For instance, if the submission order contains the following
subsets::

    S1, S2, S3, S4, S5

the subset processing mechanism will start from S1, and continue through the order
down to S5. `Subset processing` is the act of executing statistical technique
for this subset (that in turn triggers job creation and execution, as well as
production of results afterwards).

To fully enable "test mode", both 'test_mode_elems' and 'test_mode_elems_order'
parameters must be specified.

For instance, to enable test mode and retain only 5 first subsets during the
processing of the '<=' category, to enable test mode and skip entire '>' category,
and to not enable the test mode for the top category::

    {
    # ...
        # define categorizer(s)
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
        # ...
        'subset_hierarchy_components_map' : {
            'SCNull' : {
                '__all__' : {
                    # test mode is not enabled here, subset processing is not artificially altrered
                    'misc' : {
                    },
                    # ...
                }
            },
            'SCSizeThreshold' : {
                '<=' : {
                    'misc' : {
                        'test_mode_elems' : 5,
                        'test_mode_elems_order' : 'first',
                    },
                    # ...
                },
                '>' : {
                    'misc' : {
                        # NOTE: the following is equal to specifying 'None' as statistical technique for this category
                        'test_mode_elems' : 0,
                        'test_mode_elems_order' : 'first',
                    },
                    # ...
                }
            },
            # ...
        }
    # ...
    }

.. note::

    It is advised to keep 'misc' section for each category, even if "test mode"
    will not be used.

Putting it all together
=======================

Here we show the example of all sections of application profile for 'experiment.py'
application (some parameters were omitted for clarity). The complete profile
with comments is available in file 'examples/GSE7390/GSE7390_cfg.py'::

    {
        'annotation_file' : {
            'path' : 'GPL96.txt.bz2',
            'metadata' : {
                'delimiter' : '\t',
                'comment' : '#',
            },
            'indexes' : ('ID', 'Representative Public ID', 'Gene Symbol'),
        },
        'gedm_file' : {
            'path' : 'GSE7390.txt.bz2',
            'metadata' : {
                'delimiter' : None,
                'comment' : '#',
            },
            'indexes' : None,
        },
        'labels_file' : {
            'path' : 'GSE7390_labels.csv.txt',
            'metadata' : {
                'delimiter' : None,
                'comment' : '#',
            },
            'indexes' : (),
        },
    
        'go_domain' : 'MF',
    
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
                    'error_func' : l1l2py.tools.balanced_classification_error,
                    'return_predictions' : True,
                    'global_degrees_of_freedom' : None,
                    'job_importable' : False,
                },
            },
            'L1L2_L1L2' : {
                'kdvs.fw.impl.stat.L1L2.L1L2_L1L2' : {
                    'external_k' : 4,
                    'internal_k' : 3,
                    'tau_min_scale' : 1. / 3,
                    'tau_max_scale' : 1. / 8,
                    # ...
                },
            },
            'L1L2_RLS' : {
                'kdvs.fw.impl.stat.L1L2.L1L2_RLS' : {
                    'external_k' : 4,
                    'lambda_min' : 1e-1,
                    'lambda_max' : 1e4,
                    'lambda_range_type' : 'geometric',
                    # ...
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
                    'postenvop' : [],
                    'misc' : {
                    },
                },
            },
            'SCSizeThreshold' : {
                '<=' : {
                    'orderer' : 'SONull',
                    'technique' : 'L1L2_RLS',
                    'outer_selector' : 'PKCSelector_ClsErrThr',
                    'inner_selector' : 'VarSelector_ClsErrThr_AllVars',
                    'reporter' : ['L1L2_VarFreq_Reporter', 'L1L2_VarCount_Reporter', 'L1L2_PKC_Reporter'],
                    'preenvop' : [],
                    'postenvop' : [],
                    'misc' : {
                        'test_mode_elems' : 1,
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
                        'test_mode_elems' : 1,
                        'test_mode_elems_order' : 'last',
                    },
                },
            },
        },
    }

.. _applications_configurationfile:

Configuration file
++++++++++++++++++

Default configuration
=====================

The 'experiment.py' applications loads and interprets default configuration file:

    kdvs/config/default_cfg.py

See :ref:`framework_configurationfiles` and :ref:`annex_defaultconfigurationfile`
for more details.

User configuration
==================

The 'experiment.py' application accepts user configuration file specified with
``-c`` command line option (see :ref:`applications_commandlineparameters`). If output
directory was not specified, the location of user configuration file serves as
the `root output directory`; see also :ref:`applications_outputdirectory`.

.. _applications_outputdirectory:

Output directory
++++++++++++++++

The output directory for 'experiment.py' application is specified in two ways.
Command line option ``-o`` may be used (see :ref:`applications_commandlineparameters`),
or if not used, the directory in which `user configuration file` is located
becomes root output directory (``$ROOT_OUTPUT_DIRECTORY``).

In root output directory, KDVS stores all the artefacts produced. The following
subdirectory tree is created::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            $dbm_location/
            $subsets_location/
            $subsets_results_location/
            $jobs_location/
            $debug_output_location/
            
where ``$dbm_location`` is a value of 'dbm_location' variable in `default configuration file`;
all standard subdirectories are specified as configurable locations (see
:ref:`annex_defaultconfigurationfile`, option group 'Standard locations').
Assuming the default locations are not overridden, the following subdirectory
tree is created::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            db/
            ss/
            ss_results/
            jobs/
            debug/

Databases
=========

The 'experiment.py' application creates three standard databases, controlled by
:class:`~kdvs.core.db.DBManager` instance. The names of databases are also
configurable, specified in variables ``$data_db_id`` and ``$map_db_id`` (DATA
and MAPS by default). One additional database is always called 'kdvs.root'.

kdvs.root
~~~~~~~~~

The 'kdvs.root' database contains the diagnostic information regarding all other
databases. It is created automatically by :class:`~kdvs.core.db.DBManager` instance.
Currently, the implementation is provided for SQLite database backend (see
:class:`~kdvs.core.provider.SQLite3DBProvider`). It contains single table 'DB'
that lists all other databases used by KDVS. The 'DB' table has the following columns:

    * 'db' (string) -- the name of database
    * 'created' (integer) -- 1 if database was created from scratch, 0 if
      existing database was accessed
    * 'db_loc' (string) -- location of the database; the following format is used::

        "<host_name>://<physical_location>"

      where 'host_name' is the name of the machine (via :func:`socket.gethostname`),
      and 'physical_location' is filesystem path to the SQLite database file, e.g.::

        "localhost:///home/grzegorz/KDVS_output/db/DATA.db"

For default configuration, the typical content of 'DB' table in 'kdvs.root'
database, after successfull completion of the experiment, is similar to:

======= ========== ====================================================
db      created    db_loc
======= ========== ====================================================
DATA    1          "localhost:///home/grzegorz/KDVS_output/db/DATA.db"
MAPS    1          "localhost:///home/grzegorz/KDVS_output/db/MAPS.db"
======= ========== ====================================================

DATA
~~~~

The DATA database contains the content of all data files `before any mapping has been
produced`. The names of tables vary regarding the names of the files specified
in default/user configuration file (see `annotation_file`_, `gedm_file`_, `labels_file`_,
:ref:`annex_defaultconfigurationfile`, :ref:`annex_staticdatafiles`). Many names
come from name components of file paths, extracted with :func:`~kdvs.core.util.getFileNameComponent`
function. Typically, the following tables are created:

    * Table that holds numerical content of MDM (see :ref:`background_measurementdatamatrix`);
      the table name comes from name component of file path specified in
      application profile (see `gedm_file`_).

      For instance, when '/home/grzegorz/GSE7390.txt.bz2' is specified as file
      path, then 'GSE7390' is extracted as table name.

    * Table that holds the content of annotation file (see :ref:`background_annotationmatrix`);
      the table name comes from name component of file path specified in application
      profile (see `annotation_file`_).

      For instance, when '/home/grzegorz/GPL96.txt.bz2' is specified as file
      path, then 'GPL96' is extracted as table name.

    * Table that holds label information (see :ref:`background_labelinformation`);
      the table name comes from name component of file path specified in application
      profile (see `labels_file`_).

      For instance, when '/home/grzegorz/GSE7390_labels.csv.txt' is specified as file
      path, then 'GSE7390_labels' is extracted as table name.

    * Table(s) that hold information defined in `static data files` that have
      been configured as loadable (with 'loadToDB' parameter set to True; see
      :ref:`annex_staticdatafiles`); so far, 'experiment.py' application uses
      one such file that contains information about gene naming from HGNC consortium
      (see :mod:`~kdvs.fw.impl.annotation.HGNC` module for more information and
      README file in 'data' directory). As before, each table name comes from name
      component of file path specified in path specification of :ref:`annex_staticdatafiles`.

      For HGNC, if the default location of static file is used::

        $KDVS_ROOT/data/HGNC/HGNC.tsv.gz

      then the extracted table name will be 'HGNC'.

.. note::

    Some tables in DATA database may contain `post--processed` content. For instance,
    in 'experiment.py' application, HGNC data is post--processed after loading
    into database to remove some artifacts and speedup further querying. The post--processing
    uses helper tables stored in MAPS database (see `MAPS`_ below). See also
    :meth:`~kdvs.bin.experiment.postprocessStaticData` action and
    :mod:`~kdvs.fw.impl.annotation.HGNC` module for more details.

MAPS
~~~~

The MAPS database contains helper tables for `query--intensive mappings` produced
by KDVS. Typically, those tables are used by `mapping builders`,
i.e. concrete implementations of :class:`~kdvs.fw.Map.PKCIDMap`,
:class:`~kdvs.fw.Map.PKCGeneMap` and :class:`~kdvs.fw.Map.GeneIDMap` classes
(see also :ref:`framework_localdataintegration`). Currently, the following tables
are created by 'experiment.py' application:

    * 'hgnc_previous', that contains `inverted` mapping between currently approved
      HGNC gene symbol(s) and previously approved HGNC gene symbols(s); this
      helper table is generated with :func:`~kdvs.fw.impl.annotation.HGNC.generateHGNCPreviousSymbols`
      function inside :meth:`~kdvs.bin.experiment.postprocessStaticData` action;
      the table structure follows :data:`~kdvs.fw.impl.annotation.HGNC.HGNCPREVIOUS_TMPL`
      template.

    * 'hgnc_synonyms', that contains `inverted` mapping between currently approved
      HGNC gene symbol(s) and actual synonymous HGNC gene symbols(s); this
      helper table is generated with :func:`~kdvs.fw.impl.annotation.HGNC.generateHGNCSynonyms`
      function inside :meth:`~kdvs.bin.experiment.postprocessStaticData` action;
      the table structure follows :data:`~kdvs.fw.impl.annotation.HGNC.HGNCSYNONYMS_TMPL`
      template.

    * 'em2annotation', that contains bioinformatic annotations associated with
      each individual measurement (see :ref:`background_measurementdatamatrix`).
      The annotations are taken from :ref:`background_annotationmatrix`. This
      table is generated by concrete implementation of :class:`~kdvs.fw.Map.GeneIDMap`
      builder (see :class:`~kdvs.fw.impl.map.GeneID.GPL.GeneIDMapGPL` and
      :class:`~kdvs.fw.impl.map.GeneID.HGNC_GPL.GeneIDMapHGNCGPL`). It is used
      by :func:`~kdvs.fw.Annotation.get_em2annotation` function to provide
      necessary annotations for reporters (see :ref:`framework_reporting`).
      The table structure follows :data:`~kdvs.fw.Annotation.EM2ANNOTATION_TMPL`
      template.

    * 'goterm2em', that contains `inverted` mapping between measurements and prior
      knowledge concepts (i.e. PKC -> Var, see :ref:`framework_localdataintegration`).
      This table is generated by concrete implementation of :class:`~kdvs.fw.Map.PKCIDMap`
      builder (see :class:`~kdvs.fw.impl.map.PKCID.GPL.PKCIDMapGOGPL`). It is
      used to generate all data subsets (see :ref:`framework_datasubsets`).
      The table structure follows :data:`~kdvs.fw.impl.map.PKCID.GPL.GOTERM2EM_TMPL`
      template.

Subsets
=======

Data subsets (see :ref:`framework_datasubsets` and :ref:`framework_subsethierarchy`)
are built and serialized in :meth:`~kdvs.bin.experiment.buildPKDrivenDataSubsets`
action. The `numerical content` of each data subset (coming from :attr:`array`
attribute of :class:`~kdvs.fw.DataSet.DataSet` instance) is serialized separately
under the filekey equal to related PKC ID. No textual representation is saved.

.. note::

    All possible data subsets are generated and serialized at once. There is
    currently no possibility to exclude some data subsets from generation other
    than manually altering the finished :class:`~kdvs.fw.Map.PKCIDMap` mapping
    before execution of :meth:`~kdvs.bin.experiment.buildPKDrivenDataSubsets`, or
    manipulating prior knowledge representation before this mapping is constructed
    in :meth:`~kdvs.bin.experiment.buildPKCIDMap`.

.. note::

    Currently, for GO terms, the `numerical name part` is extracted with
    :func:`~kdvs.fw.impl.pk.go.GeneOntology.GO_id2num` and used as filekey for
    data subset; this is `hardcoded`.

For instance, assuming the following prior knowledge concepts (see :ref:`background_priorknowledge`)::

    'concept1', 'concept2', 'concept3'

when data subsets are successfully generated, they will be serialized as follows::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            $subsets_location/
                concept1
                concept2
                concept3

Serialization follows current KDVS serialization protocol (see :ref:`annex_serialization`).


Subsets results
===============

All descriptive results, including: completely filled :class:`~kdvs.fw.Stat.Results`
instances, reports, associated plots, and some useful descriptive mappings, are saved into
this location::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            $subsets_results_location/

that becomes the following, if default configuration is used::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            ss_results/

:class:`~kdvs.fw.Stat.Results` instances
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Even if :meth:`~kdvs.fw.Stat.Technique.produceResults` method returns :class:`~kdvs.fw.Stat.Results`
instance, it is `incomplete`, among others, due to selection not being performed
yet, possible delay in producing certain plots, etc. That is why concrete
implementations of statistical techniques assign None to certain Results elements,
and serialization of complete :class:`~kdvs.fw.Stat.Results` instances is delayed
until :meth:`~kdvs.bin.experiment.storeCompleteResults` action.

For each valid Results instance, a new sublocation is created inside
``$subsets_results_location``, and Results instance itself, along with textual
representation, accompanied by additional artefacts, such as plots, are serialized
there into the following configurable filekey::

    'PKCID_resultsSuffix'

where 'PKCID' is the ID of associated prior knowledge concept (see `Subsets`_ above),
and 'resultsSuffix' is defined in ``$subset_results_suffix`` variable
(see :ref:`annex_defaultconfigurationfile`). Serialization follows current KDVS
serialization protocol (see :ref:`annex_serialization`).

For instance, assuming the following prior knowledge concepts (see :ref:`background_priorknowledge`)::

    'concept1', 'concept2', 'concept3'

and assuming that :class:`~kdvs.fw.impl.stat.L1L2.L1L2_RLS` technique is used
against them (and has been declared as 'L1L2_RLS' in application profile),
the following artefacts are saved (assuming default configuration)::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            ss_results/
                concept1/
                    concept1_RES
                    concept1_RES.txt
                    concept1_prediction_error_ts.pdf
                    concept1_prediction_error_tr.pdf
                    concept1_NullDOF__vars_freqs.txt
                concept2/
                    concept1_RES
                    concept1_RES.txt
                    concept1_prediction_error_ts.pdf
                    concept1_prediction_error_tr.pdf
                    concept1_NullDOF__vars_freqs.txt
                concept3/
                    concept1_RES
                    concept1_RES.txt
                    concept1_prediction_error_ts.pdf
                    concept1_prediction_error_tr.pdf
                    concept1_NullDOF__vars_freqs.txt

Refer to individual concrete technique implementations for more details.

Reports
~~~~~~~

All individual reports (see :ref:`framework_reporting`) are saved here during
:meth:`~kdvs.bin.experiment.prepareReports` action. Refer to concrete
:class:`~kdvs.fw.Report.Reporter` implementations for specific details.

.. note::

    Reports are produced successfully only if related :class:`~kdvs.fw.Stat.Results`
    instances have been successfully created and serialized.

For instance, the :class:`~kdvs.fw.impl.report.L1L2.L1L2_PKC_Reporter` may produce
the following reports (names may vary depending on how statistical techniques
were declared in application profile, and the degrees of freedom the technique
uses; see `statistical_techniques`_ above and :ref:`framework_statisticaltechniques`);
default configuration is assumed::

    $ROOT_OUTPUT_DIRECTORY/
        KDVS_output/
            ss_results/
                L1L2_RLS_NullDOF_err_stats.txt
                L1L2_L1L2_mu0_err_stats.txt
                L1L2_L1L2_mu1_err_stats.txt
                L1L2_L1L2_mu2_err_stats.txt

Plots
~~~~~

Plots (see :ref:`framework_plotting`) may be produced by concrete implementations
of :class:`~kdvs.fw.Stat.Technique` class or inside reports (see :ref:`framework_reporting`).
Currently, all plots are produced by techniques, and are saved in
:meth:`~kdvs.bin.experiment.storeCompleteResults` action.

Miscellaneous
~~~~~~~~~~~~~

Currently, the following artefacts are saved in ``$subsets_results_location``:

    * "technique2ssname" mapping between statistical techniques and all assigned
      data subsets (i.e. subsets that this technique is executed against, see
      `statistical_techniques`_ above and :ref:`framework_statisticaltechniques`)::

        {
            techniqueID1 : [ subsetID1, ..., subsetIDk1 ],
            ...
            techniqueIDn : [ subsetID1, ..., subsetIDkn ]
        }

      along with textual representation, is serialized under configurable filekey
      ``$technique2ssname_key`` (see :ref:`annex_defaultconfigurationfile`); assuming
      default configuration::

        $ROOT_OUTPUT_DIRECTORY/
            KDVS_output/
                ss_results/
                    TECH2SS
                    TECH2SS.txt

    * if any exception(s) were thrown during any job execution, a serialized list
      of those exceptions is saved under configurable
      filekey ``$jobs_exceptions_key`` (see :ref:`annex_defaultconfigurationfile`)


Jobs results
============

Each :class:`~kdvs.fw.Job.Job` instance, together with related raw job output,
is serialized by KDVS for diagnostic purposes if the job bears `custom ID`
(see :ref:`framework_jobcreationandexecution`).

The following artefacts are serialized chronologically in 'experiment.py' application:

    * in :meth:`~kdvs.bin.experiment.submitSubsetOperations`:

        * if :class:`~kdvs.fw.Job.Job` instance bears custom ID 'customID', the
          instance itself is serialized into the following filekey::

            'customID'

        * "jobIDmap" mapping between default job IDs and custom job IDs, along
          with textual representation, is serialized under configurable filekey
          ``$jobID_map_key`` (see :ref:`annex_defaultconfigurationfile`)

    * in :meth:`~kdvs.bin.experiment.executeSubsetOperations`:

        * if :class:`~kdvs.fw.Job.Job` instance bears custom ID 'customID', the
          raw output of this job (i.e. obtained with :meth:`~kdvs.fw.Job.JobContainer.getJobResult`
          method of job container) is serialized into the following filekey::

            'customID_rawOutputSuffix'

          where 'rawOutputSuffix' is defined in ``$subset_results_suffix`` variable
          (see :ref:`annex_defaultconfigurationfile`)

        * any miscellaneous data produced by job container (obtained with
          :meth:`~kdvs.fw.Job.JobContainer.getMiscData` method), along with
          textual representation, is serialized under configurable filekey
          ``$jobs_misc_data_key`` (see :ref:`annex_defaultconfigurationfile`)

Assuming default configuration, and that the following example jobs bear custom IDs::

    job1, job2, job3

the following artefacts are saved::

        $ROOT_OUTPUT_DIRECTORY/
            KDVS_output/
                jobs/
                    JOBID_MAP.txt
                    JOBID_MAP
                    JC_MISC_DATA.txt
                    JC_MISC_DATA
                    job1
                    job1__RAW_OUT
                    job2
                    job2__RAW_OUT
                    job3
                    job3__RAW_OUT

.. _applications_debugoutput:

Debug output
============

The 'experiment.py' application produces additional debug output if ``--use-debug-output``
command line option is specified (see :ref:`applications_commandlineparameters`).

Debug output are various serialized objects, typically accompanied with respective
textual representation. Serialization follows current KDVS serialization protocol
(see :ref:`annex_serialization`) unless stated otherwise.

Currently, the following debug artefacts are produced:

    * in :meth:`~kdvs.bin.experiment.loadStaticData`, for each `managed static file`,
      a textual dump of its content is saved under the filekey::

        'pkc_manager_<managerID>_<dumpSuffix>'

      where 'managerID' is defined in 'DBID' entry parameter (see also :ref:`annex_staticdatafiles`)
      and 'dumpSuffix' is taken from ``$pk_manager_dump_suffix`` variable
      (see :ref:`annex_defaultconfigurationfile`) 

    * in :meth:`~kdvs.bin.experiment.buildGeneIDMap`, a serialized mapping under
      the configurable filekey ``$geneidmap_key`` (see :ref:`annex_defaultconfigurationfile`)

    * in :meth:`~kdvs.bin.experiment.buildPKCIDMap`, a serialized mapping under
      the configurable filekey ``$pkcidmap_key`` (see :ref:`annex_defaultconfigurationfile`),
      and serialized part of this mapping for selected GO domain under the filekey::

        ``$pkcidmap_key``_GO_``$go_domain``

      where ``$go_domain`` comes from application profile in user configuration file
      (see `go_domain`_)

    * in :meth:`~kdvs.bin.experiment.buildPKDrivenDataSubsets`, the following
      serialized mapping, along with textual representation, is preserved::

        {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}

      under the configurable filekey ``$subsets_key`` (see :ref:`annex_defaultconfigurationfile`)

    * in :meth:`~kdvs.bin.experiment.buildSubsetHierarchy`, the following artefacts
      are preserved:

        * serialized subset hierarchy (see :ref:`framework_subsethierarchy`),
          along with textual representation, is stored under configurable filekey
          ``$subset_hierarchy_key`` (see :ref:`annex_defaultconfigurationfile`);
          more precisely, it contains two attributes 'hierarchy' and 'symboltree'
          wrapped in dictionary

        * serialized `operations map`, along with textual representation, is stored
          under configurable filekey ``$operations_map_key`` (see :ref:`annex_defaultconfigurationfile`);
          more precisely, it contains textual `operation IDs` instead of actual Python
          calls

    * in :meth:`~kdvs.bin.experiment.submitSubsetOperations`, the complete
      submission order for all unique categories
      (see `misc`_ above for an explanation), along with textual representation,
      is serialized under the configurable filekey ``$submission_order_key``
      (see :ref:`annex_defaultconfigurationfile`)

    * in :meth:`~kdvs.bin.experiment.postprocessSubsetOperations`, the following artefacts
      are preserved:

        * job group completion mapping::

            {
                PKCID1: {
                    'completed': True/False,
                    'jobs': {
                        JobID1: True/False,
                        ...
                        JobIDn : True/False
                    }
                },
                ...
                PKCIDk: {
                    'completed': True/False,
                    'jobs': {
                        JobID1: True/False,
                        ...
                        JobIDn : True/False
                    }
                },
            }

          along with textual representation, is serialized under configurable filekey
          ``$group_completion_key`` (see :ref:`annex_defaultconfigurationfile`)

        * "technique2DOF" mapping between statistical technique IDs and associated
          degrees of freedom, that depends on the declarations of statistical
          techniques in application profile (see `statistical_techniques`_ above
          and :ref:`framework_statisticaltechniques`)::

            {
                techID1: {
                    'DOFS_IDXS': (1, ..., K1),
                    'DOFs': (dof1, ..., dofK1)
                },
                ...
                techIDn: {
                    'DOFS_IDXS': (1, ..., Kn),
                    'DOFs': (dof1, ..., dofKn)
                }
            }
                
          along with textual representation, is serialized under configurable
          filekey ``$technique2dof_key`` (see :ref:`annex_defaultconfigurationfile`)

    * in :meth:`~kdvs.bin.experiment.performSelections`, the following artefacts
      are preserved:

        * outer selection markings (see :ref:`framework_selecting`) for all unique
          categories, along with textual representation, are serialized under
          the configurable filekey ``$outer_selection_key`` (see :ref:`annex_defaultconfigurationfile`)

        * inner selection markings (see :ref:`framework_selecting`) for all unique
          categories, along with textual representation, are serialized under
          the configurable filekey ``$inner_selection_key`` (see :ref:`annex_defaultconfigurationfile`)

    * in :meth:`~kdvs.bin.experiment.prepareReports`, the following artefacts
      are preserved:
    
        * "em2annotation" mapping, obtained with :func:`~kdvs.fw.Annotation.get_em2annotation`
          function, along with textual representation, is serialized under
          the configurable filekey ``$em2annotation_key`` (see :ref:`annex_defaultconfigurationfile`)

        * "pkcid2ssname", bi--directional mapping between PKC IDs (i.e. GO terms)
          and subset names, along with textual representation, is serialized under
          the configurable filekey ``$pkcid2ssname_key`` (see :ref:`annex_defaultconfigurationfile`)

.. _applications_usingwrapper:

Using wrapper.py
++++++++++++++++

Overview
========

The 'experiment.py' application can be also executed with 'wrapper.py' (see :ref:`annex_wrapper`);
assuming that KDVS source archive has been unpacked to ``$KDVS_ROOT``::

    cd $KDVS_ROOT
    python wrapper.py kdvs/bin/experiment.py [options]

See :ref:`applications_commandlineparameters` for full option list.

.. _applications_commandlineparameters:

Command line parameters
+++++++++++++++++++++++

.. program-output:: python ../wrapper.py kdvs/bin/experiment.py -h

