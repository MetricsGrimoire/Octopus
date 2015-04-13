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

import github3

from octopus.backends import Backend
from octopus.model import Platform, Project, Repository


GITHUB_URL = 'https://github.com/'


class GitHubPlatform(Backend):

    def __init__(self, session, owner, repository=None, url=None,
                 user=None, password=None, oauth_token=None):
        super(GitHubPlatform, self).__init__('github')

        self.session = session
        self.owner = owner
        self.repository = repository

        if oauth_token:
            kwargs = {'token' : oauth_token}
        else:
            kwargs = {'username' : user,
                      'password' : password}

        if url:
            self.gh = github3.GitHubEnterprise(url, **kwargs)
            self.url = url
        else:
            self.gh = github3.login(**kwargs)
            self.url = GITHUB_URL

    @classmethod
    def set_arguments_subparser(cls, parser):
        subparser = parser.add_parser('github', help='GitHub backend')

        # GitHub options
        group = subparser.add_argument_group('GitHub options')
        group.add_argument('--gh-user', dest='gh_user',
                           help='GiHub user name',
                           default=None)
        group.add_argument('--gh-password', dest='gh_password',
                           help='GitHub user password',
                           default=None)
        group.add_argument('--gh-token', dest='gh_token',
                           help='GitHub OAuth token',
                           default=None)
        group.add_argument('--gh-url', dest='gh_url',
                           help='URL of the GitHub Enterprise instance',
                           default=None)

        # Positional arguments
        subparser.add_argument('owner',
                               help='Owner of the repository on GitHub')
        subparser.add_argument('repository', nargs='?', default=None,
                               help='Name of the repository on GitHub')


    def fetch(self):
        platform = Platform.as_unique(self.session, url=self.url)

        if not platform.id:
            platform.type = 'github'

        try:
            project = self._fetch_project(self.owner, self.repository, platform)
        except github3.exceptions.ForbiddenError, e:
            msg = "GitHub - " + e.message + "To resume, wait some minutes"
            raise Exception(msg)
        except github3.exceptions.AuthenticationFailed, e:
            raise Exception("GitHub - " + e.message)

        platform.projects.append(project)

        return platform

    def _fetch_project(self, owner, repository, platform):
        o = self.gh.organization(owner)

        if isinstance(o, github3.null.NullObject):
            raise Exception("GitHub - organization %s does not exist."
                            % owner)

        project = Project().as_unique(self.session, url=o.html_url,
                                      platform=platform)
        if not project.id:
            project.name = owner

        if repository:
            r = self.gh.repository(owner, repository)

            if isinstance(r, github3.null.NullObject):
                raise Exception("GitHub - repository %s:%s does not exist."
                                % (owner, repository))
            repositories = [r]
        else:
            repositories = [r for r in o.repositories()]

        for r in repositories:
            repo = self._fetch_repository(r)
            project.repositories.append(repo)

        return project

    def _fetch_repository(self, r):
        repo = Repository().as_unique(self.session, url=r.html_url)

        if not repo.id:
            repo.name = r.name
            repo.clone_url = r.clone_url
            repo.type = 'git'

        repo.starred = r.stargazers_count
        repo.forks = r.fork_count
        repo.watchers = r.watchers

        return repo
