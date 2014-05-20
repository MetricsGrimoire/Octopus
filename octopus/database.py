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
#         Santiago Dueñas <sduenas@bitergia.com>
#

from sqlalchemy import create_engine
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker

from octopus.model import ModelBase


class Database(object):

    def __init__(self, user, password, database, host='localhost', port='3306'):
        # Create an engine
        self.url = URL('mysql', user, password, host, port, database)
        self._engine = create_engine(self.url, echo=True)
        self._session = None

        # Create the schema on the database.
        # It won't replace any existing schema
        ModelBase.metadata.create_all(self._engine)

    def connect(self):
        if not self._session:
            Session = sessionmaker(bind=self._engine)
            self._session = Session()

    def disconnect(self):
        if self._session:
            self._session.close()

    def add(self, instance):
        try:
            self._session.add(instance)
            self._session.commit()
        except:
            self._session.rollback()
