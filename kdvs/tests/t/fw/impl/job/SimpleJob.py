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

from kdvs.core.error import Error
from kdvs.fw.Job import NOTPRODUCED, Job
from kdvs.fw.impl.job.SimpleJob import SimpleJobContainer, SimpleJobExecutor
from kdvs.tests import resolve_unittest
import re
import time

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

class TestSimpleJobContainer1(unittest.TestCase):

    def setUp(self):
        self.f0 = _f0
        self.f1 = _f1
        self.f2 = _f2
        self.f3 = _f3
        self.f4 = _f4
        self.arg0 = ()
        self.arg1 = (1, 2, 3, 4)
        self.arg2 = [0.5, 1, 2, 3, 4]
        self.arg3 = [0.5]
        self.arg4 = [i for i in range(10) if i % 2 == 1]  # 1 3 5 7 9
        self.ref_increment_ids = ['Job%d' % i for i in range(10)]
        self.jobs0 = [Job(self.f0, self.arg0) for _ in range(10)]
        self.jobs1 = [Job(self.f1, self.arg1) for _ in range(10)]
        self.jobs2 = [Job(self.f2, self.arg2) for _ in range(10)]
        self.jobs3 = [Job(self.f3, self.arg3) for _ in range(10)]
        self.jobs4 = [Job(self.f4, self.arg4) for _ in range(10)]

    def test_init1(self):
        sjc1 = SimpleJobContainer()
        self.assertEqual([], sjc1.joblist)
        self.assertEqual({}, sjc1.jobs)

    def test_addJob1(self):
        jc = SimpleJobContainer(incrementID=False)
        for j in self.jobs0:
            jc.addJob(j)
        self.assertTrue(all([re.match("[0-9a-f]{16}", k) for k in jc.jobs.keys()]))

    def test_addJob2(self):
        jc = SimpleJobContainer(incrementID=True)
        for j in self.jobs0:
            jc.addJob(j)
        ref_ids = set(self.ref_increment_ids)
        ids = set(jc.jobs.keys())
        self.assertEqual(ref_ids, ids)

    def test_start1(self):
        jc = SimpleJobContainer(incrementID=True)
        for j in self.jobs0:
            jc.addJob(j)
        jc.start()
        exc = jc.close()
        res = [jc.getJobResult(jid) for jid in self.ref_increment_ids]
        for r in res:
            self.assertIsNone(r)
        for ref_jid, (jid, ex) in zip(self.ref_increment_ids, exc):
            self.assertEqual(ref_jid, jid)
            self.assertIsInstance(ex, Error)
        jc.clear()

    def test_start2(self):
        jc = SimpleJobContainer(incrementID=True)
        for j in self.jobs1:
            jc.addJob(j)
        jc.start()
        exc = jc.close()
        res = [jc.getJobResult(jid) for jid in self.ref_increment_ids]
        ref_res = set([10])
        self.assertEqual(ref_res, set(res))
        self.assertEqual([], exc)
        jc.clear()

    def test_start3(self):
        jc = SimpleJobContainer(incrementID=True)
        for j in self.jobs2:
            jc.addJob(j)
        jc.start()
        exc = jc.close()
        res = [jc.getJobResult(jid) for jid in self.ref_increment_ids]
        ref_res = set([10])
        self.assertEqual(ref_res, set(res))
        self.assertEqual([], exc)
        jc.clear()

    def test_start4(self):
        jc = SimpleJobContainer(incrementID=True)
        for j in self.jobs3:
            jc.addJob(j)
        jc.start()
        exc = jc.close()
        res = [jc.getJobResult(jid) for jid in self.ref_increment_ids]
        for r in res:
            self.assertEqual(NOTPRODUCED, r)
        for ref_jid, (jid, ex) in zip(self.ref_increment_ids, exc):
            self.assertEqual(ref_jid, jid)
            self.assertIsInstance(ex, Error)
        jc.clear()

    def test_start5(self):
        jc = SimpleJobContainer(incrementID=True)
        for j in self.jobs4:
            jc.addJob(j)
        jc.start()
        exc = jc.close()
        res = [jc.getJobResult(jid) for jid in self.ref_increment_ids]
        ref_res = [[i * i for i in range(10) if i % 2 == 1] for _ in range(10)]
        self.assertEqual(ref_res, res)
        self.assertEqual([], exc)
        jc.clear()


class TestSimpleJobExecutor1(unittest.TestCase):

    def setUp(self):
        self.f0 = _f0
        self.f1 = _f1
        self.f2 = _f2
        self.f3 = _f3
        self.f4 = _f4
        self.arg0 = ()
        self.arg1 = (1, 2, 3, 4)
        self.arg2 = [2, 1, 2, 3, 4]
        self.arg3 = [1]
        self.arg4 = [i for i in range(10) if i % 2 == 1]  # 1 3 5 7 9
        self.ref_increment_ids = ['Job%d' % i for i in range(10)]
        self.jobs0 = [Job(self.f0, self.arg0) for _ in range(10)]
        self.jobs1 = [Job(self.f1, self.arg1) for _ in range(10)]
        self.jobs2 = [Job(self.f2, self.arg2) for _ in range(10)]
        self.jobs3 = [Job(self.f3, self.arg3) for _ in range(10)]
        self.jobs4 = [Job(self.f4, self.arg4) for _ in range(10)]

    def test_init1(self):
        jex = SimpleJobExecutor(self.jobs0)
        self.assertEqual(self.jobs0, jex.jobs_to_execute)

    def test_init2(self):
        with self.assertRaises(TypeError):
            SimpleJobExecutor()

    def test_run1(self):
        jex = SimpleJobExecutor(self.jobs0)
        jex.run()
        exc = jex.close()
        res = jex.getJobResults()
        for r in res:
            self.assertIsNone(r)
        for ref_jid, (jid, ex) in zip(self.ref_increment_ids, exc):
            self.assertEqual(ref_jid, jid)
            self.assertIsInstance(ex, Error)

    def test_run2(self):
        jex = SimpleJobExecutor(self.jobs1)
        jex.run()
        exc = jex.close()
        res = jex.getJobResults()
        ref_res = set([10])
        self.assertEqual(ref_res, set(res))
        self.assertSequenceEqual([], exc)

    def test_run3(self):
        jex = SimpleJobExecutor(self.jobs2)
        jex.run()
        exc = jex.close()
        res = jex.getJobResults()
        ref_res = set([10])
        self.assertEqual(ref_res, set(res))
        self.assertSequenceEqual([], exc)

    def test_run4(self):
        jex = SimpleJobExecutor(self.jobs3)
        jex.run()
        exc = jex.close()
        res = jex.getJobResults()
        for r in res:
            self.assertEqual(NOTPRODUCED, r)
        for ref_jid, (jid, ex) in zip(self.ref_increment_ids, exc):
            self.assertEqual(ref_jid, jid)
            self.assertIsInstance(ex, Error)

    def test_run5(self):
        jex = SimpleJobExecutor(self.jobs4)
        jex.run()
        exc = jex.close()
        res = jex.getJobResults()
        ref_res = [[i * i for i in range(10) if i % 2 == 1] for _ in range(10)]
        self.assertEqual(ref_res, res)
        self.assertEqual([], exc)
