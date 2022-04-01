# Copyright 2021 Universität Tübingen, DKFZ and EMBL for the German Human Genome-Phenome Archive (GHGA)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
    String,
    Table
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref

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


user_service_table = Table('service_user', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('service_id', Integer, ForeignKey('services.id'))
)


class Group(Base):
    __tablename__    = 'groups'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    name             = Column(Text, nullable=False, unique=True)
    # Relationships
    user             = relationship('User', back_populates='group')
    submissions      = relationship('Submission', back_populates='group')
    regrequests      = relationship('RegRequest', back_populates='group')


class User(Base):
    __tablename__        = 'users'
    id                   = Column(Integer, primary_key=True)
    uuid                 = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    site_id              = Column(String(50), unique=True, nullable=False, index=True)
    email                = Column(Text, unique=True)
    fullname             = Column(Text)
    pwhash               = Column(String(60))
    group_id             = Column(Integer, ForeignKey('groups.id'), nullable=False)
    enabled              = Column(Boolean(create_constraint=False), nullable=False)
    site_admin           = Column(Boolean(create_constraint=False), nullable=False)
    group_admin          = Column(Boolean(create_constraint=False), nullable=False)
    site_read            = Column(Boolean(create_constraint=False), nullable=False)
    tfa_secret           = Column(Text)

    # Relationships
    group                = relationship('Group', back_populates='user')
    metadatasets         = relationship('MetaDataSet', back_populates='user')
    files                = relationship('File', back_populates='user')
    passwordtokens       = relationship('PasswordToken', back_populates='user')
    apikeys              = relationship('ApiKey', back_populates='user')
    services             = relationship('Service', secondary=user_service_table, back_populates='users')
    service_executions   = relationship('ServiceExecution', back_populates='user')
    tfatokens            = relationship('TfaToken', back_populates='user')
    used_passwords       = relationship('UsedPassword', back_populates='user')
    login_attempts       = relationship("LoginAttempt", back_populates='user', cascade="all, delete-orphan")


class LoginAttempt(Base):
    __tablename__    = 'loginattempts'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    timestamp        = Column(DateTime, nullable=False)
    # Relationships
    user             = relationship('User', back_populates='login_attempts')


class ApiKey(Base):
    __tablename__    = 'apikeys'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    value            = Column(String(64), nullable=False, unique=True)
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


class TfaToken(Base):
    __tablename__ = 'tfatokens'
    id            = Column(Integer, primary_key=True)
    uuid          = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id       = Column(Integer, ForeignKey('users.id'), nullable=False)
    value         = Column(Text, nullable=False, unique=True)
    expires       = Column(DateTime, nullable=False)
    secret        = Column(Text, default=None)
    # Relationships
    user          = relationship('User', back_populates='tfatokens')


class UsedPassword(Base):
    __tablename__ = 'usedpasswords'
    id            = Column(Integer, primary_key=True)
    uuid          = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id       = Column(Integer, ForeignKey('users.id'), nullable=False)
    pwhash        = Column(Text, nullable=False, unique=True)

    # Relationships
    user          = relationship('User', back_populates='used_passwords')


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
    access_token     = Column(String(64), nullable=True)
    content_uploaded = Column(Boolean(create_constraint=False), nullable=False)
    checksum         = Column(Text, nullable=False)
    filesize         = Column(BigInteger, nullable=True)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    upload_expires   = Column(DateTime, nullable=True)
    # Relationships
    metadatumrecord  = relationship('MetaDatumRecord', back_populates='file', uselist=False)
    user             = relationship('User', back_populates='files')
    downloadtokens  = relationship('DownloadToken', back_populates='file')


class DownloadToken(Base):
    __tablename__    = 'downloadtokens'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    file_id          = Column(Integer, ForeignKey('files.id'), nullable=False)
    value            = Column(Text, nullable=False, unique=True)
    expires          = Column(DateTime, nullable=False)
    # Relationships
    file             = relationship('File', back_populates='downloadtokens')


