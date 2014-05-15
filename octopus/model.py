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

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

# FIXME: add unique checks


ModelBase = declarative_base()


class Platform(ModelBase):
    __tablename__ = 'platforms'

    id = Column(Integer, primary_key=True)
    url = Column(String(128))
    type = Column(String(32))

    projects = relationship("Project", backref='platforms')


class Project(ModelBase):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    url = Column(String(128))
    platform_id = Column(Integer, ForeignKey('platforms.id'))

