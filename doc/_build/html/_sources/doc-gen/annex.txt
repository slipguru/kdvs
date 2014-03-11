.. _annex:

Annex
*****

.. _annex_defaultconfigurationfile:

Default configuration file
--------------------------

The default configuration file is located in the following location:

    kdvs/config/default_cfg.py

For programmatic use, see :ref:`framework_configurationfiles`.

.. note::

    When referring to the variable from default configuration file, the following
    notation is used:

        ``$log_name``

The current variables, in logical subgroups, are listed below. Note that
many options are valid only for 'experiment.py' application.

===============================  ===========  ================================= ===========================================
Name                             Type         Value                             Description
===============================  ===========  ================================= ===========================================
**Logging**                                                                     Options related to logging, i.e. default
                                                                                loggers, default logger configuration etc
-------------------------------  -----------  --------------------------------- -------------------------------------------
log_name                         string       kdvs                              name of the default logger (see also
                                                                                :class:`logging.Logger`)

log_file                         string       kdvs.log                          path to default log file, relative to the
                                                                                user configuration file

log_type_def_std                 string       kdvs.core.log.StreamLogger        default class for stream-oriented logger

log_type_def_file                string       kdvs.core.log.RotatingFileLogger  default class for file-oriented logger
**Application profile**                                                         Options related to application profile
                                                                                that will be read and parsed by the
                                                                                application
-------------------------------  -----------  --------------------------------- -------------------------------------------

experiment_profile               string       kdvs.fw.impl.app.Profile.         default class of application profile
                                              NULL_PROFILE

experiment_profile_inst          dict         {}                                default content of application profile
                                                                                instance
**Initializers**                                                                Options related to various standard
                                                                                dynamically initialized components
-------------------------------  -----------  --------------------------------- -------------------------------------------
job_container_type               string       kdvs.fw.impl.job.SimpleJob.       default class of job container
                                              SimpleJobContainer
job_container_cfg                dict         {}                                default initialization parameters for job
                                                                                container instance
storage_manager_type             string       kdvs.fw.StorageManager.           default class of storage manager
                                              StorageManager
execution_environment_type       string       kdvs.core.env.                    default class of execution environment
                                              LoggedExecutionEnvironment
execution_environment_exp_cfg    dict         {                                 default initialization parameters for
                                              'logger' : Logger(),              execution environment instance
                                              }
job_group_manager_type           string       kdvs.fw.Job.JobGroupManager       default class of job group manager
job_group_manager_cfg            dict         {}                                default initialization parameters for
                                                                                job group manager instance
**Database IDs**                                                                Options related to databases controlled
                                                                                by :class:`~kdvs.core.db.DBManager`
-------------------------------  -----------  --------------------------------- -------------------------------------------
data_db_id                       string       DATA                              default DB where all data tables will be
                                                                                stored
map_db_id                        string       MAPS                              default DB where all mapping tables will
                                                                                be stored
misc_db_id                       string       MISC                              default DB where all miscellaneous tables
                                                                                will be stored
**Standard filekeys**                                                           Options related to standard files
                                                                                produced by KDVS; each file is identified
                                                                                by `filekey`; standard files are stored
                                                                                in standard locations (see below); many
                                                                                standard files contains diagnostic
                                                                                information that can be suppressed; see
                                                                                'experiment.py' description for more
                                                                                details
-------------------------------  -----------  --------------------------------- -------------------------------------------
cfg_key                          string       CFG                               default filekey for serialized initial
                                                                                configuration; initial configuration
                                                                                contains all environment variables;
                                                                                textual version is also saved
                                                                                evaluated before execution of any actions
ts_start_key                     string       TS_START                          default filekey for starting timestamp;
                                                                                KDVS saves starting timestamp in plain
                                                                                text for easier diagnostics if necessary
                                                                                (no log parsing nedded)
ts_end_key                       string       TS_END                            default filekey for ending timestamp;
                                                                                KDVS saves ending timestamp in plain text
                                                                                for easier diagnostics if necessary
                                                                                (no log parsing nedded)
pkcidmap_key                     string       PKCIDMAP                          default filekey for serialized mapping
                                                                                :class:`~kdvs.fw.Map.PKCIDMap`
geneidmap_key                    string       GENEIDMAP                         default filekey for serialized mapping
                                                                                :class:`~kdvs.fw.Map.GeneIDMap`
