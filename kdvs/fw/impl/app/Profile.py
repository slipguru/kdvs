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
Provides functionality regarding handling application profiles. Also, provides
pre--defined concrete profiles. Specific profile is read by application from
configuration file. Application checks if the profile is complete, that is, if
it contains all listed sections, and if section content is wrapped in correct
data structure.
"""
# ---- predefined profiles

NULL_PROFILE = {
}
r"""
Simplest 'null' application profile that contains no elements to be checked against.
"""

MA_GO_PROFILE = {
    # ---- data section
    'annotation_file' : {},
    'gedm_file' : {},
    'labels_file' : {},
    # ---- GO section
    'go_domain' : '',
    # ---- subsets section
    # ---- initializers for all individual components
    'subset_categorizers' : {},
    'subset_orderers' : {},
    'statistical_techniques' : {},
    'subset_outer_selectors' : {},
    'subset_inner_selectors' : {},
    'reporters' : {},
    'envops' : {},
    # ---- subset hierarchy categorizer tree (as a linear iterable of categorizers)
    'subset_hierarchy_categorizers_chain' : (),
    # ---- fully expanded assignments of individual operations
    'subset_hierarchy_components_map' : {},
}
r"""
Application profile used by 'experiment' application. It is organized as a
dictionary

    * {section_name : section_prototype}

where 'section_prototype' refers to the example instance of the type that
contains section content. For instance, when 'section_prototype' is an empty
dictionary, it will be checked during profile validation that the content of
the section is wrapped in a dictionary. Some sections may use different
containers, like iterables, if necessary. See content of
'example_experiment_cfg.py' in `example_experiment` directory for an example of
how this particular profile may be specified.
"""
