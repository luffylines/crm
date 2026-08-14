"""
Database initialization script.
Migrates existing users from users.json to the database.
Run this once before starting the application.
"""
import os
import json
from app import app, db
from models import User
from dotenv import load_dotenv

# Load environment variables
dotenv_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

def init_db():
    """Initialize database and create tables."""
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Check if users already exist
        existing_users = User.query.count()
        if existing_users > 0:
            print(f"✓ Database already initialized with {existing_users} users")
            return
        
        # Migrate users from users.json
        try:
            users_path = os.path.join(os.path.dirname(__file__), "users.json")
            with open(users_path, 'r') as f:
                data = json.load(f)
            
            for user_data in data.get('users', []):
                username = user_data.get('username', '').strip().lower()
                password = user_data.get('password', '')
                
                if not username or not password:
                    continue
                
                # Determine role: set 'admin' user as Admin, others as User
                role = 'Admin' if username == 'admin' else 'User'
                
                # Check if user already exists
                existing = User.query.filter_by(username=username).first()
                if existing:
                    print(f"⊘ User '{username}' already exists, skipping")
                    continue
                
                # Create new user
                user = User(
                    username=username,
                    role=role,
                    is_active=True
                )
                user.set_password(password)
                db.session.add(user)
                print(f"✓ Created user: {username} (role: {role})")
            
            db.session.commit()
            print("✓ Successfully migrated users from users.json")
        
        except FileNotFoundError:
            print("⊘ users.json not found, skipping migration")
        except Exception as e:
            print(f"✗ Error migrating users: {e}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
