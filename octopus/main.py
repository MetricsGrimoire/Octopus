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

from argparse import ArgumentParser

from octopus.backends.puppet import PuppetForge
from octopus.database import Database
from octopus.model import Platform


def parse_args():
    parser = ArgumentParser(usage="Usage: '%(prog)s [options] URL")

    # Positional arguments
    parser.add_argument('url', help='URL used to fetch info about projects')

    # Required arguments
    parser.add_argument('-b', '--backend', dest='backend',
                        help='Backend used to fetch projects info', required=True,
                        choices=['puppet'])

    # Database options
    group = parser.add_argument_group('Database options')
    group.add_argument('-u', '--user', dest='db_user',
                       help='Database user name',
                       default='root')
    group.add_argument('-p', '--password', dest='db_password',
                       help='Database user password',
                       default='')
    group.add_argument('-d', dest='db_name',
                       help='Name of the database where fetched projects will be stored')
    group.add_argument('--host', dest='db_hostname',
                       help='Name of the host where the database server is running',
                       default='localhost')
    group.add_argument('--port', dest='db_port',
                       help='Port of the host where the database server is running',
                       default='3306')

    # Debugging parameter
    parser.add_argument('-g', '--debug', help='Enable debug mode',
                       action='store_true', dest='debug',
                       default=False)

    # Parse arguments
    args = parser.parse_args()

    return args


def fetch(url, platform_type, debug=False):
    if platform_type != 'puppet':
        return None

    # Create the object to retrieve the projects
    forge = PuppetForge(url)

    # Define the platform
    platform = Platform()
    platform.type = 'puppet'
    platform.url = url

    print('Fetching projects from %s' % url)

    # Fetch projects and releases from the forge
    for project in forge.projects():
        user = project.users[0]
        for release in forge.releases(project.name, user.username):
            user.releases.append(release)
            project.releases.append(release)
        platform.projects.append(project)
        if(debug):
            print('Project %s fetched' % project.name)

    print('Fetch process completed')

    return platform


def store(user, password, database, instance):
    # Insert retrieved data into the database
    db = Database(user, password, database)
    db.connect()
    db.add(instance)
    db.disconnect()


def main():
    args = parse_args()
    platform = fetch(args.url, args.backend, args.debug)
    store(args.db_user, args.db_password, args.db_name, platform)
