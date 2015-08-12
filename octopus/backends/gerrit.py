# -*- coding: utf-8 -*-
#
# Copyright (C) 2014-2015 Bitergia
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# Authors:
#     Daniel Izquierdo <dizquierdo@bitergia.com>
#

from octopus.backends import Backend
from octopus.model import Platform, GerritRepository

import subprocess

class Gerrit(Backend):

    def __init__(self, session, gerrit_user, gerrit_url):
        super(Gerrit, self).__init__('gerrit')
        self.session = session
        self.gerrit_user = gerrit_user
        self.url = gerrit_url

    @classmethod
    def set_arguments_subparser(cls, parser):
        subparser = parser.add_parser('gerrit', help='Gerrit backend')

        # Gerrit options
        group = subparser.add_argument_group('Gerrit options')
        group.add_argument('--gerrit-user', dest='gerrit_user',
                           help='Gerrit user name. Public key has to already be in server',
                           default=None)
        group.add_argument('--gerrit-url', dest='gerrit_url',
                           help='Gerrit URL', default=None)

    def fetch(self):
        platform = Platform.as_unique(self.session, url=self.url)

        if not platform.id:
            platform.type = 'gerrit'

        for repository in self._repositories(self.url, self.session, self.gerrit_user):
            repo = GerritRepository()
            repo.name = repository
            platform.gerrit_repositories.append(repo)

        return platform

    def _repositories(self, url, platform, session):
        proc = subprocess.Popen(["ssh", "-l", self.gerrit_user, "-p", "29418", self.url, "gerrit", "ls-projects"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = proc.communicate()
        return output[0].split("\n")

