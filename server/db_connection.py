import os

from dotenv import load_dotenv
from sqlalchemy.pool import NullPool
from sqlmodel import create_engine

load_dotenv()

DATABASE_STRING = os.getenv("DATABASE_STRING")
engine = create_engine(DATABASE_STRING, poolclass=NullPool)