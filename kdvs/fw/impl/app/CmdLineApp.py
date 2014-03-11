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
Provides skeleton implementation for basic command line application that uses
KDVS API; the 'experiment' application is based on it.
"""

from kdvs import SYSTEM_NAME_UC
from kdvs.core.config import evaluateUserCfg
from kdvs.core.db import DBManager
from kdvs.core.error import Error
from kdvs.core.log import _LEVELS
from kdvs.core.util import quote, isDirWritable, getSerializableContent, \
    serializeObj, importComponent, pprintObj, serializeTxt
from kdvs.fw.App import App, AppProfile
from optparse import OptionParser
import datetime
import os

class CmdLineApp(App):
    r"""
Simple implementation of KDVS application that is configured from command line
arguments. The functionality is tailored for 'experiment' application, which means
the arguments are currently hard--coded:

.. program-output:: python ../wrapper.py kdvs/bin/experiment.py -h
    """
    def __init__(self):
        r"""
        """
        super(CmdLineApp, self).__init__()

    def prepareEnv(self):
        r"""
Interprets command line arguments, reads specified configuration file, initializes
specific logging mechanism, initializes default paths, and creates concrete
:class:`~kdvs.core.env.ExecutionEnvironment` instance.
        """
        # ---- process command line arguments
        # NOTE: optparse is deprecated, but since we want to ensure compatibility with
        # Python 2.6+, we still use it here
        desc = 'Knowledge Driven Variable Selection Experiment Application'
        parser = OptionParser(description=desc)
        parser.add_option("-c", "--config-file", action="store", dest="cfg_file",
            help="read configuration from CFGFILE", metavar="CFGFILE")
        parser.add_option("-s", "--src-data-dir", action="store", dest="src_data_dir",
            help="read data files from SDDIR", metavar="SDDIR", default=None)
        parser.add_option("-o", "--output-dir", action="store", dest="output_dir",
            help="store all results in OUTDIR", metavar="OUTDIR", default=None)
        parser.add_option("-l", "--log-file", action="store", dest="log_path",
            help="direct log output to LOGFILE", metavar="LOGFILE", default=None)
        parser.add_option("--ignore-default-config", action="store_true", dest="ignore_default_cfg",
            help="ignore default configuration (advanced)", default=False)
        parser.add_option("--log-to-stdout", action="store_true", dest="log_to_stdout",
            help="log output to stdout", default=False)
        parser.add_option("--use-debug-output", action="store_true", dest="use_debug_output",
            help="write (lots of) detailed debug output", default=False)
        parser.add_option("--log-level", action="store", dest="log_level",
            help="set log level to specified", default='INFO')
        # get only options here
        options = parser.parse_args()[0]
        # check user config file
        if not options.cfg_file:
            raise Error('Configuration file not specified! Use -h option for more details.')
        abs_cfg_file_path = os.path.abspath(options.cfg_file)
        if not os.path.exists(abs_cfg_file_path):
            raise Error('Configuration file %s not available!' % quote(abs_cfg_file_path))
        cfg_root = os.path.split(abs_cfg_file_path)[0]
        # check output directory
        if options.output_dir is None:
            output_dir = cfg_root
        else:
            output_dir = options.output_dir
        if not isDirWritable(output_dir):
            raise Error('Designated output directory %s is not writable!' % quote(output_dir))
        # ---- process config file
        cfg_vars = evaluateUserCfg(options.cfg_file, options.ignore_default_cfg)
        # ---- configure logging facilities
        log_name = cfg_vars['log_name']
        log_file = cfg_vars['log_file']
        log_level = _LEVELS[options.log_level]
        log_cfg = dict()
        if options.log_to_stdout is True:
            log_type = cfg_vars['log_type_def_std']
        else:
            log_type = cfg_vars['log_type_def_file']
            if options.log_path is None:
                log_path = os.path.join(output_dir, log_file)
            else:
                log_path = os.path.realpath(os.path.abspath(options.log_path))
            log_cfg['path'] = log_path
        log_cfg['name'] = log_name
        log_cfg['level'] = log_level
        logger = importComponent(log_type)(**log_cfg)
        # ---- configure execution environment
        env_type = cfg_vars['execution_environment_type']
        env_exp_cfg = cfg_vars['execution_environment_exp_cfg']
        env_cfg = {'logger' : logger}
        self.env = importComponent(env_type)(env_exp_cfg, env_cfg)
        # ---- finish
        # check data directory
        if options.src_data_dir is None:
            data_path = cfg_vars['def_data_path']
        else:
            data_path = os.path.abspath(options.src_data_dir)
        # update variables
        self.env.updateVars(cfg_vars)
#        self.env.addVar('logger', logger)
        self.env.addVar('output_dir', output_dir)
        self.env.addVar('data_path', data_path)
        self.env.addVar('use_debug_output', options.use_debug_output)
        # shortcut for logger
        self.logger = self.env.logger

    def appProlog(self):
        r"""
