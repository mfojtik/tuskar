# vim: tabstop=4 shiftwidth=4 softtabstop=4
# -*- encoding: utf-8 -*-
#
# Copyright 2013 Hewlett-Packard Development Company, L.P.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
SQLAlchemy models.
"""

import json
import urlparse
import logging

from oslo.config import cfg

from sqlalchemy import Column, ForeignKey
from sqlalchemy import Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, VARCHAR
from sqlalchemy.orm import relationship

from tuskar.openstack.common.db.sqlalchemy import models

sql_opts = [
    cfg.StrOpt('mysql_engine',
               default='InnoDB',
               help='MySQL engine')
]

cfg.CONF.register_opts(sql_opts)


logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def table_args():
    engine_name = urlparse.urlparse(cfg.CONF.database_connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': cfg.CONF.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""

    impl = VARCHAR

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class TuskarBase(models.TimestampMixin,
                 models.ModelBase):

    metadata = None

    def as_dict(self):
        d = {"id": self['id']}
        for c in self.__table__.columns:
            if c.name == 'id':
                continue
            if c.name.endswith('_url'):
                d[c.name.replace('_url', '')] = {
                        'links': [
                                {"rel": "self", "url": self[c.name]}
                            ]
                        }
            else:
                d[c.name] = self[c.name]
        return d


Base = declarative_base(cls=TuskarBase)


class Blaa(Base):
    """Represents a blaa."""

    __tablename__ = 'blaas'
    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), unique=True)
    description = Column(Text, nullable=True)


class Sausage(Base):
    """Represents a sausage."""

    __tablename__ = 'sausages'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    blaa_id = Column(Integer, ForeignKey('blaas.id'), nullable=True)


class Capacity(Base):
    """Represents a Capacity."""

    __tablename__ = 'capacities'
    id = Column(Integer, primary_key=True)
    name = Column(String(length=64))
    value = Column(String(length=128))


class RackCapacities(Base):
    """Represents a many-to-many relation between Rack and Capacity"""

    __tablename__ = 'rack_capacities'
    id = Column(Integer, primary_key=True)
    rack_id = Column(Integer, ForeignKey('racks.id'), primary_key=True)
    capacity_id = Column(Integer, ForeignKey('capacities.id'),
            primary_key=True)


class Rack(Base):
    """Represents a Rack."""

    __tablename__ = 'racks'
    id = Column(Integer, primary_key=True)
    name = Column(Text, unique=True)
    slots = Column(Integer)
    subnet = Column(String(length=64))
    chassis_url = Column(Text)
    capacities = relationship("Capacity",
            secondary=Base.metadata.tables['rack_capacities'],
            lazy='joined')

    def as_dict(self):
        d = super(Rack, self).as_dict()

        def convert_capacity(c):
            return {'name': c.name, 'value': c.value}

        d['capacities'] = [convert_capacity(c) for c in self['capacities']]

        return d
