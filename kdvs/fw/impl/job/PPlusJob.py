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
Provides concrete implementation of the job container that uses PPlus library
(https://bitbucket.org/slipguru/pplus). IMPORTANT NOTE: this job container works
only with PPlus v0.5.2.
"""

from kdvs import ROOT_IMPORT_PATH
from kdvs.core.dep import verifyDepModule
from kdvs.core.error import Error
from kdvs.core.util import serializeObj, deserializeObj, importComponent
from kdvs.fw.Job import JobContainer, JobStatus, JOBERROR
import copy
import os
import re
import shutil
import socket
import sys
import time
try:
    import pplus
    from pplus import PPlusError
except ImportError:
    pass

# keys: <jobID>_IN | <jobID>_OUT
_KEY2JOBID_PATT = re.compile('([a-zA-Z0-9]+)_(IN|OUT)')
r"""
Regular expression of the file with raw input and raw output for each job.
"""

# wrapper executed on worker machine
def _pplusJobWrapper(pc, input_key, output_key, job_error_signal):
    # reconstruct input data
    with open(pc.get_path(input_key), 'rb') as in_fh:
        jobwrap = deserializeObj(in_fh)
    # reconstruct call func
    call_module = jobwrap['callmodule']
    call_name = jobwrap['callname']
    if call_module is not None:
        # importable job, from one of submitted modules
        # find requested module and get the function
        import sys
        module = sys.modules[call_module]
        call_func = getattr(module, call_name)
    else:
        # just find the call
        try:
            call_func = globals()[call_name]
        except KeyError:
            try:
                call_func = locals()[call_name]
            except KeyError:
                pc.session_logger.error('%s not found in expected scope!' % call_name)
                pc.session_logger.error(globals())
                pc.session_logger.error(locals())
    call_args = jobwrap['callargs']
    # execute call
    try:
        call_result = call_func(*call_args)
    except BaseException, e:
        call_result = (job_error_signal, e)
        raise e
    finally:
        # serialize output data
        with pc.write_remotely(output_key, binary=True) as out_fh:
            serializeObj(call_result, out_fh, protocol=None)


class PPlusJobContainer(JobContainer):
    r"""
Job container that uses PPlus v0.5.2. During instantiation, all parameters except
'incrementID', are passed directly to 'pplus.PPlusConnection'. Refer to the PPlus
documentation for more details.

See Also
--------
pplus.PPlusConnection
    """

    def __init__(self, **kwargs):
        r"""
Parameters
----------
kwargs : dict
    keyworded parameters passed directly to PPlusConnection, except 'incrementID'
    (if present)
        """
        verifyDepModule('pplus')
        # process one argument explicitly
        try:
            incrementID = kwargs['incrementID']
            del kwargs['incrementID']
        except KeyError:
            incrementID = True
        # check if there are no more arguments
        if len(kwargs) == 0:
            # local connection with minimum workers allocated
            self.pconn = pplus.PPlusConnection(debug=True, local_workers_number=1)
        else:
            # if not, everything else goes to PPlusConnection
            self.pconn = pplus.PPlusConnection(**kwargs)
        super(PPlusJobContainer, self).__init__(incrementID)
        self.submitted = list()
        self._exceptions = list()
        self.miscData['experimentID'] = self.pconn.id
        self.miscData['sessionID'] = self.pconn.session_id
        self.miscData['diskDataPath'] = self.pconn.disk_path
        self.miscData['diskCachePath'] = self.pconn.cache_path
        self.miscData['isDebug'] = self.pconn.is_debug

    def start(self):
        r"""
By default, provide some time for auto--discovery of Parallel Python to warm up
(by sleeping for 5 secs).

See Also
--------
time.sleep
        """
        # provide some time for pp auto-discovery
        time.sleep(5)

    def addJob(self, job, importable=False):
        r"""
The job is added to Parallel Python queue and then executed based on internal
Parallel Python scheduler. Once added, its status is changed to EXECUTING. The
job is actually passed as 'depfunc', together with its name, found in proper scope
on worker machine, and executed there. NOTE: earlier versions of PPlus will raise
an exception here since they require submission of job as callable, not as name.

Parameters
----------
job : :class:`~kdvs.fw.Job.Job`
    job to be executed by this container

importable : boolean
    the job may be self--contained (i.e. does not use any external libraries) or
    it can use the external code that is already installed (in the sense of
    importable Python module) on worker machine; in the first case, the job is
    said to be 'not importable', in the second case the job is 'importable';
    True if the job is importable, False if not; False by default
        """
        # add job to container
        jobID = super(PPlusJobContainer, self).addJob(job)
        # prepare depfuncs and modules
        try:
            depfuncs = list(job.additional_data['depfuncs'])
        except KeyError:
            depfuncs = list()
        try:
            modules = list(job.additional_data['modules'])
        except KeyError:
            modules = list()
        # modules for use by job wrapper
        modules.extend(['sys', 're'])
        # depfuncs to use by job wrapper
        depfuncs.extend([serializeObj, deserializeObj])

        # prepare jobwrap instance
        jobwrap = dict()
        # make deep copy of call arguments
        jobwrap['callargs'] = self._copy_args(job.call_args)
        jobwrap['jobdata'] = dict()
        # resolve job call handling
        call_name = job.call_func.__name__
        if importable:
            # if job is to be importable on worker machine, we submit correct module and call name
            call_module = job.call_func.__module__
            modules.append(call_module)
            jobwrap['callmodule'] = call_module
        else:
            # otherwise we add call itself as depfunc
            # first import module that contains the call
            call_module = importComponent(job.call_func.__module__)
            # find requested function
            call_func = getattr(call_module, call_name)
            # make call visible to PP for adding as depfunc
            callpath = os.path.abspath(os.path.join(ROOT_IMPORT_PATH, call_func.__module__))
            sys.path.insert(0, callpath)
            # request call to be added as depfunc
            depfuncs.append(call_func)
            jobwrap['callmodule'] = None

        jobwrap['callname'] = call_name

        # serialize jobwrap as input object
        input_key = self.getJobInputKey(jobID)
        with self.pconn.write_remotely(input_key, binary=True) as out_fh:
            serializeObj(jobwrap, out_fh)
# DEBUG
#        with self.pconn.write_remotely(input_key + '.txt', binary=True) as outtxt:
#            pprintObj(jobwrap, outtxt)
# DEBUG
        # obtain output key for this job
        output_key = self.getJobOutputKey(jobID)
        # obtain job error signal
        job_error_signal = JOBERROR.srepr
        # make job wrapper call visible to PP for adding as depfunc
        wrapperpath = os.path.abspath(os.path.dirname(__file__))
        sys.path.insert(0, wrapperpath)
        # request job wrapper to be added as depfunc
        depfuncs.append(_pplusJobWrapper)
        # physical submission
        # NOTE: we submit function NAME here, not function itself; since
        # depfuncs are 'exec'-uted by PP before resolving of actual job call,
        # PPlus may perform the lookup of function object in globals()/locals()
        # by name
        self.pconn.submit(_pplusJobWrapper.func_name,
                          args=(input_key, output_key, job_error_signal),
                          depfuncs=tuple(depfuncs),
                          modules=tuple(modules))
        # we are done here, remove wrapper path
        sys.path.pop(0)
        # we are done here, remove call path
        if not importable:
            sys.path.pop(0)
        # finish submission in job container
        self.submitted.append(jobID)
        self._job(jobID).status = JobStatus.EXECUTING
        return jobID

    def getJobInputKey(self, jobID):
        r"""
Get PPlus key for the file that contains job raw input for the specific job.

Parameters
----------
jobID : string
    identifier of already added job

Returns
-------
key : string
    PPlus key for the requested file

Notes
-----
See 'File key' in PPlus documentation
        """
        return '%s_IN' % jobID

    def getJobOutputKey(self, jobID):
        r"""
Get PPlus key for the file that contains job raw output for the specific job.

Parameters
----------
jobID : string
    identifier of already added job

Returns
-------
key : string
    PPlus key for the requested file

Notes
-----
See 'File key' in PPlus documentation
        """
        return '%s_OUT' % jobID

    def getJobIDForKey(self, filekey):
        r"""
Get identifier of the job for specific PPlus file key.

Parameters
----------
key : string
    PPlus key for the requested file (input/output)

Returns
-------
jobID : string
    identifier of already added job that is associated with requested file key

Notes
-----
See 'File key' in PPlus documentation
        """
        return _KEY2JOBID_PATT.match(filekey).groups()[0]

    def close(self):
        r"""
Collect all raw results from jobs already added. Blocking call.

Returns
-------
exceptions : tuple of tuples
    tuple of the following tuples ('PPlusJobs', e), where 'e' is the instance
    of `PPlusError` generated during execution of jobs; the exception instance
    contains the details of the error, including identifier of the job that failed;
    note that some jobs may still finish normally, so the length of this tuple may vary

See Also
--------
PPlusConnection.collect
PPlusError
        """
        super(PPlusJobContainer, self).close()
        self._collect()
        return self._exceptions

    def postClose(self, destPath, *args):
        r"""
Perform the following operations AFTER the container has been close()d: copy
'experiment.log' to results sublocation specified with file system directory path
'destPath', and copy 'master session' log to the same sublocation.

See Also
--------
kdvs.fw.StorageManager.StorageManager

Notes
-----
See 'PPlus logging' in PPlus documentation
        """
        super(PPlusJobContainer, self).postClose(destPath)
        # copy main log "experiment.log" to destination
        ddpath = self.miscData['diskDataPath']
        explog_path = os.path.join(ddpath, 'experiment.log')
        shutil.copy(explog_path, destPath)
        # copy main cache log from master machine "<>.master.<>.log" to destination
        cpath = self.miscData['diskCachePath']
        wmasterlog_path = os.path.join(cpath, 'logs', '%s.%s.%s.log' % (
                                                    socket.gethostname(),
                                                    'master',
                                                    self.miscData['sessionID']))
        dmaster_path = os.path.join(destPath, 'master_session.log')
        shutil.copy(wmasterlog_path, dmaster_path)


    def _collect(self):
#        # blocking call
        try:
            self.pconn.collect()
            for jobID in self.submitted:
                self.jobs[jobID].status = JobStatus.FINISHED
                output_key = self.getJobOutputKey(jobID)
                with open(self.pconn.get_path(output_key), 'rb') as in_fh:
                    finalResult = deserializeObj(in_fh)
#                with self.pconn.write_remotely(output_key, binary=True) as out_fh:
#                    serializeObj(res, out_fh, protocol=None)
                self.jobs[jobID].result = finalResult
        except PPlusError, e:
            for jobID in self.submitted:
                self.jobs[jobID].status = JobStatus.FINISHED
            self._exceptions.append(('PPlusJobs', e))

    def __del__(self):
        try:
            if self.pconn._server is not None:
                self.pconn._server.destroy()
        except:
            pass

    def _copy_args(self, ar):
        return copy.deepcopy(ar)
