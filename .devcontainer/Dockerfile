#!/bin/sh
# Copyright 2021 Universität Tübingen
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

# This is just the base image.
# Upon docker-compose launch,
# vscode will mount the source code
# of data meta and will install it
# from there.

FROM python:3.8

# install essential dependencies
RUN apt-get update -qq -y
RUN apt-get install -y \
    build-essential \
    postgresql-client \
    libmemcached-dev \
    gettext \
    nodejs \
    npm \
    less

# make docker util scripts available on path
# the "/workspace" will be mounted later by docker-compose
ENV PATH /workspace/docker/:$PATH
