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
Provides KDVS application 'experiment'. It performs prior--knowledge--guided
feature selection and re--annotation, according to specified configuration.
It uses Gene Ontology as prior knowledge source and microarray gene expression
as measured data.

IMPORTANT NOTE. This application is not polished enough. The API needs to be
refined more. Some details are still hard--coded.
"""

from kdvs.core.error import Error, Warn
from kdvs.core.util import getFileNameComponent, importComponent, serializeObj, \
    pprintObj, deserializeObj, writeObj, serializeTxt, quote, resolveIndexes
from kdvs.fw.Annotation import get_em2annotation
from kdvs.fw.Categorizer import Categorizer
from kdvs.fw.DSV import DSV
from kdvs.fw.Job import NOTPRODUCED
from kdvs.fw.Map import SetBDMap
from kdvs.fw.Stat import Labels, RESULTS_PLOTS_ID_KEY
from kdvs.fw.impl.annotation.HGNC import correctHGNCApprovedSymbols, \
    generateHGNCPreviousSymbols, generateHGNCSynonyms
from kdvs.fw.impl.app.CmdLineApp import CmdLineApp
from kdvs.fw.impl.data.PKDrivenData import PKDrivenDBDataManager, \
    PKDrivenDBSubsetHierarchy
from kdvs.fw.impl.pk.go.GeneOntology import GO_id2num, GO_num2id
import collections
import glob
import operator
import os
from kdvs.core.provider import fileProvider

class MA_GO_Experiment_App(CmdLineApp):
    r"""
