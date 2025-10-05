#!/usr/bin/env python3
"""
Database initialization script.
Run this to create the database tables and add test users.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models.models import Base, User, UserRole
from app.core.security import get_password_hash

def init_db():
    """Initialize the database with tables and test users."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    
    # Add test users
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        
        # Check if users already exist
        existing_recruiter = db.query(User).filter(User.email == "recruiter@example.com").first()
        existing_candidate = db.query(User).filter(User.email == "candidate@example.com").first()
        
        if not existing_recruiter:
            recruiter = User(
                email="recruiter@example.com",
                hashed_password=get_password_hash("strongpassword"),
                role=UserRole.RECRUITER
            )
            db.add(recruiter)
            print("✅ Test recruiter user created")
        else:
            print("ℹ️  Test recruiter user already exists")
            
        if not existing_candidate:
            candidate = User(
                email="candidate@example.com",
                hashed_password=get_password_hash("strongpassword"),
                role=UserRole.CANDIDATE
            )
            db.add(candidate)
            print("✅ Test candidate user created")
        else:
            print("ℹ️  Test candidate user already exists")
        
        db.commit()
        print("🎉 Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
