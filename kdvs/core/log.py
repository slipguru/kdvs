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
Provides logging utilities for KDVS.
"""

from kdvs import SYSTEM_NAME_LC
from logging import Handler, Formatter, getLogger, StreamHandler, CRITICAL, \
    FATAL, ERROR, WARNING, INFO, DEBUG, NOTSET
from logging.handlers import RotatingFileHandler
import os
import socket
import sys
import uuid

_LEVELS = {
    CRITICAL : 'CRITICAL',
    FATAL : 'FATAL',
    ERROR : 'ERROR',
    WARNING : 'WARNING',
    INFO : 'INFO',
    DEBUG : 'DEBUG',
    NOTSET : 'NOTSET',
    'CRITICAL' : CRITICAL,
    'FATAL' : FATAL,
    'ERROR' : ERROR,
    'WARN' : WARNING,
    'WARNING' : WARNING,
    'INFO' : INFO,
    'DEBUG' : DEBUG,
    'NOTSET' : NOTSET,
}

class Logger(object):
    r"""
Abstract logger for KDVS system.
    """

    def __init__(self, name=None, level=INFO, handler=None, formatter=None, add_atts=None):
        r"""
Parameters
----------
name : string/None
    name of the logger; if None, random name will be used

level : integer
    level granularity of this logger, INFO by default

handler : Handler/None
    handler for the logger; if None, null handler will be used (that does not emit anything)

formatter : Formatter/None
    formatter for the logger; if None, standard Formatter will be used

add_atts : dict/None
    any custom attributes to be associated with the logger

See Also
--------
logging
logging.handlers
logging.Formatter
        """
        self.std_atts = dict()
        self.add_atts = dict()
        if name is None:
            self.std_atts['name'] = self._get_random_name()
        else:
            self.std_atts['name'] = name
        self._logger = getLogger(self.std_atts['name'])
        self.std_atts['level'] = level
        if handler is None:
            self.std_atts['handler'] = NullHandler()
        else:
            self.std_atts['handler'] = handler
        if formatter is None:
            self.std_atts['formatter'] = Formatter()
        else:
            self.std_atts['formatter'] = formatter
        self.std_atts['handler'].setFormatter(self.std_atts['formatter'])
        self._logger.addHandler(self.std_atts['handler'])
        self._logger.setLevel(self.std_atts['level'])
        if not add_atts is None:
            self.add_atts.update(add_atts)

    def __getattr__(self, attr):
        return getattr(self._logger, attr)

    def _get_random_name(self):
        # pick semi-random name
        return "%s_%s" % (SYSTEM_NAME_LC, uuid.uuid1().hex)

    def _get_level_txt(self):
        return _LEVELS[self.std_atts['level']]

    def stdAttrs(self):
        r"""
Return dictionary of standard attributes for the logger.
        """
        return self.std_atts

    def addAttrs(self):
        r"""
Return dictionary of associated custom attributes for the logger.
        """
        return self.add_atts


class RotatingFileLogger(Logger):

    r"""
Logger that uses rotating file mechanism. By design, the default logger that KDVS
uses.
    """

    def __init__(self, name=None, level=INFO, path=None, maxBytes=10 * 1024 * 1024, backupCount=5):
        r"""
Parameters
----------
name : string/None
    name of the logger; if None, random name will be used

level : integer
    level granularity of this logger, INFO by default

path : string/None
    path to log file; if None, random log file will be created in current directory,
    as per os.getcwd()

maxBytes : integer
    maximum size of log file in bytes before it gets rotated; 10 MB by default

backupCount : integer
    maximum number of old log files kept in rotation cycle; 5 by default

See Also
--------
logging.handlers.RotatingFileHandler
        """
        if path is None:
            path = os.path.join(os.getcwd(), self._get_random_name() + os.path.extsep + 'log')
#        import logging.handlers
#        handler=logging.handlers.RotatingFileHandler(path, mode='a',
        handler = RotatingFileHandler(path, mode='a',
                        maxBytes=maxBytes, backupCount=backupCount, delay=True)
        formatter = Formatter("%(asctime)s - %(name)s - " + socket.gethostname() + " - %(levelname)s - %(message)s")
        super(RotatingFileLogger, self).__init__(name, level, handler, formatter, {'path' : path})


class StreamLogger(Logger):

    r"""
Logger that directs messages to specified stream.
    """

    def __init__(self, name=None, level=INFO, stream=sys.stdout):
        r"""
Parameters
----------
name : string/None
    name of the logger; if None, random name will be used

level : integer
    level granularity of this logger, INFO by default

stream : file
    Stream to direct messages to; :py:class:`sys.stdout` by default

See Also
--------
logging.StreamHandler
        """
        handler = StreamHandler(stream)
        formatter = Formatter("%(asctime)s - %(name)s - " + socket.gethostname() + " - %(levelname)s - %(message)s")
        super(StreamLogger, self).__init__(name, level, handler, formatter)

# ---- utilities for null logging

class NullHandler(Handler):
    r"""
Null handler used for compatibility with Python 2.6. It consumes given messages
without emitting them.

See Also
--------
logging.NullHandler
    """
    # helper null handler for compatibility with Python 2.6+
    def __init__(self):
        r"""
        """
        Handler.__init__(self)

    def emit(self, *args):
        r"""
        """
        pass

    def flush(self):
        r"""
        """
        Handler.flush(self)

    def close(self):
        r"""
        """
        Handler.close(self)