subsets_key                      string       SUBSETS                           default filekey for serialized subsets
                                                                                mapping; see also :meth:`~kdvs.bin.experiment.buildPKDrivenDataSubsets`
                                                                                action in 'experiment.py'
subsets_results_key              string       SUBSETS_RESULTS                   default filekey for serialized subsets
                                                                                results (currently not used)
subset_hierarchy_key             string       SUBSET_HIERARCHY                  default filekey for serialized
                                                                                representation of subset hierarchy
                                                                                (hierarchy + symboltree); see
                                                                                also :meth:`~kdvs.bin.experiment.buildSubsetHierarchy`
                                                                                action in 'experiment.py'
operations_map_key               string       OP_MAP                            default filekey for serialized
                                                                                representation of all operations performed
                                                                                on the whole category tree; see also
                                                                                :meth:`~kdvs.bin.experiment.buildSubsetHierarchy`
                                                                                action in 'experiment.py'
jobID_map_key                    string       JOBID_MAP                         default filekey for serialized mapping
                                                                                between default job IDs (assigned by job
                                                                                container) and custom job IDs (assigned
                                                                                by technique during job creation); see
                                                                                also :meth:`~kdvs.bin.experiment.submitSubsetOperations`
                                                                                action in 'experiment.py'
submission_order_key             string       SUBMISSION_ORDER                  default filekey for serialized submission
                                                                                order, i.e. the `final` list of all subsets
                                                                                to be processed (i.e. execution of
                                                                                statistical technique, job creation,
                                                                                results creation); submission order is
                                                                                altered by "test mode"; see also
                                                                                :meth:`~kdvs.bin.experiment.submitSubsetOperations`
                                                                                action in 'experiment.py'
jobs_exceptions_key              string       JEXC                              default filekey for serialized
                                                                                representation of job exceptions (if any
                                                                                were thrown during job execution); see also
                                                                                :meth:`~kdvs.bin.experiment.executeSubsetOperations`
                                                                                action in 'experiment.py'
jobs_misc_data_key               string       JC_MISC_DATA                      default filekey for serialized
                                                                                representation of miscellaneous data
                                                                                produced by job container (may be empty);
                                                                                see also
                                                                                :meth:`~kdvs.bin.experiment.executeSubsetOperations`
                                                                                action in 'experiment.py'
group_completion_key             string       GRCOMP                            default filekey for serialized information
                                                                                of job group completion dictionary; see
                                                                                also :meth:`~kdvs.bin.experiment.postprocessSubsetOperations`
                                                                                action in 'experiment.py'
technique2dof_key                string       TECH2DOF                          default filekey for serialized mapping
                                                                                between ID of statistical techniques and
                                                                                their degrees of freedom; see also
                                                                                :meth:`~kdvs.bin.experiment.postprocessSubsetOperations`
                                                                                action in 'experiment.py'
technique2ssname_key             string       TECH2SS                           default filekey for serialized mapping
                                                                                between ID of statistical techniques and
                                                                                subsets they are assigned to; see also
                                                                                :meth:`~kdvs.bin.experiment.postprocessSubsetOperations`
                                                                                action in 'experiment.py'
outer_selection_key              string       OUTER_SELECTION                   default filekey for serialized results of
                                                                                outer selection (selection markings); see
                                                                                also :meth:`~kdvs.bin.experiment.performSelections`
                                                                                action in 'experiment.py'
inner_selection_key              string       INNER_SELECTION                   default filekey for serialized results of
                                                                                inner selection (selection markings); see
                                                                                also :meth:`~kdvs.bin.experiment.performSelections`
                                                                                action in 'experiment.py'
em2annotation_key                string       EM2ANNOTATION                     default filekey for serialized mapping
                                                                                between measurements and annotations;
                                                                                see also :func:`~kdvs.fw.Annotation.get_em2annotation`
pkcid2ssname_key                 string       PKCID2SS                          default filekey for serialized mapping
                                                                                between PKC IDs and subsets IDs;
                                                                                see also :meth:`~kdvs.bin.experiment.prepareReports`
                                                                                action in 'experiment.py'
misc_view_key                    string       MISC                              default filekey for any miscellaneous
                                                                                information (currently not used)
**Standard locations**                                                          Options related to standard locations
                                                                                controlled by :class:`~kdvs.fw.StorageManager.StorageManager`
                                                                                instance; "debug" location contains many
                                                                                optional files; all locations are relative
                                                                                to output directory; see 'experiment.py'
                                                                                description for more details
