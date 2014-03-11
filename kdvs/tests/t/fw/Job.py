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

from kdvs.core.error import Error, Warn
from kdvs.fw.Job import Job, JobContainer, NOTPRODUCED, JobStatus, \
    JobGroupManager
from kdvs.fw.Map import SetBDMap
from kdvs.tests import resolve_unittest, TEST_INVARIANTS
import copy
import os
import re

unittest = resolve_unittest()

def _f0():
    return 0

def _f1(*args):
    return sum(args)

def _f2():
    pass

class TestJob1(unittest.TestCase):

    def setUp(self):
        self.f0 = _f0
        self.f1 = _f1
        self.f2 = _f2
        self.arg0 = ()
        self.arg1 = (1, 2, 3, 4)

    def test_init1(self):
        job0 = Job(call_func=self.f0, call_args=self.arg0)
        self.assertEqual(self.f0, job0.call_func)
        self.assertEqual(self.arg0, job0.call_args)
        job1 = Job(call_func=self.f0, call_args=self.arg1)
        self.assertEqual(self.f0, job1.call_func)
        self.assertEqual(self.arg1, job1.call_args)
        self.assertEqual(JobStatus.CREATED, job0.status)
        self.assertEqual(NOTPRODUCED, job0.result)

    def test_init2(self):
        with self.assertRaises(Error):
            Job(call_func=None, call_args=None)
        with self.assertRaises(Error):
            Job(call_func=None, call_args=self.arg0)
        with self.assertRaises(Error):
            Job(call_func=self.f0, call_args=None)
        with self.assertRaises(TypeError):
            Job(call_func=self.f0)
        with self.assertRaises(TypeError):
            Job(call_args=self.arg0)

    def test_execute1(self):
        job1 = Job(self.f0, self.arg0)
        self.assertEqual(0, job1.execute())
        job2 = Job(self.f0, self.arg1)
        with self.assertRaises(Error):
            job2.execute()
        job3 = Job(self.f1, self.arg0)
        self.assertEqual(0, job3.execute())
        job4 = Job(self.f1, self.arg1)
        self.assertEqual(10, job4.execute())
        job5 = Job(self.f2, self.arg0)
        self.assertIsNone(job5.execute())
        job6 = Job(self.f2, self.arg1)
        with self.assertRaises(Error):
            job6.execute()

