from flask import Flask, request, jsonify, redirect, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)
app.secret_key='hci420'

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db = SQLAlchemy(app)

# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False, unique=True)
    last_name = db.Column(db.String(80), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    is_counselor = db.Column(db.Boolean, default=False)
    

# Create the database (run once)
with app.app_context():
    db.create_all()

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    new_user = User(first_name=data['first_name'],
                     last_name=data['last_name'],
                     email=data['email'], 
                     password=hashed_password,
                     is_counselor=data['is_counselor'])
    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify({"message": "User created successfully."}), 201
    except Exception as e:
        db.session.rollback()  # Roll back the failed transaction
        print(f"Error during signup: {str(e)}")  # This will help you debug
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"message": "Email or name already registered!"}), 400
        return jsonify({"message": f"Error during signup: {str(e)}"}), 400

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data['email']).first()

    if user and check_password_hash(user.password, data['password']):
        session['id']=user.id
        session['Fist_name']=user.first_name
        session['Last_name']=user.last_name
        session['is_counselor']=user.is_counselor
        if session['is_counselor']:
            return jsonify({
                "message": "Login successful!",
                "redirect_url": "http://127.0.0.1:5500/psyc_home.html#"
            }), 200
        else:          
            return jsonify({
                "message": "Login successful!",
                "redirect_url": "http://127.0.0.1:5500/home_page.html#"
            }), 200
    return jsonify({"message": "Invalid credentials!"}), 401

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
