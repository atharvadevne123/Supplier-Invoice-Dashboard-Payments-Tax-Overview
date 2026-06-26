"""Alembic migration environment configuration.

This module configures the Alembic runtime context for both online
(direct DB connection) and offline (SQL script generation) migration modes.
It attaches the application's declarative metadata so Alembic can generate
auto-migrations from ORM model changes.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.database import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode without an active database connection.

    Generates SQL statements to stdout or a file instead of executing them.
    Useful for review workflows where DDL must be approved before execution.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in online mode against a live database connection.

    Uses NullPool to avoid connection pooling during migrations, which is
    safer for long-running DDL operations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
