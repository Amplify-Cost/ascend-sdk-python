from models import Base
from sqlalchemy import create_engine

engine = create_engine("sqlite:///ow-ai.db")

if __name__ == "__main__":
    print("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Done.")
