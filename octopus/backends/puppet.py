# -*- coding: utf-8 -*-
#
# Copyright (C) 2014 Bitergia
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
#     Santiago Dueñas <sduenas@bitergia.com>
#

import urlparse

import requests

from octopus.backends import Backend, ProjectsIterator


PROJECTS_LIMIT = 20
PUPPET_MODULES_PATH = '/v3/modules'


class PuppetForge(Backend):

    def __init__(self):
        super(PuppetForge, self).__init__('puppet')


class PuppetForgeFetcher(object):

    HEADERS = {'User-Agent': 'Octopus/0.0.1'}

    def __init__(self, base_url):
        self.base_url = base_url
        self._last_url = None

    @property
    def last_url(self):
        return self._last_url

    def projects(self, offset, limit=PROJECTS_LIMIT):
        params = {'offset' : offset,
                  'limit' : limit}
        url = urlparse.urljoin(self.base_url, PUPPET_MODULES_PATH)

        r = requests.get(url, params=params,
                         headers=PuppetForgeFetcher.HEADERS)

        self._last_url = r.url
        return r.json()


class PuppetForgeProjectsIterator(ProjectsIterator):

    def __init__(self, base_url):
        super(PuppetForgeProjectsIterator, self).__init__()
        self.fetcher = PuppetForgeFetcher(base_url)
        self.projects = []
        self.has_next = True
        self.offset = 0

    def __iter__(self):
        return self

    def next(self):
        # Check if there are parsed projects in the stack
        if self.projects:
            return self.projects.pop()

        # Check if there are more projects to fetch
        if not self.has_next:
            raise StopIteration

        # Fetch new set of projects
        json = self.fetcher.projects(self.offset, PROJECTS_LIMIT)

        if not json['pagination']['next']:
            self.has_next = False
        else:
            self.offset += PROJECTS_LIMIT

        for r in json['results']:
            self.projects.append(r)

        return self.projects.pop()
