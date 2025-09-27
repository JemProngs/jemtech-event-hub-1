#!/usr/bin/env python3
import os
import bcrypt as bcrypt_module  # Import the bcrypt module directly
from app import app, db
from models import User


def reset_database():
    with app.app_context():
        # Delete the database file if it exists
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"Removed existing database: {db_path}")

        # Create all tables
        db.create_all()
        print("Created new database schema")

        # Create admin user using direct bcrypt module
        hashed_password = bcrypt_module.hashpw('admin123'.encode('utf-8'), bcrypt_module.gensalt())

        admin_user = User(
            username='admin',
            email='admin@jemtech.com',
            password_hash=hashed_password.decode('utf-8'),
            first_name='System',
            last_name='Administrator',
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Created admin user: admin/admin123")

        print("Database reset completed successfully!")


if __name__ == '__main__':
    reset_database()