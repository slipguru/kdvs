# -*- coding: utf-8 -*-
# Copyright (c) 2010, 2011, Sebastian Wiesner <lunaryorn@googlemail.com>
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""
    sphinxcontrib.programoutput
    ===========================

    This extension provides a directive to include the output of commands as
    literal block while building the docs.

    .. moduleauthor::  Sebastian Wiesner  <lunaryorn@googlemail.com>
"""

from __future__ import (print_function, division, unicode_literals,
                        absolute_import)

import sys
import shlex
from subprocess import Popen, PIPE, STDOUT
from collections import defaultdict, namedtuple

from docutils import nodes
from docutils.parsers import rst
from docutils.parsers.rst.directives import flag, unchanged, nonnegative_int


__version__ = '0.5'


class program_output(nodes.Element):
    pass


def _slice(value):
    parts = [int(v.strip()) for v in value.split(',')]
    if len(parts) > 2:
        raise ValueError('too many slice parts')
    return tuple((parts + [None]*2)[:2])


class ProgramOutputDirective(rst.Directive):
    has_content = False
    final_argument_whitespace = True
    required_arguments = 1

    option_spec = dict(shell=flag, prompt=flag, nostderr=flag,
                       ellipsis=_slice, extraargs=unchanged,
                       returncode=nonnegative_int)

    def run(self):
        node = program_output()
        node.line = self.lineno
        node['command'] = self.arguments[0]

        if self.name == 'command-output':
            node['show_prompt'] = True
        else:
            node['show_prompt'] = 'prompt' in self.options

        node['hide_standard_error'] = 'nostderr' in self.options
        node['extraargs'] = self.options.get('extraargs', '')
        node['use_shell'] = 'shell' in self.options
        node['returncode'] = self.options.get('returncode', 0)
        if 'ellipsis' in self.options:
            node['strip_lines'] = self.options['ellipsis']
        return [node]


_Command = namedtuple('Command', 'command shell hide_standard_error')


class Command(_Command): #pylint: disable=W0232
    """
    A command to be executed.
    """

    def __new__(cls, command, shell=False, hide_standard_error=False):
        if isinstance(command, list):
            command = tuple(command)
        return _Command.__new__(cls, command, shell, hide_standard_error)

    @classmethod
    def from_program_output_node(cls, node):
        """
        Create a command from a :class:`program_output` node.
        """
        extraargs = node.get('extraargs', '')
        command = (node['command'] + ' ' + extraargs).strip()
        return cls(command, node['use_shell'], node['hide_standard_error'])

    def execute(self):
        """
        Execute this command.

        Return the :class:`~subprocess.Popen` object representing the running
        command.
        """
        # pylint: disable=E1101
        if isinstance(self.command, unicode):
            command = self.command.encode(sys.getfilesystemencoding())
        else:
            command = self.command
        if isinstance(command, basestring) and not self.shell:
            command = shlex.split(command)
        return Popen(command, shell=self.shell, stdout=PIPE,
                     stderr=PIPE if self.hide_standard_error else STDOUT)

    def get_output(self):
        """
        Get the output of this command.

        Return a tuple ``(returncode, output)``.  ``returncode`` is the
        integral return code of the process, ``output`` is the output as
        unicode string, with final trailing spaces and new lines stripped.
        """
        process = self.execute()
        output = process.communicate()[0].decode(
            sys.getfilesystemencoding()).rstrip()
        return process.returncode, output

    def __str__(self):
        # pylint: disable=E1101
        if isinstance(self.command, tuple):
            return repr(list(self.command))
        return repr(self.command)


class ProgramOutputCache(defaultdict): # pylint: disable=W0232
    """
    Execute command and cache their output.

    This class is a mapping.  Its keys are :class:`Command` objects represeting
    command invocations.  Its values are tuples of the form ``(returncode,
    output)``, where ``returncode`` is the integral return code of the command,
    and ``output`` is the output as unicode string.

    The first time, a key is retrieved from this object, the command is
    invoked, and its result is cached.  Subsequent access to the same key
    returns the cached value.
    """

    def __missing__(self, command):
        """
        Called, if a command was not found in the cache.

        ``command`` is an instance of :class:`Command`.
        """
        result = command.get_output()
        self[command] = result
        return result


def run_programs(app, doctree):
    """
    Execute all programs represented by ``program_output`` nodes in
    ``doctree``.  Each ``program_output`` node in ``doctree`` is then
    replaced with a node, that represents the output of this program.

    The program output is retrieved from the cache in
    ``app.env.programoutput_cache``.
    """
    if app.config.programoutput_use_ansi:
        # enable ANSI support, if requested by config
        from sphinxcontrib.ansi import ansi_literal_block
        node_class = ansi_literal_block
    else:
        node_class = nodes.literal_block

    cache = app.env.programoutput_cache

    for node in doctree.traverse(program_output):
        command = Command.from_program_output_node(node)
        try:
            returncode, output = cache[command]
        except EnvironmentError as error:
            error_message = 'Command {0} failed: {1}'.format(command, error)
            error_node = doctree.reporter.error(error_message, base_node=node)
            node.replace_self(error_node)
        else:
            if returncode != node['returncode']:
                app.warn('Unexpected return code {0} from command {1}'.format(
                    returncode, command))

            # replace lines with ..., if ellipsis is specified
            if 'strip_lines' in node:
                lines = output.splitlines()
                start, stop = node['strip_lines']
                lines[start:stop] = ['...']
                output = '\n'.join(lines)

            if node['show_prompt']:
                tmpl = app.config.programoutput_prompt_template
                output = tmpl.format(command=node['command'], output=output,
                                     returncode=returncode)

            new_node = node_class(output, output)
            new_node['language'] = 'text'
            node.replace_self(new_node)


def init_cache(app):
    """
    Initialize the cache for program output at
    ``app.env.programoutput_cache``, if not already present (e.g. being
    loaded from a pickled environment).

    The cache is of type :class:`ProgramOutputCache`.
    """
    if not hasattr(app.env, 'programoutput_cache'):
        app.env.programoutput_cache = ProgramOutputCache()


def setup(app):
    app.add_config_value('programoutput_use_ansi', False, 'env')
    app.add_config_value('programoutput_prompt_template',
                         '$ {command}\n{output}', 'env')
    app.add_directive('program-output', ProgramOutputDirective)
    app.add_directive('command-output', ProgramOutputDirective)
    app.connect(b'builder-inited', init_cache)
    app.connect(b'doctree-read', run_programs)