class TestJobContainer1(unittest.TestCase):

    def setUp(self):
        self.test_write_root = TEST_INVARIANTS['test_write_root']
        self.f0 = _f0
        self.arg0 = ()
        self.jobs = [Job(call_func=self.f0, call_args=self.arg0) for _ in range(10)]
        self.ref_increment_ids = ['Job%d' % i for i in range(10)]
        self.miscData1 = {'experimentID' : 'exp1'}
        self.destPath1 = self.test_write_root
        self.destPath2 = os.path.join(self.test_write_root, 'AAAAA')

    def test_init1(self):
        jc = JobContainer()
        self.assertEqual({}, jc.jobs)
        self.assertEqual({}, jc.miscData)

    def test_addJob1(self):
        jc = JobContainer(incrementID=False)
        for j in self.jobs:
            jc.addJob(j)
        self.assertTrue(all([re.match("[0-9a-f]{16}", k) for k in jc.jobs.keys()]))

    def test_addJob2(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        ref_ids = set(self.ref_increment_ids)
        ids = set(jc.jobs.keys())
        self.assertEqual(ref_ids, ids)

    def test_hasJobs1(self):
        jc = JobContainer(incrementID=True)
        self.assertFalse(jc.hasJobs())

    def test_hasJobs2(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        self.assertTrue(jc.hasJobs())

    def test_getJob1(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        j5 = jc.getJob('Job5')
        self.assertEqual(j5, self.jobs[5])

    def test_getJob2(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        with self.assertRaises(KeyError):
            jc.getJob('JobXXX')

    def test_getJobStatus1(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        for jid in self.ref_increment_ids:
            self.assertEqual(JobStatus.ADDED, jc.getJobStatus(jid))

    def test_getJobResults1(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        for jid in self.ref_increment_ids:
            self.assertEqual(NOTPRODUCED, jc.getJobResult(jid))

    def test_removeJob1(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        self.assertEqual(JobStatus.ADDED, jc.jobs['Job1'].status)
        with self.assertRaises(Warn):
            jc.removeJob('Job1')
        jc.jobs['Job1'].status = JobStatus.FINISHED
        jc.removeJob('Job1')
        ref_job_ids = set(['Job%d' % i for i in [0, 2, 3, 4, 5, 6, 7, 8, 9]])
        job_ids = set(jc.jobs.keys())
        self.assertEqual(ref_job_ids, job_ids)

    def test_removeJob2(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        self.assertEqual(JobStatus.ADDED, jc.jobs['Job1'].status)
        jc.jobs['Job1'].status = JobStatus.EXECUTING
        with self.assertRaises(Warn):
            jc.removeJob('Job1')
        jc.jobs['Job1'].status = JobStatus.FINISHED
        jc.removeJob('Job1')
        ref_job_ids = set(['Job%d' % i for i in [0, 2, 3, 4, 5, 6, 7, 8, 9]])
        job_ids = set(jc.jobs.keys())
        self.assertEqual(ref_job_ids, job_ids)

    def test_removeJob3(self):
        jc = JobContainer(incrementID=True)
        for j in self.jobs:
            jc.addJob(j)
        self.assertEqual(JobStatus.ADDED, jc.jobs['Job1'].status)
        jc.jobs['Job1'].status = 'XXXXXXXXXXX'
        with self.assertRaises(Error):
            jc.removeJob('Job1')
        jc.jobs['Job1'].status = JobStatus.FINISHED
        jc.removeJob('Job1')
        ref_job_ids = set(['Job%d' % i for i in [0, 2, 3, 4, 5, 6, 7, 8, 9]])
        job_ids = set(jc.jobs.keys())
        self.assertEqual(ref_job_ids, job_ids)

    def test_clear1(self):
        jc = JobContainer(incrementID=True)
        self.assertEqual(0, len(jc.jobs))
        jc.clear()
        self.assertEqual(0, len(jc.jobs))
        for j in self.jobs:
            jc.addJob(j)
        self.assertEqual(10, len(jc.jobs))
        jc.clear()
        self.assertEqual(0, len(jc.jobs))

    def test_miscData1(self):
        jc = JobContainer(incrementID=True)
        jc.miscData['experimentID'] = 'exp1'
        self.assertEqual(self.miscData1, jc.getMiscData())
        jc.clearMiscData()
        self.assertEqual({}, jc.getMiscData())

    def test_postClose1(self):
        jc = JobContainer(incrementID=True)
        jc.postClose(self.destPath1)
        with self.assertRaises(Error):
            jc.postClose(self.destPath2)


class TestJobGroupManager1(unittest.TestCase):

    def setUp(self):
        self.all_job_ids = ['Job%d' % i for i in range(100)]
        # construct ten groups
        self.groups1 = dict([(gk, set()) for gk in range(10)])
        for i, jobID in enumerate(self.all_job_ids):
            self.groups1[i % 10].add(jobID)
        self.groups2 = copy.copy(self.groups1)
        del self.groups2[5]
        self.lookup_jobs = ['Job66', 'Job35', 'Job7']
        self.lookup_jobs_groups = [6, 5, 7]

    def test_init1(self):
        jgm = JobGroupManager()
        self.assertIsInstance(jgm._jgmap, SetBDMap)
        self.assertItemsEqual({}, jgm._jgmap.getFwdMap())
        self.assertItemsEqual({}, jgm._jgmap.getBwdMap())

    def test_addJobIDToGroup1(self):
        jgm = JobGroupManager()
        for i, jid in enumerate(self.all_job_ids):
            jgm.addJobIDToGroup(i % 10, jid)
        ref_groups = range(10)
        self.assertItemsEqual(ref_groups, jgm.getGroups())
        for g in ref_groups:
            group_jobs = jgm.getGroupJobsIDs(g)
            self.assertItemsEqual(self.groups1[g], group_jobs)

    def test_addGroup1(self):
        jgm = JobGroupManager()
        for g in range(10):
            group_jobs = [jid for (i, jid) in enumerate(self.all_job_ids) if i % 10 == g]
            jgm.addGroup(g, group_jobs)
        ref_groups = range(10)
        self.assertItemsEqual(ref_groups, jgm.getGroups())
        for g in ref_groups:
            group_jobs = jgm.getGroupJobsIDs(g)
            self.assertItemsEqual(self.groups1[g], group_jobs)

    def test_remGroup1(self):
        jgm = JobGroupManager()
        for g in range(10):
            group_jobs = [jid for (i, jid) in enumerate(self.all_job_ids) if i % 10 == g]
            jgm.addGroup(g, group_jobs)
        jgm.remGroup(5)
        ref_groups = range(10)
        ref_groups.remove(5)
        self.assertItemsEqual(ref_groups, jgm.getGroups())
        for g in ref_groups:
            group_jobs = jgm.getGroupJobsIDs(g)
            self.assertItemsEqual(self.groups2[g], group_jobs)

    def test_findGroupByJobID1(self):
        jgm = JobGroupManager()
        for g in range(10):
            group_jobs = [jid for (i, jid) in enumerate(self.all_job_ids) if i % 10 == g]
            jgm.addGroup(g, group_jobs)
        lookup_groups = [jgm.findGroupByJobID(ljid) for ljid in self.lookup_jobs]
        self.assertEqual(self.lookup_jobs_groups, lookup_groups)

    def test_clear1(self):
        jgm = JobGroupManager()
        for g in range(10):
            group_jobs = [jid for (i, jid) in enumerate(self.all_job_ids) if i % 10 == g]
            jgm.addGroup(g, group_jobs)
        jgm.clear()
        self.assertItemsEqual({}, jgm._jgmap.getFwdMap())
        self.assertItemsEqual({}, jgm._jgmap.getBwdMap())
