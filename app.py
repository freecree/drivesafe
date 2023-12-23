from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from extensions import db

socketio = SocketIO()

def create_app():
  app = Flask(__name__)

  app.secret_key = 'your_secret_key'  # Change this to a strong secret key
  app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

  db.init_app(app)

  from auth import bp as auth_bp
  app.register_blueprint(auth_bp)

  from main import bp as main_bp
  app.register_blueprint(main_bp)

  login_manager = LoginManager()
  login_manager.login_view = 'auth.login'
  login_manager.login_message = "Будь ласка, авторизуйтесь для доступу в систему"
  login_manager.init_app(app)
  
  from models.user import User
  @login_manager.user_loader
  def load_user(user_id):
    return User.query.get(int(user_id))

  socketio.init_app(app)
  # socketio.run(app, debug=True)
  return app


# if __name__ == '__main__':
#   app = create_app()

#   socketio.run(app, debug=True)

