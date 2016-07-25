#!/usr/bin/env python
#coding=utf-8
#
# django-gpg-sign-middleware - https://github.com/mtigas/django-gpg-sign-middleware
# Copyright © 2016, Mike Tigas.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at
# your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import subprocess
from distutils.core import setup, Command

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()

setup(name="django-gpg-sign-middleware",
      description='Django middleware that GPG signs your HTML pages.',
      long_description=readme,
      maintainer="Mike Tigas",
      version="0.1.0",
      packages=["gpgsign"],
      license="GNU Affero General Public License v3 or later (AGPLv3+)"
      url='https://github.com/mtigas/django-gpg-sign-middleware',
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Framework :: Django',
          'Environment :: Web Environment',
          'Programming Language :: Python',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Security',
      ],
      requires=['django (>=1.4)', 'gnupg (>=2.0.2)'])
