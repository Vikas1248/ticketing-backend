from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os

DATABASE_URL = "postgresql://ticketing_db_maej_user:6GXM8XlQT1peTOnRoJgKg9s8enLCXZfk@dpg-d6ve2lsr85hc73bae6og-a.oregon-postgres.render.com:5432/ticketing_db_maej"
print("DATABASE_URL:", DATABASE_URL)

from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()