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

from argparse import ArgumentParser

from octopus.backends.docker import DockerRegistry
from octopus.backends.github import GitHubPlatform
from octopus.backends.puppet import PuppetForge
from octopus.backends.gerrit import Gerrit
from octopus.database import Database


def main():
    args = parse_args()

    db = Database(args.db_user, args.db_password, args.db_name)
    session = db.connect()

    if args.backend == 'docker':
        backend = DockerRegistry(session, args.url,
                                 args.owner, args.repository)
    elif args.backend == 'puppet':
        backend = PuppetForge(session, args.url)
    elif args.backend == 'github':
        backend = GitHubPlatform(session, owner=args.owner, repository=args.repository,
                                 url=args.gh_url, user=args.gh_user, password=args.gh_password,
                                 oauth_token=args.gh_token)
    elif args.backend == 'gerrit':
        backend = Gerrit(session, gerrit_user=args.gerrit_user, gerrit_url=args.gerrit_url)
    else:
        print('Backend %s not found' % args.backend)
        return

    if args.export:
        # This write in stdout info linked to the selected backend
        backend.export()
    else:
        print('Fetching...')
        if args.backend == 'gerrit':
            # Restart the database
            db.clear()
        platform = backend.fetch()
        print('Fetch processes completed')

        store(db, session, platform)
        print('Storage processes completed')

    session.close()


def parse_args():
    parser = ArgumentParser()

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

    # Add specific backend subparsers
    subparsers = parser.add_subparsers(dest='backend',
                                       help='Backend help')

    DockerRegistry.set_arguments_subparser(subparsers)
    GitHubPlatform.set_arguments_subparser(subparsers)
    PuppetForge.set_arguments_subparser(subparsers)
    Gerrit.set_arguments_subparser(subparsers)

    # Parse arguments
    args = parser.parse_args()

    return args


def store(db, session, platform):
    try:
        db.store(session, platform)
    except Exception, e:
        raise RuntimeError(str(e))
