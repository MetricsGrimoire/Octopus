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
    PuppetForgeProjectsIterator
from octopus.model import Project
from mock_http_server import MockHTTPServer
from utils import read_file


# HTTP server configuration
HTTP_HOST = 'localhost'
HTTP_PORT = 9999
TEST_FILES_DIRNAME = 'data'
TIMEOUT = 5
MOCK_HTTP_SERVER_URL = 'http://' + HTTP_HOST + ':' + str(HTTP_PORT)

PUPPET_MODULES_1 = 'puppet_modules_1.json'
PUPPET_MODULES_2 = 'puppet_modules_2.json'


class MockPuppetForgeHTTPHandler(BaseHTTPRequestHandler):
    """Mock Puppet Forge requests handler"""

    def do_GET(self):
        parts = urlparse.urlparse(self.path)
        qs = self._parse_GET_query(parts.query)

        if parts.path == '/v3/modules':
            self.projects(qs)
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

    def not_found(self):
        self.send_error(404, 'Not found')

    def _parse_GET_query(self, query):
        if not query:
            return None
        return urlparse.parse_qs(query)


class TestPuppetForge(unittest.TestCase):

    def test_backend(self):
        backend = PuppetForge()
        self.assertIsInstance(backend, Backend)
        self.assertEqual('puppet', backend.name)


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

    def test_last_requested_url(self):
        test_modules_url_50 = MOCK_HTTP_SERVER_URL + '/v3/modules?limit=50&offset=0'
        test_modules_url_10 = MOCK_HTTP_SERVER_URL + '/v3/modules?limit=10&offset=20'

        fetcher = PuppetForgeFetcher(MOCK_HTTP_SERVER_URL)

        fetcher.projects(0, 50)
        self.assertEqual(test_modules_url_50, fetcher.last_url)

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

        project = projects[1]
        self.assertEqual('concat', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/puppetlabs-concat', project.url)

        project = projects[19]
        self.assertEqual('openldap', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/camptocamp-openldap', project.url)

        project = projects[20]
        self.assertEqual('altlib', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/opentable-altlib', project.url)

        project = projects[38]
        self.assertEqual('vagrant', project.name)
        self.assertEqual(MOCK_HTTP_SERVER_URL + '/v3/modules/mjanser-vagrant', project.url)


if __name__ == "__main__":
    unittest.main()
