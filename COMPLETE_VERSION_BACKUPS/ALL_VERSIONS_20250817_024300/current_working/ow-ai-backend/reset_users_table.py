from database import Base, engine
import models  # ✅ GOOD


print("Dropping 'users' table...")
User.__table__.drop(engine)

print("Recreating all tables...")
Base.metadata.create_all(bind=engine)

print("✅ Users table reset successfully.")
