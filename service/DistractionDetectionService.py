from cnn.ResNetModel import ResNetModel
import datetime
from extensions import db
from service.DistractionService import DistractionService as DistrServ

NORMAL_DRIVING_CLASS = 0

class DistractionDetectionService:
  def __init__(self):
    self.cnn_model = ResNetModel()
    self.temp_predictions = {
      'last_all': [], # todo: save probabilities by driver
      'last_summarise': -1,
      'last_pred_time': datetime.datetime.now()
    }

  def make_prediction(self, frame, driver_folder):
    proba = self.cnn_model.predict_by_frame(frame)
    predictions_output = self.__form_predict_per_time(proba)

    current_datetime = datetime.datetime.now()
    predictions_date = current_datetime.strftime("[%y.%m.%d: %H:%M:%S]")

    return predictions_output, predictions_date

  def __form_predict_per_time(self, proba):
    two_max_pred = self.__get_two_max_pred(proba)
    if (self.__is_normal_driving_twice_in_row(two_max_pred[0]['predicted_class'])):
      return 0

    if (self.__is_time_interval()):
      self.temp_predictions['last_pred_time'] = datetime.datetime.now()
      self.temp_predictions['last_summarise'] = two_max_pred[0]['predicted_class']
      return two_max_pred
    return 0
  
  def __get_two_max_pred(self, proba):
    sorted_proba = sorted(proba, reverse=True)
    predictions = []

    first_max = sorted_proba[0]
    second_max = sorted_proba[1]

    first_class = self.__to_predicted_class(proba.index(first_max))
    second_class = self.__to_predicted_class(proba.index(second_max))

    predictions.append({'predicted_class': first_class, 'probability': first_max })

    if (self.__is_low_proba(first_max, second_max)
    and DistrServ.is_distraction(second_class) 
    and first_class != second_class):
      predictions.append({'predicted_class': second_class, 'probability': second_max })

    return predictions
  
  def __is_low_proba(self, first_predict, second_predict):
    return (first_predict - second_predict) < 0.35

  def __is_time_interval(self):
    current_time = datetime.datetime.now()
    time_threshold = datetime.timedelta(seconds=3)
    return current_time - self.temp_predictions['last_pred_time'] >= time_threshold
  
  def __is_normal_driving_twice_in_row(self, current_pred):
    last_pred = self.temp_predictions['last_summarise']
    return DistrServ.is_normal_driving(last_pred) and DistrServ.is_normal_driving(current_pred)

  def __to_predicted_class(self, model_class):
    mapping = {
        0: [0],          # Normal
        1: [1, 2, 3, 4], # Phone
        2: [5],          # Radio
        3: [6],          # Drinking
        4: [7],          # Reaching behind
    }
    for key, values in mapping.items():
      if model_class in values:
        return key
    return -1


