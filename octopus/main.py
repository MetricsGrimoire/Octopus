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
from octopus.model import Platform, User, Project, Release


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


def fetch_and_store(url, platform_type, session, debug=False):
    if platform_type != 'puppet':
        return

    np = 0
    tp = 0
    nr = 0
    tr = 0

    platform = session.query(Platform).\
        filter(Platform.url == url).first()

    if not platform:
        platform = Platform()
        platform.type = 'puppet'
        platform.url = url
        session.add(platform)

        if debug:
            print('Platform %s added' % platform)
    elif debug:
        print('Platform %s already stored' % platform)

    # Create the object to retrieve the projects
    forge = PuppetForge(url)

    print('Fetching projects from %s' % url)

    # Fetch projects and releases from the forge
    for project in forge.projects():
        user = project.users.pop(0)

        stored_user = session.query(User).\
            filter(User.username == user.username).first()

        if not stored_user:
            session.add(user)
            stored_user = user

        for release in forge.releases(project.name, stored_user.username):
            release.project = project
            project.releases.append(release)

        if debug:
            print('Project %s fetched' % project.name)

        stored_project = session.query(Project).\
            filter(Project.url == project.url).first()

        tp += 1

        if not stored_project:
            project.platform_id = platform.id
            session.add(project)

            np += 1
            nr += len(project.releases)
            tr += len(project.releases)

            if debug:
                print('Project %s and related releases inserted' % project)
        else:
            if debug:
                print('Project %s already stored' % project)

            for release in project.releases:
                tr += 1

                stored_release = session.query(Release).\
                    filter(Release.name == release.name,
                           Release.version == release.version,
                           Release.project == stored_project)

                if not stored_release:
                    user.releases.append(release)
                    release.project_id = stored_project.id
                    session.add(release)

                    nr += 1

                    if debug:
                        print('Release %s inserted' % release)
                elif debug:
                    print('Release %s already stored' % release)

    print('Fetch and storage processes completed')
    print('Total %d/%d of new projects inserted' % (np, tp))
    print('Total %d/%d of new releases inserted' % (nr, tr))


def main():
    args = parse_args()

    db = Database(args.db_user, args.db_password, args.db_name)

    with db.connect() as session:
        fetch_and_store(args.url, args.backend, session, args.debug)
