from app import app, db

with app.app_context():
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    print("✓ Database tables created successfully!")
    
    # Verify tables were created
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tables created: {tables}")
    
    if 'users' in tables:
        columns = [col['name'] for col in inspector.get_columns('users')]
        print(f"Users table columns: {columns}")
