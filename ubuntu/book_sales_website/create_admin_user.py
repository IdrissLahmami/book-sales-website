from database_schema import db, User
from werkzeug.security import generate_password_hash
from app import app

ADMIN_EMAIL = 'admin@example.com'
ADMIN_PASSWORD = 'admin123'

with app.app_context():
    user = User.query.filter_by(email=ADMIN_EMAIL).first()
    if user:
        print(f"Admin user already exists: {ADMIN_EMAIL}")
    else:
        admin = User(
            name='Admin',
            email=ADMIN_EMAIL,
            password=generate_password_hash(ADMIN_PASSWORD),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
