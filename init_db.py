from database import engine, Base
import models

print("Creating database schema...")
Base.metadata.create_all(bind=engine)
print("✅ Tables created!")
