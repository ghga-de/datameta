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
