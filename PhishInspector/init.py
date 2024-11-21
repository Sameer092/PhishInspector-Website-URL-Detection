from flask import Flask
from flask_sqlalchemy import SQLAlchemy

#vAdd the Database postgres credentials and connection
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sam:1122@localhost/pishing'
app.config['SECRET_KEY'] = 'your_secret_key'

db = SQLAlchemy(app)
