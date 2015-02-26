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

import urlparse

import bs4
import requests

from octopus.backends import Backend
from octopus.model import Platform, Project, Repository


DOCKER_OWNER_PATH = '/u/'
HEADERS = {'User-Agent': 'Octopus/0.0.1'}


class DockerRegistry(Backend):

    def __init__(self, session, url, owner, repository):
        super(DockerRegistry, self).__init__('docker')

        self.session = session
        self.base_url = url
        self.owner = owner
        self.repository = repository

    @classmethod
    def set_arguments_subparser(cls, parser):
        subparser = parser.add_parser('docker', help='Docker registry backend')

        # Positional arguments
        subparser.add_argument('url',
                               help='Docker registry url')
        subparser.add_argument('owner',
                               help='Owner of the repository on Docker Hub')
        subparser.add_argument('repository', nargs='?', default=None,
                               help='Name of the repository on Docker Hub')


    def fetch(self):
        platform = Platform.as_unique(self.session, url=self.base_url)

        if not platform.id:
            platform.type = 'docker'

        platform = self._fetch(self.base_url, self.owner, self.repository, platform)

        return platform

    def _fetch(self, url, owner, repository, platform):
        project = self._fetch_project(owner, platform)
        repo = self._fetch_repository(owner, repository, platform)

        project.repositories.append(repo)
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

        project = Project().as_unique(self.session, name=owner,
                                      platform=platform)

        if not project.id:
            project.url = url

        return project

    def _fetch_repository(self, owner, repository, platform):
        url = urlparse.urljoin(self.base_url, DOCKER_OWNER_PATH)
        url = urlparse.urljoin(url, owner + '/' + repository)

        try:
            r = requests.get(url, headers=HEADERS)
            r.raise_for_status()
        except requests.exceptions.HTTPError, e:
            msg = "Docker - repository %s:%s. Error: %s" \
                % (owner, repository, str(e))
            raise Exception(msg)

        try:
            stars, downloads = self._parse_repository_html(r.text)
        except Exception, e:
            msg = "Docker - repository %s:%s. Error: %s" \
                % (owner, repository, str(e))

        repo = Repository().as_unique(self.session, url=url)

        if not repo.id:
            repo.name = repository
            repo.type = 'docker'

        repo.starred = stars
        repo.downloads = downloads

        return repo

    def _parse_repository_html(self, html):
        soup = bs4.BeautifulSoup(html)

        stars = int(soup.find('a', {'class' : 'stars'}).text)
        downloads = int(soup.find('span', {'class' : 'downloads'}).text)

        return stars, downloads
