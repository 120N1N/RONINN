import sys
import os
import bcrypt

# Add parent to path to support running directly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.database import SessionLocal
from backend.db import models

def test_login():
    db = SessionLocal()
    try:
        users = db.query(models.User).all()
        print(f"Total users in DB: {len(users)}")
        for u in users:
            print(f"- ID: {u.id}, Username: {u.username}, Email: {u.email}")
            print(f"  Hashed password: {u.hashed_password}")
            
            # Test verification
            pw_to_test = "admin123"
            try:
                matches = bcrypt.checkpw(pw_to_test.encode('utf-8'), u.hashed_password.encode('utf-8'))
                print(f"  Verification check with '{pw_to_test}': {matches}")
            except Exception as e:
                print(f"  Verification check failed with error: {e}")
    except Exception as e:
        print("Database query failed:", e)
    finally:
        db.close()

if __name__ == "__main__":
    test_login()
