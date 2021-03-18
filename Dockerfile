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

FROM continuumio/miniconda3:4.9.2-alpine

ENV PATH /opt/conda/bin/conda:$PATH

# Install psql client for pre-launch check and npm for frontend deps
RUN apk add postgresql-client npm

# Install requirements that would otherwise build from source or take long to install via conda
RUN conda install -c conda-forge gettext pylibmc psycopg2 pandas'=1.2.2' && conda clean --all

# Copy the datameta source into the container
COPY setup.py /tmp/datameta.src/
COPY datameta /tmp/datameta.src/datameta
COPY README.md /tmp/datameta.src/README.md
COPY CHANGES.md /tmp/datameta.src/CHANGES.md
COPY LICENSE.txt /tmp/datameta.src/LICENSE.txt
COPY MANIFEST.in /tmp/datameta.src/MANIFEST.in
COPY docker/launcher /usr/local/bin

# Install frontend deps
RUN npm install --prefix /tmp/datameta.src/datameta/static/

# Create a user to run datameta
RUN adduser --disabled-password --home /var/datameta datameta
RUN chown -R datameta /tmp/datameta.src

# Install datameta from the copied source
RUN pip install --no-cache-dir /tmp/datameta.src

# Copy the configuration file into the container
COPY conf/docker_production.ini /docker_production.ini

# Drop privileges
USER datameta

# Make sure we see Python's output in the logs
ENV PYTHONUNBUFFERED=1

# Launch the application
CMD launcher
