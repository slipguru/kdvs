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
Provides high--level functionality for handling of computational jobs by KDVS.
"""

from kdvs.core.error import Warn, Error
from kdvs.core.util import quote, isListOrTuple, Constant
from kdvs.fw.Map import SetBDMap
import itertools
import os
import types
import uuid

NOTPRODUCED = Constant('NotProduced')
r"""
Constant used to signal when job produced no results.
"""

JOBERROR = Constant('JobError')
r"""
Constant used to signal when job ended with an error.
"""

DEFAULT_CALLARGS_LISTING_THR = 2
r"""
Default number of job arguments presented, used in job listings, logs, etc.
"""

class JobStatus(object):
    r"""
A container for constants that represent the state of the job during its lifecycle.
Also provides list of those statuses.
    """
    CREATED = Constant('CREATED')
    ADDED = Constant('ADDED')
    EXECUTING = Constant('EXECUTING')
    FINISHED = Constant('FINISHED')
    statuses = (CREATED, ADDED, EXECUTING, FINISHED)

class Job(object):
    r"""
High--level wrapper over computational job that KDVS manages. Job consists of
a function with arguments and possibly with some additional data. Newly created
Job is in the state of CREATED, and its results are NOTPRODUCED.
    """
    def __init__(self, call_func, call_args, additional_data={}):
        r"""
Parameters
----------
call_func : function
    function to be executed as computational job

call_args : list/tuple
    positional arguments for the function to be executed as computational job

additional_data : dict
    any additional data that are associated with the job

Raises
------
Error
    if proper job function was not specified
Error
    if proper list/tuple of job arguments was not specified
Error
    if additional data could not be accessed (in sense of dict.update)
        """
        if not isinstance(call_func, types.FunctionType):
            raise Error('Function expected! (got %s)' % call_func.__class__)
        if not isListOrTuple(call_args):
            raise Error('List or tuple expected! (got %s)' % call_args.__class__)
        self.call_func = call_func
        self.call_args = call_args
        self.additional_data = dict()
        try:
            self.additional_data.update(additional_data)
        except Exception, e:
            raise Error('Could not obtain job additional data! (Reason: %s)' % e)
        self.status = JobStatus.CREATED
        self.result = NOTPRODUCED

    def execute(self):
        r"""
Execute specified job function with specified arguments and return the result.
Job execution is considered successful if no exception has been raised during
running of job function.

Returns
-------
result : object
    Result of job function; jobs can also return :data:`JOBERROR` if necessary

Raises
------
Error
    if any exception was raised during an execution; essentially, reraise Error
    with the underlying details
        """
        try:
            return self.call_func(*self.call_args)
        except Exception, e:
            raise Error('Could not execute %s! (Reason: %s)' % (self.__class__.__name__, e))

    def __str__(self):
        if self.result != NOTPRODUCED:
            res = "PRODUCED"
        else:
            res = str(NOTPRODUCED)
        try:
            cfunc = quote(self.call_func.__name__)
        except:
            cfunc = "<Function>"
        if len(self.call_args) <= DEFAULT_CALLARGS_LISTING_THR:
            cargs = 'args: %s' % str(self.call_args)
        else:
            cargs = "args: >%s" % DEFAULT_CALLARGS_LISTING_THR
        jobstr = "<Job (%s with %s) (Status: %s, Result: %s)>" % (cfunc, cargs, self.status, res)
        return jobstr

    def __repr__(self):
        return self.__str__()


class JobContainer(object):
    r"""
An abstract container that manages jobs. Must be subclassed.
    """
    def __init__(self, incrementID=False):
        r"""
Parameters
----------
incrementID : boolean
    if True, each new job receives simple integer as its ID: 1,2,3,...; if False,
    each new job receives more complex UUID type 4 as its ID

See Also
--------
uuid
        """
        if incrementID:
            self._count = itertools.count()
            self._idgen = self._generateIncrementJobID
        else:
            self._idgen = self._generateUUIDJobID
        self.jobs = dict()
        self.miscData = dict()

    def addJob(self, job, **kwargs):
        r"""
Add job to the execution queue and schedule for execution. Job changes its status to ADDED.

Parameters
----------
job : :class:`Job`
    job to be added

kwargs : dict
    any additional keyword arguments; used in subclasses for finer control

Returns
-------
jobID : string
    identifier assigned to the new job
        """
        jobID = self._idgen()
        job.status = JobStatus.ADDED
        self.jobs[jobID] = job
        return jobID

    def getJobCount(self):
        r"""
Return number of jobs currently managed by this container. NOTE: this method
does not differentiate between executed and not executed jobs.
        """
        return len(self.jobs)

    def hasJobs(self):
        r"""
Return True if container manages any jobs, False otherwise.
        """
        return self.getJobCount() > 0

    def getJob(self, jobID):
        r"""
Return instance of Job by its jobID.

