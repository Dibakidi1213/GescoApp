from __future__ import with_statement
import sys
import os
from logging.config import fileConfig

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app  # noqa: E402
from models import db  # noqa: E402

target_metadata = db.metadata


def run_migrations_offline():
    url = app.config.get('SQLALCHEMY_DATABASE_URI')
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = None
    # Use Flask-SQLAlchemy engine within app context
    with app.app_context():
        connectable = db.engine
        with connectable.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