class Submission(Base):
    __tablename__    = 'submissions'
    id               = Column(Integer, primary_key=True)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    date             = Column(DateTime)
    label            = Column(String(100), nullable=True)
    group_id         = Column(Integer, ForeignKey('groups.id'), nullable=False)
    # Relationships
    metadatasets     = relationship('MetaDataSet', back_populates='submission')
    group            = relationship('Group', back_populates='submissions')


class MetaDatum(Base):
    __tablename__      = 'metadata'
    id                 = Column(Integer, primary_key=True)
    uuid               = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    name               = Column(Text, nullable=False)
    regexp             = Column(Text, nullable=True)
    short_description  = Column(Text, nullable=True)
    long_description   = Column(Text, nullable=True)
    datetimefmt        = Column(Text, nullable=True)
    datetimemode       = Column(Enum(DateTimeMode), nullable=True)
    mandatory          = Column(Boolean(create_constraint=False), nullable=False)
    example            = Column(Text, nullable=False)
    order              = Column(Integer, nullable=False)
    isfile             = Column(Boolean(create_constraint=False), nullable=False)
    submission_unique  = Column(Boolean(create_constraint=False), nullable=False)
    site_unique        = Column(Boolean(create_constraint=False), nullable=False)
    service_id         = Column(Integer, ForeignKey('services.id'), nullable=True)
    # Relationships
    metadatumrecords   = relationship('MetaDatumRecord', back_populates='metadatum')
    service            = relationship('Service', back_populates='target_metadata')


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
    id               = Column(Integer, primary_key=True)
    site_id          = Column(String(50), unique=True, nullable=False, index=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    submission_id    = Column(Integer, ForeignKey('submissions.id'), nullable=True)
    is_deprecated    = Column(Boolean, default=False)
    deprecated_label = Column(String, nullable=True)
    replaced_by_id   = Column(Integer, ForeignKey('metadatasets.id'), nullable=True)
    # Relationships
    user                 = relationship('User', back_populates='metadatasets')
    submission           = relationship('Submission', back_populates='metadatasets')
    metadatumrecords     = relationship('MetaDatumRecord', back_populates='metadataset')
    replaces             = relationship('MetaDataSet', backref=backref('replaced_by', remote_side=[id]))
    service_executions   = relationship('ServiceExecution', back_populates = 'metadataset')


class ApplicationSetting(Base):
    __tablename__ = 'appsettings'
    id           = Column(Integer, primary_key=True)
    uuid         = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    key          = Column(Text, unique=True, nullable=False)
    int_value    = Column(Integer, nullable=True)
    str_value    = Column(Text, nullable=True)
    float_value  = Column(Float, nullable=True)
    date_value   = Column(Date, nullable=True)
    time_value   = Column(Time, nullable=True)


class Service(Base):
    __tablename__ = 'services'
    id           = Column(Integer, primary_key=True)
    uuid         = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    site_id      = Column(String(50), unique=True, nullable=False, index=True)
    name         = Column(Text, nullable=True, unique=True)
    # Relationships
    users           = relationship('User', secondary=user_service_table, back_populates='services')
    # unfortunately, 'metadata' is a reserved keyword for sqlalchemy classes
    service_executions   = relationship('ServiceExecution', back_populates = 'service')
    target_metadata      = relationship('MetaDatum', back_populates = 'service')
    users                = relationship('User',
            secondary=user_service_table,
            back_populates='services')


class ServiceExecution(Base):
    __tablename__    = 'serviceexecutions'
    id               = Column(Integer, primary_key=True)
    uuid             = Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, nullable=False)
    service_id       = Column(Integer, ForeignKey('services.id'), nullable=False)
    user_id          = Column(Integer, ForeignKey('users.id'), nullable=False)
    metadataset_id   = Column(Integer, ForeignKey('metadatasets.id'), nullable=False)
    datetime         = Column(DateTime, nullable=False)
    # Relationships
    metadataset      = relationship('MetaDataSet', back_populates='service_executions')
    service          = relationship('Service', back_populates='service_executions')
    user             = relationship('User', back_populates='service_executions')
