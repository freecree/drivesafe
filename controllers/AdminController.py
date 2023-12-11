from flask import render_template, redirect, url_for, request, flash
from flask_login import login_user, login_required, logout_user
from flask_sqlalchemy import SQLAlchemy
from models.models import User
# from app_auth import db

class AdminController:
  def __init__(self, db):
    self.db = db
    # @staticmethod
  def login(self):
    if request.method == 'POST':
      username = request.form['username']
      password = request.form['password']
      user = User.query.filter_by(username=username).first()

      if user and user.password == password:
          login_user(user)
          return redirect(url_for('video'))
      else:
          flash('Login failed. Please check your username and password.')
    return render_template('login.html')

  # @staticmethod
  @login_required
  def logout(self):
    logout_user()
    return redirect(url_for('login'))

  # @staticmethod
  def register(self):
    if request.method == 'POST':
      username = request.form['username']
      password = request.form['password']
      user = User(username=username, password=password)
      self.db.session.add(user)
      self.db.session.commit()
      flash('Registration successful. You can now log in.')
      return redirect(url_for('login'))
    return render_template('register.html')
