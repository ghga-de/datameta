# Local Installation

- Change directory into your newly created project if not already there. Your
  current directory should be the same as this README.txt file and setup.py.

    cd datameta

- Create a Python virtual environment, if not already created.

    python3 -m venv env

- Upgrade packaging tools, if necessary.

    env/bin/pip install --upgrade pip setuptools

- Install NPM dependencies

    npm install --prefix datameta/static/

- Install the project in editable mode with its testing requirements.

    env/bin/pip install -e ".[testing]"

- Initialize the database using Alembic.

    env/bin/alembic -c development.ini upgrade head

- Load default data into the database using a script. Change the initial user and group information to your requirements.

    env/bin/initialize_datameta_db \
        -c development.ini \
        --initial-user-fullname "First User Fullname" \
        --initial-user-email "first@user.email" \
        --initial-user-pass "initialPassword" \
        --initial-group "My Organization"

- Run your project's tests.

    env/bin/pytest

- Run your project.

    env/bin/pserve development.ini

