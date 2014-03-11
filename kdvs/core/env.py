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
Provides functionality of encapsulated execution environment for small dependent
computational tasks (dubbed actions). Actions are encapsulated Python callables
that can be submitted to environment for execution. Actions are executed in
submission order. Actions can communicate through shared variables that are
kept within the environment instance. In addition, environment can verify if
certain variables are present before or after the execution of specific action.
"""

from kdvs.core.action import ActionSpec
from kdvs.core.error import Error
from kdvs.core.util import quote, importComponent, Configurable
import sys

class ExecutionEnvironment(Configurable):
    r"""
Implements basic execution environment, where set of actions is executed in order,
and common set of environment variables is available for any action to store to
and retrieve data from. The environment is configurable.
    """

    def __init__(self, expected_cfg, env_cfg):
        r"""
Parameters
----------
expected_cfg : dict
    expected configuration of environment

env_cfg : dict
    provided environment configuration as read from configuration file

Raises
------
Error
    if provided configuration does not conform to expected configuration
        """
        # actions to execute by this environment
        self._actions = []
        # any global variables we want to preserve between actions
        self._vars = {}
        super(ExecutionEnvironment, self).__init__(expected_cfg, env_cfg)
        self._vars.update(self._cfg)

    def actions(self):
        r"""
Returns list of actions submitted for execution by this environment.

Returns
-------
actions : iterable of ActionSpec
    all actions submitted for execution by this environment
        """
        return self._actions

    def addAction(self, action_spec):
        r"""
Submit instance of action specification (ActionSpec) for execution by this environment.

See Also
--------
kdvs.core.action.ActionSpec
        """
        self._actions.append(action_spec)

    def addCallable(self, action_callable, action_kwargs=None, action_input=None, action_output=None):
        r"""
Submit specified callable for execution by this environment.

Parameters
----------
action_callable : callable
    callable to be executed

action_kwargs : dict/None
    any keyworded arguments passed to callable

action_input : list/tuple/None
    names of the variables that shall be present in the environment before
    the execution of the action

action_output : list/tuple/None
    names of the variables that shall be present in the environment after
    the execution of the action
        """
        if action_kwargs is None:
            action_kwargs = {}
        if action_input is None:
            action_input = ()
        if action_output is None:
            action_output = ()
        action_spec = ActionSpec(action_input, action_output, action_callable, (), action_kwargs)
        self.addAction(action_spec)

    def clearActions(self):
        r"""
Clear all currently submitted actions.
        """
        del self._actions[:]

    def addVar(self, varkey, var, replace=False):
        r"""
Add new variable to execution environment, with possible replacement. Variables
are managed in a dictionary, therefore all rules for adding items to standard
dictionaries apply here as well.

Parameters
----------
varkey : object
    hashable key for new variable

var : object
    value for new variable

replace : bool
    if True, already existing variable will be replaced

Raises
------
ValueError
    if variable already exists and replacement was not requested
        """
        if varkey in self._vars and replace is False:
            raise ValueError('Variable already exists! ("%s" -> %s)' % (varkey, str(var)))
        self._vars[varkey] = var

    def delVar(self, varkey):
        r"""
Remove requested variable from execution environment. If variable does not exist,
do nothing.

Parameters
----------
varkey : object
    key of variable to be removed
        """
        try:
            del self._vars[varkey]
        except:
            pass

    def updateVars(self, vardict, replace=False):
        r"""
Add all variables from requested dictionary to execution environment.

Parameters
----------
vardict : dict
    dictionary of variables to be added

replace : bool
    if True, any already existing variable will be replaced

Raises
------
ValueError
    if one of new variables already exists (replacements are not requested here)

See Also
--------
addVar
        """
        for (vk, v) in vardict.iteritems():
            self.addVar(vk, v, replace)

    def var(self, varkey):
        r"""
Retrieve value of variable present in execution environment.

Parameters
----------
varkey : object
    key of variable to be retrieved

Returns
-------
var : object
    value of requested variable

Raises
------
ValueError
    if variable does not exist
        """
        if varkey not in self._vars:
            raise ValueError('Variable not found! ("%s")' % (varkey))
        else:
            return self._vars[varkey]

    def varkeys(self):
        r"""
Retrieve keys of all existing variables present in execution environment.

Returns
-------
varkeys : iterable
    keys of variables present in execution environment
        """
        return self._vars.keys()

    def _verify_action_input(self, action_name, act_input):
        for var in act_input:
            if var not in self.varkeys():
                raise ValueError("To execute '%s', variable '%s' must be present in environment!" % (action_name, var))

    def _verify_action_output(self, action_name, act_output):
        for var in act_output:
            if var not in self.varkeys():
                raise ValueError("Variable '%s' is not present in environment after '%s'!" % (var, action_name))

    def _dump_actions(self):
        for aspec in self._actions:
            print aspec

    def execute(self, verify_io=True, dump_env=False):
        r"""
