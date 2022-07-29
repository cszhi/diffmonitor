import os
import sys

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

app = Flask(__name__)

dotenv_path = os.path.join(os.path.dirname(app.root_path), '.env')
if os.path.exists(dotenv_path):
	load_dotenv(dotenv_path)

SQLALCHEMY_DATABASE_URI = prefix + os.path.join(os.path.dirname(app.root_path), 'data.db')
if os.getenv("DB_DRIVER") == 'mysql':
	MYSQL_USER = os.getenv("MYSQL_USER", 'root')
	MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", 'password')
	MYSQL_HOST = os.getenv("MYSQL_HOST", '127.0.0.1')
	MYSQL_PORT = os.getenv("MYSQL_PORT", 3306)
	MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", 'diffmonitor')
	SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://' + MYSQL_USER + ':' + MYSQL_PASSWORD + '@' + MYSQL_HOST + ':' + MYSQL_PORT + '/' + MYSQL_DATABASE

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev123')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#app.config['SQLALCHEMY_ECHO'] = True

db = SQLAlchemy(app)
login_manager = LoginManager(app)

@login_manager.user_loader
def load_user(user_id):
	from diffmonitor.models import User
	user = User.query.get(int(user_id))
	return user

login_manager.login_view = 'login'

@app.context_processor
def inject_user():
	from diffmonitor.models import User
	user = User.query.first()
	return dict(user=user)

from diffmonitor import views, errors, commands, apis

if __name__ == '__main__':
    app.run()