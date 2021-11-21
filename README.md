# DataMeta - submission server for data and associated metadata

Data submission made easy! DataMeta allows you to easily define sample sheet columns, value
constraints for the sample sheet and columns which are associated with raw data file names.

DataMeta is quick and easy to deploy on your local infrastructure and scales for high numbers of
users!

![demo](./img/datameta.demo.gif?raw=true)

## Quick Installation

1. Create a directory for the datameta configuration (of your choice)
   ```
   mkdir /usr/local/lib/datameta
   cd /usr/local/lib/datameta
   ```

1. Edit the configuration file

   The fields that require changing are marked with `# CHANGEME`. You may want
   to perform additional adjustments to the compose file to fit your needs.

1. Download the Docker compose file
   ```
   curl -LO https://datameta.org/minimal/docker-compose.yml
   ```

1. Create the Docker volumes for persistent file and database storage
   ```
   docker volume create datameta-db
   docker volume create datameta-filestorage
   ```

1. Start up your DataMeta Instance
   ```
   docker-compose up -d
   ```