Execute all submitted actions so far in submission order (FIFO) and performs explicit
garbage collection between each action run. When any action raises an exception
during its run, the whole execution is stopped and diagnostic information is returned.
If all actions finish without exception, also clear them.

Parameters
----------

verify_io : bool
    if environment shall perform verification of input and output for every action
    executed; True by default

dump_env : bool
    if in case of exception thrown by action, all environment variables shall be
    returned in diagnostic information

Returns
-------
diagnostic : tuple/None
    None if all actions were executed silently, otherwise the following information is returned:
        * number of action that has thrown an exception
        * total number of actions to be executed
        * failed action details, as tuple (action_func_callable, args, kwargs)
        * thrown exception details, as tuple (exception instance, result of 'sys.exc_info')
        * details of actions already executed before failed action, as iterable of tuples (action_func_callable, args, kwargs)
        * details of actions to be executed after failed action, as iterable of tuples (action_func_callable, args, kwargs)
        * if environment dump was requested, all environment variables present in the moment of exception throw

Notes
-----
Dumping the environment that executes many long and complicated interlinked actions
that use lots of environment variables produces a LOT OF diagnostic information.

See Also
--------
:func:`sys.exc_info`
        """
        # run all collected actions so far according to FIFO policy and
        # perform garbage collection after every successful action;
        # in case of exception inside action, stop and return all available info
        # return all remaining actions left in the stack
        import gc
        exc = None
        err_act = None
        actions_num = len(self._actions)
        for i, action_spec in enumerate(self._actions):
            act_input, act_output, func, args, kwargs = action_spec.as_tuple()
            if verify_io:
                self._verify_action_input(func.__name__, act_input)
            try:
                func(self, *args, **kwargs)
                gc.collect()
                # ---- run post action callback
                self.postActionCallback()
            except Exception, e:
                # which action thrown an exception?
                err_act = (i + 1, actions_num, action_spec)
                # what exception exactly?
                exc = (e, sys.exc_info())
                # stop the execution and return
                break
            if verify_io:
                self._verify_action_output(func.__name__, act_output)
        if err_act is not None and exc is not None:
            ret = [err_act, exc, self._actions[:i], self._actions[i + 1:]]
            if dump_env:
                ret.append(self._vars)
            return ret
        else:
            self.clearActions()
            return None

    def postActionCallback(self):
        r"""
Callback function called after each successful action execution. By default
it does nothing.
        """
        pass


class LoggedExecutionEnvironment(ExecutionEnvironment):
    r"""
Implements execution environment that utilizes logging.

See Also
--------
ExecutionEnvironment
    """
    def __init__(self, expected_cfg, env_cfg):
        r"""
Parameters
----------
expected_cfg : dict
    expected configuration of environment

env_cfg : dict
    provided environment configuration as read from configuration file

Raises
------
Error
    if provided configuration does not conform to expected configuration
        """
        super(LoggedExecutionEnvironment, self).__init__(expected_cfg, env_cfg)
#        if 'logger' in env_cfg:
#            self.addVar('logger', env_cfg['logger'])
        self._initialize_logging()

    def _initialize_logging(self):
        self.logger = self.var('logger')
        self.logger.info('Log %s of level %s initialized' % (self.logger.std_atts['name'], self.logger._get_level_txt()))
        self.logger.info('Handler: %s, Additional attributes: %s' % (self.logger.std_atts['handler'].__class__.__name__, repr(self.logger.add_atts)))

    def execute(self):
        r"""
Execute actions and log any diagnostic information obtained.

See Also
--------
ExecutionEnvironment.execute
        """
        left = super(LoggedExecutionEnvironment, self).execute()
        if left:
            w, e, ex_acts, left_acts = left
            wmsg1 = 'Exception thrown in action %d of %d!' % (w[0], w[1])
            self.logger.error(wmsg1)
            wmsg2 = 'Action spec: (%s)' % w[2]
            self.logger.error(wmsg2)
            eas = [str(ea) for ea in ex_acts]
            eas.insert(0, 'Actions executed:')
            self.logger.error('\n\t'.join(eas))
            las = [str(la) for la in left_acts]
            las.insert(0, 'Actions left:')
            self.logger.error('\n\t'.join(las))
            self.logger.error('Exception Details:', exc_info=e[1])

    def postActionCallback(self):
        r"""
Called after each successful action execution. Flushes pending logger output.
        """
        super(LoggedExecutionEnvironment, self).postActionCallback()
        # ---- flush pending logger output
        self.logger.std_atts['handler'].flush()
