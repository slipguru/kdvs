#!/usr/bin/env python

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

from distutils.core import setup
from setuptools import find_packages
import kdvs

_version = kdvs.version

_short_description = """
Knowledge Driven Variable Selection (KDVS) is an experimental knowledge extraction
system that utilizes statistical learning and novel data and knowledge integration
methodologies.
"""

setup(
      name='KDVS',
      version=_version,
      description=_short_description,
      author='KDVS Developers',
      author_email='slipguru@disi.unige.it',
      maintainer='Grzegorz Zycinski',
      maintainer_email='g.zycinski@gmail.com',
      url='http://slipguru.disi.unige.it/Research/KDVS/',
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'Environment :: Console',
            'Intended Audience :: Science/Research',
            'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
            'Natural Language :: English',
            'Operating System :: MacOS',
            'Operating System :: Microsoft :: Windows',
            'Operating System :: Unix',
            'Programming Language :: Python',
            'Topic :: Scientific/Engineering :: Artificial Intelligence',
            'Topic :: Scientific/Engineering :: Information Analysis',
            'Topic :: Scientific/Engineering :: Bio-Informatics',
           ],
      packages=find_packages(),
      package_data={
            'kdvs' : [
                'config/default_cfg.py',
                'data/GO/*',
                'data/HGNC/*',
                'data/README',
                ],
            },
      requires=[
                'numpy (>=1.4.0)',
                'matplotlib (>=1.2.1)',
                'l1l2py (==1.0.5)'
            ],
)
