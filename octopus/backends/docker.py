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
#     Santiago Dueñas <sduenas@bitergia.com>
#

import datetime
import urlparse

import requests

from octopus.backends import Backend
from octopus.model import Platform, Project, Repository, RepositoryLog


DOCKER_OWNER_PATH = '/u/'
DOCKER_REPOSITORY_PATH = '/r/'
DOCKER_API_REPOSITORIES = '/v2/repositories/'
HEADERS = {'User-Agent': 'Octopus/0.0.1'}


class DockerRegistry(Backend):

    def __init__(self, session, url, owner):
        super(DockerRegistry, self).__init__('docker')

        self.session = session
        self.base_url = url
        self.owner = owner

    @classmethod
    def set_arguments_subparser(cls, parser):
        subparser = parser.add_parser('docker', help='Docker registry backend')

        # Positional arguments
        subparser.add_argument('url',
                               help='Docker registry url')
        subparser.add_argument('owner',
                               help='Owner of the repositories on Docker Hub')

    def fetch(self):
        platform = Platform.as_unique(self.session, url=self.base_url)

        if not platform.id:
            platform.type = 'docker'

        platform = self._fetch(self.owner, platform)

        return platform

    def _fetch(self, owner, platform):
        project = self._fetch_project(owner, platform)
        platform.projects.append(project)

        return platform

    def _fetch_project(self, owner, platform):
        url = urlparse.urljoin(self.base_url, DOCKER_OWNER_PATH)
        url = urlparse.urljoin(url, owner)

        try:
            r = requests.get(url, headers=HEADERS)
            r.raise_for_status()
        except requests.exceptions.HTTPError, e:
            msg = "Docker - owner %s. Error: %s" % (owner, str(e))
            raise Exception(msg)

        project = Project().as_unique(self.session, url=url,
                                      platform=platform)

        if not project.id:
            project.name = owner

        repositories = self._fetch_repositories(owner)

        for repo in repositories:
            project.repositories.append(repo)

        return project

    def _fetch_repositories(self, owner):
        page = 1
        fetching = True
        repositories = []

        while fetching:
            json_data = self._fetch_repositories_json(owner, page)
            page += 1

            for raw_repo in json_data['results']:
                repo = self._parse_repository_json(owner, raw_repo)
                repositories.append(repo)

                if not json_data['next']:
                    fetching = False

        return repositories

    def _fetch_repositories_json(self, owner, page=1):
        url = urlparse.urljoin(self.base_url, DOCKER_API_REPOSITORIES)
        url = urlparse.urljoin(url, owner)

        params = {'page' : page}

        try:
            r = requests.get(url, headers=HEADERS, params=params)
            r.raise_for_status()
        except requests.exceptions.HTTPError, e:
            msg = "Docker - repositories %s. Error: %s" \
                % (owner, str(e))
            raise Exception(msg)

        return r.json()

    def _parse_repository_json(self, owner, raw_repo):
        name = raw_repo['name']

        url = urlparse.urljoin(self.base_url, DOCKER_REPOSITORY_PATH)
        url = urlparse.urljoin(url, owner + '/' + name)

        repo = Repository().as_unique(self.session, url=url)

        if not repo.id:
            repo.name = name
            repo.type = 'docker'

        repo.starred = int(raw_repo['star_count'])
        repo.pulls = int(raw_repo['pull_count'])

        repo_log = RepositoryLog(date=datetime.datetime.now(),
                                 starred=repo.starred,
                                 pulls=repo.pulls)
        repo.log.append(repo_log)

        return repo