Parameters
----------
jobID : string
    job ID

Returns
-------
job : :class:`Job`
    job with requested ID, if exists
        """
        return self._job(jobID)

    def getJobStatus(self, jobID):
        r"""
Return status of requested job.

Parameters
----------
jobID : string
    job ID

Returns
-------
status : one of :attr:`JobStatus.statuses`
    status of job with requested ID, if exists
        """
        return self._job(jobID).status

    def getJobResult(self, jobID):
        r"""
Return results produced by requested job. May be NOTPRODUCED.

Parameters
----------
jobID : string
    job ID

Returns
-------
result : object
    result of job with requested ID, if exists
        """
        return self._job(jobID).result

    def removeJob(self, jobID):
        r"""
Remove requested job from this manager.

Parameters
----------
jobID : string
    job ID

Raises
------
Warn
    if the job is not yet executed and/or finished
Warn
    if the job has unrecognized status
        """
        jobStatus = self.getJobStatus(jobID)
        if jobStatus == JobStatus.FINISHED:
            del self.jobs[jobID]
        elif jobStatus == JobStatus.EXECUTING:
            raise Warn('The job is not yet finished!')
        elif jobStatus == JobStatus.ADDED:
            raise Warn('The job is not yet executed!')
        else:
            st = ','.join([quote(s) for s in JobStatus.statuses])
            raise Error('Unknown job status! (got %s) (shall be %s)' % (jobStatus, st))

    def clear(self):
        r"""
Remove all jobs from this container.
        """
        self.jobs.clear()

    def start(self):
        r"""
Must be implemented in subclass.
        """
        raise NotImplementedError('Must be implemented in subclass!')

    def close(self):
        r"""
Typically implemented in subclass to clean after itself. By default it does nothing.
        """
        # implemented by subclasses
        pass

    def postClose(self, destPath, *args):
        r"""
Used by subclasses. Currently used only in 'experiment' application. By default
it checks if given destination path exists.
        """
        # overloaded by subclasses
        # by default it checks if given destination path exists
        if not os.path.exists(destPath):
            raise Error('Destination path "%s" does not exist!' % destPath)

    def getMiscData(self):
        r"""
Return any miscellaneous data associated with this container. Typically, subclasses
add some to improve job management or provide some debug information.
        """
        return self.miscData

    def clearMiscData(self):
        r"""
Remove any miscellaneous data associated with this container.
        """
        self.miscData.clear()

    def _generateIncrementJobID(self):
        return 'Job%d' % self._count.next()

    def _generateUUIDJobID(self):
        return uuid.uuid4().hex

    def _job(self, jobID):
        return self.jobs[jobID]


class JobGroupManager(object):
    r"""
Simple manager of groups of jobs. Can be used for finer execution control and
to facilitate reporting.
    """
    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    any keyworded arguments that may be used by the user for finer control (e.g.
    in sublass); currently, no arguments are used
        """
        self._jgmap = SetBDMap()

    def addJobIDToGroup(self, group_name, jobID):
        r"""
Add requested job to specified job group. If group was not defined before, it will
be created.

Parameters
----------
group_name : string
    name of the group

jobID : string
    job ID
        """
        self._jgmap[group_name] = jobID

    def addGroup(self, group_name, group_job_ids):
        r"""
Add series of jobs to specified job group (shortcut). If group was not defined before, it will
be created.

Parameters
----------
group_name : string
    name of the group

group_job_ids : iterable of string
    job IDs
        """
        for jid in group_job_ids:
            self.addJobIDToGroup(group_name, jid)

    def remGroup(self, group_name):
        r"""
Remove specified job group from this manager. All associated job IDs are removed as
well. NOTE: physical jobs are left intact.

Parameters
----------
group_name : string
    name of the group
        """
        del self._jgmap[group_name]

    def clear(self):
        r"""
Removes all job groups from this manager.
        """
        self._jgmap.clear()

    def getGroupJobsIDs(self, group_name):
        r"""
Get list of job IDs associated with specified job group name.

Parameters
----------
group_name : string
    name of the group

Returns
-------
jobIDs : iterable of string
    all job IDs from requested group, if exists
        """
        return list(self._jgmap.getFwdMap()[group_name])

    def findGroupByJobID(self, jobID):
        r"""
Identify job group of the requested job ID.

Parameters
----------
jobID : string
    job ID

Returns
-------
group_name : string
    name of the group with requested job, if exists

Raises
------
Error
    if jobID is found in more than one group
        """
        gr = self._jgmap.getBwdMap()[jobID]
        if len(gr) > 1:
            # should not happen with SetBDMap but to be safe...
            raise Error('Job shall be internally assigned to single group! (got %s)' % gr)
        # return single element from the set
        return next(iter(gr))

    def getGroups(self):
        r"""
Get list of all job group names managed by this manager.
        """
        return self._jgmap.getFwdMap().keys()
