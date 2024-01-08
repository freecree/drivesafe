from flask_sqlalchemy import SQLAlchemy

from extensions import db

class Driver(db.Model):
  __tablename__ = 'drivers'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(80), nullable=False)
  folder_id = db.Column(db.String(80), unique=True, nullable=False)
  driving_time = db.Column(db.Integer, default=0, nullable=False)

  def __repr__(self) -> str:
    return f'<Driver {self.name}'