Main application class. It interprets the instance of
:data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE`.
    """
    def prepare(self):
        r"""
Add all actions, in the following order:

    * :func:`resolveStaticDataFiles`
    * :func:`loadStaticData`
    * :func:`postprocessStaticData`
    * :func:`loadUserData`
    * :func:`resolveProfileComponents`
    * :func:`buildGeneIDMap`
    * :func:`buildPKCIDMap`
    * :func:`obtainLabels`
    * :func:`buildPKDrivenDataSubsets`
    * :func:`buildSubsetHierarchy`
    * :func:`submitSubsetOperations`
    * :func:`executeSubsetOperations`
    * :func:`postprocessSubsetOperations`
    * :func:`performSelections`
    * :func:`storeCompleteResults`
    * :func:`prepareReports`
        """
        self.env.addCallable(resolveStaticDataFiles)
        self.env.addCallable(loadStaticData)
        self.env.addCallable(postprocessStaticData)
        self.env.addCallable(loadUserData)
        self.env.addCallable(resolveProfileComponents)
        self.env.addCallable(buildGeneIDMap)
        self.env.addCallable(buildPKCIDMap)
        self.env.addCallable(obtainLabels)
        self.env.addCallable(buildPKDrivenDataSubsets)
        self.env.addCallable(buildSubsetHierarchy)
        self.env.addCallable(submitSubsetOperations)
        self.env.addCallable(executeSubsetOperations)
        self.env.addCallable(postprocessSubsetOperations)
        self.env.addCallable(performSelections)
        self.env.addCallable(storeCompleteResults)
        self.env.addCallable(prepareReports)

# ---- experiment methods

def resolveStaticDataFiles(env):
    r"""
Action that resolves file paths for all static data files, according to specification.
Specification is taken from 'static_data_files' dictionary that comes from default
configuration file. The names may contain '*' and are interpreted according to
:mod:`glob` module rules. Also opens the files and stores their file handles in
the same dictionary (under the keys 'path' and 'fh'). See 'kdvs/config/default_cfg.py'
for details.

See Also
--------
kdvs.core.config.getDefaultCfgFilePath
kdvs.core.config.getDefaultDataRootPath
    """
    env.logger.info('Started resolving static data files')
    data_path = env.var('data_path')
    static_data_files = env.var('static_data_files')
    for sfID, sfdata in static_data_files.iteritems():
        spec = sfdata['spec']
        # parse specification and resolve physical path
        # specification follows rules for 'glob' file name matching
        dirs = spec[:-1]
        filepattern = spec[-1]
        frootdir = os.path.join(data_path, *dirs)
        fpatt = os.path.join(frootdir, filepattern)
        foundfiles = [(p, os.path.getmtime(p)) for p in glob.glob(fpatt)]
        foundfiles.sort(key=operator.itemgetter(1))
        # get newest file as found
        foundfile = foundfiles[0][0]
        sfdata['path'] = foundfile
        # open file and store fh
        sfdata['fh'] = fileProvider(sfdata['path'])
        env.logger.info('File %s resolved as %s' % (quote(sfID), quote(foundfile)))
    env.logger.info('Finished resolving static data files')

def loadStaticData(env):
    r"""
Action that loads all static data files, either into database governed by the instance
of :class:`~kdvs.core.db.DBManager`, or through associated manager, if present.
It interprets 'static_data_files' dictionary that comes from default configuration
file. It uses two exclusive elements. If 'loadToDb' is True, the file is loaded
into database and wrapped in :class:`~kdvs.fw.DSV.DSV` instance. If 'manager' is
not None, it instantiates the :class:`~kdvs.fw.PK.PKCManager` instance that
governs the content of the file; also, if debug output was requested, it instructs
the manager to :meth:`dump` all the information. See 'kdvs/config/default_cfg.py'
for details.

The 'experiment' application recognizes two static data files. See 'kdvs/data/README'
for details.

Raises
------
Warn
    if more than one manager was specified for static data file
    """
    env.logger.info('Started loading static data files')
    dbm = env.var('dbm')
    data_db_id = env.var('data_db_id')
    pk_manager_dump_suffix = env.var('pk_manager_dump_suffix')
    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    static_data_files = env.var('static_data_files')
    for stfiledata in static_data_files.values():
        if stfiledata['loadToDB']:
            stfile_path = stfiledata['path']
            stfile_table = stfiledata['DBID']
            stfile_delim = stfiledata['metadata']['delimiter']
            stfile_comment = stfiledata['metadata']['comment']
            # for DSV we overwrite normal fh preservation mechanism
            stfile_fh = DSV.getHandle(stfile_path, 'rb')
            stfiledata['fh'] = stfile_fh
            stfile_dsv = DSV(dbm, data_db_id, stfile_fh, dtname=stfile_table, delimiter=stfile_delim, comment=stfile_comment)
            stfile_indexes = resolveIndexes(stfile_dsv, stfiledata['indexes'])
            stfile_dsv.create(indexed_columns=stfile_indexes)
            stfile_dsv.loadAll()
            stfile_dsv.close()
            env.addVar('%s_table' % stfiledata['DBID'], stfile_table)
            env.addVar('%s_dsv' % stfiledata['DBID'], stfile_dsv)
            env.logger.info('Loaded %s into %s as %s' % (stfile_path, data_db_id, stfile_table))
        elif stfiledata['manager'] is not None:
            if len(stfiledata['manager']) == 1:
                managerClassName, managerParams = next(iter(stfiledata['manager'].items()))
                managerClass = importComponent(managerClassName)
                manager = managerClass()
                manager.configure(**managerParams['configure'])
                managerID = 'pkc_manager'
                env.logger.info('Configured manager %s of class %s' % (managerID, managerClassName))
                manager.load(stfiledata['fh'], **managerParams['load'])
                env.logger.info('Loaded %s' % stfiledata['path'])
                env.addVar(managerID, manager)
                if use_debug_output:
                    dump = manager.dump()
                    dump_key = '%s_%s_%s' % (managerID, stfiledata['DBID'], pk_manager_dump_suffix)
                    dump_path = os.path.join(debug_output_path, dump_key)
                    with open(dump_path, 'wb') as f:
                        pprintObj(dump, f)
                    env.logger.info('Manager %s content dumped as %s' % (managerID, dump_key))
            else:
                raise Warn('More than 1 manager specified for static data file %s!' % (stfiledata['path']))
    env.logger.info('Finished loading static data files')


def postprocessStaticData(env):
    r"""
Action that performs postprocessing of static data. Currently, it performs
corrections of withdrawn symbols, and generates helper tables with HGNC synonyms
and previous symbols; helper tables are wrapped in :class:`~kdvs.fw.DBTable.DBTable`
instances.

See Also
--------
kdvs.fw.impl.annotation.HGNC.correctHGNCApprovedSymbols
kdvs.fw.impl.annotation.HGNC.generateHGNCPreviousSymbols
kdvs.fw.impl.annotation.HGNC.generateHGNCSynonyms
    """
    env.logger.info('Started postprocessing static data')

    map_db_id = env.var('map_db_id')
    static_data_files = env.var('static_data_files')
    hgnc_dsv_var = '%s_dsv' % static_data_files['hgnc_file']['DBID']
    hgnc_dsv = env.var(hgnc_dsv_var)
    # ---- correct symbols in HGNC for unified querying
    correctHGNCApprovedSymbols(hgnc_dsv)
    env.logger.info('HGNC symbols corrected')
    # ---- create inverted table for HGNC previous symbols
    previous_dt = generateHGNCPreviousSymbols(hgnc_dsv, map_db_id)
    env.addVar('previous_dt', previous_dt)
    env.logger.info('Generated index of HGNC Previous Symbols')
    # ---- create inverted table for HGNC proper synonyms
    synonyms_dt = generateHGNCSynonyms(hgnc_dsv, map_db_id)
    env.addVar('synonyms_dt', synonyms_dt)
    env.logger.info('Generated index of HGNC Synonyms')

    env.logger.info('Finished postprocessing static data')


def loadUserData(env):
    r"""
Action that resolves and loads user data files. The following profile sections are
interpreted:

    * 'annotation_file'
    * 'gedm_file'
    * 'labels_file'

All these are DSV files; after loading into database, they are wrapped in
:class:`~kdvs.fw.DSV.DSV` instances.

See 'kdvs/example_experiment/example_experiment_cfg.py' for details.
    """
    env.logger.info('Started loading user data')
    dbm = env.var('dbm')
    data_db_id = env.var('data_db_id')
    profile = env.var('profile')
    # ---- load annotations file
    anno_data = profile['annotation_file']
    anno_file = os.path.abspath(anno_data['path'])
    anno_table = getFileNameComponent(anno_file)
    anno_delim = anno_data['metadata']['delimiter']
    anno_comment = anno_data['metadata']['comment']
    anno_fh = DSV.getHandle(anno_file, 'rb')
    anno_dsv = DSV(dbm, data_db_id, anno_fh, dtname=anno_table, delimiter=anno_delim, comment=anno_comment)
    anno_indexes = resolveIndexes(anno_dsv, anno_data['indexes'])
    anno_dsv.create(indexed_columns=anno_indexes)
    anno_dsv.loadAll()
    anno_dsv.close()
    env.addVar('anno_table', anno_table)
    env.addVar('anno_dsv', anno_dsv)
    env.logger.info('Loaded %s into %s as %s' % (anno_file, data_db_id, anno_table))
    # ---- load GEDM
    gedm_data = profile['gedm_file']
    gedm_file = os.path.abspath(gedm_data['path'])
    gedm_table = getFileNameComponent(gedm_file)
    gedm_delim = gedm_data['metadata']['delimiter']
    gedm_comment = gedm_data['metadata']['comment']
    gedm_fh = DSV.getHandle(gedm_file, 'rb')
    gedm_dsv = DSV(dbm, data_db_id, gedm_fh, dtname=gedm_table, delimiter=gedm_delim, comment=gedm_comment)
    gedm_indexes = resolveIndexes(gedm_dsv, gedm_data['indexes'])
    gedm_dsv.create(indexed_columns=gedm_indexes)
    gedm_dsv.loadAll()
    gedm_dsv.close()
    env.addVar('gedm_table', gedm_table)
    env.addVar('gedm_dsv', gedm_dsv)
    env.logger.info('Loaded %s into %s as %s' % (gedm_file, data_db_id, gedm_table))
    # ---- load labels
    labels_data = profile['labels_file']
    labels_file = labels_data['path']
    if labels_file is not None:
        labels_file = os.path.abspath(labels_file)
        labels_table = getFileNameComponent(labels_file)
        labels_delim = labels_data['metadata']['delimiter']
        labels_comment = labels_data['metadata']['comment']
        labels_fh = DSV.getHandle(labels_file, 'rb')
        labels_dsv = DSV(dbm, data_db_id, labels_fh, dtname=labels_table, delimiter=labels_delim, comment=labels_comment)
        labels_indexes = resolveIndexes(labels_dsv, labels_data['indexes'])
        labels_dsv.create(indexed_columns=labels_indexes)
        labels_dsv.loadAll()
        labels_dsv.close()
        env.addVar('labels_table', labels_table)
        env.addVar('labels_dsv', labels_dsv)
        env.logger.info('Loaded %s into %s as %s' % (labels_file, data_db_id, labels_table))
    env.logger.info('Finished loading user data')


def resolveProfileComponents(env):
    r"""
Action that goes through application profile and resolves all dynamically created
components, that is, reads the individual specifications, creates instances, and
performs individual configurations. Currently, the following groups of components
are processed, and concrete instances are created:

    * categorizers (:class:`~kdvs.fw.Categorizer.Categorizer`)
    * orderers (:class:`~kdvs.fw.Categorizer.Orderer`)
    * statistical techniques (:class:`~kdvs.fw.Stat.Technique`)
    * outer selectors (:class:`~kdvs.fw.impl.stat.PKCSelector.OuterSelector`)
    * inner selectors (:class:`~kdvs.fw.impl.stat.PKCSelector.InnerSelector`)
    * reporters (:class:`~kdvs.fw.Report.Reporter`)
    * EnvOps (:class:`~kdvs.fw.EnvOp.EnvOp`)

Also, for statistical techniques, the corresponding degrees of freedom (DOFs) are
expanded.
    """
    env.logger.info('Started resolving profile components')
    profile = env.var('profile')
    # ---- resolve categorizers
    categorizers = _resolveProfileInstanceGroup(profile['subset_categorizers'])
    # add reversed lookup by internal IDs
    catIDmap = dict()
    for catID, ct in categorizers.iteritems():
        catIDmap[ct.id] = catID
    env.addVar('pc_categorizers', categorizers)
    env.addVar('pc_catidmap', catIDmap)
    env.logger.info('Resolved subset categorizers (%d found)' % (len(categorizers.keys())))
    # ---- resolve subset orderers
    sords = _resolveProfileInstanceGroup(profile['subset_orderers'])
    env.addVar('pc_sords', sords)
    env.logger.info('Resolved subset orderers (%d found)' % (len(sords.keys())))
    # ---- resolve statistical techniques
    # statistical technique is configured by parameters
    stechs = _resolveProfileInstanceGroup(profile['statistical_techniques'])
    # resolve null dofs
    for stechInst in stechs.values():
        dofs = stechInst.parameters['global_degrees_of_freedom']
        if dofs is None:
            dofs = (env.var('null_dof'),)
            stechInst.parameters['global_degrees_of_freedom'] = dofs
    env.addVar('pc_stechs', stechs)
    env.logger.info('Resolved statistical techniques (%d found)' % (len(stechs.keys())))
    # ---- resolve outer level selectors
    # outer level selector is configured by parameters
    osels = _resolveProfileInstanceGroup(profile['subset_outer_selectors'])
    env.addVar('pc_osels', osels)
    env.logger.info('Resolved subset outer selectors (%d found)' % (len(osels.keys())))
    # ---- resolve inner level selectors
    # inner level selector is configured by parameters
    isels = _resolveProfileInstanceGroup(profile['subset_inner_selectors'])
    env.addVar('pc_isels', isels)
    env.logger.info('Resolved subset inner selectors (%d found)' % (len(isels.keys())))
    # ---- resolve reporters
    # reporter is configured by parameters
    reporters = _resolveProfileInstanceGroup(profile['reporters'])
    env.addVar('pc_reporters', reporters)
    env.logger.info('Resolved reporters (%d found)' % (len(reporters.keys())))
    # ---- resolve envops
    # envop is configured by parameters
    envops = _resolveProfileInstanceGroup(profile['envops'])
    env.addVar('pc_envops', envops)
    env.logger.info('Resolved EnvOps (%d found)' % (len(envops.keys())))
    #
    env.logger.info('Finished resolving profile components')


def buildGeneIDMap(env):
    r"""
Action that constructs the concrete instance of :class:`~kdvs.fw.Map.GeneIDMap`
and builds appropriate mapping. The instance type is specified in user
configuration file as 'geneidmap_type' variable. Also, if debug output was
requested, dump the mapping. See
'kdvs/example_experiment/example_experiment_cfg.py' for details.
    """
    env.logger.info('Started building GeneID Map')
    map_db_id = env.var('map_db_id')
    static_data_files = env.var('static_data_files')
    hgnc_dsv_var = '%s_dsv' % static_data_files['hgnc_file']['DBID']
    hgnc_dsv = env.var(hgnc_dsv_var)
    anno_dsv = env.var('anno_dsv')
    geneidmap_type = env.var('geneidmap_type')
    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    # ---- construct GeneID map
    env.logger.info('Started building GeneID map of type %s' % geneidmap_type)
    geneidmap_class = importComponent(geneidmap_type)
    geneidmap = geneidmap_class()
    geneidmap.build(anno_dsv, hgnc_dsv, map_db_id)
    env.addVar('geneidmap', geneidmap)
    nentries_geneidmap = len(geneidmap.gene2emid.getFwdMap().keys())
    env.logger.info('GeneID map built (%d entries found)' % (nentries_geneidmap))
    # ---- serialize GeneID map
    if use_debug_output:
        geneidmap_key = env.var('geneidmap_key')
        with open(os.path.join(debug_output_path, geneidmap_key), 'wb') as f:
            serializeObj(geneidmap.gene2emid, f)
        env.logger.info('GeneID map serialized to %s' % geneidmap_key)
    env.logger.info('Finished building GeneID Map')


def buildPKCIDMap(env):
    r"""
Action that constructs the concrete instance of :class:`~kdvs.fw.Map.PKCIDMap`
and builds appropriate mapping. The instance type is specified in user
configuration file as 'pkcidmap_type' variable. Also, if debug output was
requested, dumps the mapping. In addition, since in 'experiment' application
Gene Ontology is used as prior knowledge source, builds specialized submapping
for selected GO domain. The GO domain is specified in :data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE`
as 'go_domain' element. See 'kdvs/example_experiment/example_experiment_cfg.py' for details.

