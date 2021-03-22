# Local Installation

Install dependencies, e.g. via [brew](https://brew.sh/).

```
brew install postgresql memcached libmemcached npm
```

Register postgresql as a service

```
brew services start postgresql
```


Clone this repository:
```
git clone https://github.com/ghga-de/datameta.git
```

Change directory into your newly created project if not already there. Your
  current directory should be the same as this README.md file and setup.py.

```
cd datameta
```

Create a Python virtual environment, if not already created.

This can be done via `venv`:

```
python3 -m venv <environment_name>
```

or `conda`:

```
conda create -y -n <environment_name> 'python>3'
```

Activate the environment

With `venv` ([docs](https://docs.python.org/3/tutorial/venv.html)):

```
source <path/to/environment>/bin/activate
```

With conda

```
conda activate <environment_name>
```

Upgrade packaging tools, if necessary.

```
pip install --upgrade pip setuptools
```

Install NPM dependencies

```
npm install --prefix datameta/static/
```

Install the project in editable mode with its testing requirements.

```
pip install -e ".[testing]"
```

Create a postgresql database, then add the path to the database to the `development.ini` found in `datameta/config`, 
e.g. `sqlalchemy.url = postgresql://localhost/<dbname>`. A copy of the `development.ini` can be placed at an arbitrary location 
named `/path/to/config/` in the following.

```
createdb <dbname>
```

Initialize the database using Alembic.

```
<path/to/environment>/bin/alembic -c <path/to/config>/development.ini upgrade head
```

Load default data into the database using a script. Change the initial user and group information to your requirements.

```
<path/to/environment>/bin/initialize_datameta_db \
        -c <path/to/config>/development.ini \
        --initial-user-fullname "First User Fullname" \
        --initial-user-email "first@user.email" \
        --initial-user-pass "initialPassword" \
        --initial-group "My Organization"
```

Run your project's tests.

```
<path/to/environment>/bin/pytest
```

Start the `memcached` process.

```
nohup memcached &
```

Run your project.

```
<path/to/environment>/bin/pserve /path/to/config/development.ini
```

