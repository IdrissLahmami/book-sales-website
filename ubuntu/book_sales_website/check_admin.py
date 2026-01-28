from app import app, db
from database_schema import User

with app.app_context():
    # Check for admin user
    admin = User.query.filter_by(email='admin@example.com').first()
    
    if admin:
        print("✓ Admin user found:")
        print(f"  Email: {admin.email}")
        print(f"  Name: {admin.name}")
        print(f"  Is Admin: {admin.is_admin}")
    else:
        print("✗ No admin user found!")
    
    # List all users
    all_users = User.query.all()
    print(f"\n Total users in database: {len(all_users)}")
    for user in all_users:
        print(f"  - {user.email} (Admin: {user.is_admin})")
