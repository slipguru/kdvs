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

# set this to False if you want to preserve 'cache' and 'disk' PPlus directories
# between individual tests; useful for error debugging
TEAR_DOWN_PPLUS_DIRS = True

from kdvs.fw.Job import Job, JobStatus, JOBERROR
from kdvs.fw.impl.job.PPlusJob import PPlusJobContainer
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
from kdvs.tests.utils import nostderr, nostdout
import logging
import os
import shutil
import time
# try:
#    import pplus
#    pplusFound = True
# except ImportError:
#    pplusFound = False
unittest = resolve_unittest()

def _f0(*args):
    pass
    # passive return None -- valid result

def _f1(*args):
    return sum(args)

def _f2(*args):
    time.sleep(args[0])
    return sum(args[1:])

def _f3(*args):
    time.sleep(args[0])
    raise KeyError

def _f4(*args):
    # square arguments
    return [a * a for a in args]

# utility function to destroy pplus server
def _destroyPPlusServer(ppJobContainer):
    if ppJobContainer.pconn._server is not None:
        ppJobContainer.pconn._server.destroy()

# @unittest.skipUnless(pplusFound, 'pplus not found')
class TestPPlusJobContainer1(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        os.chdir(self.test_write_root)
#        try:
#            # set up master connection
#            self.pconn = pplus.PPlusConnection(debug=True, local_workers_number=1)
#        except OSError:
#            raise unittest.SkipTest('pplus not initialized properly')
        self.f0 = _f0
        self.f1 = _f1
        self.f2 = _f2
        self.f3 = _f3
        self.f4 = _f4
        self.arg0 = ()
        self.arg1 = (1, 2, 3, 4)
        self.arg2 = [1.0, 1, 2, 3, 4]
        self.arg3 = [0.5]
        self.arg4 = [i for i in range(10) if i % 2 == 1]  # 1 3 5 7 9
        self.ref_increment_ids = ['Job%d' % i for i in range(10)]
        self.jobs0 = [Job(self.f0, self.arg0) for _ in range(10)]
        self.jobs1 = [Job(self.f1, self.arg1) for _ in range(10)]
        self.jobs2 = [Job(self.f2, self.arg2) for _ in range(10)]
        self.jobs3 = [Job(self.f3, self.arg3) for _ in range(10)]
        self.jobs4 = [Job(self.f4, self.arg4) for _ in range(10)]
        self.refMiscData1 = ('experimentID', 'diskDataPath', 'isDebug')
        self.destPath1 = os.path.join(self.test_write_root, 'logs')

    def tearDown(self):
        # destroy PPlus server
#        if self.pconn._server is not None:
#            self.pconn._server.destroy()
        # close explicitly and remove handlers under Windows
        # shutdown to close file based handlers
        logging.shutdown()
        # remove unused handlers for main PPlus logger (handlers are not removed during shutdown)
        rl = logging.getLogger('pplus')
        for hl in rl.handlers:
            rl.removeHandler(hl)
        if TEAR_DOWN_PPLUS_DIRS:
#            try:
            shutil.rmtree(os.path.join(TEST_INVARIANTS['test_write_root'], 'cache'))
            shutil.rmtree(os.path.join(TEST_INVARIANTS['test_write_root'], 'disk'))
#            except OSError:
#                pass

    def test_init1(self):
        with nostderr():
            try:
#                ppjc1 = PPlusJobContainer(self.pconn)
                ppjc1 = PPlusJobContainer()
                self.assertSequenceEqual({}, ppjc1.jobs)
                self.assertSequenceEqual([], ppjc1.submitted)
                ppjc1.start()
                ppjc1.close()
                ppjc1.clear()
                _destroyPPlusServer(ppjc1)
            except OSError:
                self.skipTest('pplus not initialized properly')

    def test_addJob1(self):
        with nostderr():
            try:
#                ppjc1 = PPlusJobContainer(self.pconn)
                ppjc1 = PPlusJobContainer()
                ppjc1.start()
                j1 = Job(self.f0, self.arg0)
                jid1 = ppjc1.addJob(j1, importable=True)
                self.assertEqual(JobStatus.EXECUTING, ppjc1.getJobStatus(jid1))
                ppjc1.close()
                self.assertEqual(JobStatus.FINISHED, ppjc1.getJobStatus(jid1))
                self.assertIsNone(ppjc1.getJobResult(jid1))
                ppjc1.clear()
                _destroyPPlusServer(ppjc1)
            except OSError:
                self.skipTest('pplus not initialized properly')

    def test_addJob2(self):
        with nostderr():
            try:
#                ppjc1 = PPlusJobContainer(self.pconn)
                ppjc1 = PPlusJobContainer()
                ppjc1.start()
                jobIDs0 = [ppjc1.addJob(j, importable=True) for j in self.jobs0]
                st1 = set([ppjc1.getJobStatus(jid) for jid in jobIDs0])
                ref_st1 = set([JobStatus.EXECUTING])
                self.assertEqual(ref_st1, st1)
                ppjc1.close()
                st2 = set([ppjc1.getJobStatus(jid) for jid in jobIDs0])
                ref_st2 = set([JobStatus.FINISHED])
                self.assertEqual(ref_st2, st2)
                res = [ppjc1.getJobResult(jid) for jid in jobIDs0]
                ref_res = [None for _ in res]
                self.assertSequenceEqual(ref_res, res)
                ppjc1.clear()
                _destroyPPlusServer(ppjc1)
            except OSError:
                self.skipTest('pplus not initialized properly')

    def test_addJob3(self):
        with nostderr():
            try:
#                ppjc1 = PPlusJobContainer(self.pconn)
                ppjc1 = PPlusJobContainer()
                ppjc1.start()
                jobIDs1 = [ppjc1.addJob(j, importable=True) for j in self.jobs1]
                jobIDs2 = [ppjc1.addJob(j, importable=True) for j in self.jobs2]
                ist1 = set([ppjc1.getJobStatus(jid) for jid in jobIDs1])
                ist2 = set([ppjc1.getJobStatus(jid) for jid in jobIDs2])
                ref_ist = set([JobStatus.EXECUTING])
                self.assertEqual(ref_ist, ist1 & ist2)
                ppjc1.close()
                est1 = set([ppjc1.getJobStatus(jid) for jid in jobIDs1])
                est2 = set([ppjc1.getJobStatus(jid) for jid in jobIDs2])
                ref_est = set([JobStatus.FINISHED])
                self.assertEqual(ref_est, est1 & est2)
                res1 = [ppjc1.getJobResult(jid) for jid in jobIDs1]
                res2 = [ppjc1.getJobResult(jid) for jid in jobIDs2]
                ref_res1 = [10 for _ in res1]
                ref_res2 = [10 for _ in res2]
                self.assertEqual(ref_res1, res1)
                self.assertEqual(ref_res2, res2)
                ppjc1.clear()
                _destroyPPlusServer(ppjc1)
            except OSError:
                self.skipTest('pplus not initialized properly')

    def test_addJob4(self):
        with nostderr():
            # we suppress also some stdout from PPlus since we produce deliberate job errors
            with nostdout():
                try:
                    ppjc1 = PPlusJobContainer()
                    ppjc1.start()
                    jobIDs1 = [ppjc1.addJob(j, importable=True) for j in self.jobs3]
                    jobIDs2 = [ppjc1.addJob(j, importable=True) for j in self.jobs4]
                    ist1 = set([ppjc1.getJobStatus(jid) for jid in jobIDs1])
                    ist2 = set([ppjc1.getJobStatus(jid) for jid in jobIDs2])
                    ref_ist = set([JobStatus.EXECUTING])
                    self.assertEqual(ref_ist, ist1 & ist2)
                    ppjc1.close()
                    est1 = set([ppjc1.getJobStatus(jid) for jid in jobIDs1])
                    est2 = set([ppjc1.getJobStatus(jid) for jid in jobIDs2])
                    ref_est = set([JobStatus.FINISHED])
                    self.assertEqual(ref_est, est1 & est2)
                    res1 = [ppjc1.getJobResult(jid) for jid in jobIDs1]
                    res2 = [ppjc1.getJobResult(jid) for jid in jobIDs2]
                    for cns, r1 in res1:
                        self.assertEqual(JOBERROR.srepr, cns)
                        self.assertIsInstance(r1, BaseException)
                    ref_res2 = [[i * i for i in range(10) if i % 2 == 1]] * 10
                    self.assertEqual(ref_res2, res2)
                    ppjc1.clear()
                    _destroyPPlusServer(ppjc1)
                except OSError:
                    self.skipTest('pplus not initialized properly')

    def test_miscData1(self):
        with nostderr():
            try:
                ppjc1 = PPlusJobContainer()
                ppjc1.start()
                ppjc1.close()
                ppjc1.clear()
                md = ppjc1.getMiscData()
                for mdk in self.refMiscData1:
                    self.assertIn(mdk, md)
                refRootPath = os.path.join(TEST_INVARIANTS['test_write_root'], 'disk')
                rootp, _, edir = md['diskDataPath'].rpartition(os.path.sep)
                self.assertEqual(refRootPath, rootp)
                self.assertRegexpMatches(edir, '[a-f0-9]{16}')
                self.assertEqual(True, md['isDebug'])
                label, _, uid = md['experimentID'].rpartition('_')
                self.assertEqual('', label)
                self.assertRegexpMatches(uid, '[a-f0-9]{16}')
                self.assertEqual(edir, uid)
                _destroyPPlusServer(ppjc1)
            except OSError:
                self.skipTest('pplus not initialized properly')

    def test_postClose1(self):
        os.mkdir(self.destPath1)
        with nostderr():
            try:
                ppjc1 = PPlusJobContainer()
                ppjc1.start()
                j1 = Job(self.f0, self.arg0)
                jid1 = ppjc1.addJob(j1, importable=True)
                ppjc1.close()
                self.assertIsNone(ppjc1.getJobResult(jid1))
                ppjc1.clear()
                ppjc1.postClose(self.destPath1)
                dfiles = os.listdir(self.destPath1)
                self.assertEqual(2, len(dfiles))
                self.assertIn('experiment.log', dfiles)
                self.assertIn('master_session.log', dfiles)
                _destroyPPlusServer(ppjc1)
            except OSError:
                self.skipTest('pplus not initialized properly')
        shutil.rmtree(self.destPath1)
