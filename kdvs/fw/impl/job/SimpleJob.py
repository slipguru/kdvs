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
Provides simple 'null' job container that executes jobs as ordinary callables
in the order of submission; no parallel execution mechanisms are used. It requires
no external libraries.
"""

from kdvs.core.error import Error
from kdvs.core.util import isListOrTuple
from kdvs.fw.Job import JobContainer, JobStatus

class SimpleJobContainer(JobContainer):
    r"""
Simple 'null' job container. It recognizes single parameter 'incrementID'; if not
present, it is assumed to be True.
    """
    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones
        """
        # we recognize only one argument here
        try:
            incrementID = kwargs['incrementID']
        except KeyError:
            incrementID = True
        super(SimpleJobContainer, self).__init__(incrementID)
        self.joblist = list()
        self._exceptions = None

    def addJob(self, job, **kwargs):
        r"""
The job is added to internal list.

Parameters
----------
job : :class:`~kdvs.fw.Job.Job`
    job to be executed by this container

kwargs : dict
    any other arguments; not used
        """
        jobID = super(SimpleJobContainer, self).addJob(job)
        self.joblist.append((jobID, job))
        return jobID

    def start(self):
        r"""
Finish job submission stage and execute already added jobs, in the order of adding.
Blocking call.
        """
        self._exceptions = list()
        for jobID, jobObj in self.joblist:
            self.jobs[jobID].status = JobStatus.EXECUTING
            try:
                # blocking call
                result = jobObj.execute()
                self.jobs[jobID].status = JobStatus.FINISHED
                self.jobs[jobID].result = result
            except Exception, e:
                self.jobs[jobID].status = JobStatus.FINISHED
                self._exceptions.append((jobID, e))

    def close(self):
        r"""
Finish execution stage and return any exceptions raised during execution.

Returns
-------
exception : tuple of tuples
    tuple of the following tuples: (jobID, e), where 'jobID' is the identifier
    of the failed job, and 'e' is an instance of Exception that was raised during
    execution; note that some jobs may still finish correctly so the length of
    this tuple may vary
        """
        super(SimpleJobContainer, self).close()
        return self._exceptions

    def postClose(self, destPath, *args):
        r"""
Do nothing in post--closing stage.
        """
        super(SimpleJobContainer, self).postClose(destPath)


class SimpleJobExecutor(object):
    r"""
Convenient wrapper for an iterable of jobs that creates simple job container which
executes them.
    """
    def __init__(self, jobs_to_execute):
        r"""
Parameters
----------
jobs_to_execute : iterable of :class:`~kdvs.fw.Job.Job`
    jobs to be executed

Raises
------
Error
    if iterable is incorrectly specified
        """
        if not isListOrTuple(jobs_to_execute):
            raise Error('List or tuple expected! (got %s)' % jobs_to_execute.__class__)
        self.jobs_to_execute = jobs_to_execute

    def run(self):
        r"""
Create an instance of SimpleJobContainer, add requested jobs, and execute them.
        """
        self.sjc = SimpleJobContainer()
        self.jobIDs = [self.sjc.addJob(j) for j in self.jobs_to_execute]
        self.sjc.start()

    def close(self):
        r"""
Close simple job container and return any exceptions raised during execution.

See Also
--------
SimpleJobContainer.close
        """
        exc = self.sjc.close()
        return exc

    def getJobResults(self):
        r"""
Get iterable of all job results for executed jobs.

See Also
--------
JobContainer.getJobResults
        """
        return [self.sjc.getJobResult(jid) for jid in self.jobIDs]
