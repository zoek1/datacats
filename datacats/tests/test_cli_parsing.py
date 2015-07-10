# Copyright 2014-2015 Boxkite Inc.

# This file is part of the DataCats package and is released under
# the terms of the GNU Affero General Public License version 3.0.
# See LICENSE.txt or http://www.fsf.org/licensing/licenses/agpl-3.0.html

from unittest import TestCase

from datacats.cli.main import _subcommand_arguments
from datacats.error import DatacatsError


def _s(cmd):
    command, args = _subcommand_arguments(cmd.split())
    return command, ' '.join(args)


class TestParseArguments(TestCase):
    def test_help(self):
        self.assertEqual(_s('help'), (None, '--help'))

    def test_help_long_option(self):
        self.assertEqual(_s('--help'), (None, '--help'))

    def test_help_short_option(self):
        self.assertEqual(_s('-h'), (None, '-h'))

    def test_bad_subcommand(self):
        self.assertRaises(DatacatsError, _s, 'whatsup')

    def test_help_subcommand(self):
        self.assertEqual(_s('help info'), ('info', '--help info'))

    def test_subcommand(self):
        self.assertEqual(_s('info'), ('info', 'info'))

    def test_subcommand_option_first(self):
        self.assertEqual(_s('-q info'), ('info', '-q info'))

    def test_subcommand_option_last(self):
        self.assertEqual(_s('info -q'), ('info', 'info -q'))