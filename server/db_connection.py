from sqlmodel import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_STRING = os.getenv("DATABASE_STRING")
engine = create_engine(DATABASE_STRING)