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


def main():
    args = parse_args()

    db = Database(args.db_user, args.db_password, args.db_name)
    session = db.connect()

    if args.backend != 'puppet':
        return

    backend = PuppetForge(args.url, session)

    platform = backend.fetch()
    print('Fetch processes completed')

    store(db, session, platform)
    print('Storage processes completed')

    session.close()


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


def store(db, session, platform):
    try:
        db.store(session, platform)
    except Exception, e:
        raise RuntimeError(str(e))
