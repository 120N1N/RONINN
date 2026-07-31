import sys
import os
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add parent to path to support running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import models

db_files = ["corvus_red.db", "corvus_v3.db", "corvus.db"]

def seed_db(db_name):
    # Find database absolute path
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(root_dir, db_name)
    print(f"[*] Checking database: {db_path} ...")
    
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    
    # Ensure tables exist
    try:
        models.Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"  [!] Failed to check/create tables: {e}")
        return
        
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        existing = db.query(models.User).filter(models.User.username == "admin").first()
        if existing:
            # Update password to ensure it matches
            existing.hashed_password = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
            db.commit()
            print(f"  [+] Admin user updated/verified successfully in {db_name}!")
            return
            
        hashed = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode('utf-8')
        admin = models.User(
            username="admin",
            email="admin@corvus.net",
            hashed_password=hashed
        )
        db.add(admin)
        db.commit()
        print(f"  [+] Admin user (admin / admin123) successfully seeded in {db_name}!")
    except Exception as e:
        print(f"  [!] Error seeding {db_name}: {e}")
    finally:
        db.close()

def main():
    for db_file in db_files:
        seed_db(db_file)

if __name__ == "__main__":
    main()
