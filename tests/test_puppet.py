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

import os.path
import sys
import unittest
import urlparse

if not '..' in sys.path:
    sys.path.insert(0, '..')

from BaseHTTPServer import BaseHTTPRequestHandler

from octopus.backends import Backend
from octopus.backends.puppet import PuppetForge, PuppetForgeFetcher,\
    PuppetForgeProjectsIterator, PuppetForgeReleasesIterator
from octopus.model import Project, User, Release

from mock_http_server import MockHTTPServer
from utils import read_file


# HTTP server configuration
HTTP_HOST = 'localhost'
HTTP_PORT = 9999
TEST_FILES_DIRNAME = 'data'
TIMEOUT = 5
MOCK_HTTP_SERVER_URL = 'http://' + HTTP_HOST + ':' + str(HTTP_PORT)

# Mock projects
PUPPET_PROJECT_STDLIB = 'puppetlabs-stdlib'
PUPPET_PROJECT_VAGRANT = 'mjanser-vagrant'
PUPPET_PROJECT_ERROR = 'raise-error'

# Data files
PUPPET_MODULES_1 = 'puppet_modules_1.json'
PUPPET_MODULES_2 = 'puppet_modules_2.json'
PUPPET_RELEASES_STDLIB_1 = 'puppet_rel_stdlib_1.json'
PUPPET_RELEASES_STDLIB_2 = 'puppet_rel_stdlib_2.json'
PUPPET_RELEASES_VAGRANT = 'puppet_rel_vagrant.json'
PUPPET_RELEASES_ERROR = 'puppet_rel_error.json'


class MockPuppetForgeHTTPHandler(BaseHTTPRequestHandler):
    """Mock Puppet Forge requests handler"""

    def do_GET(self):
        parts = urlparse.urlparse(self.path)
        qs = self._parse_GET_query(parts.query)

        if parts.path == '/v3/modules':
            self.projects(qs)
        elif parts.path == '/v3/releases':
            self.releases(qs)
        else:
            self.not_found()

    def projects(self, qs):
        if 'offset' in qs:
            offset = int(qs['offset'][0])
        else:
            offset = 0

        if offset < 20:
            filepath = os.path.join(TEST_FILES_DIRNAME, PUPPET_MODULES_1)
        else:
            filepath = os.path.join(TEST_FILES_DIRNAME, PUPPET_MODULES_2)
        json = read_file(filepath)

        self.send_response(200, 'Ok')
        self.end_headers()
        self.wfile.write(json)

    def releases(self, qs):
        if 'offset' in qs:
            offset = int(qs['offset'][0])
        else:
            offset = 0

        project_name = qs['module'][0]

        if project_name == PUPPET_PROJECT_ERROR:
            # Simulate errors
            filename = PUPPET_RELEASES_ERROR
        elif project_name == PUPPET_PROJECT_VAGRANT:
            filename = PUPPET_RELEASES_VAGRANT
        elif offset < 20:
            filename = PUPPET_RELEASES_STDLIB_1
        else:
            filename = PUPPET_RELEASES_STDLIB_2

        filepath = os.path.join(TEST_FILES_DIRNAME, filename)
        json = read_file(filepath)

        self.send_response(200, 'Ok')
        self.end_headers()
        self.wfile.write(json)

    def not_found(self):
        self.send_error(404, 'Not found')

    def _parse_GET_query(self, query):
        if not query:
            return None
        return urlparse.parse_qs(query)


