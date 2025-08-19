# alembic/env.py
import os, sys
from logging.config import fileConfig

# Ensure project root on sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alembic import context
from sqlalchemy import create_engine, pool

# Import Base and **all** model modules so tables are registered
from database import Base

# Importing modules is enough to register their models with Base.metadata
import models                     # users, alerts, logs, rules, smart_rules, etc.
import models_data_rights         # GDPR/CCPA models
import models_mcp_governance      # MCP governance models

# Alembic config
config = context.config

# Optional: log config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def _get_sqlalchemy_url():
    # Prefer env var (Railway/Prod), fall back to alembic.ini
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    return config.get_main_option("sqlalchemy.url")

def run_migrations_offline() -> None:
    url = _get_sqlalchemy_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
        render_as_batch=True,  # <- critical for SQLite schema changes
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = create_engine(
        _get_sqlalchemy_url(),
        poolclass=pool.NullPool,
        future=True,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # <- critical for SQLite schema changes
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