See Also
--------
kdvs.fw.impl.map.PKCID.GPL
    """
    env.logger.info('Started building PKCID Map')
    map_db_id = env.var('map_db_id')
    profile = env.var('profile')
    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    # ---- construct PKCID map
    pkcidmap_type = env.var('pkcidmap_type')
    pkcidmap_class = importComponent(pkcidmap_type)
    pkcidmap = pkcidmap_class()
    env.logger.info('Started building PKCID map of type %s' % pkcidmap_type)
    anno_dsv = env.var('anno_dsv')
    pkcidmap.build(anno_dsv, map_db_id)
    env.addVar('pkcidmap', pkcidmap)
    nentries_pkcidmap = len(pkcidmap.pkc2emid.getFwdMap().keys())
    env.logger.info('PKCID map built (%d entries found)' % (nentries_pkcidmap))
    # ---- serialize PKCID map
    if use_debug_output:
        pkcidmap_key = env.var('pkcidmap_key')
        with open(os.path.join(debug_output_path, pkcidmap_key), 'wb') as f:
            serializeObj(pkcidmap.pkc2emid, f)
        env.logger.info('PKCID map serialized to %s' % pkcidmap_key)
    # ---- resolving map for GO domain
    go_domain = profile['go_domain']
    go_domain_map = pkcidmap.getMapForDomain(go_domain)
    env.addVar('go_domain_map', go_domain_map)
    nentries_go_domain_map = len(go_domain_map.getFwdMap().keys())
    env.logger.info('Obtained detailed PKCID map for GO domain %s (%d entries found)' % (go_domain, nentries_go_domain_map))
    # ---- serialize PKCID map for GO domain
    if use_debug_output:
        go_domain_map_key = '%s_GO_%s' % (pkcidmap_key, go_domain)
        with open(os.path.join(debug_output_path, go_domain_map_key), 'wb') as f:
            serializeObj(go_domain_map, f)
        env.logger.info('Detailed PKCID map for GO domain %s serialized to %s' % (go_domain, go_domain_map_key))
    env.logger.info('Finished building PKCID Map')

def obtainLabels(env):
    r"""
