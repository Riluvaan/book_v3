from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev_secret_key")

# PostgreSQL connection from Render environment
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL").replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# MODELS
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="staff")

class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    stock = db.Column(db.Integer, default=0)
    department = db.relationship("Department", backref="items")

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(255))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    quantity = db.Column(db.Integer)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship("User")
    item = db.relationship("Item")

# ROUTES
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    activities = Activity.query.order_by(Activity.timestamp.desc()).all()
    return render_template('index.html', activities=activities)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role
            return redirect(url_for('index'))
        flash('Invalid login details')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/activities', methods=['GET', 'POST'])
def activities():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        description = request.form['description']
        item_id = request.form['item_id']
        quantity = int(request.form['quantity'])
        new_activity = Activity(description=description, item_id=item_id,
                                quantity=quantity, user_id=session['user_id'])
        db.session.add(new_activity)
        db.session.commit()
        flash('Activity added successfully.')
        return redirect(url_for('activities'))
    items = Item.query.all()
    activities = Activity.query.order_by(Activity.timestamp.desc()).all()
    return render_template('activities.html', activities=activities, items=items)

@app.route('/users', methods=['GET', 'POST'])
def users():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect(url_for('login'))
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        db.session.add(User(username=username, password=password, role=role))
        db.session.commit()
        flash('User added successfully.')
    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/departments', methods=['GET', 'POST'])
def departments():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        db.session.add(Department(name=name))
        db.session.commit()
        flash('Department added.')
    departments = Department.query.all()
    return render_template('departments.html', departments=departments)

@app.route('/initdb')
def initdb():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password=generate_password_hash("password123"), role="admin")
        clerk = User(username="clerk", password=generate_password_hash("password123"), role="staff")
        db.session.add_all([admin, clerk])
        db.session.commit()
    flash('Database initialized.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
