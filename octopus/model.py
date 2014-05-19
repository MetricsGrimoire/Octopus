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

from sqlalchemy import Table, Column, DateTime, Integer, String, ForeignKey
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


projects_users_table = Table('projects_users', ModelBase.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)


class Project(ModelBase):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    url = Column(String(128))
    created_on = Column(DateTime())
    updated_on = Column(DateTime())
    platform_id = Column(Integer, ForeignKey('platforms.id'))

    # many to many projects-users relationship
    users = relationship("User", secondary=projects_users_table)

    # one to many projects-releases relationship
    releases = relationship("Release", backref='project_releases')


class User(ModelBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = name = Column(String(32))

    releases = relationship("Release", backref='user_releases')


class Release(ModelBase):
    __tablename__ = 'releases'

    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    version = Column(String(32))
    url = Column(String(128))
    file_url = Column(String(128))
    created_on = Column(DateTime())
    updated_on = Column(DateTime())
    author_id = Column(Integer, ForeignKey('users.id'))
    project_id = Column(Integer, ForeignKey('projects.id'))