Action that obtains information about samples and labels (if present) and creates
:class:`~kdvs.fw.Stat.Labels` instance. It reads samples from primary dataset,
reads labels file, and re--orders labels according to samples from primary dataset.
Primary dataset has been specified in :data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE`
as 'gedm_file' element, loaded earlier into database, and wrapped in :class:`~kdvs.fw.DSV.DSV`
instance.
    """
    env.logger.info('Started obtaining labels')
    # ---- determine samples
    gedm_dsv = env.var('gedm_dsv')
    gedm_samples = gedm_dsv.header[1:]
    env.addVar('gedm_samples', gedm_samples)
    env.logger.info('%d samples obtained from data' % len(gedm_samples))
    unused_sample_label = env.var('unused_sample_label')
    env.logger.info('Unused sample label: %d' % unused_sample_label)
    try:
        labels_dsv = env.var('labels_dsv')
        labels_inst = Labels(labels_dsv, unused_sample_label)
        labels = labels_inst.getLabels(samples_order=gedm_samples, as_array=False)
        labels_num = labels_inst.getLabels(samples_order=gedm_samples, as_array=True)
        samples = labels_inst.getSamples(samples_order=gedm_samples)
        env.addVar('labels_inst', labels_inst)
        env.addVar('labels', labels)
        env.addVar('labels_num', labels_num)
        env.addVar('samples', samples)
        env.logger.info('Labels read (%d used)' % (len(labels_inst.labels)))
    except ValueError:
        pass
    env.logger.info('Finished obtaining labels')

def buildPKDrivenDataSubsets(env):
    r"""
Action that builds all prior--knowledge--driven data subsets. The 'build' refers
to querying of samples and variables from primary dataset. At this stage,
the mapping 'subsets'

    * {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}

is constructed, and the :class:`numpy.ndarray` component of :class:`~kdvs.fw.DataSet.DataSet`
is serialized for each data subset. Currently, the instances of :class:`~kdvs.fw.DataSet.DataSet`
are not preserved to conserve memory. Also, the iterable of tuples (pkcID, size),
sorted in descending order wrt subset size (i.e. starting from largest), is
constructed here as 'pkc2ss'.
    """
    env.logger.info('Started building PKC driven data subsets')
    gedm_dsv = env.var('gedm_dsv')
    pkcidmap = env.var('pkcidmap')
    # ---- create instance
    pkdm = PKDrivenDBDataManager(gedm_dsv, pkcidmap)
    env.addVar('pkdm', pkdm)
    env.logger.info('Created %s instance' % (pkdm.__class__.__name__))
    # ---- resolve samples
    try:
        samples = env.var('samples')
    except ValueError:
        samples = '*'
    # ---- generate subsets for specific PKCID map
    go_domain_map = env.var('go_domain_map').getMap()
    sslen = len(go_domain_map.keys())
    env.logger.info('Started generating subsets (%d)' % sslen)
    # create subset location
    rootsm = env.var('rootsm')
    rloc = env.var('root_output_location')
    subsets_location_part = env.var('subsets_location')
    ssloc = rootsm.sublocation_separator.join([rloc, subsets_location_part])
    rootsm.createLocation(ssloc)
    env.addVar('subsets_location_id', ssloc)
    sslocpath = rootsm.getLocation(ssloc)
    # proceed with generating
    subset_dict = dict()
    pkc2ss = list()
    for i, pkcID in enumerate(go_domain_map.keys()):
        pkc_ssinfo, pkc_ds = pkdm.getSubset(pkcID, forSamples=samples, get_ssinfo=True, get_dataset=True)
        pkc_ds_content = pkc_ds.array
        ds_vars = pkc_ssinfo['rows']
        ds_samples = pkc_ssinfo['cols']
        ssname = GO_id2num(pkcID, numint=False)
        subset_dict[pkcID] = dict()
        subset_dict[pkcID]['mat'] = ssname
        subset_dict[pkcID]['shape'] = pkc_ds_content.shape
        subset_dict[pkcID]['vars'] = ds_vars
        subset_dict[pkcID]['samples'] = ds_samples
        # resolve subset key and serialize subset
        ss_key = ssname
        ss_path = os.path.join(sslocpath, ss_key)
        with open(ss_path, 'wb') as f:
            serializeObj(pkc_ds_content, f)
        env.logger.info('Serialized subset (%d of %d) to %s' % (i + 1, sslen, ss_key))
        # add size entry
        pkc2ss.append((pkcID, len(ds_vars)))
    # finalize pkc2ss by sorting according to size
    pkc2ss = sorted(pkc2ss, key=operator.itemgetter(1), reverse=True)
    # preserve subsets
    env.addVar('subsets', subset_dict)
    # preserve pkc2ss
    env.addVar('pkc2ss', pkc2ss)
    # ---- serialize meta dictionary of subsets
    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    if use_debug_output:
        subsets_key = env.var('subsets_key')
        subsets_txt_key = '%s%s' % (subsets_key, env.var('txt_suffix'))
        subsets_path = os.path.join(debug_output_path, subsets_key)
        with open(subsets_path, 'wb') as f:
            serializeObj(subset_dict, f)
        subsets_txt_path = os.path.join(debug_output_path, subsets_txt_key)
        with open(subsets_txt_path, 'wb') as f:
            pprintObj(subset_dict, f)
        env.logger.info('Subsets dictionary serialized to %s' % subsets_key)
        env.logger.info('Finished building PKC driven data subsets')

def buildSubsetHierarchy(env):
    r"""
Action that constructs the instance of
:class:`~kdvs.fw.impl.data.PKDrivenData.PKDrivenDBSubsetHierarchy`. Also,
constructs the `operation map`, that is, determines the sequence of all
operations to be performed on each category, and within, on each data subset,
such as orderers, env--ops, statistical techniques, reporters etc. The `operation
map` has two components: executable and textual. The executable component stores
all references to actual callables to be performed; the textual component stores
all textual IDs of the configurable instances that provide the callables themselves.
The textual IDs are taken from user configuration file; the instances were created
in :meth:`resolveProfileComponents` action. In addition, if debug output was
requested, serializes constructed data structures.
    """
    env.logger.info('Started building subset hierarchy')
    profile = env.var('profile')
#    rlocpath = env.var('root_output_path')
    subsets = env.var('subsets')
    pkdm = env.var('pkdm')
    categorizers = env.var('pc_categorizers')
    catIDmap = env.var('pc_catidmap')
    orderers = env.var('pc_sords')
    stechs = env.var('pc_stechs')
    osels = env.var('pc_osels')
    isels = env.var('pc_isels')
    reporters = env.var('pc_reporters')
    envops = env.var('pc_envops')
    # ---- resolve samples
    try:
        samples = env.var('samples')
    except ValueError:
        samples = '*'
    # ---- get related profile components
    # obtain categorizers chain
    cchain = profile['subset_hierarchy_categorizers_chain']
    env.logger.info('Categorizers chain utilized: %s' % (cchain,))
    # collect all symbols for subset hierarchy
    initial_symbols = subsets.keys()
    env.logger.info('Initial symbols (PKC IDs) resolved (%d found)' % len(initial_symbols))
    # ---- build subset hierarchy with recognized categorizers
    pkdrivenss = PKDrivenDBSubsetHierarchy(pkdm_inst=pkdm, samples_iter=samples)
    pkdrivenss.build(cchain, categorizers, initial_symbols)
    env.logger.info('Subset hierarchy built: %s' % pkdrivenss.hierarchy)
    env.logger.info('Root symbol tree categories: %s' % (pkdrivenss.symboltree.keys()))
    for cat, stcnt in pkdrivenss.symboltree.iteritems():
        for symbolcat, symbols in stcnt.iteritems():
            env.logger.info('Symbol tree category %s of %s with %d symbols' % (symbolcat, cat, len(symbols)))
    env.addVar('pkdrivenss', pkdrivenss)
    # obtain components map
    cmap = profile['subset_hierarchy_components_map']
    # prepare operations map for each member of all symbols groups
    # create map with instances and textual image with IDs as referred to in configuration file
    operations_map = dict()
    operations_map_img = dict()
    # walk hierarchy with this embedded recursive function
    def _walk_hierarchy(parent_category):
        if parent_category in pkdrivenss.symboltree:
            # if requested category is present we proceed
            st_elem = pkdrivenss.symboltree[parent_category]
            # obtain descending categories and associated symbols lists
            for category, syms in st_elem.iteritems():
                # identify categorizer and category
                intID, intCat = Categorizer.deuniquifyCategory(category)
                if intID is not None and intCat is not None:
                    catID = catIDmap[intID]
                    # get components
                    components = cmap[catID][intCat]
                    # single orderer
                    ordererID = components['orderer']
                    try:
                        orderer_inst = orderers[ordererID]
                    except KeyError:
                        orderer_inst = None
                    # single technique
                    techID = components['technique']
                    try:
                        tech_inst = stechs[techID]
                    except KeyError:
                        tech_inst = None
                    # single outer selector
                    oselID = components['outer_selector']
                    try:
                        osel_inst = osels[oselID]
                    except KeyError:
                        osel_inst = None
                    # single inner selector
                    iselID = components['inner_selector']
                    try:
                        isel_inst = isels[iselID]
                    except KeyError:
                        isel_inst = None
                    # category can have many reporters that are executed in order specified here
                    reporterIDs = components['reporter']
                    try:
                        reporter_insts = [reporters[rID] for rID in reporterIDs]
                    except:
                        reporter_insts = None
                    # category can have many pre-EnvOps that are executed in order specified here
                    preenvopIDs = components['preenvop']
                    try:
                        preenvop_insts = [envops[eID] for eID in preenvopIDs]
                    except:
                        preenvop_insts = None
                    # category can have many post-EnvOps that are executed in order specified here
                    postenvopIDs = components['postenvop']
                    try:
                        postenvop_insts = [envops[eID] for eID in postenvopIDs]
                    except:
                        postenvop_insts = None
                    # miscellaneous data that follows
                    miscData = components['misc']
                # fill operations map
                operations_map[category] = dict()
                operations_map_img[category] = dict()
                # fill real map record with instances and image map record with IDs
                # global operations (on all symbols)
                if len(miscData) > 0:
                    operations_map[category]['__misc_data__'] = miscData
                    operations_map_img[category]['__misc_data__'] = miscData
                operations_map[category]['__orderer__'] = orderer_inst
                operations_map_img[category]['__orderer__'] = ordererID
                operations_map[category]['__outer_selector__'] = osel_inst
                operations_map_img[category]['__outer_selector__'] = oselID
                operations_map[category]['__inner_selector__'] = isel_inst
                operations_map_img[category]['__inner_selector__'] = iselID
                operations_map[category]['__reporters__'] = reporter_insts
                operations_map_img[category]['__reporters__'] = reporterIDs
                operations_map[category]['__preenvops__'] = preenvop_insts
                operations_map_img[category]['__preenvops__'] = preenvopIDs
                operations_map[category]['__postenvops__'] = postenvop_insts
                operations_map_img[category]['__postenvops__'] = postenvopIDs
                # local operations (for each symbol)
                for sym in syms:
                    operations_map[category][sym] = dict()
                    operations_map_img[category][sym] = dict()
                    operations_map[category][sym]['__technique__'] = tech_inst
                    operations_map_img[category][sym]['__technique__'] = techID
#                    operations_map[category][sym]['__reporter__'] = reporter_inst
#                    operations_map_img[category][sym]['__reporter__'] = reporterID
                # repeat the same for each descending category
                _walk_hierarchy(category)
        else:
            # (done for visibility)
            # otherwise we simply return and associated execution branch ends
            pass
    # ---- perform walking the hierarchy starting from root
    env.logger.info('Started building operations map')
    _walk_hierarchy(None)
    env.logger.info('Finished building operations map')
    # preserve operation maps
    env.addVar('operations_map', operations_map)
    env.addVar('operations_map_img', operations_map_img)
    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    if use_debug_output:
        # ---- serialize subset hierarchy
        pkdrivenss_imgobj = {'hierarchy' : dict(pkdrivenss.hierarchy), 'symboltree' : dict(pkdrivenss.symboltree)}
        subset_hierarchy_key = env.var('subset_hierarchy_key')
        subset_hierarchy_txt_key = '%s%s' % (subset_hierarchy_key, env.var('txt_suffix'))
        subset_hierarchy_path = os.path.join(debug_output_path, subset_hierarchy_key)
        with open(subset_hierarchy_path, 'wb') as f:
            serializeObj(pkdrivenss_imgobj, f)
        subset_hierarchy_txt_path = os.path.join(debug_output_path, subset_hierarchy_txt_key)
        with open(subset_hierarchy_txt_path, 'wb') as f:
            pprintObj(pkdrivenss_imgobj, f)
        env.logger.info('Subset hierarchy serialized to %s' % subset_hierarchy_key)
        # ---- serialize operations map
        operations_map_imgobj = operations_map_img
        operations_map_key = env.var('operations_map_key')
        operations_map_txt_key = '%s%s' % (operations_map_key, env.var('txt_suffix'))
        operations_map_path = os.path.join(debug_output_path, operations_map_key)
        with open(operations_map_path, 'wb') as f:
            serializeObj(operations_map_imgobj, f)
        operations_map_txt_path = os.path.join(debug_output_path, operations_map_txt_key)
        with open(operations_map_txt_path, 'wb') as f:
            pprintObj(operations_map_imgobj, f)
        env.logger.info('Operations map serialized to %s' % operations_map_key)
        env.logger.info('Finished building subset hierarchy')

def submitSubsetOperations(env):
    r"""
Action that does the following:

    * instantiates requested concrete :class:`~kdvs.fw.Job.JobContainer` and :class:`~kdvs.fw.Job.JobGroupManager` instances, as specified in configuration file(s)
    * for each category:

        * executes associated pre--Env-Op(s)
        * determines `test mode` directives, if any; in test mode, only fraction of computational jobs are executed;
            looks for two directives in dictionary 'subset_hierarchy_components_map'->category_name->'misc'
            in :data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE`:

                * 'test_mode_elems' (integer) -- number of test data subsets to consider
                * 'test_mode_elems_order' (string) ('first'/'last') -- consider 'first' or 'last' number of data subsets

            only computational jobs generated for specified test data subsets will be executed

        * determine `submission order`, i.e. the final list of data subsets to process further
        * executes associated orderer(s) on the generated submission order
        * for each data subset:

            * generates all job(s) and adds them to job container

    * starts job container

    * serializes the following technical mapping: { internal_job_ID : custom_job_ID },
        where internal job ID is assigned by job container and custom job ID comes
        from statistical technique

    * if debug output was requested, serializes the submission order
    """
    env.logger.info('Started submitting subset operations')
    profile = env.var('profile')
    categorizers = env.var('pc_categorizers')
    operations_map = env.var('operations_map')
    operations_map_img = env.var('operations_map_img')
    subsets = env.var('subsets')
    labels_num = env.var('labels_num')
    samples = env.var('samples')
    # ---- instantiate job container
    job_container_type = env.var('job_container_type')
    job_container_cfg = env.var('job_container_cfg')
    jobContainer = importComponent(job_container_type)(**job_container_cfg)
    # ---- instantiate job group manager
    job_group_manager_type = env.var('job_group_manager_type')
    job_group_manager_cfg = env.var('job_group_manager_cfg')
    jobGroupManager = importComponent(job_group_manager_type)(**job_group_manager_cfg)
    # get location of subsets
    rootsm = env.var('rootsm')
    rloc = env.var('root_output_location')
    ss_loc_id = env.var('subsets_location_id')
    sslocpath = rootsm.getLocation(ss_loc_id)
    # prepare location for results
    subsets_results_location_part = env.var('subsets_results_location')
    ssresloc = rootsm.sublocation_separator.join([rloc, subsets_results_location_part])
    rootsm.createLocation(ssresloc)
    env.addVar('subsets_results_location_id', ssresloc)
    # prepare location for jobs
    jobs_location_part = env.var('jobs_location')
    jobsloc = rootsm.sublocation_separator.join([rloc, jobs_location_part])
    rootsm.createLocation(jobsloc)
    env.addVar('jobs_location_id', jobsloc)
    jobs_path = rootsm.getLocation(jobsloc)
    env.addVar('jobs_path', jobs_path)
    # get text suffix
    txt_suffix = env.var('txt_suffix')
    # cached job dictionaries
    # jobs grouped by categorizers
    ss_jobs = dict()
    # linear cache of job objects (volatile, not saved)
    all_jobs = dict()
    # job ID map
    # (map between automatically assigned jobIDs and customIDs created by the user)
    jobIDmap = dict()
    # default additional job data
    additionalJobData = { 'samples' : samples }
#    # get pkc2ss mapping
#    misc = env.var('misc')
#    pkc2ss = misc['data_pkc2ss']
    pkc2ss = env.var('pkc2ss')
    # test jobs may be requested
    test_mode_elems = None
    test_mode_elems_order = None
    # submission order for all categories
    submission_order = dict()
    ss_submitted = dict()
    # one must walk categories in relative order to categorizers chain
    # the order of categories within categories is irrelevant
    cchain = profile['subset_hierarchy_categorizers_chain']
    # ---- walk categorizers
    for categorizerID in cchain:
        categorizer = categorizers[categorizerID]
        categories = [categorizer.uniquifyCategory(c) for c in categorizer.categories()]
        submission_order[categorizerID] = dict()
        ss_submitted[categorizerID] = dict()

        ss_jobs[categorizerID] = dict()

        # ---- walk associated categories
        for category in categories:
            # ---- process operations map
            cdata = operations_map[category]
            env.logger.info('Started processing operations for category %s' % category)
            # ---- execute all pre-EnvOps here
            preenvops = cdata['__preenvops__']
            if preenvops is not None:
                env.logger.info('Found %d pre-EnvOps for category %s : %s' % (len(preenvops), category, operations_map_img[category]['__preenvops__']))
                for preenvopID, preenvop in zip(operations_map_img[category]['__preenvops__'], preenvops):
                    preenvop.perform(env)
                    env.logger.info('Pre-EnvOp %s executed' % (preenvopID))
            else:
                env.logger.info('No pre-EnvOps present for category %s' % (category))
            # get misc data if any
            try:
                misc_data = cdata['__misc_data__']
                env.logger.info('Found misc data for category %s' % (category))
                try:
                    test_mode_elems = misc_data['test_mode_elems']
                    test_mode_elems_order = misc_data['test_mode_elems_order']
                    env.logger.info('Test mode specification (#: %d, order: %s) present for category %s' % (test_mode_elems, test_mode_elems_order, category))
                except KeyError:
                    test_mode_elems = None
                    test_mode_elems_order = None
            except KeyError:
                test_mode_elems = None
                test_mode_elems_order = None
                env.logger.info('No misc data present for category %s' % (category))
            # get orderer instance
            orderer = cdata['__orderer__']
            if orderer is not None:
                env.logger.info('Found orderer for category %s : %s' % (category, operations_map_img[category]['__orderer__']))
            else:
                env.logger.info('No orderer present for category %s' % (category))
            # ---- get all subset symbols for this category
            symbols = set([s for s in cdata.keys() if not s.startswith('__') and not s.endswith('__')])
#            symbols = set(cdata.keys()) - set(['__misc_data__', '__orderer__', '__outer_selector__'])
            env.logger.info('Symbols found for category %s : %d' % (category, len(symbols)))
            # ---- apply orderer
            env.logger.info('Started determining subset ordering')
            if orderer is not None:
                # get all PKC IDs already sorted starting from the largest subset
                local_pkc2ss = [pss[0] for pss in pkc2ss if pss[0] in symbols]
                env.logger.info('Built local pkc2ss map (%d elements found)' % (len(local_pkc2ss)))
                orderer.build(local_pkc2ss)
                ss_submission_order = orderer.order()
                env.logger.info('Submission order determined from orderer')
            else:
                ss_submission_order = symbols
                env.logger.info('Submission order non-specific')
            # ---- process test requests
            if test_mode_elems is not None and test_mode_elems_order is not None:
                if test_mode_elems_order == 'first':
                    ss_submission_order = ss_submission_order[:test_mode_elems]
                elif test_mode_elems_order == 'last':
                    ss_submission_order = ss_submission_order[-test_mode_elems:]
                test_submission_listing_thr = env.var('test_submission_listing_thr')
                if len(ss_submission_order) <= test_submission_listing_thr:
                    subm_listing = ', '.join(ss_submission_order)
                else:
                    subm_listing = '>%d,skipped' % test_submission_listing_thr
                env.logger.info('Test mode submission requested for category %s (%s subsets): %s' % (category, len(ss_submission_order), subm_listing))
                env.logger.info('NOTE: only requested test jobs will be submitted')
            env.logger.info('Finished determining subset ordering')
            # ---- store determined submission order
            submission_order[categorizerID][category] = list(ss_submission_order)
            ss_submitted[categorizerID][category] = list()
            ss_jobs[categorizerID][category] = dict()
            total_ss_jobs = len(ss_submission_order)
            # ---- submit subset operations
            for i, pkcid in enumerate(ss_submission_order):
                # obtain operations for subset
                scdata = cdata[pkcid]
                # get technique
                technique = scdata['__technique__']
                technique_id = operations_map_img[category][pkcid]['__technique__']
#                # get reporter ID
#                reporter_id = operations_map_img[category][pkcid]['__reporter__']
                if technique is not None:
                    # ---- obtain subset instance
                    ss = subsets[pkcid]
                    ssname = ss['mat']
                    # ---- deserialize subset
                    ss_path = os.path.join(sslocpath, ssname)
                    with open(ss_path, 'rb') as f:
                        ss_num = deserializeObj(f)
                    env.logger.info('Deserialized subset %s' % ssname)
                    # cache jobs
                    ss_jobs[categorizerID][category][pkcid] = dict()
                    # resolve assignment of jobs to group
                    job_group = ssname
                    # job may be importable if run with remote job container
                    job_importable = technique.parameters['job_importable']
                    # lazy evaluation of jobs
                    for customID, job in technique.createJob(ssname, ss_num, labels_num, additionalJobData):
                        # add job to container
                        jobID = jobContainer.addJob(job, importable=job_importable)
#                        jobID = jobContainer.addJob(job)
                        # assign job to group
                        jobGroupManager.addJobIDToGroup(job_group, jobID)
                        # add to cache grouped by categorizers
                        ss_jobs[categorizerID][category][pkcid][jobID] = dict()
                        ss_jobs[categorizerID][category][pkcid][jobID]['job'] = job
                        ss_jobs[categorizerID][category][pkcid][jobID]['mat'] = ssname
                        ss_jobs[categorizerID][category][pkcid][jobID]['technique'] = technique_id
#                        ss_jobs[categorizerID][category][pkcid][jobID]['reporter'] = reporter_id
                        # add to linear cache
                        all_jobs[jobID] = dict()
                        all_jobs[jobID]['job'] = job
                        all_jobs[jobID]['mat'] = ssname
                        all_jobs[jobID]['technique'] = technique_id
#                        all_jobs[jobID]['reporter'] = reporter_id
                        # store original job information in jobs location
                        if customID is not None:
                            jobIDmap[jobID] = customID
                            env.logger.info('Custom ID provided for job %s: %s' % (jobID, customID))
                            ss_jobs[categorizerID][category][pkcid][jobID]['customID'] = customID
                            all_jobs[jobID]['customID'] = customID
                            # store these raw job data
                            job_stor = all_jobs[jobID]
                            job_stor_key = customID
                            with open(os.path.join(jobs_path, job_stor_key), 'wb') as f:
                                serializeObj(job_stor, f)
#                            job_stor_txt_key = '%s%s' % (job_stor_key, txt_suffix)
#                            with open(os.path.join(jobs_path, job_stor_txt_key), 'wb') as f:
#                                pprintObj(job_stor, f)
                        # submission finished
                        env.logger.info('Job submitted for %s (%d of %d) (in group %s): %s' % (pkcid, i + 1, total_ss_jobs, job_group, jobID))
                    ss_submitted[categorizerID][category].append(pkcid)
            env.logger.info('Finished processing operations for category %s' % category)
    # finished, preserve submission order
    env.addVar('submission_order', submission_order)
    #
    jobContainer.start()
    env.logger.info('Job container started with %d jobs' % (jobContainer.getJobCount()))
    env.addVar('jobContainer', jobContainer)
    env.addVar('ss_jobs', ss_jobs)
    env.addVar('all_jobs', all_jobs)
    env.addVar('ss_submitted', ss_submitted)
    env.addVar('jobGroupManager', jobGroupManager)
    # immediately store jobIDmap if any customIDs were provided
    jobID_map_key = env.var('jobID_map_key')
    if len(jobIDmap.keys()) > 0:
        with open(os.path.join(jobs_path, jobID_map_key), 'wb') as f:
            serializeObj(jobIDmap, f)
        jobID_map_txt_key = '%s%s' % (jobID_map_key, txt_suffix)
        jobID_map_lines = ["%s\t%s\n" % (jid, jobIDmap[jid]) for jid in sorted(jobIDmap.keys())]
        with open(os.path.join(jobs_path, jobID_map_txt_key), 'wb') as f:
            serializeTxt(jobID_map_lines, f)
#            pprintObj(jobIDmap, f)
#    env.addVar('jobIDmap', jobIDmap)

    # store submission order for debug purposes
    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    if use_debug_output:
        submission_order_key = env.var('submission_order_key')
        submission_order_txt_key = '%s%s' % (submission_order_key, txt_suffix)
        submission_order_path = os.path.join(debug_output_path, submission_order_key)
        with open(submission_order_path, 'wb') as f:
            serializeObj(submission_order, f)
        submission_order_txt_path = os.path.join(debug_output_path, submission_order_txt_key)
        with open(submission_order_txt_path, 'wb') as f:
            pprintObj(submission_order, f)
        env.logger.info('Submission order dictionary serialized to %s' % submission_order_key)

    env.logger.info('Finished submitting subset operations')

def executeSubsetOperations(env):
    r"""