class TestPuppetForge(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = MockHTTPServer(HTTP_HOST, HTTP_PORT, TEST_FILES_DIRNAME,
                                   MockPuppetForgeHTTPHandler)
        cls.httpd.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.stop()

    def test_backend(self):
        backend = PuppetForge(MOCK_HTTP_SERVER_URL)
        self.assertIsInstance(backend, Backend)
        self.assertEqual('puppet', backend.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL, backend.url)

    def test_projects(self):
        backend = PuppetForge(MOCK_HTTP_SERVER_URL)

        iterator = backend.projects()
        self.assertIsInstance(iterator, PuppetForgeProjectsIterator)

        projects = [p for p in iterator]
        self.assertEqual(39, len(projects))

    def test_releases(self):
        backend = PuppetForge(MOCK_HTTP_SERVER_URL)

        iterator = backend.releases('stdlib', 'puppetlabs')
        self.assertIsInstance(iterator, PuppetForgeReleasesIterator)

        releases = [r for r in iterator]
        self.assertEqual(30, len(releases))

class TestPuppetForgeFetcher(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = MockHTTPServer(HTTP_HOST, HTTP_PORT, TEST_FILES_DIRNAME,
                                   MockPuppetForgeHTTPHandler)
        cls.httpd.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.stop()

    def test_readonly_properties(self):
        fetcher = PuppetForgeFetcher(MOCK_HTTP_SERVER_URL)
        self.assertRaises(AttributeError, setattr, fetcher, 'last_url', MOCK_HTTP_SERVER_URL)
        self.assertEqual(None, fetcher.last_url)

    def test_projects_request(self):
        fetcher = PuppetForgeFetcher(MOCK_HTTP_SERVER_URL)

        json = fetcher.projects(0, 20)
        self.assertEqual(0, json['pagination']['offset'])
        self.assertEqual(20, json['pagination']['limit'])
        self.assertEqual(20, len(json['results']))

        json = fetcher.projects(20, 20)
        self.assertEqual(20, json['pagination']['offset'])
        self.assertEqual(20, json['pagination']['limit'])
        self.assertEqual(None, json['pagination']['next'])
        self.assertEqual(19, len(json['results']))

    def test_releases_request(self):
        fetcher = PuppetForgeFetcher(MOCK_HTTP_SERVER_URL)

        json = fetcher.releases('stdlib', 'puppetlabs', 0, 20)
        self.assertEqual(0, json['pagination']['offset'])
        self.assertEqual(20, json['pagination']['limit'])
        self.assertEqual(20, len(json['results']))

        json = fetcher.releases('stdlib', 'puppetlabs', 20, 20)
        self.assertEqual(20, json['pagination']['offset'])
        self.assertEqual(20, json['pagination']['limit'])
        self.assertEqual(None, json['pagination']['next'])
        self.assertEqual(10, len(json['results']))

        json = fetcher.releases('vagrant', 'mjanser', 0, 20)
        self.assertEqual(0, json['pagination']['offset'])
        self.assertEqual(20, json['pagination']['limit'])
        self.assertEqual(None, json['pagination']['next'])
        self.assertEqual(3, len(json['results']))

    def test_last_requested_url(self):
        test_modules_url_50 = MOCK_HTTP_SERVER_URL + '/v3/modules?limit=50&offset=0'
        test_modules_url_10 = MOCK_HTTP_SERVER_URL + '/v3/modules?limit=10&offset=20'
        test_releases_url_vagrant = MOCK_HTTP_SERVER_URL + '/v3/releases?limit=16&module=mjanser-vagrant&offset=8'

        fetcher = PuppetForgeFetcher(MOCK_HTTP_SERVER_URL)

        fetcher.projects(0, 50)
        self.assertEqual(test_modules_url_50, fetcher.last_url)

        fetcher.releases('vagrant', 'mjanser', 8, 16)
        self.assertEqual(test_releases_url_vagrant, fetcher.last_url)

        fetcher.projects(20, 10)
        self.assertEqual(test_modules_url_10, fetcher.last_url)


class TestPuppetForgeProjectsIterator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = MockHTTPServer(HTTP_HOST, HTTP_PORT, TEST_FILES_DIRNAME,
                                   MockPuppetForgeHTTPHandler)
        cls.httpd.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.stop()

    def test_is_iterable(self):
        import collections
        iterator = PuppetForgeProjectsIterator(MOCK_HTTP_SERVER_URL)
        self.assertIsInstance(iterator, collections.Iterable)

    def test_projects_iterator(self):
        iterator = PuppetForgeProjectsIterator(MOCK_HTTP_SERVER_URL)

        projects = [elem for elem in iterator]
        self.assertEqual(39, len(projects))

        for project in projects:
            self.assertIsInstance(project, Project)

    def test_projects_content(self):
        iterator = PuppetForgeProjectsIterator(MOCK_HTTP_SERVER_URL)

        projects = [elem for elem in iterator]

        project = projects[0]
        self.assertEqual('stdlib', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/puppetlabs-stdlib', project.url)
        self.assertEqual('2011-05-24 18:34:58', str(project.created_on))
        self.assertEqual('2014-05-14 04:41:21', str(project.updated_on))
        self.assertEqual(1, len(project.users))

        project = projects[1]
        self.assertEqual('concat', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/puppetlabs-concat', project.url)
        self.assertEqual('2013-08-09 17:55:07', str(project.created_on))
        self.assertEqual('2014-05-14 04:33:21', str(project.updated_on))
        self.assertEqual(1, len(project.users))

        project = projects[19]
        self.assertEqual('openldap', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/camptocamp-openldap', project.url)
        self.assertEqual('2014-02-07 00:02:42', str(project.created_on))
        self.assertEqual('2014-05-14 04:38:46', str(project.updated_on))
        self.assertEqual(1, len(project.users))

        project = projects[20]
        self.assertEqual('altlib', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/opentable-altlib', project.url)
        self.assertEqual('2014-03-20 09:19:47', str(project.created_on))
        self.assertEqual('2014-05-14 00:38:56', str(project.updated_on))
        self.assertEqual(1, len(project.users))

        project = projects[38]
        self.assertEqual('vagrant', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/mjanser-vagrant', project.url)
        self.assertEqual('2014-05-10 01:04:25', str(project.created_on))
        self.assertEqual('2014-05-14 04:34:00', str(project.updated_on))
        self.assertEqual(1, len(project.users))


    def test_projects_users(self):
        iterator = PuppetForgeProjectsIterator(MOCK_HTTP_SERVER_URL)

        projects = [elem for elem in iterator]

        a_user = projects[0].users[0]
        self.assertIsInstance(a_user, User)
        self.assertEqual('puppetlabs', a_user.username)

        b_user = projects[1].users[0]
        self.assertIsInstance(b_user, User)
        self.assertEqual('puppetlabs', b_user.username)

        # a_user and b_user must be the same
        self.assertEqual(a_user, b_user)

        # Check the rest of users
        user = projects[19].users[0]
        self.assertIsInstance(user, User)
        self.assertEqual('camptocamp', user.username)

        user = projects[20].users[0]
        self.assertIsInstance(user, User)
        self.assertEqual('opentable', user.username)

        user = projects[38].users[0]
        self.assertIsInstance(user, User)
        self.assertEqual('mjanser', user.username)


class TestPuppetForgeReleasesIterator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.httpd = MockHTTPServer(HTTP_HOST, HTTP_PORT, TEST_FILES_DIRNAME,
                                   MockPuppetForgeHTTPHandler)
        cls.httpd.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.stop()

    def test_is_iterable(self):
        import collections
        iterator = PuppetForgeReleasesIterator(MOCK_HTTP_SERVER_URL,
                                               'stdlib', 'puppetlabs')
        self.assertIsInstance(iterator, collections.Iterable)

    def test_releases_iterator(self):
        iterator = PuppetForgeReleasesIterator(MOCK_HTTP_SERVER_URL,
                                               'stdlib', 'puppetlabs')

        releases = [elem for elem in iterator]
        self.assertEqual(30, len(releases))

        for release in releases:
            self.assertIsInstance(release, Release)

    def test_releases_error_response(self):
        # The list should be empty and the iterator
        # print a warning message to the standard output
        if not hasattr(sys.stdout, 'getvalue'):
            self.fail('This test needs to run in buffered mode')

        # Force server to simulate an error while getting
        # info from releases
        iterator = PuppetForgeReleasesIterator(MOCK_HTTP_SERVER_URL,
                                               'error', 'raise')

        releases = [elem for elem in iterator]
        self.assertListEqual([], releases)

        output = sys.stdout.getvalue().strip()
        self.assertRegexpMatches(output, 'Warning: Invalid full modulename')

    def test_releases_content(self):
        iterator = PuppetForgeReleasesIterator(MOCK_HTTP_SERVER_URL,
                                               'stdlib', 'puppetlabs')

        releases = [elem for elem in iterator]

        release = releases[0]
        self.assertEqual('puppetlabs-stdlib', release.name)
        self.assertEqual('4.1.0', release.version)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/releases/puppetlabs-stdlib-4.1.0', release.url)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/files/puppetlabs-stdlib-4.1.0.tar.gz', release.file_url)
        self.assertEqual('2013-05-13 08:31:19', str(release.created_on))
        self.assertEqual('2013-05-13 08:31:19', str(release.updated_on))

        release = releases[1]
        self.assertEqual('puppetlabs-stdlib', release.name)
        self.assertEqual('3.2.0', release.version)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/releases/puppetlabs-stdlib-3.2.0', release.url)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/files/puppetlabs-stdlib-3.2.0.tar.gz', release.file_url)
        self.assertEqual('2012-11-28 14:53:03', str(release.created_on))
        self.assertEqual('2012-11-28 14:53:03', str(release.updated_on))

        release = releases[29]
        self.assertEqual('puppetlabs-stdlib', release.name)
        self.assertEqual('0.1.6', release.version)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/releases/puppetlabs-stdlib-0.1.6', release.url)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/files/puppetlabs-stdlib-0.1.6.tar.gz', release.file_url)
        self.assertEqual('2011-06-15 18:55:45', str(release.created_on))
        self.assertEqual('2011-06-15 18:55:45', str(release.updated_on))

        # Check releases from other project 
        iterator = PuppetForgeReleasesIterator(MOCK_HTTP_SERVER_URL,
                                               'vagrant', 'mjanser')

        releases = [elem for elem in iterator]
        self.assertEqual(3, len(releases))

        release = releases[0]
        self.assertEqual('mjanser-vagrant', release.name)
        self.assertEqual('1.1.0', release.version)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/releases/mjanser-vagrant-1.1.0', release.url)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/files/mjanser-vagrant-1.1.0.tar.gz', release.file_url)
        self.assertEqual('2014-05-10 03:48:43', str(release.created_on))
        self.assertEqual('2014-05-10 03:48:43', str(release.updated_on))

        release = releases[1]
        self.assertEqual('mjanser-vagrant', release.name)
        self.assertEqual('1.0.0', release.version)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/releases/mjanser-vagrant-1.0.0', release.url)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/files/mjanser-vagrant-1.0.0.tar.gz', release.file_url)
        self.assertEqual('2014-05-10 01:23:58', str(release.created_on))
        self.assertEqual('2014-05-10 03:48:35', str(release.updated_on))

        release = releases[2]
        self.assertEqual('mjanser-vagrant', release.name)
        self.assertEqual('0.1.0', release.version)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/releases/mjanser-vagrant-0.1.0', release.url)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/files/mjanser-vagrant-0.1.0.tar.gz', release.file_url)
        self.assertEqual('2014-05-10 01:04:45', str(release.created_on))
        self.assertEqual('2014-05-10 01:23:51', str(release.updated_on))


if __name__ == "__main__":
    unittest.main()
