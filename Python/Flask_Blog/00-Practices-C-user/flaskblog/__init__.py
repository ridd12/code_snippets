from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager


app = Flask(__name__)

# $ python
# >>> import secrets
# >>> secrets.token_hex(16)
app.config['SECRET_KEY'] = 'ada8419b155676bc78c2296aba9c7c7d'
# /// represents the relative directory from the current file (flaskblog.py). 
# that is, site.db has the same directory as this __init__.py
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)   # Used to hash the password
login_manager = LoginManager(app)
# This (login_view) tells where is the login route located
login_manager.login_view = 'login'     # which is login() in routes.py
login_manager.login_message_category = 'info'  #add bootstrap class to make nice view for flash message

# import routes from flaskblog package
from flaskblog import routes