from extensions import db
from models.distraction import Distraction

NORMAL_DRIVING_CLASS = 0

class DistractionService:
  def save_distraction(driver_folder, predictions_date, predicted_class):
    if (DistractionService.is_distraction(predicted_class)):
      distraction_record = Distraction(
        driver_folder=driver_folder,
        date=predictions_date,
        distracted_class=predicted_class
      )
      db.session.add(distraction_record)
      db.session.commit()

  def is_distraction(predicted_class):
    return predicted_class != NORMAL_DRIVING_CLASS

  def is_normal_driving(predicted_class):
    return predicted_class == NORMAL_DRIVING_CLASS