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
Checks PPlus jobs for completion. See 'pplus_job_verifier.py -h' for help.
"""

from kdvs.core.util import deserializeObj
import collections
import optparse
import os
import re

def main():

    # this file is to be found
    exp_log_file_name = 'experiment.log'

    # output file name of this script
    output_file_name = 'pplus_job_verifier_output.txt'

# 2013-04-04 18:24:19,942 - pplus - compbio - DEBUG - Task (remote) 8 started on 10.251.61.233:60000
    log_line_job_start_patt = re.compile('^.*Task (?:\(remote)\)? (\d+) started on (.*\:.*)$')
# 2013-04-04 18:24:20,851 - pplus - compbio - DEBUG - Task (remote) 2 ended
    log_line_job_end_patt = re.compile('^.*Task (?:\(remote)\)? (\d+) ended$')

    # class of job container we accompany
    ppjc_klass = 'kdvs.fw.impl.job.PPlusJob.PPlusJobContainer'

    # for autodiscovery, configuration file to be found in KDVS output directory
    cfg_name = 'CFG'
    # for autodiscovery, jobs location to be resolved in full parh inside KDVS output directory
    jobs_location_var = 'jobs_location'

    # custom epilog formatting
    optparse.OptionParser.format_epilog = lambda self, formatter: self.epilog
    parser = optparse.OptionParser(description=
                                  'Companion script for %s. '
                                  'Checks "%s" for consistency of job submission '
                                  'and job completion messages. '
                                  'INPUT: When -d option is given, it resolves the log file as follows: '
                                  'finds configuration file %s in given directory, looks for most probable location '
                                  'in "%s" variable, and looks for "%s" there. '
                                  'When -f option is given, it looks directly for given file bypassing automatic discovery. '
                                  'OUTPUT: Writes "%s" file to directory specified with -o option. '
                                  'Default output directory: "%s". '
                                  '' % (
                                        ppjc_klass,
                                        exp_log_file_name,
                                        cfg_name,
                                        jobs_location_var,
                                        exp_log_file_name,
                                        output_file_name,
                                        os.getcwd()
                                    ),
                                   epilog=
                                  '"%s" contains the following data: \n'
                                  '(1) for jobs submitted but apparently not completed, job ID and machine designated to execute it, \n'
                                  '(2) listing of jobs per machine. \n' % (
                                        output_file_name,
                                        )
                                  )
    parser.add_option("-d", "--kdvs-output-dir", dest="kdvs_output_dir",
                  help="scan KDVS output directory DIR for 'experiment.log' file", metavar="DIR", default=None)
    parser.add_option("-f", "--experiment-log-file", dest="exp_log_path",
                  help="path to 'experiment.log' file", default=None)
    parser.add_option("-o", "--output-dir", dest="output_dir",
                  help="write result files into directory ODIR", metavar="ODIR", default=None)

    options = parser.parse_args()[0]

    kdvs_output_dir = options.kdvs_output_dir
    exp_log_path = options.exp_log_path
    output_dir = options.output_dir
    if output_dir is None:
        output_dir = os.path.abspath(os.getcwd())

    if kdvs_output_dir is None and exp_log_path is None:
        raise Exception('Exactly one of the options: -d or -f, must be specified!')

    if kdvs_output_dir is not None and exp_log_path is not None:
        raise Exception('Exactly one of the options: -d or -f, must be specified!')

    if kdvs_output_dir is not None:
        kdvs_output_dir = os.path.abspath(kdvs_output_dir)
        if not os.path.exists(kdvs_output_dir):
            raise Exception('KDVS output directory "%s" not found!' % kdvs_output_dir)
        cfg_path = os.path.join(kdvs_output_dir, cfg_name)
        if not os.path.exists(cfg_path):
            raise Exception('Configuration file "%s" not found!' % cfg_path)
        with open(cfg_path, 'rb') as f:
            cfg = deserializeObj(f)
        try:
            jobs_location = cfg[jobs_location_var]
        except KeyError:
            raise Exception('Variable "%s"not found in %s!' % (jobs_location_var, cfg_name))
        exp_log_file_path = os.path.join(kdvs_output_dir, jobs_location, exp_log_file_name)

    if exp_log_path is not None:
        exp_log_file_path = os.path.abspath(exp_log_path)

    if not os.path.exists(exp_log_file_path):
        raise Exception('Resolved log file "%s" not found!' % (exp_log_file_path))

    print 'Checking job completion...',

    with open(exp_log_file_path, 'rb') as f:
        loglines = f.readlines()

    jobdata = dict()
    jpm = collections.defaultdict(list)

    for logline in loglines:
        job_start_match = log_line_job_start_patt.match(logline)
        job_end_match = log_line_job_end_patt.match(logline)
        if job_start_match is not None:
            jobID, machine = job_start_match.groups()
            if jobID not in jobdata:
                jobdata[jobID] = dict()
                jobdata[jobID]['machine'] = machine
                jobdata[jobID]['finished'] = False
            else:
                # shall not happen but..
                raise Exception('Starting JobID already in jobdata!! (%d)' % jobID)
            jpm[machine].append(jobID)
        if job_end_match is not None:
            jobID, = job_end_match.groups()
            if jobID not in jobdata:
                # shall not happen but..
                raise Exception('Ending JobID not in jobdata!! (%d)' % jobID)
            else:
                jobdata[jobID]['finished'] = True

    not_finished_jobs = [(jid, jd['machine']) for jid, jd in jobdata.iteritems() if jd['finished'] is False]
    nfj_lines = ['%s on %s\n' % (jid, mach) for jid, mach in not_finished_jobs]

    output_file_path = os.path.join(output_dir, output_file_name)

    with open(output_file_path, 'wb') as wf:
        wf.write('Jobs (apparently) started but not finished:\n')
        wf.writelines(nfj_lines)
        wf.write('\nJobs per machine:\n')
        for machine, jobs in jpm.iteritems():
            wf.write('%s : (%d) %s\n' % (machine, len(jobs), ', '.join(jobs)))

    print 'done'
    print '%s written' % (output_file_path)
    print 'All Done'

if __name__ == '__main__':
    main()
