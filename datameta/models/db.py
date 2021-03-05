# Copyright (c) 2021 Universität Tübingen, Germany
# Authors: Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from sqlalchemy import (
    Column,
    Enum,
    Boolean,
    Integer,
    BigInteger,
    Float,
    Text,
    ForeignKey,
    Date,
    Time,
    DateTime,
    String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .meta import Base

import datetime
import uuid
import enum

class DateTimeMode(enum.Enum):
    DATE      = 0
    DATETIME  = 1
    TIME      = 2

    def type(self):
        if self.value == 0:
            return datetime.date
        if self.value == 1:
            return datetime.datetime
        if self.value == 2:
            return datetime.time

class Group(Base):
    __tablename__    = 'groups'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    name             = Column(Text, nullable=False)
    # Relationships
    user             = relationship('User', back_populates='group')
    metadatasets     = relationship('MetaDataSet', back_populates='group')
    files            = relationship('File', back_populates='group')
    regrequests      = relationship('RegRequest', back_populates='group')

class User(Base):
    __tablename__    = 'users'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    email            = Column(Text, unique=True)
    fullname         = Column(Text)
    pwhash           = Column(String(60))
    group_id         = Column(Integer, ForeignKey('groups.id'), nullable=False)
    enabled          = Column(Boolean(create_constraint=False), nullable=False)
    site_admin       = Column(Boolean(create_constraint=False), nullable=False)
    group_admin      = Column(Boolean(create_constraint=False), nullable=False)
    # Relationships
    group            = relationship('Group', back_populates='user')
    metadatasets     = relationship('MetaDataSet', back_populates='user')
    files            = relationship('File', back_populates='user')
    passwordtokens   = relationship('PasswordToken', back_populates='user')
    apikeys          = relationship('ApiKey', back_populates='user')

class ApiKey(Base):
    __tablename__    = 'apikeys'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    value            = Column(String(64), nullable=False)
    label            = Column(String(200))
    expires          = Column(DateTime, nullable=True)
    # Relationships
    user             = relationship('User', back_populates='apikeys')

class PasswordToken(Base):
    __tablename__    = 'passwordtokens'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    value            = Column(Text, nullable=False, unique=True)
    expires          = Column(DateTime, nullable=False)
    # Relationships
    user             = relationship('User', back_populates='passwordtokens')

class RegRequest(Base):
    __tablename__    = 'regrequests'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    fullname         = Column(Text, nullable=False)
    email            = Column(Text, nullable=False)
    group_id         = Column(Integer, ForeignKey('groups.id'), nullable=True)
    new_group_name   = Column(Text)
    # Relationships
    group            = relationship('Group', back_populates='regrequests')

class File(Base):
    __tablename__    = 'files'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    name             = Column(Text, nullable=False)
    storage_uri      = Column(String(2048), unique=True, nullable=True)
    content_uploaded = Column(Boolean(create_constraint=False), nullable=False)
    checksum         = Column(Text, nullable=False)
    filesize         = Column(BigInteger, nullable=True)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    group_id         = Column(Integer, ForeignKey('groups.id'), nullable=False)
    upload_expires   = Column(DateTime, nullable=True)
    # Relationships
    metadatumrecord  = relationship('MetaDatumRecord', back_populates='file', uselist=False)
    group            = relationship('Group', back_populates='files')
    user             = relationship('User', back_populates='files')

class Submission(Base):
    __tablename__    = 'submissions'
    id               = Column(Integer, primary_key=True)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    date             = Column(DateTime)
    # Relationships
    metadatasets     = relationship('MetaDataSet', back_populates='submission')

class MetaDatum(Base):
    __tablename__      = 'metadata'
    id                 = Column(Integer, primary_key=True)
    uuid               = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name               = Column(Text, nullable=False)
    regexp             = Column(Text, nullable=True)
    lintmessage        = Column(Text, nullable=True)
    datetimefmt        = Column(Text, nullable=True)
    datetimemode       = Column(Enum(DateTimeMode), nullable=True)
    mandatory          = Column(Boolean(create_constraint=False), nullable=False)
    order              = Column(Integer, nullable=False)
    isfile             = Column(Boolean(create_constraint=False), nullable=False)
    submission_unique  = Column(Boolean(create_constraint=False), nullable=False)
    site_unique        = Column(Boolean(create_constraint=False), nullable=False)
    # Relationships
    metadatumrecords   = relationship('MetaDatumRecord', back_populates='metadatum')

class MetaDatumRecord(Base):
    __tablename__    = 'metadatumrecords'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    metadatum_id     = Column(Integer, ForeignKey('metadata.id'), nullable=False)
    metadataset_id   = Column(Integer, ForeignKey('metadatasets.id'), nullable=False)
    file_id          = Column(Integer, ForeignKey('files.id'), nullable=True)
    value            = Column(Text, nullable=True)
    # Relationships
    metadatum        = relationship('MetaDatum', back_populates='metadatumrecords')
    metadataset      = relationship('MetaDataSet', back_populates='metadatumrecords')
    file             = relationship('File', back_populates='metadatumrecord')

class MetaDataSet(Base):
    """A MetaDataSet represents all metadata associated with *one* record"""
    __tablename__  = 'metadatasets'
    id             = Column(Integer, primary_key=True)
    site_id        = Column(String(50), unique=True, nullable=False, index=True)
    uuid           = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id        = Column(Integer, ForeignKey('users.id'), nullable=False)
    group_id       = Column(Integer, ForeignKey('groups.id'), nullable=False)
    submission_id  = Column(Integer, ForeignKey('submissions.id'), nullable=True)
    # Relationships
    group            = relationship('Group', back_populates='metadatasets')
    user             = relationship('User', back_populates='metadatasets')
    submission       = relationship('Submission', back_populates='metadatasets')
    metadatumrecords = relationship('MetaDatumRecord', back_populates='metadataset')

class ApplicationSettings(Base):
    __tablename__ = 'appsettings'
    id           = Column(Integer, primary_key=True)
    uuid         = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    key          = Column(Text, unique=True, nullable=False)
    int_value    = Column(Integer, nullable=True)
    str_value    = Column(Text, nullable=True)
    float_value  = Column(Float, nullable=True)
    date_value   = Column(Date, nullable=True)
    time_value   = Column(Time, nullable=True)
