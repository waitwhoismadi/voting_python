import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, User, generate_password_hash

def create_admin():
    with app.app_context():
        print("🔐 Creating Admin User")
        print("-" * 30)
        
        username = input("Enter username: ")
        email = input("Enter email: ")
        password = input("Enter password: ")
        is_super = input("Make super admin? (y/n): ").lower() == 'y'
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            print(f"❌ Username '{username}' already exists!")
            return
        
        if User.query.filter_by(email=email).first():
            print(f"❌ Email '{email}' already exists!")
            return
        
        # Create admin user
        admin = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            is_admin=True,
            is_super_admin=is_super
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print(f"✅ Admin user '{username}' created successfully!")
        if is_super:
            print("👑 User has super admin privileges")

if __name__ == '__main__':
    create_admin()