# from flask_login import UserMixin, LoginManager
from flask_login import LoginManager, UserMixin
from flask_sqlalchemy import SQLAlchemy

from extensions import db

class User(UserMixin, db.Model):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(80), unique=True, nullable=False)
  password = db.Column(db.String(120), nullable=False)

  def __repr__(self) -> str:
    return f'<User {self.username}'
