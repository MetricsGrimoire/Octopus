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
#         Daniel Izquierdo <dizquierdo@bitergia.com>
#

from sqlalchemy import select

class Query(object):
    """Use to query database and export data"""

    def __init__(self, session, alchemy_object):
        self.session = session
        self.alchemy_object = alchemy_object

    def data(self):
        return self.session.execute(select([self.alchemy_object]))
