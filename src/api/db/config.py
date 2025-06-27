# pip install python-decouple

from decouple import config as decouple_config

_DATABASE_URL = decouple_config("DATABASE_URL", default="")

# Fix Railway's postgresql:// URL to use psycopg driver instead of psycopg2
if _DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = _DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
else:
    DATABASE_URL = _DATABASE_URL

