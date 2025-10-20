from app import db, User, Department, Item
from werkzeug.security import generate_password_hash

# Create all tables
db.create_all()

# Add sample users if they don't exist
if not User.query.filter_by(username="admin").first():
    admin = User(username="admin", password=generate_password_hash("password123"), role="admin")
    clerk = User(username="clerk", password=generate_password_hash("password123"), role="staff")
    db.session.add_all([admin, clerk])
    db.session.commit()

# Add sample departments if none exist
if Department.query.count() == 0:
    dept1 = Department(name="Sales")
    dept2 = Department(name="Inventory")
    db.session.add_all([dept1, dept2])
    db.session.commit()

print("Database initialized with sample users and departments.")
