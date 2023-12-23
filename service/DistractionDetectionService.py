from cnn.ResNetModel import ResNetModel
import datetime
from extensions import db
from models.distraction import Distraction

DISTRACTED_PHONE_CLASS = 1
DISTRACTED_PHONE_GROUPED_CLASSES = [1, 2, 3, 4]
PREDICTIONS_TEMP_SIZE = 10

class DistractionDetectionService:
  def __init__(self):
    self.cnn_model = ResNetModel()
    self.temp_predictions = {
      'last_all': [],
      'last_summarise': 0,
      'last_pred_time': datetime.datetime.now()
    }

  def make_prediction(self, frame, driver_folder):
    proba = self.cnn_model.predict_by_frame(frame)

    predictions_output = self.__form_predict_per_time(proba)
    current_datetime = datetime.datetime.now()
    predictions_date = current_datetime.strftime("[%y.%m.%d: %H:%M:%S]")

    distracted_class = proba.index(max(proba))
    if distracted_class in DISTRACTED_PHONE_GROUPED_CLASSES:
      distracted_class = DISTRACTED_PHONE_CLASS
    
    self.save_distraction(driver_folder, predictions_date, distracted_class)

    return predictions_output, predictions_date

  def __form_predict_per_time(self, proba):
    comp1 = self.temp_predictions['last_summarise'] == 0
    comp2 = proba.index(max(proba)) == 0
    if (comp2 and comp1):
        return 0
    current_datetime = datetime.datetime.now()
    time_threshold = datetime.timedelta(seconds=2)
    if (current_datetime - self.temp_predictions['last_pred_time'] >= time_threshold):
      self.temp_predictions['last_pred_time'] = current_datetime
      self.temp_predictions['last_summarise'] = proba.index(max(proba))
      return self.__get_predictions_output(proba)
    return 0

  def __get_predictions_output(self, probabilities):
    sorted_probabilities = sorted(probabilities, reverse=True)
    predictions = []

    first_max = sorted_probabilities[0]
    second_max = sorted_probabilities[1]

    predictions.append({ 'distracted_class': probabilities.index(first_max), 'probability': first_max })
    if (first_max - second_max < 0.35):
      predictions.append({'distracted_class': probabilities.index(second_max), 'probability': second_max })
    return predictions
  
  def save_distraction(self, driver_folder, predictions_date, distracted_class):
    distraction_record = Distraction(
      driver_folder=driver_folder,
      date=predictions_date,
      distracted_class=distracted_class
    )
    db.session.add(distraction_record)
    db.session.commit()

