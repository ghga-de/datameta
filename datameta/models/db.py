# Copyright (c) 2021 Leon Kuchenbecker <leon.kuchenbecker@uni-tuebingen.de>
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
    Index,
    Integer,
    Float,
    Text,
    ForeignKey,
    Date,
    Time,
    DateTime
)
from sqlalchemy.orm import relationship

from .meta import Base

class Group(Base):
    __tablename__    = 'groups'
    id               = Column(Integer, primary_key=True)
    name             = Column(Text, nullable=False)
    # Relationships
    user             = relationship('User', back_populates='group')
    metadatasets     = relationship('MetaDataSet', back_populates='group')

class User(Base):
    __tablename__    = 'users'
    id               = Column(Integer, primary_key=True)
    email            = Column(Text, unique=True)
    fullname         = Column(Text)
    pwhash           = Column(Text)
    group_id         = Column(Integer, ForeignKey('groups.id'), nullable=False)
    # Relationships
    group            = relationship('Group', back_populates='user')
    metadatasets            = relationship('MetaDataSet', back_populates='user')

class File(Base):
    __tablename__    = 'files'
    id               = Column(Integer, primary_key=True)
    name             = Column(Text, nullable=False)
    # Relationships
    metadatumrecord   = relationship('MetaDatumRecord', back_populates='file')

class Submission(Base):
    __tablename__    = 'submissions'
    id               = Column(Integer, primary_key=True)
    date             = Column(DateTime)
    # Relationships
    metadatasets     = relationship('MetaDataSet', back_populates='submission')

class MetaDatum(Base):
    __tablename__    = 'metadata'
    id               = Column(Integer, primary_key=True)
    name             = Column(Text, nullable=False)
    regexp           = Column(Text, nullable=True)
    datetimefmt      = Column(Text, nullable=True)
    # Relationships
    metadatumrecords  = relationship('MetaDatumRecord', back_populates='metadatum')

class MetaDatumRecord(Base):
    __tablename__    = 'metadatumrecords'
    id               = Column(Integer, primary_key=True)
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
    key          = Column(Text, unique=True, nullable=False)
    int_value    = Column(Integer, nullable=True)
    str_value    = Column(Text, nullable=True)
    float_value  = Column(Float, nullable=True)
    date_value   = Column(Date, nullable=True)
    time_value   = Column(Time, nullable=True)
