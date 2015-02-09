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

from sqlalchemy import Table, Column, DateTime, Integer, String,\
    ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


ModelBase = declarative_base()


class UniqueObject(object):

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError

    @classmethod
    def as_unique(cls, session, *arg, **kw):
        return _unique(
                    session,
                    cls,
                    cls.unique_filter,
                    cls,
                    arg, kw
               )


class Platform(UniqueObject, ModelBase):
    __tablename__ = 'platforms'

    id = Column(Integer, primary_key=True)
    url = Column(String(128))
    type = Column(String(32))

    projects = relationship("Project", backref='platforms')

    __table_args__ = (UniqueConstraint('url', name='_url_unique'),
                      {'mysql_charset': 'utf8'})


    def __repr__(self):
        return self.url

    @classmethod
    def unique_filter(cls, query, url):
        return query.filter(Platform.url == url)


projects_users_table = Table('projects_users', ModelBase.metadata,
    Column('project_id', Integer, ForeignKey('projects.id')),
    Column('user_id', Integer, ForeignKey('users.id'))
)


class Project(UniqueObject, ModelBase):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(32))
    url = Column(String(128))
    created_on = Column(DateTime())
    updated_on = Column(DateTime())
    platform_id = Column(Integer, ForeignKey('platforms.id'))

    # one to one project-platform relationship
    platform = relationship("Platform", backref='project_platform')

    # many to many projects-users relationship
    users = relationship("User", secondary=projects_users_table)

    # one to many projects-releases relationship
    releases = relationship("Release", backref='project_releases')

    __table_args__ = (UniqueConstraint('url', 'platform_id', name='_project_unique'),
                      {'mysql_charset': 'utf8'})

    @classmethod
    def unique_filter(cls, query, name, platform):
        return query.filter(Project.name == name,
                            Project.platform == platform)

    def __repr__(self):
        return self.name


class User(UniqueObject, ModelBase):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(32))
    email = Column(String(128))

    releases = relationship("Release", backref='user_releases')

    __table_args__ = (UniqueConstraint('username', name='_username_unique'),
                      {'mysql_charset': 'utf8'})

    @classmethod
    def unique_filter(cls, query, username):
        return query.filter(User.username == username)

    def __repr__(self):
        return self.username


class Release(UniqueObject, ModelBase):
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

    # one to one release-user relationship
    user = relationship("User", backref='release_user')

    # one to one release-project relationship
    project = relationship("Project", backref='release_project')

    __table_args__ = (UniqueConstraint('name', 'version', 'author_id', name='_release_unique'),
                      {'mysql_charset': 'utf8'})

    @classmethod
    def unique_filter(cls, query, name, version, user):
        return query.filter(Release.name == name,
                            Release.version == version,
                            Release.user == user)

    def __repr__(self):
        return "%s (%s)" % (self.name, self.version)


def _unique(session, cls, queryfunc, constructor, arg, kw):
    with session.no_autoflush:
        q = session.query(cls)
        q = queryfunc(q, *arg, **kw)

        obj = q.first()

        if not obj:
            obj = constructor(*arg, **kw)

        session.add(obj)
    return obj
