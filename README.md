# DataMeta - submission server for data and associated metadata

Data submission made easy! DataMeta allows you to easily define sample sheet columns, value
constraints for the sample sheet and columns which are associated with raw data file names.

DataMeta is quick and easy to deploy on your local infrastructure and scales for high numbers of
users!

![demo](./img/datameta.demo.gif?raw=true)

## Quick Installation

1. Download the Docker compose file
   ```
   curl -LO https://raw.githubusercontent.com/ghga-de/datameta/main/datameta.compose.yml
   ```

1. Create the Docker volumes for persistent file and database storage
   ```
   docker volume create datameta-db
   docker volume create datameta-filestorage
   ```

1. Start up your DataMeta Instance
   ```
   docker stack deploy --compose-file datameta.compose.yml datameta
   ```

1. Connect to your DataMeta instance at http://localhost:9950 and log in with the default
   account `admin@admin.admin`. The initial password can be obtained using
   `docker logs {your_app_container_id}`.

## Full Installation Instructions

Detailed installation instructions can be found [here](./docs).
