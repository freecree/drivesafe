from extensions import db

class Distraction(db.Model):
  __tablename__ = 'distractions'
  id = db.Column(db.Integer, primary_key=True)
  driver_folder = db.Column(db.Integer, db.ForeignKey('drivers.folder_id'), nullable=False)
  date = db.Column(db.String(80), nullable=False)
  distracted_class = db.Column(db.String(80), nullable=False)

  def __repr__(self) -> str:
    return (
      f'<Distraction id={self.id}, '
      f'driver_folder={self.driver_folder}, '
      f'date={self.date}, '
      f'distracted_class={self.distracted_class}>'
    )