from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template,flash,url_for,redirect,jsonify,session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todos.db'
# Additional named binds
app.config['SQLALCHEMY_BINDS'] = {
    'contact': 'sqlite:///contact.db', #,.. you can add more binds here
    'user': 'sqlite:///user.db'
}
app.config['SECRET_KEY']= 'your_secret_key' # for CSRF protection
db = SQLAlchemy(app)

ist = pytz.timezone('Asia/Kolkata')
"""Create the database and the table
with app.app_context():
    db.create_all()"""

class Todo(db.Model): # Table/Entity name is 'employee'
    # __tablename__ = 'employee' # Table name in the database
    # Column names and their types
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    # timestamp = db.Column(db.DateTime, default=db.func.current_timestamp()) # optional
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(ist))
    reminder_time = db.Column(db.DateTime, nullable=True)  # NEW: reminder datetime
    user_id = db.Column(db.Integer, nullable=False)  # 👈 new
    def __init__(self, task, description,reminder_time=None, user_id=None):
        self.task = task
        self.description = description
        self.reminder_time = reminder_time
        self.user_id = user_id

class Contact(db.Model):
    __bind_key__ = 'contact'  # Tells SQLAlchemy to use the contact.db bind
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    def __init__(self, name, email, message):
        self.name = name
        self.email = email
        self.message = message

class User(db.Model):
    __bind_key__ = 'user'  # Tells SQLAlchemy to use the user.db bind
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # todos = db.relationship('Todo', backref='user', lazy=True)

    def __init__(self, username, password):
        self.username = username
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "error")
        else:
            new_user = User(username=username, password=password)
            db.session.add(new_user)
            db.session.commit()
            flash("Registration successful!", "success")
            return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.check_password(request.form['password']):
            session['user_id'] = user.id
            session['username'] = user.username
            flash("Login successful", "success")
            return redirect(url_for('show_all'))
        else:
            flash("Invalid credentials", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    # session.clear()  # Clear all session data
    flash("Logged out", "success")
    return redirect(url_for('login'))

@app.route('/')
def show_all():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    todos = Todo.query.filter_by(user_id=session['user_id']).order_by(Todo.timestamp.desc()).all()
    return render_template('show_all.html', todos=todos)

@app.route('/addtodo', methods=['GET', 'POST'])
def add_todo():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        if not request.form['task'] or not request.form['description']:
            flash('Please fill out all fields', 'error')
        else:
            task = request.form['task']
            description = request.form['description']
            reminder_time_str = request.form.get("reminder_time")
            reminder_time = datetime.strptime(reminder_time_str, "%Y-%m-%dT%H:%M") if reminder_time_str else None
            new_todo = Todo(task=task, description=description,reminder_time=reminder_time,user_id=session['user_id'])
            db.session.add(new_todo)
            db.session.commit()
            flash('Todo added successfully!', 'success')
        return redirect(url_for('show_all'))
    return render_template('add_todo.html') # b/c by default it renders for GET request

@app.route('/deletetodo/<int:id>')
def delete_todo(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    todo = Todo.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    db.session.delete(todo)
    db.session.commit()
    flash('Todo deleted successfully!', 'success')
    return redirect(url_for('show_all'))        
    
@app.route('/updatetodo/<int:id>', methods=['GET', 'POST'])
def edit_todo(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    todo = Todo.query.filter_by(id=id, user_id=session['user_id']).first_or_404()
    if request.method == 'POST':
        if not request.form['task'] or not request.form['description']:
            flash('Please fill out all fields', 'error')
        else:
            todo= Todo.query.get(id)
            todo.task = request.form['task']
            todo.description = request.form['description']
            # todo.timestamp = db.func.current_timestamp()
            todo.timestamp = datetime.now(ist)  # assign actual datetime object
            reminder_time_str = request.form.get("reminder_time")
            todo.reminder_time = datetime.strptime(reminder_time_str, "%Y-%m-%dT%H:%M") if reminder_time_str else None
            db.session.commit()
            flash('Todo updated successfully!', 'success')
            return redirect(url_for('show_all'))
    return render_template('edit_todo.html',todo=todo)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact',methods=['GET', 'POST'])
def contact():
    replies= Contact.query.all()
    if request.method == 'POST':
        if not request.form['name'] or not request.form['email'] or not request.form['message']:
            flash('Please fill out all fields', 'error')
        else:
            name = request.form['name']
            email = request.form['email']
            message = request.form['message']

            new_contact = Contact(name=name, email=email, message=message)
            db.session.add(new_contact)
            db.session.commit()
            flash('Message sent successfully!', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html',replies=replies)

@app.route('/get_due_reminders')
def get_due_reminders():
    now = datetime.now()
    due_tasks = Todo.query.filter(Todo.reminder_time <= now).all()
    return jsonify([
        {'id': t.id, 'task': t.task, 'description': t.description}
        for t in due_tasks
    ])
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Create the database and the table defined by [your class] SQLAlchemy models.
    app.run(debug=True)