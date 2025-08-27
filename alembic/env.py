# alembic/env.py
import os
from logging.config import fileConfig
from sqlalchemy import create_engine, pool
from alembic import context

config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Import ONLY your metadata (no engine/session side-effects)
from database import Base
target_metadata = Base.metadata

def run_migrations_online():
    url = os.environ["DATABASE_URL"]
    connectable = create_engine(url, poolclass=pool.NullPool, future=True)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
