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
import dateutil.parser

import requests

from octopus.backends import Backend, ProjectsIterator, ReleasesIterator
from octopus.model import Platform, Project, User, Release


PROJECTS_LIMIT = 20
RELEASES_LIMIT = 20
PUPPET_MODULES_PATH = '/v3/modules'
PUPPET_RELEASES_PATH = '/v3/releases'


class PuppetForge(Backend):

    def __init__(self, url, session):
        super(PuppetForge, self).__init__('puppet')
        self.url = url
        self.session = session

    def fetch(self):
        platform = Platform.as_unique(self.session, url=self.url)

        if not platform.id:
            platform.type = 'puppet'

        for project in self._projects(self.url, platform, self.session):
            for release in self._releases(self.url, project, project.users[0], self.session):
                project.releases.append(release)

            platform.projects.append(project)

        return platform

    def _projects(self, url, platform, session):
        return PuppetForgeProjectsIterator(url, platform, session)

    def _releases(self, url, project, user, session):
        return PuppetForgeReleasesIterator(url, project, user, session)


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

    def releases(self, project, username, offset, limit=RELEASES_LIMIT):
        module = username + '-' + project
        params = {'offset' : offset,
                  'limit' : limit,
                  'module' : module}

        url = urlparse.urljoin(self.base_url, PUPPET_RELEASES_PATH)

        r = requests.get(url, params=params,
                         headers=PuppetForgeFetcher.HEADERS)

        self._last_url = r.url
        return r.json()


class PuppetForgeProjectsIterator(ProjectsIterator):

    def __init__(self, base_url, platform, session):
        super(PuppetForgeProjectsIterator, self).__init__()
        self.fetcher = PuppetForgeFetcher(base_url)
        self.base_url = base_url
        self.session = session
        self.platform = platform
        self.projects = []
        self.users = {}
        self.has_next = True
        self.offset = 0

    def __iter__(self):
        return self

    def next(self):
        # Check if there are parsed projects in the queue
        if self.projects:
            return self.projects.pop(0)

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
            project = Project().as_unique(self.session, name=r['name'],
                                          platform=self.platform)
            project.updated_on = unmarshal_timestamp(r['updated_at'])

            if not project.id:
                project.url = self.base_url + r['uri']
                project.created_on = unmarshal_timestamp(r['created_at'])

            # Assign owner of the project
            username = r['owner']['username']

            if not username in self.users:
                user = User().as_unique(self.session, username=username)
                self.users[username] = user
            else:
                user = self.users[username]

            project.users.append(user)

            self.projects.append(project)

        return self.projects.pop(0)


class PuppetForgeReleasesIterator(ReleasesIterator):

    def __init__(self, base_url, project, user, session):
        super(PuppetForgeReleasesIterator, self).__init__()
        self.fetcher = PuppetForgeFetcher(base_url)
        self.base_url = base_url
        self.project = project
        self.user = user
        self.session = session
        self.releases = []
        self.has_next = True
        self.offset = 0

    def __iter__(self):
        return self

    def next(self):
        # Check if there are parsed releases in the queue
        if self.releases:
            return self.releases.pop(0)

        # Check if there are more releases to fetch
        if not self.has_next:
            raise StopIteration

        # Fetch new set of releases
        json = self.fetcher.releases(self.project.name, self.user.username,
                                     self.offset, RELEASES_LIMIT)

        if 'errors' in json:
            print "Warning: " + json['errors'][0]
            raise StopIteration

        if not json['pagination']['next']:
            self.has_next = False
        else:
            self.offset += RELEASES_LIMIT

        for r in json['results']:
            version = r['metadata']['version']

            # Some json objects might not include the official
            # name of the release. For those cases, build a new one.
            if not 'name' in r['metadata']:
                name = '-'.join((self.user.username, self.project.name, version))
            else:
                name = r['metadata']['name']

            release = Release().as_unique(self.session,
                                          name=name,
                                          version=version,
                                          user=self.user)

            release.url = self.base_url + r['uri']
            release.file_url = self.base_url + r['file_uri']
            release.created_on = unmarshal_timestamp(r['created_at'])
            release.updated_on = unmarshal_timestamp(r['updated_at'])

            self.releases.append(release)

        return self.releases.pop(0)


def unmarshal_timestamp(ts):
    # FIXME: store time zone data
    return dateutil.parser.parse(ts).replace(tzinfo=None)
