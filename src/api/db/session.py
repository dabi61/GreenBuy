from .config import DATABASE_URL
from sqlmodel import SQLModel, Session
import sqlmodel

if DATABASE_URL == "":
    raise NotImplementedError("DATABASE_URL needs to be set")

print("DATABASE_URL =", DATABASE_URL)
print("TYPE =", type(DATABASE_URL))
engine = sqlmodel.create_engine(DATABASE_URL)


def init_db():
    print("creating database")
    SQLModel.metadata.create_all(engine)



def get_session():
    with Session(engine) as session:
        yield session