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
Provides high--level functionality for generation of reports by KDVS.
"""

from kdvs.core.util import Parametrizable
from kdvs.fw.StorageManager import SUBLOCATION_SEPARATOR
import os

DEFAULT_REPORTER_PARAMETERS = ()
r"""
Default parameters for reporter.
"""

# by default, reporter should expose dictionary {file_name->[file_content_lines]}
# reporter files are stored by default into 'results' standard sublocation;
# this may be overriden by using 'subloc1/.../sublocN/file_name' in the key

class Reporter(Parametrizable):
    r"""
Abstract reporter. Reporter produces reports based on results obtained from
statistical techniques, where each subset has associated single technique, and
each computational job executes technique on a subset. Reporter may work across
single category of results (in that case reports are "local"), or can cross
boundaries of individual categories (in that case reports are "global"). Each
reporter may produce many single reports. Reporters are parametrizable, and report
generation is done in the background in callback fashion after all computational
jobs has been executed. Reporters are closely tied with respected statistical
techniques.
    """
    def __init__(self, ref_parameters, **kwargs):
        r"""
Parameters
----------
ref_parameters : iterable
    reference parameters to be checked against during instantiation; empty tuple
    by default

kwargs : dict
    actual parameters supplied during instantiation; they will be checked against
    reference ones
        """
        super(Reporter, self).__init__(ref_parameters, **kwargs)
        self._reports = dict()
        self._sm = None
        self._ssresloc = None
        self._data = None
        # separator is public so one can construct locations in overloaded methods
        self.locsep = SUBLOCATION_SEPARATOR

    # for simple reports that do not cross the boundaries of categories
    # by default it does nothing
    # normally it should be sufficient to implement only this method
    def produce(self, resultsIter):
        r"""
Produce reports. This method works across single category of results. By
default, it does nothing. The implementation should fill `self._reports` with
mapping

    * {file_name : [file_content_lines]}
    
By default, all report files will be created in standard sublocation `results`.
This may be changed by specifying 'subloc1/.../sublocN/file_name' as file name.
The new sublocation paths may be constructed with given location separator
`self.locsep`.

Parameters
----------
resultsIter : iterable of :class:`~kdvs.fw.Stat.Results`
    iterable of results obtained across single category

See Also
--------
kdvs.fw.Categorizer.Categorizer
kdvs.fw.StorageManager.StorageManager
        """
        pass

    # for advanced reports that need to cross the boundaries of categories
    # by default it does nothing
    # NOTE: reporter can use currentCategorizerID/currentCategoryID, e.g. if
    # reporting across only limited portion of categories tree; this information
    # can be also ignored if needed
    def produceForHierarchy(self, subsetHierarchy, ssIndResults, currentCategorizerID, currentCategoryID):
        r"""
Produce reports. This method works across the whole category tree. By default, it
does nothing. The implementation should fill `self._reports` with mapping

    * {file_name : [file_content_lines]}
    
By default, all report files will be created in standard sublocation `results`.
This may be changed by specifying 'subloc1/.../sublocN/file_name' as file name.
The new sublocation paths may be constructed with given location separator
`self.locsep`. NOTE: reporter of this type may be requested to work starting on
specific level of category tree; level is given by categorizer and category; in
that case, it has access to the whole starting categorizer, and all subtree
below it, and can start from given category.

Parameters
----------
subsetHierarchy : :class:`~kdvs.fw.SubsetHierarchy.SubsetHierarchy`
    current hierarchy of subsets that contains whole category tree

ssIndResults : dict of iterable of :class:`kdvs.fw.Stat.Results`
    iterables of Results obtained for all categories at once

currentCategorizerID : string
    identifier of Categorizer from which the reporter will start work

currentCategoryID : string
    optionally, identifier of category the reporter shall start with

See Also
--------
kdvs.fw.StorageManager.StorageManager
        """
        pass

    # may be overloaded to check if specific additional data have been provided
    def initialize(self, storageManager, subsets_results_location, additionalData):
        r"""
Initialize the reporter. Since reporter produces physical files, the concrete
storage must be assigned for them. Also, it may accept any additional data
necessary for its work.

Parameters
----------

storageManager : :class:`~kdvs.fw.StorageManager.StorageManager`
    instance of storage manager that will govern the production of physical files

subsets_results_location : string
    identifier of standard location used to store KDVS results

additionalData : object
    any additional data used by the reporter
        """
        self._sm = storageManager
        self._ssresloc = subsets_results_location
        self._data = additionalData

    def finalize(self):
        r"""
Finalize reporter's work by writing report files and clearing them.
        """
        self._storeOutputFiles()
        self._reports.clear()

    def getReports(self):
        r"""
Get currently generated reports as dictionary

    * {'file_name' : ['file_content_lines']}
        """
        return self._reports

    def openReport(self, rlocation, content):
        r"""
Request opening of new report in given location with specified content.

Parameters
----------
rlocation : string
    location of new report; equivalent to 'file_name'

content : iterable
    content of new report; equivalent of 'file_content_lines'
        """
        self._reports[rlocation] = content

    def getAdditionalData(self):
        r"""
Return any additional data associated with this reporter.
        """
        return self._data

    def _storeOutputFiles(self):
        for rlocation, rdata in self._reports.iteritems():
            rpath = self._obtainPath(rlocation)
            with open(rpath, 'wb') as f:
                f.writelines(rdata)

    def _obtainPath(self, flocation):
        # check if output file needs to be placed in new sublocation
        lparts = flocation.split(self.locsep)
        if len(lparts) > 1:
            # nested sublocation was requested, isolate it
            # join elements back all but the last one and root in 'results'
            lparts.insert(0, self._ssresloc)
            floc = self.locsep.join(lparts[:-1])
            # file name is the last part
            fname = lparts[-1]
        else:
            floc = self._ssresloc
            fname = lparts[0]
        # get the sublocation if exists already
        fpath = self._sm.getLocation(floc)
        if fpath is None:
            # sublocation does not exists, create it
            self._sm.createLocation(floc)
            fpath = self._sm.getLocation(floc)
        return os.path.join(fpath, fname)
