import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from logging.config import fileConfig
from decouple import config as decouple_config

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Import only models, not routers to avoid dependency issues
from sqlmodel import SQLModel
from api.user.model import User
from api.shop.model import Shop
from api.attribute.model import Attribute
from api.address.model import Address
from api.cart.model import Cart, CartItem
from api.category.model import Category
from api.order.model import Order, OrderItem
from api.sub_category.model import SubCategory
from api.chat.model import ChatRoom, ChatMessage
from api.payment.model import Payment, PaymentMethod, RefundRequest
from api.product.model import Product
target_metadata = SQLModel.metadata


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Use DATABASE_URL from environment variable if available
    database_url = decouple_config('DATABASE_URL', default=None)
    url = database_url if database_url else config.get_main_option("sqlalchemy.url")
    
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Use DATABASE_URL from environment variable if available
    database_url = decouple_config('DATABASE_URL', default=None)
    
    if database_url:
        # Override the config with DATABASE_URL from environment
        configuration = config.get_section(config.config_ini_section, {})
        configuration['sqlalchemy.url'] = database_url
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )
    else:
        # Fallback to config from ini file
        connectable = engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
