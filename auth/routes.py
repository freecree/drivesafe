from auth import bp
from flask import request, flash, render_template, redirect, url_for
from flask_login import login_user, logout_user, login_required
from flask_socketio import SocketIO
from models.user import User

@bp.route('/logout')
@login_required
def logout():
  logout_user()
  return redirect(url_for('auth.login'))

@bp.route('/')
def login():
  return render_template('login.html')

@bp.route('/', methods=['POST'])
def login_post():
  if request.method == 'POST':
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
      flash('Неправильні дані для входу. Будь ласка, перевірте логін та пароль')
      return redirect(url_for('auth.login'))
    login_user(user)
  return redirect(url_for('main.main'))