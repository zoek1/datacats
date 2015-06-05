# Copyright 2014-2015 Boxkite Inc.

# This file is part of the DataCats package and is released under
# the terms of the GNU Affero General Public License version 3.0.
# See LICENSE.txt or http://www.fsf.org/licensing/licenses/agpl-3.0.html

import sys
from os import listdir
from os.path import isdir, exists

from datacats.cli import manage
from datacats.docker import check_connectivity
from datacats.error import DatacatsError


def write(s):
    sys.stdout.write(s)
    sys.stdout.flush()


def install(environment, opts):
    """Install or reinstall Python packages within this environment

Usage:
  datacats install [-c] [--address=IP] [ENVIRONMENT]

Options:
  -c --clean            Reinstall packages into a clean virtualenv
  --address=IP          The address to bind to when reloading after install [default: 127.0.0.1]

ENVIRONMENT may be an environment name or a path to an environment directory.
Default: '.'
"""
    environment.require_data()
    install_all(environment, opts['--clean'])

    if 'web' in environment.containers_running():
        # FIXME: reload without changing debug setting?
        manage.reload_(environment, {
            '--production': False,
            'PORT': None,
            '--background': False,
            '--address': opts['--address']})


def install_all(environment, clean):
    logs = check_connectivity()
    if logs.strip():
        raise DatacatsError(logs)
    srcdirs = set()
    reqdirs = set()
    for d in listdir(environment.target):
        fulld = environment.target + '/' + d
        if not isdir(fulld):
            continue
        if not exists(fulld + '/setup.py'):
            continue
        srcdirs.add(d)
        if (exists(fulld + '/requirements.txt') or
                exists(fulld + '/pip-requirements.txt')):
            reqdirs.add(d)
    try:
        srcdirs.remove('ckan')
        reqdirs.remove('ckan')
    except KeyError:
        raise DatacatsError('ckan not found in environment directory')

    if clean:
        environment.clean_virtualenv()

    for s in ['ckan'] + sorted(srcdirs):
        write('Installing ' + s)
        environment.install_package_develop(s)
        write('\n')
    for s in ['ckan'] + sorted(reqdirs):
        write('Installing ' + s + ' requirements')
        environment.install_package_requirements(s)
        write('\n')