Action that performs the following:

    * closes job container and executes submitted jobs; this call is blocking for most job containers;
        any exceptions from jobs are serialized for further manual inspection

    * :meth:`postClose`-ses job container and serializes its technical data obtained with :meth:`getMiscData`, if any

    * collects all raw job results and prepares them for further post--processing and generation of :class:`~kdvs.fw.Stat.Results` instances
    """
    env.logger.info('Started executing subset operations')
    # get root output location (for subsets)
    rootsm = env.var('rootsm')
#    rlocpath = env.var('root_output_path')
    # retrieve results location
    ssresloc = env.var('subsets_results_location_id')
    ssreslocpath = rootsm.getLocation(ssresloc)
    # retrieve jobs location path
    jobs_path = env.var('jobs_path')
    jobs_raw_output_suffix = env.var('jobs_raw_output_suffix')
    txt_suffix = env.var('txt_suffix')
    #
    jobContainer = env.var('jobContainer')
#    ss_jobs = env.var('ss_jobs')
    all_jobs = env.var('all_jobs')
    # possibly blocking call
    env.logger.info('About to close job container (possibly blocking call)')
    jexc = jobContainer.close()
    env.logger.info('Job container closed (%d job exceptions)' % (len(jexc)))
    if len(jexc) > 0:
        jobs_exceptions_key = env.var('jobs_exceptions_key')
        jobs_exceptions_txt_key = '%s%s' % (jobs_exceptions_key, txt_suffix)
        with open(os.path.join(ssreslocpath, jobs_exceptions_key), 'wb') as f:
            serializeObj(jexc, f)
        with open(os.path.join(ssreslocpath, jobs_exceptions_txt_key), 'wb') as f:
            pprintObj(jexc, f)
        env.logger.info('Jobs exceptions serialized to %s' % jobs_exceptions_key)

    # ---- execute postClose for current job container
    destPath = jobs_path
    env.logger.info('Started post closing job container with destination path "%s"' % destPath)
    jobContainer.postClose(destPath)
    env.logger.info('Finished post closing job container')
    # ---- store misc data from job container
    jmdata = jobContainer.getMiscData()
    jobs_misc_data_key = env.var('jobs_misc_data_key')
    jobs_misc_data_txt_key = '%s%s' % (jobs_misc_data_key, txt_suffix)
    with open(os.path.join(destPath, jobs_misc_data_key), 'wb') as f:
        serializeObj(jmdata, f)
    with open(os.path.join(destPath, jobs_misc_data_txt_key), 'wb') as f:
        pprintObj(jmdata, f)
    env.logger.info('Job container misc data serialized to %s' % jobs_misc_data_key)

    # ---- retrieve results
    # the content of all_jobs and ss_jobs will be updated simultaneously
    for jobID, jobdata in all_jobs.iteritems():
        jobResult = jobContainer.getJobResult(jobID)
        jobdata['job'].result = jobResult
        # save raw output immediately if customID was provided
        try:
            customID = jobdata['customID']
            jobs_raw_output_key = '%s_%s' % (customID, jobs_raw_output_suffix)
            with open(os.path.join(jobs_path, jobs_raw_output_key), 'wb') as f:
                serializeObj(jobResult, f)
#            jobs_raw_output_txt_key = '%s%s' % (jobs_raw_output_key, txt_suffix)
#            with open(os.path.join(jobs_path, jobs_raw_output_txt_key), 'wb') as f:
#                pprintObj(jobResult, f)
        except:
            pass
    env.logger.info('Job results collected')

    # TODO: decide if we want to store such large object!
#    use_debug_output = env.var('use_debug_output')
#    debug_output_path = env.var('debug_output_path')
#    if use_debug_output:
#        txt_suffix = env.var('txt_suffix')
#        subsets_results_key = env.var('subsets_results_key')
#        subsets_results_txt_key = '%s%s' % (subsets_results_key, txt_suffix)
#        subsets_results_path = os.path.join(debug_output_path, subsets_results_key)
#        with open(subsets_results_path, 'wb') as f:
#            serializeObj(ss_jobs, f)
#        subsets_results_txt_path = os.path.join(debug_output_path, subsets_results_txt_key)
#        with open(subsets_results_txt_path, 'wb') as f:
#            pprintObj(ss_jobs, f)
#        env.logger.info('Subsets results dictionary serialized to %s' % subsets_results_key)

    env.logger.info('Finished executing subset operations')


def postprocessSubsetOperations(env):
    r"""
