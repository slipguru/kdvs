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

from kdvs import SYSTEM_NAME_LC
from kdvs.core.action import ActionSpec
from kdvs.core.config import evaluateUserCfg, getDefaultCfgFilePath, mergeCfg
from kdvs.core.db import DBManager
from kdvs.core.dep import verifyDepModule
from kdvs.core.env import ExecutionEnvironment, LoggedExecutionEnvironment
from kdvs.core.error import Error
from kdvs.core.log import Logger, NullHandler, StreamLogger, RotatingFileLogger
from kdvs.core.provider import fileProvider, SQLite3DBProvider
from kdvs.core.util import isListOrTuple, CommentSkipper, isTuple, \
    isIntegralNumber, className, emptyGenerator, Parametrizable, Configurable
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
from kdvs.tests.utils import test_dir_writable, count_lines
from logging import shutdown, DEBUG, ERROR
import gc
import os
import sys
import types

unittest = resolve_unittest()

class TestLog(unittest.TestCase):

    def setUp(self):
        test_write_root = TEST_INVARIANTS['test_write_root']
        self.path2 = 'test.log'
        self.path3 = os.path.abspath(os.path.join(test_write_root, 'test.log'))
        self.loglines1 = ['Log Message 1']
        self.loglines2 = ['Log Message 1', 'Log Message 2']

    def tearDown(self):
        shutdown()
        gc.collect()
        try:
            path1 = getattr(self, 'path1')
            if os.path.exists(path1):
                os.remove(path1)
        except:
            pass
        if os.path.exists(self.path2):
            os.remove(self.path2)
        if os.path.exists(self.path3):
            os.remove(self.path3)

    def test_NullLogger(self):
        logger = Logger(level=DEBUG)
        for l in self.loglines1:
            logger.info(l)
        self.assertIn('handler', logger.std_atts)
        self.assertIsInstance(logger.std_atts['handler'], NullHandler)

    def test_StreamLogger1(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        for l in self.loglines2:
            logger.info(l)
        ref_lines = test_stream.getvalue().splitlines()
        self.assertEqual(2, len(ref_lines))
        ref_lines_len = [len(l) for l in ref_lines]
        self.assertEqual(1, len(set(ref_lines_len)))
        ref_lines_msg = [l.endswith(m) for l, m in zip(ref_lines, self.loglines2)]
        self.assertTrue(all(ref_lines_msg))

    def test_StreamLogger2(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=ERROR, stream=test_stream)
        for l in self.loglines2:
            logger.debug(l)
            logger.info(l)
            logger.error(l)
        ref_lines = test_stream.getvalue().splitlines()
        self.assertNotEqual(6, len(ref_lines))
        self.assertEqual(2, len(ref_lines))
        ref_lines_len = [len(l) for l in ref_lines]
        self.assertEqual(1, len(set(ref_lines_len)))
        ref_lines_msg = [l.endswith(m) for l, m in zip(ref_lines, self.loglines2)]
        self.assertTrue(all(ref_lines_msg))

    def test_RFLogger1(self):
        cwd = os.getcwd()
        dw = test_dir_writable(cwd)
        if dw is False:
            self.skipTest('%s not writable' % cwd)
        else:
            logger = RotatingFileLogger()
            for l in self.loglines2:
                logger.info(l)
            self.assertIn('path', logger.add_atts)
            self.path1 = logger.add_atts['path']
            self.assertGreater(os.path.getsize(self.path1), 0)
            with open(self.path1, 'rb') as f:
                ref_lines = [l.strip() for l in f.readlines()]
            self.assertEqual(2, len(ref_lines))
            ref_lines_len = [len(l) for l in ref_lines]
            self.assertEqual(1, len(set(ref_lines_len)))
            ref_lines_msg = [l.endswith(m) for l, m in zip(ref_lines, self.loglines2)]
            self.assertTrue(all(ref_lines_msg))

    def test_RFLogger2(self):
        cwd = os.getcwd()
        dw = test_dir_writable(cwd)
        if dw is False:
            self.skipTest()
        else:
            logger = RotatingFileLogger(path=self.path2)
            for l in self.loglines2:
                logger.info(l)
            self.assertGreater(os.path.getsize(self.path2), 0)
            with open(self.path2, 'rb') as f:
                ref_lines = [l.strip() for l in f.readlines()]
            self.assertEqual(2, len(ref_lines))
            ref_lines_len = [len(l) for l in ref_lines]
            self.assertEqual(1, len(set(ref_lines_len)))
            ref_lines_msg = [l.endswith(m) for l, m in zip(ref_lines, self.loglines2)]
            self.assertTrue(all(ref_lines_msg))

    def testRFLogger3(self):
        logger = RotatingFileLogger(path=self.path3)
        for l in self.loglines2:
            logger.info(l)
        self.assertGreater(os.path.getsize(self.path3), 0)
        with open(self.path3, 'rb') as f:
            ref_lines = [l.strip() for l in f.readlines()]
        self.assertEqual(2, len(ref_lines))
        ref_lines_len = [len(l) for l in ref_lines]
        self.assertEqual(1, len(set(ref_lines_len)))
        ref_lines_msg = [l.endswith(m) for l, m in zip(ref_lines, self.loglines2)]
        self.assertTrue(all(ref_lines_msg))

class TestDep(unittest.TestCase):

    def test_positive(self):
        osmod = sys.modules['os']
        osm = verifyDepModule('os')
        self.assertIsInstance(osm, types.ModuleType)
        self.assertEquals(osmod, osm)

    def test_negative(self):
        with self.assertRaises(Error):
            import uuid
            verifyDepModule(uuid.uuid4().hex)

class TestAction(unittest.TestCase):

    @staticmethod
    def _callable1(self):
        pass

    @staticmethod
    def _callable2(self, *args, **kwargs):
        return len(args) + len(kwargs.keys())

    def test_ActionSpec1(self):
        aspec = ActionSpec([], [], TestAction._callable1, [], {})
        self.assertSequenceEqual([], aspec.input_vars)
        self.assertSequenceEqual([], aspec.output_vars)
        self.assertSequenceEqual([], aspec.args)
        self.assertDictEqual({}, aspec.kwargs)
        self.assertIsInstance(aspec.func, types.FunctionType)

    def test_ActionSpec2(self):
        with self.assertRaises(Error):
            ActionSpec('', '', None, '', '')

    def test_ActionSpec3(self):
        aspec = ActionSpec(['var1', 'var2'], ['var3', 'var4'], TestAction._callable2, ['arg1', 'arg2'], {'arg3' : 1, 'arg4' : 2})
        self.assertSequenceEqual(['var1', 'var2'], aspec.input_vars)
        self.assertSequenceEqual(['var3', 'var4'], aspec.output_vars)
        self.assertSequenceEqual(['arg1', 'arg2'], aspec.args)
        self.assertDictEqual({'arg3' : 1, 'arg4' : 2}, aspec.kwargs)
        self.assertIsInstance(aspec.func, types.FunctionType)
        res = aspec.func(self, *aspec.args, **aspec.kwargs)
        self.assertEqual(len(aspec.args) + len(aspec.kwargs), res)

    def test_ActionSpec4(self):
        aspec = ActionSpec(['var1', 'var2'], ['var3', 'var4'], TestAction._callable2, ['arg1', 'arg2'], {'arg3' : 1, 'arg4' : 2})
        self.assertSequenceEqual(['var1', 'var2'], aspec.input_vars)
        self.assertSequenceEqual(['var3', 'var4'], aspec.output_vars)
        self.assertSequenceEqual(['arg1', 'arg2'], aspec.args)
        self.assertDictEqual({'arg3' : 1, 'arg4' : 2}, aspec.kwargs)
        self.assertIsInstance(aspec.func, types.FunctionType)
        self.assertEqual(len(aspec.as_tuple()), 5)


class TestEnv(unittest.TestCase):

    @staticmethod
    def _a0(env):
        env.addVar('a0_res', None)

    @staticmethod
    def _a1(env, a=0, b=0, c=0):
        env.addVar('d', int(a) + int(b) + int(c))

    @staticmethod
    def _a2(env, a=None, b=None, c=None, d=None):
        logger = env.var('logger')
        logger.info('%s %s %s %s' % (a, b, c, d))

    @staticmethod
    def _a3(env, a=None):
        logger = env.var('logger')
        logger.warn('%s' % a)

    @staticmethod
    def _a4(env):
        raise ValueError('Danger, Will Robinson!!!')

    @staticmethod
    def _b1(env):
        logger = env.var('logger')
        n1 = 'source1'
        s1 = 'val1'
        env.addVar(n1, s1)
        logger.info('Produced "%s" as "%s"' % (s1, n1))

    @staticmethod
    def _b2(env):
        logger = env.var('logger')
        n2 = 'source2'
        s2 = 'val2'
        env.addVar(n2, s2)
        logger.info('Produced "%s" as "%s"' % (s2, n2))

    @staticmethod
    def _b3(env):
        logger = env.var('logger')
        n1 = 'source1'
        n2 = 'source2'
        np = 'product'
        vp = env.var(n1) + '__' + env.var(n2)
        env.addVar(np, vp)
        logger.info('Consumed "%s" and "%s" in "%s" as "%s"' % (n1, n2, vp, np))

    @staticmethod
    def _b4(env):
        logger = env.var('logger')
        np = 'product'
        vp = env.var(np)
        logger.info('Found "%s" as "%s"' % (vp, np))

    @staticmethod
    def _postActionCb1():
        pass

    @staticmethod
    def _postActionCb2():
        raise KeyError

    def setUp(self):
        pass

    def tearDown(self):
        shutdown()
        gc.collect()

    def test_ExecEnv1(self):
        env = ExecutionEnvironment({}, {})
        self.assertEqual(len(env.varkeys()), 0)
        self.assertEqual(len(env.actions()), 0)
        env.addCallable(TestEnv._a0)
        self.assertEqual(len(env.varkeys()), 0)
        self.assertEqual(len(env.actions()), 1)
        env.execute()
        self.assertEqual(len(env.varkeys()), 1)
        self.assertEqual(len(env.actions()), 0)
        val = env.var('a0_res')
        self.assertIsNone(val)

    def test_ExecEnv2(self):
        env = ExecutionEnvironment({}, {})
        self.assertEqual(len(env.varkeys()), 0)
        self.assertEqual(len(env.actions()), 0)
        env.addCallable(TestEnv._a0)
        env.addCallable(TestEnv._a1, {'a' : 1, 'b' : 2, 'c' : 3})
        self.assertEqual(len(env.varkeys()), 0)
        self.assertEqual(len(env.actions()), 2)
        env.execute()
        self.assertEqual(len(env.varkeys()), 2)
        self.assertEqual(len(env.actions()), 0)
        d = env.var('d')
        self.assertEqual(d, 1 + 2 + 3)
        env.delVar('d')
        self.assertEqual(len(env.varkeys()), 1)
        env.delVar('not existing variable')

    def test_ExecEnv3(self):
        env = ExecutionEnvironment({}, {})
        env.addCallable(TestEnv._a0)
        env.addCallable(TestEnv._a4)
        env.addCallable(TestEnv._a1, {'a' : 1, 'b' : 2, 'c' : 3})
        w, e, ex_acts, left_acts = env.execute()
        executed, alladded, spec = w
        self.assertEqual(executed, 2)
        self.assertEqual(alladded, 3)
        self.assertEqual(spec.as_tuple()[2].__name__, '_a4')
        self.assertIsInstance(e[0], ValueError)
        self.assertEqual(len(ex_acts), 1)
        self.assertEqual(len(left_acts), 1)
        self.assertEqual(ex_acts[0].as_tuple()[2].__name__, '_a0')
        self.assertEqual(left_acts[0].as_tuple()[2].__name__, '_a1')

    def test_ExecEnv4(self):
        env = ExecutionEnvironment({}, {})
        env.addCallable(TestEnv._a1, {'a' : 1, 'b' : 2, 'c' : 3})
        env.addCallable(TestEnv._a4)
        env.addCallable(TestEnv._a0)
        var_dump = env.execute(dump_env=True)[-1]
        self.assertEqual(len(var_dump), 1)
        self.assertNotIn('a0_res', var_dump)
        self.assertIn('d', var_dump)
        self.assertEqual(var_dump['d'], 1 + 2 + 3)

    def test_LoggedExecEnv1(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        exp_cfg = {'logger' : Logger(), }
        env_cfg = {'logger' : logger}
        env = LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env.addCallable(TestEnv._a2, {'a' : 'a', 'b' : 'b', 'c' : 'c', 'd' :-1})
        env.addCallable(TestEnv._a3)
        env.execute()
        nls = count_lines(test_stream)
        self.assertEqual(nls, 4)

    def test_LoggedExecEnv2(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        exp_cfg = {'logger' : Logger(), }
        env_cfg = {'logger' : logger}
        env = LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env.addCallable(TestEnv._a2, {'a' : 'a', 'b' : 'b', 'c' : 'c', 'd' :-1})
        env.addCallable(TestEnv._a3)
        env.addCallable(TestEnv._a4)
        env.addCallable(TestEnv._a0)
        env.execute()
        nls = count_lines(test_stream)
        self.assertEqual(nls, 18)

    def test_LoggedExecEnv3(self):
        exp_cfg = {'logger' : 'kdvs.core.log.Logger', }
        env_cfg = {}
        with self.assertRaises(Error):
            LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env_cfg = {'non_existing_elem' : None}
        with self.assertRaises(Error):
            LoggedExecutionEnvironment(exp_cfg, env_cfg)

    def test_CondExecEnv1(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        exp_cfg = {'logger' : Logger(), }
        env_cfg = {'logger' : logger}
        env = LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env.addCallable(TestEnv._b1, action_kwargs=None, action_input=None, action_output=('source1',))
        env.addCallable(TestEnv._b2, action_kwargs=None, action_input=None, action_output=('source2',))
        env.addCallable(TestEnv._b3, action_kwargs=None, action_input=('source1', 'source2'), action_output=('product',))
        env.execute()
        self.assertIn('product', env.varkeys())
        self.assertEqual('val1__val2', env.var('product'))
        nls = count_lines(test_stream)
        self.assertEqual(nls, 5)

    def test_CondExecEnv2(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        exp_cfg = {'logger' : Logger(), }
        env_cfg = {'logger' : logger}
        env = LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env.addCallable(TestEnv._b1, action_kwargs=None, action_input=None, action_output=('source1',))
        env.addCallable(TestEnv._b2, action_kwargs=None, action_input=None, action_output=('source2',))
        env.addCallable(TestEnv._b3, action_kwargs=None, action_input=('source1', 'source2'), action_output=('some_strange_var',))
        with self.assertRaises(ValueError):
            env.execute()

    def test_postActionCb1(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        exp_cfg = {'logger' : Logger(), }
        env_cfg = {'logger' : logger}
        env = LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env.addCallable(TestEnv._a2, {'a' : 'a', 'b' : 'b', 'c' : 'c', 'd' :-1})
        env.addCallable(TestEnv._a3)
        # add custom post action callback
        env.postActionCallback = TestEnv._postActionCb1
        # and execute
        env.execute()
        nls = count_lines(test_stream)
        self.assertEqual(nls, 4)

    def test_postActionCb2(self):
        import cStringIO
        test_stream = cStringIO.StringIO()
        logger = StreamLogger(level=DEBUG, stream=test_stream)
        exp_cfg = {'logger' : Logger(), }
        env_cfg = {'logger' : logger}
        env = LoggedExecutionEnvironment(exp_cfg, env_cfg)
        env.addCallable(TestEnv._a2, {'a' : 'a', 'b' : 'b', 'c' : 'c', 'd' :-1})
        env.addCallable(TestEnv._a3)
        # add custom post action callback
        env.postActionCallback = TestEnv._postActionCb2
        # and execute
        env.execute()
        nls = count_lines(test_stream)
        self.assertEqual(nls, 15)


class TestConfig(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']

    def test_Config1(self):
        cfg_path = getDefaultCfgFilePath(os.path.join(self.test_data_root, 'test1_cfg.py'))
        cfg_vars = evaluateUserCfg(cfg_path, ignore_default_cfg=True)
        self.assertIn('val1', cfg_vars)
        self.assertEqual(cfg_vars['val1'], '1')
        self.assertIn('val2', cfg_vars)
        self.assertEqual(cfg_vars['val2'], ('Some string',))
        self.assertIn('val3', cfg_vars)
        self.assertEqual(cfg_vars['val3'], {'1': 1, 75: 'aaa', '2': None})

    def test_Config2(self):
        cfg1_path = getDefaultCfgFilePath(os.path.join(self.test_data_root, 'test1_cfg.py'))
        cfg2_path = getDefaultCfgFilePath(os.path.join(self.test_data_root, 'test2_cfg.py'))
        cfg1 = evaluateUserCfg(cfg1_path, ignore_default_cfg=True)
        cfg2 = evaluateUserCfg(cfg2_path, ignore_default_cfg=True)
        self.assertIn('val1', cfg1)
        self.assertIn('val2', cfg1)
        self.assertIn('val3', cfg1)
        self.assertIn('val1', cfg2)
        self.assertIn('file', cfg2)
        self.assertNotIn('file', cfg1)
        final_cfg = mergeCfg(cfg1, cfg2)
        self.assertIn('val1', final_cfg)
        self.assertIn('val2', final_cfg)
        self.assertIn('val3', final_cfg)
        self.assertIn('file', final_cfg)
        self.assertEqual(final_cfg['val1'], 'Child value')

    def test_Config3(self):
        cfg_path = getDefaultCfgFilePath(os.path.join(self.test_data_root, 'test1_cfg.py'))
        cfg = evaluateUserCfg(cfg_path, ignore_default_cfg=False)
        self.assertIn('default_config_loaded', cfg)
        self.assertEqual(cfg['default_config_loaded'], True)
        self.assertIn('val1', cfg)
        self.assertIn('val2', cfg)
        self.assertIn('val3', cfg)

class TestProvider(unittest.TestCase):

    def setUp(self):
        self.test_data_root = TEST_INVARIANTS['test_data_root']

    def test_FileProvider1(self):
        path_txt = os.path.abspath(os.path.join(self.test_data_root, 'file.txt'))
        path_gz = os.path.abspath(os.path.join(self.test_data_root, 'file.txt.gz'))
        path_bz2 = os.path.abspath(os.path.join(self.test_data_root, 'file.txt.bz2'))
        reflen = os.path.getsize(path_txt)
        with fileProvider(path_gz, 'rb') as f:
            flen1 = len(f.read())
        self.assertEqual(flen1, reflen)
        with fileProvider(path_bz2, 'rb') as f:
            flen2 = len(f.read())
        self.assertEqual(flen2, reflen)

    def test_SQLite3DBProvider1(self):
        sdbp = SQLite3DBProvider()
        conn = sdbp.connect(':memory:')
        c = conn.cursor()
        c.execute('pragma database_list')
        dbs = [cdb for cdb in c]
        self.assertEqual(len(dbs), 1)
        dbname = dbs[0][1]
        self.assertEqual(u'main', dbname)
        c.close()
        conn.close()

class TestDBManager(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.rootdb_path = os.path.join(self.test_write_root, '%s.root.db' % SYSTEM_NAME_LC)
        self.testdb1 = 'TestDB1'
        self.testdb1_path = os.path.join(self.test_write_root, "%s.db" % self.testdb1)
        self.testdb2 = 'TestDB2'
        self.testdb2_path = os.path.join(self.test_write_root, "%s.db" % self.testdb2)
        self.testdb3 = 'TestDB3'
        self.testdb3_path = os.path.join(self.test_write_root, "%s.db" % self.testdb3)

    def tearDown(self):
        if os.path.exists(self.testdb1_path):
            os.remove(self.testdb1_path)
        if os.path.exists(self.testdb2_path):
            os.remove(self.testdb2_path)
        if os.path.exists(self.testdb3_path):
            os.remove(self.testdb3_path)
        if os.path.exists(self.rootdb_path):
            os.remove(self.rootdb_path)

    def test_DBManager0(self):
        dbm = DBManager(self.test_write_root)
        dbm.close()
        self.assertDictEqual(dbm.db, {})
        self.assertDictEqual(dbm.db_loc, {})

    def test_DBManager1(self):
        dbm = DBManager(self.test_write_root)
        self.assertTrue(os.path.exists(self.rootdb_path))
        rootdb_loc = os.path.abspath(dbm.getDBloc(dbm.rootdb_key))
        self.assertEqual(self.rootdb_path, rootdb_loc)
        dbm.close()

    def test_DBManager2(self):
        dbm = DBManager(self.test_write_root)
        dbm.getDB('TestDB1')
        db1_path = dbm.getDBloc('TestDB1')
        ref1_path = os.path.abspath(os.path.join(self.test_write_root, 'TestDB1.db'))
        self.assertEqual(ref1_path, db1_path)
        db_created = dbm.getDB('TestDB2')
        db_opened = dbm.getDB('TestDB2')
        self.assertEqual(db_created, db_opened)
        dbm.close()

    def test_DBManager3(self):
        dbm = DBManager(self.test_write_root)
        with self.assertRaises(Error):
            dbm.getDB(None)
        self.assertIsNone(dbm.getDBloc(None))
        dbm.close()

    def test_DBManager4(self):
        dbm = DBManager(self.test_write_root)
        with self.assertRaises(Error):
            dbm.getDB(tuple())
        self.assertIsNone(dbm.getDBloc(tuple()))
        dbm.close()

    def test_DBManager5(self):
        dbm = DBManager(self.test_write_root)
        db = dbm.memdb
        self.assertIn('memdb', dbm.db)
        self.assertIn('memdb', dbm.db_loc)
        self.assertEqual(':memory:', dbm.getDBloc('memdb'))
        cs = db.cursor()
        cs.execute('create table A(a TEXT);')
        cs.execute('drop table A;')
        cs.close()
        dbm.close()

    def test_DBManager6(self):
        dbm = DBManager(self.test_write_root)
        dbm.getDB('TestDB1')
        dbm.getDB('TestDB2')
        dbm.getDB('TestDB3')
        self.assertIn('TestDB1', dbm.db)
        self.assertIn('TestDB1', dbm.db_loc)
        self.assertIn('TestDB2', dbm.db)
        self.assertIn('TestDB2', dbm.db_loc)
        self.assertIn('TestDB3', dbm.db)
        self.assertIn('TestDB3', dbm.db_loc)
        rootdb = dbm.getDB(dbm.rootdb_key)
        cs = rootdb.cursor()
        cs.execute('select db from DB')
        dbs = [str(r[0]) for r in cs.fetchall()]
        self.assertSequenceEqual(['TestDB1', 'TestDB2', 'TestDB3'], dbs)
        cs.close()
        dbm.close('TestDB2')
        self.assertIn('TestDB1', dbm.db)
        self.assertIn('TestDB1', dbm.db_loc)
        self.assertNotIn('TestDB2', dbm.db)
        self.assertNotIn('TestDB2', dbm.db_loc)
        self.assertIn('TestDB3', dbm.db)
        self.assertIn('TestDB3', dbm.db_loc)
        dbm.close()
        self.assertDictEqual(dbm.db, {})
        self.assertDictEqual(dbm.db_loc, {})

class TestIsListOrTuple(unittest.TestCase):

    def test_IsListOrTuple(self):
        obj1 = []
        obj2 = ('1', '2')
        obj3 = 'aaa'
        obj4 = 1.0
        obj5 = None
        self.assertTrue(isListOrTuple(obj1))
        self.assertTrue(isListOrTuple(obj2))
        self.assertFalse(isListOrTuple(obj3))
        self.assertFalse(isListOrTuple(obj4))
        self.assertFalse(isListOrTuple(obj5))

class TestIsTuple(unittest.TestCase):

    def test_IsTuple(self):
        obj1 = []
        obj2 = ('1', '2')
        obj3 = 'aaa'
        obj4 = 1.0
        obj5 = None
        self.assertFalse(isTuple(obj1))
        self.assertTrue(isTuple(obj2))
        self.assertFalse(isTuple(obj3))
        self.assertFalse(isTuple(obj4))
        self.assertFalse(isTuple(obj5))

class TestIsIntegralNumber(unittest.TestCase):

    def test_IsIntegralNumber(self):
        obj1 = ()
        obj2 = 2
        obj3 = 3L
        obj4 = 2.0
        obj5 = False
        obj6 = None
        self.assertFalse(isIntegralNumber(obj1))
        self.assertTrue(isIntegralNumber(obj2))
        self.assertTrue(isIntegralNumber(obj3))
        self.assertFalse(isIntegralNumber(obj4))
        # note: technically boolean is also integral type, but we are interested
        # in recognizing numbers, thus the following line is correct
        self.assertFalse(isIntegralNumber(obj5))
        self.assertFalse(isIntegralNumber(obj6))

class TestEmptyGenerator(unittest.TestCase):

    def test_emptyGenerator(self):
        g = emptyGenerator()
        res = [r for r in g]
        self.assertEqual([], res)

class TestClassName(unittest.TestCase):

    def test_className(self):
        obj1 = object
        obj2 = []
        obj3 = Logger(level=DEBUG)
        self.assertEqual('type', className(obj1))
        self.assertEqual('list', className(obj2))
        self.assertEqual('Logger', className(obj3))

class TestCommentSkipper(unittest.TestCase):

    def setUp(self):
        self.seq1 = ['Element%d' % i for i in range(10)]
        comments = ['# ' if i % 2 != 0 else '' for i in range(10)]
        self.seq2 = ['%s%s' % (c, s) for c, s in zip(comments, self.seq1)]
        self.seq2_filtered = ['Element%d' % i for i in range(0, 10, 2)]

    def test_CommentSkipper1(self):
        cs1 = CommentSkipper(self.seq1)
        seq1 = list(cs1)
        self.assertSequenceEqual(self.seq1, seq1)
        cs2 = CommentSkipper(self.seq2, comment='#')
        seq2 = list(cs2)
        self.assertSequenceEqual(self.seq2_filtered, seq2)
        cs3 = CommentSkipper(self.seq2, comment='?')
        seq3 = list(cs3)
        self.assertSequenceEqual(self.seq2, seq3)

class TestParametrizable1(unittest.TestCase):

    def setUp(self):
        self.params1 = {
            'att1' : 'val1',
            'att2' : 'val2',
            }
        self.ref_params1 = ('att1', 'att2')
        self.ref_params2 = ('att2',)
        self.ref_params3 = ('att1', 'att2', 'att3')
        self.ref_paramsX = ('XXXXX',)

    def test_init1(self):
        po = Parametrizable()
        self.assertTrue(hasattr(po, 'parameters'))
        self.assertEqual({}, po.parameters)

    def test_init2(self):
        po = Parametrizable({})
        self.assertTrue(hasattr(po, 'parameters'))
        self.assertEqual({}, po.parameters)

    def test_init3(self):
        # we supply all expected parameters
        po = Parametrizable(self.ref_params1, **self.params1)
        self.assertEqual(self.params1, po.parameters)

    def test_init4(self):
        # we skip one parameter in reference
        with self.assertRaises(Error):
            Parametrizable(self.ref_params2, **self.params1)

    def test_init5(self):
        # we add one more parameter in reference
        with self.assertRaises(Error):
            Parametrizable(self.ref_params3, **self.params1)

    def test_init6(self):
        # we supply scrambled reference
        with self.assertRaises(Error):
            Parametrizable(self.ref_paramsX, **self.params1)


class TestConfigurable1(unittest.TestCase):

    def setUp(self):
        self.def_c1 = {'key1' : '', 'key2' : 0.0, 'key3' : (), 'key4' : [], 'key5' : {}}
        self.c1 = {'key1' : 'val1',
                   'key2' : 1.0,
                   'key3' : ('val31', 'val32'),
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'}
                   }
        self.c2 = {'key1' : 'val1',
                   'key2' : 1.0,
                   'key3' : ('val31', 'val32'),
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'},
                   'key6' : 'Additional val',
                   }
        self.cx1 = {'key1' : 'val1',
                   'key2' : 1.0,
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'},
                   }
        self.cx2 = {'key1' : 'val1',
                   'key2' : 'XXXXXX',
                   'key3' : ('val31', 'val32'),
                   'key4' : ['val41'],
                   'key5' : {'sk1' : 'sv1', 'sk2' : 'sv2'},
                   }

    def test_init1(self):
        c = Configurable(self.def_c1, self.c1)
        self.assertEqual(self.c1, c._cfg)
        self.assertItemsEqual(self.c1.keys(), c.keys())
        for ck in self.c1.keys():
            self.assertEqual(self.c1[ck], c[ck])

    def test_init2(self):
        # configuration definition specifies only the required components
        c = Configurable(self.def_c1, self.c2)
        self.assertEqual(self.c1, c._cfg)
        # extra configuration components are silently ignored
        self.assertNotIn('key6', c.keys())

    def test_init3(self):
        # missing required component
        with self.assertRaises(Error):
            Configurable(self.def_c1, self.cx1)

    def test_init4(self):
        # wrong type of component
        with self.assertRaises(Error):
            Configurable(self.def_c1, self.cx2)