Creates physical root output location and debug output location, creates starting timestamp
inside the output location, serializes initial configuration for debug purposes,
creates an instance of :class:`~kdvs.core.db.DBManager`, and verifies that the experiment profile
specified in configuration file is correct.
        """
        super(CmdLineApp, self).appProlog()
        self._createRootOutputLocation(self.env)
        self._createDebugOutputLocation(self.env)
        self._storeCfg(self.env)
        self._createDB(self.env)
        self._verifyExperimentProfile(self.env)

    def appEpilog(self):
        r"""
Creates ending timestamp in root output location and finishes logging.
        """
        super(CmdLineApp, self).appEpilog()
        self._createEndTS(self.env)
        self._finished(self.env)

    def _createRootOutputLocation(self, env):
        output_dir = env.var('output_dir')
        # create default storage manager
        self.rootsm = importComponent(env.var('storage_manager_type'))(name='rootsm', root_path=output_dir)
        self.env.addVar('rootsm', self.rootsm)
        # create root location
        root_location = '%s_output' % SYSTEM_NAME_UC
        env.addVar('root_output_location', root_location)
        self.rootsm.createLocation(root_location)
        rlocpath = self.rootsm.getLocation(root_location)
        # shortcut for fast path access
        env.addVar('root_output_path', rlocpath)
        env.logger.info('Root output location created in %s' % rlocpath)
        # note start timestamp
        ts_start = datetime.datetime.now().isoformat(' ')
        ts_start_key = env.var('ts_start_key')
        with open(os.path.join(rlocpath, ts_start_key), 'wb') as f:
            serializeTxt([ts_start], f)
        env.logger.info('%s start timestamp: %s' % (SYSTEM_NAME_UC, ts_start))

    def _createDebugOutputLocation(self, env):
        rootsm = env.var('rootsm')
        rloc = env.var('root_output_location')
        try:
            debug_output_location = env.var('debug_output_location')
            debugloc = rootsm.sublocation_separator.join([rloc, debug_output_location])
            rootsm.createLocation(debugloc)
            env.addVar('debug_output_location_id', debugloc)
            debugpath = rootsm.getLocation(debugloc)
            env.addVar('debug_output_path', debugpath)
        except ValueError:
            pass

    def _storeCfg(self, env):
        cfg_key = env.var('cfg_key')
        cfg_txt_key = '%s%s' % (cfg_key, env.var('txt_suffix'))
#        debug_output_path = env.var('debug_output_path')
        root_output_path = env.var('root_output_path')
        vars_dump = dict()
        for vk in env.varkeys():
            vars_dump[vk] = getSerializableContent(env.var(vk))
        with open(os.path.join(root_output_path, cfg_key), 'wb') as f:
            serializeObj(vars_dump, f)
        with open(os.path.join(root_output_path, cfg_txt_key), 'wb') as f:
            pprintObj(vars_dump, f)
        env.logger.info('Configuration serialized to %s' % cfg_key)

    def _createDB(self, env):
        rootsm = env.var('rootsm')
        rloc = env.var('root_output_location')
        dbm_location_part = env.var('dbm_location')
        dbloc = rootsm.sublocation_separator.join([rloc, dbm_location_part])
        rootsm.createLocation(dbloc)
        env.addVar('dbm_location_id', dbloc)
        dblocpath = rootsm.getLocation(dbloc)
        dbm = DBManager(arbitrary_data_root=dblocpath)
        env.addVar('dbm', dbm)
        env.logger.info('Created DB manager in %s with root DB ID: %s' % (dblocpath, dbm.rootdb_key))

    def _verifyExperimentProfile(self, env):
        profile_type = env.var('experiment_profile')
        profile_inst = env.var('experiment_profile_inst')
        env.logger.info('Experiment profile: %s' % profile_type)
        exp_profile = importComponent(profile_type)
        profile = AppProfile(exp_profile, profile_inst)
        env.addVar('profile', profile)
        env.logger.info('Configured experiment profile (%d elements found)' % (len(profile.keys())))

    def _createEndTS(self, env):
        rootsm = env.var('rootsm')
        rloc = env.var('root_output_location')
        rlocpath = rootsm.getLocation(rloc)
        ts_end = datetime.datetime.now().isoformat(' ')
        ts_end_key = env.var('ts_end_key')
        with open(os.path.join(rlocpath, ts_end_key), 'wb') as f:
            serializeTxt([ts_end], f)
        env.logger.info('%s end timestamp: %s' % (SYSTEM_NAME_UC, ts_end))

    def _finished(self, env):
        env.logger.info('All done')
        for h in env.logger.handlers:
            h.close()
            env.logger.removeHandler(h)