-------------------------------  -----------  --------------------------------- -------------------------------------------
dbm_location                     string       db                                default location for database files
debug_output_location            string       debug                             default location for debug files (many are
                                                                                optional; see :class:`~kdvs.bin.experiment.MA_GO_Experiment_App`
                                                                                individual actions for more details
jobs_location                    string       jobs                              default location for serialized `raw`
                                                                                (unprocessed) jobs results
subsets_location                 string       ss                                default location for serialized data
                                                                                subsets
subsets_results_location         string       ss_results                        default location for serialized detailed
                                                                                results for each data subset; for each
                                                                                subset a separate subdirectory is created;
                                                                                see also :meth:`~kdvs.bin.experiment.storeCompleteResults`
                                                                                action in 'experiment.py'
plots_sublocation                string       plots                             default sublocation for plots (currently
                                                                                not used)
**Statistical artefacts**                                                       Options related to statistical techniques
                                                                                and related components
-------------------------------  -----------  --------------------------------- -------------------------------------------
unused_sample_label              integer      0                                 default label for "unused" samples; when
                                                                                sample is associated with 'unused' label,
                                                                                it will be skipped from further procesing,
                                                                                i.e. measurements for this sample will not
                                                                                be included into any data subset
null_dof                         string       NullDOF                           default symbol for unique "null" degree of
                                                                                freedom, used by statistical techniques;
                                                                                see :ref:`annex_globaltechniqueparameters`
**Miscellaneous artefacts**                                                     Options that fit elsewhere
-------------------------------  -----------  --------------------------------- -------------------------------------------
pk_manager_dump_suffix           string       _DUMP                             default filekey suffix for the dump of
                                                                                prior knowledge manager; see :class:`~kdvs.fw.PK.PKCManager`
                                                                                for more information; :class:`~kdvs.fw.impl.pk.go.GeneOntology.GOManager`
                                                                                implementation produces such dump in :meth:`~kdvs.bin.experiment.loadStaticData`
                                                                                action in 'experiment.py' application
subset_results_suffix            string       _RES                              default filekey suffix for serialized
                                                                                instance of :class:`~kdvs.fw.Stat.Results`
                                                                                for each data subset; see also :meth:`~kdvs.bin.experiment.storeCompleteResults`
                                                                                action in 'experiment.py' application
subset_ds_suffix                 string       _DS                               default filekey suffix for serialized
                                                                                data subset (currently not used)
jobs_raw_output_suffix           string       _RAW_OUT                          default filekey suffix for serialized raw
                                                                                job result; raw job results are serialized
                                                                                in :meth:`~kdvs.bin.experiment.executeSubsetOperations`
                                                                                action of 'experiment.py' when custom job
                                                                                ID is provided
txt_suffix                       string       .txt                              default prefix for serialized textual data;
                                                                                many serialized data structures have their
                                                                                textual representation saved as well; for
                                                                                example, default configuration can be saved
                                                                                both as CFG and CFG.txt
subset_submission_all_symbol     string       __all__                           default symbol for submission of all data
                                                                                subsets (currently not used)
test_submission_listing_thr      integer      5                                 default number of subsets submitted listed
                                                                                in log when "test mode" is used; if more
                                                                                subsets are submitted, ">5" will appear in
                                                                                the log
**Static data files related**                                                   Options related to static data files
                                                                                interpreted by KDVS
-------------------------------  -----------  --------------------------------- -------------------------------------------
def_data_path                    string       result of 'kdvs.core.config.      default filesystem path to directory that
                                              getDefaultDataRootPath()'         contains static data files
static_data_files                dict         see `Static data files`_          default configuration of static data files
===============================  ===========  ================================= ===========================================

.. _annex_staticdatafiles:

Static data files
+++++++++++++++++

Static data files are configured with specification evaluated from dictionary.
Each static file has its own entry as follows::

    static_data_files = {
        'fileID1' : {
            # entry parameters
        },
        # ...
        'fileIDn' : {
            # entry parameters
        },
    }

Static file may be loaded directly into KDVS database governed by :class:`~kdvs.core.db.DBManager`
instance, or managed by the concrete instance of :class:`~kdvs.fw.PK.PKCManager`.

.. note::

    In 'experiment.py' application, loading into database and managing via manager
    is `exclusive`, i.e. static file may either be loaded or managed, but not both.

Currently, the following entry parameters are interpreted:

    * 'DBID' (string) -- when loaded: the name of database table to be loaded
      into; when managed: composite part of filekey for manager dump (see
      :class:`~kdvs.fw.PK.PKCManager` API documentation)

    * 'spec' (tuple of string) -- tuple of path specification, as follows:
      ('directory', 'filename_pattern')

        * 'directory' (string) -- subdirectory of KDVS "root data directory" where
          the file is located; the `default` data directory path may be obtained
          with :meth:`~kdvs.core.config.getDefaultDataRootPath`; in 'experiment.py'
          application, the path may be overriden by user with "-s" command line
          option (see :ref:`applications_commandlineparameters`)

        * 'filename_pattern' (string) -- expression understood by :mod:`glob`
          module that specifies the name of the file; for instance, with expression::

              'go_termdb*.obo-xml*'

          the following filenames will be recognized::

              'go_termdb.obo-xml'
              'go_termdb_01_01_2014.obo-xml'
              'go_termdb.obo-xml.gz'
              'go_termdb_01_01_2014.obo-xml.bz2'

      For instance, the following specification::

        ('GO', 'go_termdb*.obo-xml*')

      defines static file located in subdirectory 'GO' of KDVS "root data directory"
      $ROOT_DATA_PATH that can be resolved into the following example absolute paths::

        '$ROOT_DATA_PATH/GO/go_termdb.obo-xml'
        '$ROOT_DATA_PATH/GO/go_termdb_01_01_2014.obo-xml'
        '$ROOT_DATA_PATH/GO/go_termdb.obo-xml.gz'
        '$ROOT_DATA_PATH/GO/go_termdb_01_01_2014.obo-xml.bz2'

      .. note::

          In 'experiment.py' application, currently the tuple is assumed to
          contain `exactly two strings`; other implementations may use more
          refined handling of the tuple content.

    * 'path' (string/None) -- absolute filesystem path to static file, or None
      if not used

      .. note::

          In 'experiment.py' application, it is always specified as None since
          absolute file path is resolved from path specification, and the value
          is automatically updated.

    * 'fh' (file--like/None) -- opened file handle for static file, or None
      if not used

      .. note::

          In 'experiment.py' application, it is always specified as None since
          after resolving absolute file path, the static file is opened, and the
          value is automatically updated.

    * 'type' (string) -- descriptive type of the file, such as 'DSV' or 'XML'

    * 'metadata' (dict/None) -- when loaded: metadata used to interpret the content
      of the file (typically DSV); when managed: None

      Currently, the following metadata are recognized:

        * 'delimiter' (string) -- delimiter that separates values in each line
          of the file
        * 'comment' (string/None) -- comment prefix; each commented line of the
          file is discarded; None if not used

    * 'loadToDB' (boolean) -- specifies if the static file shall be loaded into
      database governed by :class:`~kdvs.core.db.DBManager` instance; True if
      loaded, False otherwise

      .. note::

          In 'experiment.py' application, this parameter serves as switch;
          if True, the file is loaded into database; if False, the file is managed
          by the concrete instance of :class:`~kdvs.fw.PK.PKCManager`.

    * 'indexes' (tuple of string/None) -- when loaded: tuple of the column names that
      shall be `indexed` when loaded into database; indexing speeds up information querying
      from these columns, but increases the overall size of database, therefore
      only crucial columns should be indexed; None if the only index shall be
      created for ID column (see also :class:`~kdvs.fw.DBTable.DBTable` and
      :class:`~kdvs.fw.DSV.DSV` API documentation); empty tuple for creating no
      indexes at all; when managed: not interpreted (typically left as empty tuple)

    * 'manager' (dict/None) -- when loaded: not interpreted (typically left as None);
      when managed: component initializer of the :class:`~kdvs.fw.PK.PKCManager`
      instance (see also :ref:`applications_componentinitializers`)

      In 'experiment.py' application, the initializer has special interpretation.
      It must contain two dictionaries that define parameters for :meth:`~kdvs.fw.PK.PKCManager.configure`
      and :meth:`~kdvs.fw.PK.PKCManager.load` methods::

          {
          # ...
            'manager' : {
                'manager_import_class' : {
                    'configure' : {
                        # parameters for 'configure' method
                    },
        
                    'load' : {
                        # parameters for 'load' method
                    },
                }
            }
          # ...
          }

      Refer to the API documentation of concrete implementations of
      :class:`~kdvs.fw.PK.PKCManager` for all the parameters. For
      `Gene Ontology <http://www.geneontology.org/>`_ prior knowledge,
      :class:`~kdvs.fw.impl.pk.go.GeneOntology.GOManager` class is provided.


The following configuration currently specifies default static data files in
default configuration file 'kdvs/config/default_cfg.py'::

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

.. note::

    In :meth:`~kdvs.fw.impl.pk.go.GeneOntology.GOManager.load` method of
    :class:`~kdvs.fw.impl.pk.go.GeneOntology.GOManager`, only `keyworded` arguments
    are specified; 'experiment.py' automatically uses the value of 'fh' entry
    parameter as the first argument.


.. _annex_globaltechniqueparameters:

Global technique parameters
---------------------------

Each statistical technique must define two `global` parameters:

    * 'global_degrees_of_freedom' (tuple of string/None)
    * 'job_importable' (boolean)

Degree(s) of freedom (DOF)
++++++++++++++++++++++++++

The parameter 'global_degrees_of_freedom' lists all symbols for all `degrees of
freedom` the technique uses (see :ref:`framework_statisticaltechniques`). For
instance, if the technique uses the following range of parameters::

    0.1, 0.001, 0.000001

some meaningful name can be assigned to each value as `symbol`::

    'par_a1', 'par_2', 'par_a3'

The symbols are provided during component initialization for the individual
technique (see :ref:`applications_componentinitializers`). Note that symbols
are only specified here; it is up to the technique to reconstruct proper mapping
`symbol<->parameter_value` and construct proper jobs with proper calls that
depend on individual parameter value(s).

For instance, the technique :class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2` uses
a range of parameter `mu`, where single call for each of the parameter value is
performed, and results from those calls are recognized separately during results
interpretation. See :class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2` API documentation,
`l1l2py documentation <http://slipguru.disi.unige.it/Software/L1L2Py/>`__ and
references therein, for more details. For instance, if the range of parameter
`mu` has 3 values, and one wants the values to be associated with the following
`symbols`::

    'mu0', 'mu1', 'mu2'

the component initializer must contain the global parameter::

    {
    # ...
        'kdvs.fw.impl.stat.L1L2.L1L2_L1L2' : {
            # ...
            'global_degrees_of_freedom' : tuple(['mu%d' % i for i in range(3)]),
            # ...
        }
    # ...
    }

Note that some techniques many not need any degrees of freedom since they do not
depend on some range(s) of parameters. Still, to gather the technique implementations
under single umbrella, the "virtual degree of freedom", also referred to as "null"
degree, is created.

In that case, one can specify None as the value of global parameter::

    {
        'global_degrees_of_freedom' : None,
    }

and the `virtual degree of freedom` will be created automatically with the name
specified in 'null_dof' variable in default configuration file (see :ref:`annex_defaultconfigurationfile`).

Job importability
+++++++++++++++++

The parameter 'job_importable' specifies if the "job function" is importable on
remote machine, in case that remote job container is used;
see :ref:`framework_statisticaltechniques` and :ref:`framework_jobcreationandexecution`
for more information.

For instance, when :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer` is used,
it distributes jobs to remote machines for execution. Each :class:`~kdvs.fw.Job.Job`
instance is a wrapper around `job function`, that may contain statistical call,
such as::

    l1l2py.model_selection(...)

(see `l1l2py documentation <http://slipguru.disi.unige.it/Software/L1L2Py/core.html#complete-model-selection>`__).

If 'l1l2py.model_selection' is specified as `job function` during creation of
:class:`~kdvs.fw.Job.Job` instance, and 'l1l2py' is installed on remote machine
that will execute the job, :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`
can simply::

    import l1l2py

and execute the job function. In that case, the job is **importable** by remote
container. See also :meth:`kdvs.fw.impl.job.PPlusJob.PPlusJobContainer.addJob`
API documentation.

On the other hand, if :meth:`~kdvs.fw.impl.stat.L1L2.l1l2_l1l2_job_wrapper` is
specified as `job function`, :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer`,
even if l1l2py is installed on remote machine, cannot simply import l1l2py and
execute the job, because the physical function may not exist on remote machine
(i.e. KDVS may not be installed there). In that case,
:meth:`~kdvs.fw.impl.stat.L1L2.l1l2_l1l2_job_wrapper` function is `physically
transported` to remote machine for execution. In that case, the job is **not importable**.
See also :meth:`kdvs.fw.impl.job.PPlusJob.PPlusJobContainer.addJob` API documentation.

All reference statistical technique implementations of : :class:`~kdvs.fw.impl.stat.L1L2.L1L2_L1L2`,
:class:`~kdvs.fw.impl.stat.L1L2.L1L2_RLS`, and :class:`~kdvs.fw.impl.stat.L1L2.L1L2_OLS`,
have their `job wrappers` provided by KDVS that are used as job functions:

    * :meth:`~kdvs.fw.impl.stat.L1L2.l1l2_l1l2_job_wrapper`
    * :meth:`~kdvs.fw.impl.stat.L1L2.l1l2_rls_job_wrapper`
    * :meth:`~kdvs.fw.impl.stat.L1L2.l1l2_ols_job_wrapper`

therefore each time one of these techniques is configured in configuration file
(see :ref:`applications_componentinitializers`), one must specify the 'job_importable'
as False::

    {
    # ...

        'kdvs.fw.impl.stat.L1L2.L1L2_L1L2' : {
            # ...
            'job_importable' : False,
            # ...
        },
    
        'kdvs.fw.impl.stat.L1L2.L1L2_RLS' : {
            # ...
            'job_importable' : False,
            # ...
        },
    
        'kdvs.fw.impl.stat.L1L2.L1L2_OLS' : {
            # ...
            'job_importable' : False,
            # ...
        },

    # ...
    }

.. _annex_serialization:

Serialization
-------------

Overview
++++++++

When possible, KDVS tries to store virtually all artefacts produced, including
serialized Python objects, plain text output files, plots, etc
(see :ref:`applications_outputdirectory`). To unify this activity, KDVS uses a
`serialization protocol`, i.e. pre--defined set of functions that store the object
in question, produce textual representation if necessary, or compress it to save
space. Whenever possible, KDVS uses these functions instead of creating a file
manually.

.. note::

    Many objects produced by 'experiment.py' application have textual representation
    generated as well. While this `increases` disk space, it was intended to ease
    the verification of the content of individual binary files. Currently, it is
    not possible to directly disable it.

.. note::

    Many artefacts are already generated by 'experiment.py' application as
    "debug output" that can be omitted; for exhaustive list see
    :ref:`applications_debugoutput`.

Current protocol
++++++++++++++++

Binary data
~~~~~~~~~~~

The following functions comprise the KDVS serialization protocol of `binary data`:

    * :func:`~kdvs.core.util.serializeObj`

      this function compresses the Python object; currently it applies :mod:`gzip`
      compression to the :mod:`pickle`--d object data stream; :data:`pickle.HIGHEST_PROTOCOL`
      is used; equivalent to::

        # output_fh is a opened write--mode file--like object that will hold serialized object data
        # proto is a pickle protocol
        wrapped_out_fh = gzip.GzipFile(fileobj=output_fh)
        cPickle.Pickler(wrapped_out_fh, protocol=proto).dump(obj)

    * :func:`~kdvs.core.util.deserializeObj`

      this function decompresses the Python object; currently it loads
      :mod:`pickle`--d object data stream un--:mod:`gzip`--ing in the background;
      equivalent to::

        # input_fh is a opened read--mode file--like object with serialized object data
        wrapped_in_fh = gzip.GzipFile(fileobj=input_fh)
        return cPickle.Unpickler(wrapped_in_fh).load()

    * :func:`~kdvs.core.util.pprintObj`

      this function emits textual representation of Python object to the opened
      file--like object using :mod:`pprint` functionality; equivalent to::

        pprint.pprint(obj, out_fh)

    * :func:`~kdvs.core.util.writeObj`

      this function writes Python object "as--is" to the opened file--like object;
      equivalent to::

        output_fh.write(obj)

.. note::

    The serialization functions have been changed in KDVS 2.0 in order to ease
    future transition to different `file--like wrappers` as needed.

Textual data
~~~~~~~~~~~~

The following functions comprise the KDVS serialization protocol of `textual data`:

    * :func:`~kdvs.core.util.serializeTxt`

      this function writes an iterable of plain text lines to the opened file--like
      object; equivalent to::

        output_fh.writelines(lines)

Legacy protocol ("PZP")
+++++++++++++++++++++++

The following information is taken directly from old version of KDVS documentation
about previous serialization protocol.

.. note::

    Since KDVS 2.0 was created as a `replacement` for the old prototypic KDVS 1.0,
    the following legacy protocol is `not supported`.

The PZP (Pickle, Zip, Pickle) protocol operates on Python objects as follows:

- :mod:`pickle` the selected Python object with lowest possible pickle protocol
  (currently 0) into string (*pass1*)
- compress resulting string, using :func:`zlib.compress` with default parameters
  (*pass2*)
- :mod:`pickle` zipped string again with highest possible pickle protocol
  (currently :obj:`pickle.HIGHEST_PROTOCOL`) into string or file (*pass3*)

Pickling in `pass1` generates verbose representation that can be zipped
effectively in `pass2`; pickling again in `pass3`, while seemingly redundant,
provides simple and convenient mechanism of data verification when restoring
original object, all handled completely by Python standard library in few lines::

    def pzp_serialize(input_object):
        import cPickle
        import zlib
        # pickle, zip, pickle
        pass1=cPickle.dumps(input_object, protocol=0)
        pass2=zlib.compress(pass1)
        pass3=cPickle.dumps(pass2, protocol=cPickle.HIGHEST_PROTOCOL)
        return pass3

Analogically, reciprocal UUU (Unpickle, Unzip, Unpickle) protocol provides
mechanism for restoring original object, again in few lines:

- un-pickle given input PZP string (*pass1*)
- un-zip resulting string (*pass2*)
- un-pickle resulting string again (*pass3*)

::

    def pzp_deserialize(encoded_object):
        import cPickle
        import zlib
        # unpickle, unzip, unpickle
        pass1=cPickle.loads(encoded_object)
        pass2=zlib.decompress(pass1)
        pass3=cPickle.loads(pass2)
        return pass3


.. _annex_wrapper:

Using wrapper.py
----------------

If KDVS is not installed as Python module but unpacked from source archive,
applications and companion scripts may be still executed by using 'wrapper.py'
script.

Assuming KDVS source archive has been unpacked to ``$KDVS_ROOT``, the wrapper is
located in the following location::

    $KDVS_ROOT/wrapper.py

It can be used as follows::

    cd $KDVS_ROOT
    python wrapper.py [path to application/script] [options...]

where path to application/script is relative to ``$KDVS_ROOT``, e.g.::

    kdvs/bin/experiment.py

or::

    kdvs/tests/runTests.py

and options are specific for the application/script.

Typically, full list of options of any KDVS application/script can be listed
using ``-h`` option, for example::

    cd $KDVS_ROOT
    python wrapper.py kdvs/bin/experiment.py -h

In order to be executed with 'wrapper.py', the application/companion script
must contain the following code pattern ('pass' added for clarity)::

    def main():
        # body of application/script follows
        # ...
        pass

    if __name__=='__main__':
        main()

since 'wrapper.py' specifically looks for and executes 'main' method.

.. note::

    More refined implementation of 'wrapper.py' can be built around :mod:`runpy` module
    (bearing in mind keeping compatibility with Python 2.6).

.. _annex_contributions:

Contributions
-------------

KDVS uses contributed code located in the following location::

    kdvs/contrib

See :mod:`kdvs.contrib` API documentation for more details.

If KDVS is not installed as Python module, all contributed applications must be
executed with wrapper (see :ref:`annex_wrapper`).

Bag
+++

:class:`~kdvs.contrib.counter.Counter` class is an implementation of bag (i.e. multiset)
provided for compatibility with Python 2.6. It is based on the following:

    http://code.activestate.com/recipes/576611/

Ordered dictionary
++++++++++++++++++

:class:`~kdvs.contrib.ordereddict.OrderedDict` class is an implementation of a
dictionary that remembers the order of insertion of key--value pairs.

Dataset generator
+++++++++++++++++

:mod:`~kdvs.contrib.dataset_generation` module contains the companion application
that generates one or more randomized datasets with correlated variables. See
API documentation for the statistical properties of the variables. Such
datasets can be used to test KDVS functionality. It can be executed as follows::

    cd $KDVS_ROOT
    python wrapper.py kdvs/contrib/dataset_generation.py

It has the following command line parameters:

.. program-output:: python  ../wrapper.py kdvs/contrib/dataset_generation.py -h

Tools
-----

KDVS provides specialized tools for some activities in the following location::

    kdvs/tools

See :mod:`kdvs.tools` API documentation for more details.

If KDVS is not installed as Python module, all tools must be executed with wrapper
(see :ref:`annex_wrapper`).

PPlus job verifier
++++++++++++++++++

:mod:`~kdvs.tools.pplus_job_verifier` module contains the companion tool that checks
jobs executed by :class:`~kdvs.fw.impl.job.PPlusJob.PPlusJobContainer` instance.
It can be executed as follows::

    cd $KDVS_ROOT
    python wrapper.py kdvs/tools/pplus_job_verifier.py

It has the following command line parameters:

.. program-output:: python ../wrapper.py kdvs/tools/pplus_job_verifier.py -h

Predictions extractor
+++++++++++++++++++++

:mod:`~kdvs.tools.predictions_extractor` module contains the companion tool that
extracts predictions made during individual classification tasks.
It can be executed as follows::

    cd $KDVS_ROOT
    python wrapper.py kdvs/tools/predictions_extractor.py

It has the following command line parameters:

.. program-output:: python ../wrapper.py kdvs/tools/predictions_extractor.py -h

v1vs2
+++++

These tools were used to compare the results produced by KDVS 1.0 and KDVS 2.0
for `reference` statistical techniques. Since `full migration path` 1.0->2.0 has
not been devised as of this writing, they are provided here for future reference.
See :mod:`kdvs.tools.v1vs2` API documentation for more details.

Testing
-------

Three levels of testing are devised for KDVS:

    * unit tests (**t**)
    * function tests (**f**)
    * system tests (**s**)

Currently, only **t** tests are implemented; some dummy **f** and **s** tests
are also included for completion.

KDVS tests are located in the following location::

    kdvs/tests

See :mod:`kdvs.tests` API documentation for more details.

Test runner
+++++++++++

KDVS tests can be executed with the following companion script::

    kdvs/tests/runTests.py

It has the following command line options:

.. program-output:: python ../wrapper.py kdvs/tests/runTests.py -h

Unit tests
++++++++++

These tests are intended to test each elementary functionality of the KDVS codebase.
For instance, each single abstract class and its implementations is testable by
unit tests.

Unit tests are the only complete test suite at the time of this writing.

So far, unit tests have been successfully run on the following configurations:

    * Linux Ubuntu 12.04, Python 2.7
    * Apple OS/X 10.7, Python 2.7
    * Windows 7, Python 2.6

Function tests
++++++++++++++

These tests are intended to test separable blocks of elementary functionalities
within KDVS codebase. For instance, interplay between subset of classes that can
be separated from other classes, is testable by function tests.

No function tests exist at the time of this writing.

System tests
++++++++++++

These tests are intended to test specific complete flows of function blocks within
KDVS codebase. For instance, executing complete application with test synthetic
data, is testable by system tests.

No system tests exist at the time of this writing.

Documenting
-----------

KDVS HTML documentation is built with `sphinx <http://sphinx-doc.org>`__ as follows
(assuming ``sphinx`` is installed)::

    cd $KDVS_ROOT/doc
    make html

KDVS HTML API documentation is built with
`sphinx-apidoc <http://sphinx-doc.org/man/sphinx-apidoc.html>`__ as follows (assuming
``sphinx`` is installed)::

    cd $KDVS_ROOT
    sphinx-apidoc -f -o doc/doc-api kdvs

.. note::

    Do not use distutils 'sphinx_build' command.

Building
--------

Building KDVS requires the following Python packages:

    * :mod:`distutils` (shipped with Python)
    * `setuptools <https://pypi.python.org/pypi/setuptools>`__ (tested with v0.6)

To build KDVS source archive::

    cd $KDVS_ROOT
    python setup.py sdist

The default distribution for the current operating system (.tar.gz for Linux, .zip
for Windows) will be located in::

    $KDVS_ROOT/dist

To build KDVS binary distribution::

    cd $KDVS_ROOT
    python setup.py bdist

The default distribution for the current operating system (.tar.gz for Linux, .zip
for Windows) will be located in::

    $KDVS_ROOT/dist

To clean remaining build artefacts in the 'build' folder::

    cd $KDVS_ROOT
    python setup.py clean

Installing
----------

To install KDVS from source archive::

    cd $KDVS_ROOT
    python setup.py install

most likely preceded by ``sudo``.

Note that documentation and examples are not copied.

Uninstalling
------------

Uninstalling KDVS requires the following Python packages:

    * `pip <https://pypi.python.org/pypi/pip>`__

To uninstall KDVS::

    pip uninstall kdvs

most likely preceded by ``sudo``.

