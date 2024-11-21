# Importing required libraries
from flask import Flask, render_template, redirect, url_for, request, flash, session
import numpy as np
import pickle
from feature import FeatureExtraction  # Ensure this file and class are correctly implemented
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from init import app, db


bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Load the machine learning model
with open("pickle/model.pkl", "rb") as file:
    gbc = pickle.load(file)

# Define User model for authentication
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

# User loader callback for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Home route with phishing detection
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        url = request.form["url"]
        obj = FeatureExtraction(url)
        x = np.array(obj.getFeaturesList()).reshape(1, 30)

        y_pred = gbc.predict(x)[0]
        y_pro_phishing = gbc.predict_proba(x)[0, 0]
        y_pro_non_phishing = gbc.predict_proba(x)[0, 1]
        
        pred = "It is {0:.2f}% safe to go.".format(y_pro_phishing * 100)
        return render_template('index.html', xx=round(y_pro_non_phishing, 2), url=url, prediction=pred)
    
    return render_template("index.html", xx=-1)

# Signup route setup
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

# Login route setup
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check email and password.', 'danger')
    
    return render_template('login.html')

# Forgot password route
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        user = User.query.filter_by(username=username).first()
        
        if user:
            # Store the user's ID in the session for use in the reset_password route
            session['user_id'] = user.id
            flash("Username verified. You can now reset your password.", "success")
            return redirect(url_for("reset_password"))
        else:
            flash("Username not found.", "danger")
            
    return render_template("forgot_password.html")

# Reset password route
@app.route("/reset_password", methods=["GET", "POST"])
def reset_password():
    if 'user_id' not in session:
        flash("Access denied. Please verify your username first.", "danger")
        return redirect(url_for("forgot_password"))
    
    if request.method == "POST":
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password == confirm_password:
            # Fetch the user by the ID stored in the session
            user = User.query.get(session['user_id'])
            hashed_password = bcrypt.generate_password_hash(new_password).decode("utf-8")
            user.password = hashed_password
            db.session.commit()

            # Clear session and confirm password reset
            session.pop("user_id", None)
            flash("Password reset successful. You can now log in.", "success")
            return redirect(url_for("login"))
        else:
            flash("Passwords do not match. Please try again.", "danger")

    return render_template("reset_password.html")

@app.route("/contact")
def contactus():
    return render_template("contact.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/home")
def home():
    return render_template("index.html")


# Logout route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))

# Initialize the database tables
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