Action that performs the following:

    * checks completion of all jobs, and all individual job groups if any
    * for completed jobs and job groups, generate :class:`~kdvs.fw.Stat.Results` instances
    * serializes technical mapping { technique_ID : [subset_IDs] }, available as 'technique2ssname'
    * if debug output was requested, serialize job group completion dictionary
    * create the following technical mapping available as 'technique2DOF', and serialize it if debug output was requested:
        {techniqueID : { 'DOFS_IDXS': (0, 1, ..., n), 'DOFs': (name_DOF0, name_DOF1, ..., name_DOFn)}
    * for each category:

        * executes associated post--Env-Op(s)
    """
    env.logger.info('Started postprocessing subset operations')
    rootsm = env.var('rootsm')
#    rlocpath = env.var('root_output_path')
    # get main results location
    ssrootresloc = env.var('subsets_results_location_id')
    # get miscellaneous
    subset_results_suffix = env.var('subset_results_suffix')
    txt_suffix = env.var('txt_suffix')
    # get raw jobs results
    all_jobs = env.var('all_jobs')
    stechs = env.var('pc_stechs')
    # get job group manager
    jobGroupManager = env.var('jobGroupManager')

    # prepare dictionary of completed groups
    groupsCompleted = dict()
    allJobGroups = jobGroupManager.getGroups()
    for jobGroup in allJobGroups:
        groupJobs = jobGroupManager.getGroupJobsIDs(jobGroup)
        groupsCompleted[jobGroup] = dict()
        groupsCompleted[jobGroup]['jobs'] = dict()
        for gj in groupJobs:
            groupsCompleted[jobGroup]['jobs'][gj] = False
        groupsCompleted[jobGroup]['completed'] = False

    # ---- loop through all jobs and check their status

    for jobID, jobdata in all_jobs.iteritems():
        jobGroup = jobGroupManager.findGroupByJobID(jobID)
        jobResult = jobdata['job'].result
        if jobResult != NOTPRODUCED:
            groupsCompleted[jobGroup]['jobs'][jobID] = True
    cmpl_count = 0
    for jobGroup in allJobGroups:
        cmpl_status = all(groupsCompleted[jobGroup]['jobs'].values())
        groupsCompleted[jobGroup]['completed'] = cmpl_status
        if cmpl_status:
            cmpl_count += 1
    env.logger.info('Job groups completed: %d, not completed: %d' % (cmpl_count, len(allJobGroups) - cmpl_count))

    # ---- send jobs from completed groups to postprocessing and produce final Results

    ssIndResults = dict()
    technique2ssname = collections.defaultdict(set)

    env.logger.info('Started job postprocessing')

    for jobGroup in allJobGroups:
        if groupsCompleted[jobGroup]['completed']:
            groupJobIDs = jobGroupManager.getGroupJobsIDs(jobGroup)
            # determine common technique and subset name across completed jobs
            groupTechnique = set()
            groupSSName = set()
            groupJobs = list()
            for jobID in groupJobIDs:
                jobdata = all_jobs[jobID]
                groupTechnique.add(all_jobs[jobID]['technique'])
                groupSSName.add(all_jobs[jobID]['mat'])
                groupJobs.append(all_jobs[jobID]['job'])
            # should not be thrown but to be safe
            if len(groupTechnique) > 1 or len(groupSSName) > 1:
                raise Error('Jobs of group %s not having same technique and/or ssname! (%s,%s)' % (list(groupTechnique), list(groupSSName)))
            ssname = next(iter(groupSSName))
            techID = next(iter(groupTechnique))
            # group ssnames across techniques
            technique2ssname[techID].add(ssname)
            technique = stechs[techID]
            # compile runtime data for this technique
            # runtime data consists of useful information that can be later used
            # in reporting results
            runtime_data = dict()
            runtime_data['techID'] = techID
            # ---- produce Results
            result = technique.produceResults(ssname, groupJobs, runtime_data)
            # store Results
            ssIndResults[ssname] = result
#            # ---- serialize Results
#            # create individual location for subset
#            ssresloc = rootsm.sublocation_separator.join([ssrootresloc, ssname])
#            rootsm.createLocation(ssresloc)
#            ssreslocpath = rootsm.getLocation(ssresloc)
#            # first save any plots separately
#            ssplots = result[RESULTS_PLOTS_ID_KEY]
# #            for plotname, plotcontent in ssplots.iteritems():
#            for plotname in sorted(ssplots.keys()):
#                plotcontent = ssplots[plotname]
#                plotpath = os.path.join(ssreslocpath, plotname)
#                with open(plotpath, 'wb') as f:
#                    writeObj(plotcontent, f)
#                env.logger.info('Plot %s saved' % (plotname))
#            # serialize individual output
#            result_img = dict((k, result[k]) for k in result.keys())
#            del result_img[RESULTS_PLOTS_ID_KEY]
#            ind_subset_result_key = '%s%s' % (ssname, subset_results_suffix)
#            ind_subset_result_path = os.path.join(ssreslocpath, ind_subset_result_key)
#            with open(ind_subset_result_path, 'wb') as f:
# #                serializeObj(result, f)
#                serializeObj(result_img, f)
#            ind_subset_result_txt_key = '%s%s' % (ind_subset_result_key, txt_suffix)
#            ind_subset_result_txt_path = os.path.join(ssreslocpath, ind_subset_result_txt_key)
#            with open(ind_subset_result_txt_path, 'wb') as f:
# #                pprintObj(result, f)
#                pprintObj(result_img, f)
#            env.logger.info('Results for %s serialized to %s' % (ssname, ind_subset_result_key))

    env.logger.info('Finished job postprocessing')

    # serialize very useful technique2ssname map in results root location
    ssrootreslocpath = rootsm.getLocation(ssrootresloc)
    technique2ssname = dict([(k, list(v)) for k, v in technique2ssname.iteritems()])
    technique2ssname_key = env.var('technique2ssname_key')
    technique2ssname_path = os.path.join(ssrootreslocpath, technique2ssname_key)
    with open(technique2ssname_path, 'wb') as f:
        serializeObj(technique2ssname, f)
    technique2ssname_txt_key = '%s%s' % (technique2ssname_key, txt_suffix)
    technique2ssname_txt_path = os.path.join(ssrootreslocpath, technique2ssname_txt_key)
    t2ss_lines = list()
    for t, ssl in technique2ssname.iteritems():
        t2ss_lines.append('%s\n' % t)
        for ss in ssl:
            t2ss_lines.append('\t%s\n' % ss)
    with open(technique2ssname_txt_path, 'wb') as f:
#        pprintObj(technique2ssname, f)
        serializeTxt(t2ss_lines, f)
    env.logger.info('Technique to subset names map serialized to %s' % technique2ssname_key)

    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    if use_debug_output:
        group_completion_key = env.var('group_completion_key')
        group_completion_txt_key = '%s%s' % (group_completion_key, txt_suffix)
        group_completion_path = os.path.join(debug_output_path, group_completion_key)
        with open(group_completion_path, 'wb') as f:
            serializeObj(groupsCompleted, f)
        group_completion_txt_path = os.path.join(debug_output_path, group_completion_txt_key)
        with open(group_completion_txt_path, 'wb') as f:
            pprintObj(groupsCompleted, f)
        env.logger.info('Group completion dictionary serialized to %s' % group_completion_key)

    # create technique2DOF mapping
    technique2DOF = dict()
    for techID in technique2ssname.keys():
        technique2DOF[techID] = dict()
        technique = stechs[techID]
        dofs = technique.parameters['global_degrees_of_freedom']
        dof_idxs = tuple(range(len(dofs)))
        technique2DOF[techID]['DOFs'] = dofs
        technique2DOF[techID]['DOFS_IDXS'] = dof_idxs

    if use_debug_output:
        technique2dof_key = env.var('technique2dof_key')
        technique2dof_txt_key = '%s%s' % (technique2dof_key, txt_suffix)
        technique2dof_path = os.path.join(debug_output_path, technique2dof_key)
        with open(technique2dof_path, 'wb') as f:
            serializeObj(technique2DOF, f)
        technique2dof_txt_path = os.path.join(debug_output_path, technique2dof_txt_key)
        with open(technique2dof_txt_path, 'wb') as f:
            pprintObj(technique2DOF, f)
        env.logger.info('Technique2DOF mapping serialized to %s' % technique2dof_key)

#    env.addVar('technique2ssname', technique2ssname)
    env.addVar('technique2DOF', technique2DOF)
    env.addVar('ssIndResults', ssIndResults)

    # ---- also here, immediately after postprocessing, execute remaining post-EnvOps
    profile = env.var('profile')
    categorizers = env.var('pc_categorizers')
    operations_map = env.var('operations_map')
    operations_map_img = env.var('operations_map_img')

    # one must walk categories in relative order to categorizers chain
    # the order of categories within categories is irrelevant
    cchain = profile['subset_hierarchy_categorizers_chain']
    # ---- walk categorizers
    for categorizerID in cchain:
        categorizer = categorizers[categorizerID]
        categories = [categorizer.uniquifyCategory(c) for c in categorizer.categories()]
        # ---- walk associated categories
        for category in categories:
            # ---- process operations map
            cdata = operations_map[category]
            env.logger.info('Started processing operations for category %s' % category)
            # ---- execute all post-EnvOps here
            postenvops = cdata['__postenvops__']
            if postenvops is not None:
                env.logger.info('Found %d post-EnvOps for category %s : %s' % (len(postenvops), category, operations_map_img[category]['__postenvops__']))
                for postenvopID, postenvop in zip(operations_map_img[category]['__postenvops__'], postenvops):
                    postenvop.perform(env)
                    env.logger.info('Post-EnvOp %s executed' % (postenvopID))
            else:
                env.logger.info('No post-EnvOps present for category %s' % (category))

    env.logger.info('Finished postprocessing subset operations')

def performSelections(env):
    r"""
Action that performs the following:

    * for each category:

        * having all :class:`~kdvs.fw.Stat.Results` instances, executes associated outer selector(s) and inner selector(s)

    * if debug output was requested, serialize direct output of outer and inner selector(s)
    """
    env.logger.info('Started performing selections')

    txt_suffix = env.var('txt_suffix')
#    rlocpath = env.var('root_output_path')
    profile = env.var('profile')
    categorizers = env.var('pc_categorizers')
    operations_map = env.var('operations_map')
    operations_map_img = env.var('operations_map_img')
    submission_order = env.var('submission_order')
    subsets = env.var('subsets')
    ssIndResults = env.var('ssIndResults')

    outerSelection = dict()
    innerSelection = dict()

    # one must walk categories in relative order to categorizers chain
    # the order of categories within categories is irrelevant
    cchain = profile['subset_hierarchy_categorizers_chain']
    # ---- walk categorizers
    for categorizerID in cchain:
        categorizer = categorizers[categorizerID]
        categories = [categorizer.uniquifyCategory(c) for c in categorizer.categories()]
        outerSelection[categorizerID] = dict()
        innerSelection[categorizerID] = dict()
        # ---- walk associated categories
        for category in categories:
            outerSelection[categorizerID][category] = dict()
            innerSelection[categorizerID][category] = dict()
            # ---- process operations map
            cdata = operations_map[category]
            env.logger.info('Started processing operations for category %s' % category)
            # ---- get outer selector instance and process iterable
            outer_selector = cdata['__outer_selector__']
            if outer_selector is not None:
                env.logger.info('Found outer selector for category %s : %s' % (category, operations_map_img[category]['__outer_selector__']))
                # ---- get submission order
                subm_order = submission_order[categorizerID][category]
                env.logger.info('Submission order reconstructed with %d entries' % (len(subm_order)))
                # ---- construct results iterable ordered according to submission order
                # NOTE : we are careful here since we can have less results than
                # submission order may suggest! this is very likely when using
                # test mode, and in addition if top category encloses ALL subsets,
                # then it is pretty much guaranteed (see global submission order
                # dump for reference)
                indResultsList = list()
                for pkcid in subm_order:
                    try:
                        indResultsList.append(ssIndResults[subsets[pkcid]['mat']])
                    except:
                        pass
#                indResultsList = [ssIndResults[subsets[pkcid]['mat']] for pkcid in subm_order]
                env.logger.info('Individual results obtained (%d entries)' % (len(indResultsList)))
                # ---- perform outer selection
                outerSelectionResultsList = outer_selector.perform(indResultsList)
                for ss, oselres in zip(subm_order, outerSelectionResultsList):
                    outerSelection[categorizerID][category][ss] = oselres
                env.logger.info('Outer selection (selection level 1) done for %d individual results' % (len(indResultsList)))
            else:
                env.logger.info('No outer selector present for category %s' % (category))
            # ---- get inner selector instance and process iterable
            inner_selector = cdata['__inner_selector__']
            if inner_selector is not None:
                env.logger.info('Found inner selector for category %s : %s' % (category, operations_map_img[category]['__inner_selector__']))
                innerSelectionResultsDict = inner_selector.perform(outerSelection[categorizerID][category], ssIndResults, subsets)
                for pkcid, isdata in innerSelectionResultsDict.iteritems():
                    innerSelection[categorizerID][category][pkcid] = isdata
                env.logger.info('Inner selection (selection level 2) done for %d individual results' % (len(ssIndResults.keys())))
            else:
                env.logger.info('No inner selector present for category %s' % (category))

    env.addVar('outerSelection', outerSelection)
    env.addVar('innerSelection', innerSelection)

    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    if use_debug_output:
        outer_selection_key = env.var('outer_selection_key')
        outer_selection_txt_key = '%s%s' % (outer_selection_key, txt_suffix)
        outer_selection_path = os.path.join(debug_output_path, outer_selection_key)
        with open(outer_selection_path, 'wb') as f:
            serializeObj(outerSelection, f)
        outer_selection_txt_path = os.path.join(debug_output_path, outer_selection_txt_key)
        with open(outer_selection_txt_path, 'wb') as f:
            pprintObj(outerSelection, f)
        env.logger.info('Outer selection results dictionary serialized to %s' % outer_selection_key)
        inner_selection_key = env.var('inner_selection_key')
        inner_selection_txt_key = '%s%s' % (inner_selection_key, txt_suffix)
        inner_selection_path = os.path.join(debug_output_path, inner_selection_key)
        with open(inner_selection_path, 'wb') as f:
            serializeObj(innerSelection, f)
        inner_selection_txt_path = os.path.join(debug_output_path, inner_selection_txt_key)
        with open(inner_selection_txt_path, 'wb') as f:
            pprintObj(innerSelection, f)
        env.logger.info('Inner selection results dictionary serialized to %s' % inner_selection_key)

    env.logger.info('Finished performing selections')


def storeCompleteResults(env):
    r"""
Action that performs the following:

    * for each data subset:

        * create individual location for results under current storage manager
        * save all generated plots as physical files there
        * serialize :class:`~kdvs.fw.Stat.Results` instance there
    """
    env.logger.info('Started storing complete job results')

    rootsm = env.var('rootsm')
    # get main results location
    ssrootresloc = env.var('subsets_results_location_id')
    subset_results_suffix = env.var('subset_results_suffix')
    txt_suffix = env.var('txt_suffix')

    ssIndResults = env.var('ssIndResults')

    for ssname, result in ssIndResults.iteritems():
        # ---- serialize Results
        # create individual location for subset
        ssresloc = rootsm.sublocation_separator.join([ssrootresloc, ssname])
        rootsm.createLocation(ssresloc)
        ssreslocpath = rootsm.getLocation(ssresloc)
        # first save any plots separately
        ssplots = result[RESULTS_PLOTS_ID_KEY]
        for plotname in sorted(ssplots.keys()):
            plotcontent = ssplots[plotname]
            plotpath = os.path.join(ssreslocpath, plotname)
            with open(plotpath, 'wb') as f:
                writeObj(plotcontent, f)
            env.logger.info('Plot %s saved' % (plotname))
        # serialize individual output
        result_img = dict((k, result[k]) for k in result.keys())
        del result_img[RESULTS_PLOTS_ID_KEY]
        ind_subset_result_key = '%s%s' % (ssname, subset_results_suffix)
        ind_subset_result_path = os.path.join(ssreslocpath, ind_subset_result_key)
        with open(ind_subset_result_path, 'wb') as f:
            serializeObj(result_img, f)
        ind_subset_result_txt_key = '%s%s' % (ind_subset_result_key, txt_suffix)
        ind_subset_result_txt_path = os.path.join(ssreslocpath, ind_subset_result_txt_key)
        with open(ind_subset_result_txt_path, 'wb') as f:
            pprintObj(result_img, f)
        env.logger.info('Results for %s serialized to %s' % (ssname, ind_subset_result_key))

    env.logger.info('Finished storing complete job results')

def prepareReports(env):
    r"""
Action that performs the following:

    * obtains/constructs the following mappings/instances used by any L1L2--associated reporters:

        * `subsets`
            {PKC_ID : [subsetID, numpy.shape(ds), [vars], [samples]]}
        * `pkcid2ssname` 
            {PKC_ID : subsetID}
        * `technique2DOF`
            {techniqueID : { 'DOFS_IDXS': (0, 1, ..., n), 'DOFs': (name_DOF0, name_DOF1, ..., name_DOFn)}
        * `operations_map_img`
            (textual component of `operation map`)
        * `categories_map`
            {categorizerID : [categories]}
        * `cchain`
            i.e. categorizers chain, comes directly from :data:`~kdvs.fw.impl.app.Profile.MA_GO_PROFILE` application profile (element 'subset_hierarchy_categorizers_chain')
        * `submission_order`
            an iterable of PKC IDs sorted in order of submission of their jobs
        * `pkc_manager`
            a concrete instance of :class:`~kdvs.fw.PK.PKCManager` that governs all PKCs generated

    * for each category:

        * having all :class:`~kdvs.fw.Stat.Results` instances, and all additional data collected, executes associated reporter(s)
            (physical report files are saved to the specific location(s) under current storage manager)
    """
    env.logger.info('Started preparing reports')

    rootsm = env.var('rootsm')
    ssrootresloc = env.var('subsets_results_location_id')

    use_debug_output = env.var('use_debug_output')
    debug_output_path = env.var('debug_output_path')
    txt_suffix = env.var('txt_suffix')

    profile = env.var('profile')
    categorizers = env.var('pc_categorizers')
    operations_map = env.var('operations_map')
    operations_map_img = env.var('operations_map_img')
    submission_order = env.var('submission_order')
    pkc_manager = env.var('pkc_manager')
    subsets = env.var('subsets')

    cchain = profile['subset_hierarchy_categorizers_chain']

    technique2DOF = env.var('technique2DOF')
    pkdrivenss = env.var('pkdrivenss')
    ssIndResults = env.var('ssIndResults')

    # ---- obtain em2annotation that provides annotations for reporters
    geneidmap = env.var('geneidmap')
    em2annotation = get_em2annotation(geneidmap.dbt)
    env.logger.info('Obtained mapping em2annotation (%d entries found)' % (len(em2annotation.keys())))
    if use_debug_output:
        em2annotation_key = env.var('em2annotation_key')
        em2annotation_txt_key = '%s%s' % (em2annotation_key, txt_suffix)
        em2annotation_path = os.path.join(debug_output_path, em2annotation_key)
        with open(em2annotation_path, 'wb') as f:
            serializeObj(em2annotation, f)
        em2annotation_txt_path = os.path.join(debug_output_path, em2annotation_txt_key)
        with open(em2annotation_txt_path, 'wb') as f:
            pprintObj(em2annotation, f)
        env.logger.info('Mapping em2annotation serialized to %s' % em2annotation_key)

    # ---- obtain pkcid2ssname that will facilitate querying across various misc dictionaries
    pkcid2ssname_s = SetBDMap()
    for pkcID, sdata in subsets.iteritems():
        ssname = sdata['mat']
        pkcid2ssname_s[pkcID] = ssname
    env.logger.info('Obtained BD mapping pkcid2ssname (%d entries found)' % (len(pkcid2ssname_s.getFwdMap().keys())))
    pkcid2ssname = dict()
    pkcid2ssname['fwd'] = dict()
    for ok, ov in pkcid2ssname_s.getFwdMap().iteritems():
        iv = next(iter(ov))
        pkcid2ssname['fwd'][ok] = iv
    pkcid2ssname['bwd'] = dict()
    for ok, ov in pkcid2ssname_s.getBwdMap().iteritems():
        iv = next(iter(ov))
        pkcid2ssname['bwd'][ok] = iv
    if use_debug_output:
        pkcid2ssname_key = env.var('pkcid2ssname_key')
        pkcid2ssname_txt_key = '%s%s' % (pkcid2ssname_key, txt_suffix)
        pkcid2ssname_path = os.path.join(debug_output_path, pkcid2ssname_key)
        with open(pkcid2ssname_path, 'wb') as f:
            serializeObj(pkcid2ssname, f)
        pkcid2ssname_txt_path = os.path.join(debug_output_path, pkcid2ssname_txt_key)
        with open(pkcid2ssname_txt_path, 'wb') as f:
            pprintObj(pkcid2ssname, f)
        env.logger.info('Mapping pkcid2ssname serialized to %s' % pkcid2ssname_key)

    # quickly pre-compute all nested categories hierarchy
    categories_map = dict()
    for categorizerID in cchain:
        categorizer = categorizers[categorizerID]
        categories = [categorizer.uniquifyCategory(c) for c in categorizer.categories()]
        categories_map[categorizerID] = categories

    # prepare additional data for reporters
    reportersAdditionalData = dict()
    # in general any reporter will benefit from annotations
    reportersAdditionalData['em2annotation'] = em2annotation
    # subset details also may be useful
    reportersAdditionalData['subsets'] = subsets
    # this mapping will facilitate querying across differently keyed dictionaries
    reportersAdditionalData['pkcid2ssname'] = pkcid2ssname
    # this mapping simplifies obtaining technical details for technique
    reportersAdditionalData['technique2DOF'] = technique2DOF
    # global subset hierarchy used to construct nesting groups of subsets
#    # used for global reports that cross boundaries of categorizers
#    reportersAdditionalData['subsetHierarchy'] = pkdrivenss
    # used for identification of techniques across all categories in global reporters
    reportersAdditionalData['operations_map_img'] = operations_map_img
    # used for moving across categories in global reporters
    reportersAdditionalData['categories_map'] = categories_map
    # used for moving across categories in global reporters
    reportersAdditionalData['cchain'] = cchain
    # used for correctly resolving test modes
    reportersAdditionalData['submission_order'] = submission_order

    reportersAdditionalData['pkc_manager'] = pkc_manager

    # one must walk categories in relative order to categorizers chain
    # the order of categories within categories is irrelevant
    # ---- walk categorizers
    for categorizerID in cchain:
        categorizer = categorizers[categorizerID]
        categories = [categorizer.uniquifyCategory(c) for c in categorizer.categories()]
        # ---- walk associated categories
        for category in categories:
            # ---- process operations map
            cdata = operations_map[category]
            env.logger.info('Started processing operations for category %s' % category)
            # ---- get reporters
            reporters = cdata['__reporters__']
            if reporters is not None:
                env.logger.info('Found %d reporters for category %s : %s' % (len(reporters), category, operations_map_img[category]['__reporters__']))

                # ---- reconstruct submission order and results iterable
                subm_order = submission_order[categorizerID][category]
                env.logger.info('Submission order reconstructed with %d entries' % (len(subm_order)))
                # ---- construct results iterable ordered according to submission order
                # NOTE : we are careful here since we can have less results than
                # submission order may suggest! this is very likely when using
                # test mode, and in addition if top category encloses ALL subsets,
                # then it is pretty much guaranteed (see global submission order
                # dump for reference)
                indResultsList = list()
                for pkcid in subm_order:
                    try:
                        indResultsList.append(ssIndResults[subsets[pkcid]['mat']])
                    except:
                        pass
#                indResultsList = [ssIndResults[subsets[pkcid]['mat']] for pkcid in subm_order]
                env.logger.info('Individual results obtained (%d entries)' % (len(indResultsList)))

                for reporterID, reporter in zip(operations_map_img[category]['__reporters__'], reporters):
                    reporter.initialize(rootsm, ssrootresloc, reportersAdditionalData)
                    reporter.produce(indResultsList)
                    reporter.produceForHierarchy(pkdrivenss, ssIndResults, categorizerID, category)
                    env.logger.info('Reporter %s produced %d report(s)' % (reporterID, len(reporter.getReports().keys())))
                    reporter.finalize()

            else:
                env.logger.info('No reporters present for category %s' % (category))

    # TODO: finish!

    env.logger.info('Finished preparing reports')


# ---- private functions

def _resolveProfileInstanceGroup(profile_ig_data):
    instances = dict()
    for instID, instData in profile_ig_data.iteritems():
        for instComponentID, instParams in instData.iteritems():
            inst = importComponent(instComponentID)(**instParams)
            instances[instID] = inst
    return instances

def main():
    MA_GO_Experiment_App().run()

if __name__ == '__main__':
    main()
