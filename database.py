from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ✅ SET YOUR DATABASE URL HERE
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://ticketing_db_maej_user:6GXM8XlQT1peTOnRoJgKg9s8enLCXZfk@dpg-d6ve2lsr85hc73bae6og-a.oregon-postgres.render.com:5432/ticketing_db_maej"
)

# ✅ ENGINE (with connection fix)
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)

# ✅ SESSION
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ BASE
Base = declarative_base()