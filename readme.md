Running app:
python -m flask --app app --debug run

Script for init db:

from extensions import db
from app import create_app
from models.user import User

app = create_app()
app.app_context().push()
db.create_all()

admin = User(username='admin', password='1111')
db.session.add(admin)
db.session.commit()
