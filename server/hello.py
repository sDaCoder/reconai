import os
from dotenv import load_dotenv
from sqlmodel import SQLModel, create_engine

load_dotenv()

DATABASE_STRING = os.getenv("DATABASE_STRING")

def main():
    try:
        engine = create_engine(DATABASE_STRING)
        SQLModel.metadata.create_all(engine)
        print("Database connected successfully")
    except Exception as e:
        print("Error creating database: ", e)
    finally:
        engine.dispose()
        print("Database disposed")


if __name__ == "__main__":
    main()