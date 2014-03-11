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
Provides mechanisms for configuration of KDVS. Configuration files are normal
Python scripts that are evaluated with 'execfile'. Since KDVS uses many options
in many configuration files, this module provides utilities for evaluating and
merging configurations.
"""

import os
from kdvs import SYSTEM_ROOT_PATH

# ---- default paths

def getDefaultCfgFilePath(defpath=None):
    r"""
Return absolute path of default configuration file for KDVS.
    """
    if defpath is None:
        endpath=os.path.abspath(os.path.join(SYSTEM_ROOT_PATH, 'config', 'default_cfg.py'))
    else:
        endpath=defpath
    return os.path.abspath(endpath)

def getDefaultDataRootPath(defpath=None):
    r"""
Return absolute path of default data directory for KDVS.
    """
    if defpath is None:
        endpath=os.path.abspath(os.path.join(SYSTEM_ROOT_PATH, 'data'))
    else:
        endpath=defpath
    return os.path.abspath(endpath)

# def getREnvPath(defpath=None):
#    if defpath is None:
#        endpath=os.path.abspath(os.path.join(SYSTEM_ROOT_PATH, 'R'))
#    else:
#        endpath=defpath
#    return os.path.abspath(endpath)

def getGODataPath(defpath=None):
    r"""
Return absolute path of default Gene Ontology (GO) data directory for KDVS.
    """
    if defpath is None:
        dataroot = getDefaultDataRootPath()
        endpath=os.path.join(dataroot, 'GO')
    else:
        endpath=defpath
    return os.path.abspath(endpath)

def getVisDataPath(defpath=None):
    r"""
Return absolute path of default visualization data directory for KDVS.
    """
    if defpath is None:
        dataroot = getDefaultDataRootPath()
        endpath=os.path.join(dataroot, 'vis')
    else:
        endpath=defpath
    return os.path.abspath(endpath)

# ---- handle configuration files

def mergeCfg(parent_cfg, child_cfg):
    r"""
Merge parent end child config variables to produce final config variables, as
follows. If the variable exists only in parent config or child config, write it
to the final config. If the variable exists in both parent and child configs,
retain the one from child config.

It is used to merge variables obtained from default configuration file and
specified user configuration file.

Parameters
----------
parent_cfg : dict
    dictionary of variables obtained from parent configuration file

child_cfg : dict
    dictionary of variables obtained from child configuration file

Returns
-------
final_cfg : dict
    merged configuration variables

See Also
--------
evaluateDefaultCfg
evaluateUserCfg
    """
    # merge parent and child cfg variables to produce final cfg variables
    # if the variable exists only in parent cfg or child cfg, write it to the final cfg
    # if the variable exists in both parent and child cfg, retain the one from child cfg
    final_cfg = dict()
    for dcn, dcv in parent_cfg.iteritems():
        # scan over default cfg first
        if dcn in child_cfg.keys():
            # child cfg overwrote the variable, take new value
            final_cfg[dcn]=child_cfg[dcn]
        else:
            # variable exists solely in parent cfg, include it as well
            final_cfg[dcn]=dcv
    # child cfg might add some additional options
    for ucn, ucv in child_cfg.iteritems():
        if ucn not in final_cfg.keys():
            # child cfg added unseen variable, include it
            final_cfg[ucn]=ucv
    return final_cfg

def evaluateDefaultCfg():
    r"""
Evaluate default configuration file of KDVS and return its configuration variables.

Returns
-------
default_cfg_vars : dict
    dictionary of variables obtained from default configuration file

See Also
--------
getDefaultCfgFilePath
    """
    def_cfg_path = getDefaultCfgFilePath()
    default_cfg_vars = dict()
    execfile(def_cfg_path, globals(), default_cfg_vars)
    return default_cfg_vars

def evaluateUserCfg(cfg_file, ignore_default_cfg=False):
    r"""
Evaluate specified user configuration file of KDVS, performs merge with default
configuration, and returns final configuration variables.

Parameters
----------
cfg_file : string
    path to user configuration file

ignore_default_cfg : bool
    ignores default configuration file; no merge is performed and all variables
    come only from user configuration file; should be used with caution

Returns
-------
user_cfg : dict
    dictionary of variables obtained from user configuration file

See Also
--------
evaluateDefaultCfg
    """
    user_cfg = dict()
    execfile(cfg_file, globals(), user_cfg)
    if not ignore_default_cfg:
        default_cfg = evaluateDefaultCfg()
        final_cfg = mergeCfg(default_cfg, user_cfg)
        return final_cfg
    else:
        return user_cfg
