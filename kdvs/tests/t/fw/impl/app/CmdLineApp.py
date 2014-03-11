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

from kdvs import SYSTEM_NAME_LC, SYSTEM_NAME_UC
from kdvs.core.config import getDefaultDataRootPath
from kdvs.core.error import Error
from kdvs.core.log import RotatingFileLogger
from kdvs.fw.impl.app.CmdLineApp import CmdLineApp
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
from kdvs.tests.utils import nostderr
import logging
import os
import shutil
import sys

unittest = resolve_unittest()

class TestCmdLineApp1(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.test1_cfg_path = os.path.abspath(os.path.join(self.test_data_root, 'test1_cfg.py'))
        self.test1_cfg_wrt_path = os.path.abspath(os.path.join(self.test_write_root, 'test1_cfg.py'))
        self.test3_cfg_path = os.path.abspath(os.path.join(self.test_data_root, 'test3_cmdlineapp_minimal_cfg.py'))
        self.test3_cfg_wrt_path = os.path.abspath(os.path.join(self.test_write_root, 'test3_cmdlineapp_minimal_cfg.py'))

        self.test4_cfg_path = os.path.abspath(os.path.join(self.test_data_root, 'test4_cmdlineapp_minimal_run_cfg.py'))
        self.test4_cfg_wrt_path = os.path.abspath(os.path.join(self.test_write_root, 'test4_cmdlineapp_minimal_run_cfg.py'))

        self.def_log_file = 'kdvs.log'
        self.def_log_path = os.path.abspath(os.path.join(self.test_write_root, self.def_log_file))
        self.log_file = 'KDVS__.log'
        self.log_path = os.path.abspath(os.path.join(self.test_write_root, self.log_file))
        self.def_root_location = '%s_output' % SYSTEM_NAME_UC
        self.def_root_location_path = os.path.abspath(os.path.join(self.test_write_root, self.def_root_location))

    def tearDown(self):
        # close explicitly and remove handlers under Windows
        # shutdown to close file based handlers
        logging.shutdown()
        # remove unused handlers for main KDVS logger (handlers are not removed during shutdown)
        rl = logging.getLogger('kdvs')
        for hl in rl.handlers:
            rl.removeHandler(hl)
        if os.path.exists(self.def_log_path):
            os.remove(self.def_log_path)
        if os.path.exists(self.log_path):
            os.remove(self.log_path)
        if os.path.exists(self.test1_cfg_wrt_path):
            os.remove(self.test1_cfg_wrt_path)
        if os.path.exists(self.test3_cfg_wrt_path):
            os.remove(self.test3_cfg_wrt_path)
        if os.path.exists(self.test4_cfg_wrt_path):
            os.remove(self.test4_cfg_wrt_path)
        if os.path.exists(self.def_root_location_path):
            shutil.rmtree(self.def_root_location_path)

    def test_init1(self):
        prev_argv = list(sys.argv)
        sys.argv[:] = []
        # no options specified
        sys.argv.append('Test')
        os.chdir(self.test_write_root)
        with self.assertRaises(Error):
            CmdLineApp()
        sys.argv = list(prev_argv)

    def test_init2(self):
        prev_argv = list(sys.argv)
        sys.argv[:] = []
        # no configuration file specified
        sys.argv.append('Test')
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        os.chdir(self.test_write_root)
        with self.assertRaises(Error):
            CmdLineApp()
        sys.argv = list(prev_argv)

    def test_init3(self):
        shutil.copy(self.test1_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        sys.argv[:] = []
        # no log file specified
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test1_cfg_wrt_path)
        os.chdir(self.test_write_root)
        app = CmdLineApp()
        # default log created
        self.assertTrue(os.path.exists(self.def_log_path))
        self.assertIn('logger', app.env.varkeys())
        self.assertIsInstance(app.env.var('logger'), RotatingFileLogger)
        # default output dir selected
        self.assertEqual(self.test_write_root, app.env.var('output_dir'))
        # default configuration loaded
        self.assertTrue(app.env.var('default_config_loaded'))
        # root output location does not exist yet
        self.assertFalse(os.path.exists(self.def_root_location_path))
        sys.argv = list(prev_argv)

    def test_init4(self):
        shutil.copy(self.test1_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        os.chdir(self.test_write_root)
        sys.argv[:] = []
        # minimal argument list specified
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test1_cfg_wrt_path)
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        app = CmdLineApp()
        # requested log created
        self.assertTrue(os.path.exists(self.log_path))
        self.assertIn('logger', app.env.varkeys())
        self.assertIsInstance(app.env.var('logger'), RotatingFileLogger)
        # default output dir selected
        self.assertEqual(self.test_write_root, app.env.var('output_dir'))
        # default configuration loaded
        self.assertTrue(app.env.var('default_config_loaded'))
        # default data root directory selected
        self.assertEqual(getDefaultDataRootPath(), app.env.var('data_path'))
        sys.argv = list(prev_argv)

    def test_init5(self):
        shutil.copy(self.test3_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        os.chdir(self.test_write_root)
        sys.argv[:] = []
        # ignore default configuration file
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test3_cfg_wrt_path)
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        sys.argv.append('--ignore-default-config')
        app = CmdLineApp()
        self.assertNotIn('default_config_loaded', app.env.varkeys())
        sys.argv = list(prev_argv)

    def test_init6(self):
        shutil.copy(self.test1_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        os.chdir(self.test_write_root)
        sys.argv[:] = []
        # change root data directory
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test1_cfg_wrt_path)
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        sys.argv.append('-s')
        sys.argv.append(self.test_data_root)
        app = CmdLineApp()
        self.assertEqual(self.test_data_root, app.env.var('data_path'))
        sys.argv = list(prev_argv)

    def test_init7(self):
        shutil.copy(self.test1_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        os.chdir(self.test_write_root)
        sys.argv[:] = []
        # unrecognized option
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test1_cfg_wrt_path)
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        sys.argv.append('--XXXXXX')
        with nostderr():
            with self.assertRaises(SystemExit):
                CmdLineApp()
        sys.argv = list(prev_argv)

    def test_run1(self):
        shutil.copy(self.test1_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        os.chdir(self.test_write_root)
        sys.argv[:] = []
        # minimal argument list specified
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test1_cfg_wrt_path)
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        app = CmdLineApp()
        app.run()
        # root output location created
        self.assertTrue(os.path.exists(self.def_root_location_path))
        # root db created
        def_root_db_path = os.path.join(self.def_root_location_path, 'db', '%s.root.db' % SYSTEM_NAME_LC)
        self.assertTrue(os.path.exists(def_root_db_path))
        # initial configuration serialized
        def_cfg_path = os.path.join(self.def_root_location_path, app.env.var('cfg_key'))
        self.assertTrue(os.path.exists(def_cfg_path))
        # start timestamp created
        def_tsstart_path = os.path.join(self.def_root_location_path, app.env.var('ts_start_key'))
        self.assertTrue(os.path.exists(def_tsstart_path))
        # end timestamp created
        def_tsend_path = os.path.join(self.def_root_location_path, app.env.var('ts_end_key'))
        self.assertTrue(os.path.exists(def_tsend_path))
        sys.argv = list(prev_argv)

    def test_run2(self):
        shutil.copy(self.test4_cfg_path, self.test_write_root)
        prev_argv = list(sys.argv)
        os.chdir(self.test_write_root)
        sys.argv[:] = []
        # ignore default configuration file
        sys.argv.append('Test')
        sys.argv.append('-c')
        sys.argv.append(self.test4_cfg_wrt_path)
        sys.argv.append('-l')
        sys.argv.append(self.log_file)
        sys.argv.append('--ignore-default-config')
        app = CmdLineApp()
        app.run()
        self.assertNotIn('default_config_loaded', app.env.varkeys())
        # root output location created
        self.assertTrue(os.path.exists(self.def_root_location_path))
        # root db created
        def_root_db_path = os.path.join(self.def_root_location_path, 'db', '%s.root.db' % SYSTEM_NAME_LC)
        self.assertTrue(os.path.exists(def_root_db_path))
        # initial configuration serialized
        def_cfg_path = os.path.join(self.def_root_location_path, app.env.var('cfg_key'))
        self.assertTrue(os.path.exists(def_cfg_path))
        # start timestamp created
        def_tsstart_path = os.path.join(self.def_root_location_path, app.env.var('ts_start_key'))
        self.assertTrue(os.path.exists(def_tsstart_path))
        # end timestamp created
        def_tsend_path = os.path.join(self.def_root_location_path, app.env.var('ts_end_key'))
        self.assertTrue(os.path.exists(def_tsend_path))
        sys.argv = list(prev_argv)

