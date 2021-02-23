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