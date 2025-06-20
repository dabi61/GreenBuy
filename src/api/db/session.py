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
    try:
        # Chỉ tạo tables mới, không tạo lại tables đã tồn tại
        SQLModel.metadata.create_all(engine, checkfirst=True)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Warning: Some tables might already exist. Error: {e}")
        # Không raise error, để app có thể tiếp tục chạy



def get_session():
    with Session(engine) as session:
        yield session