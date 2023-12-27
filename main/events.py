from app import socketio
import cv2
import traceback
import datetime
import numpy as np
from PIL import Image
from torchvision import models,transforms,datasets
import torch
import torch.nn as nn
from models.distraction import Distraction
from extensions import db
from service.DistractionDetectionService import DistractionDetectionService
from service.DistractionService import DistractionService

video_states = {}
distraction_detection_service = DistractionDetectionService()

@socketio.on('ask video')
def handle_asking_video(data):
  video_key = data['video_path']
  print('In ask video: ', data)
  video_file_path = f"static/{data['video_path'].split('/')[-1]}"
  cap = cv2.VideoCapture(video_file_path)

  video_states[video_key] = True

  while video_states[video_key]:
    ret, frame = cap.read()
    if not ret:
      print('Can not read the video')
      break
    try:
      print('data: ', data)
      predictions_output, predictions_date = \
        distraction_detection_service.make_prediction(frame, data['driver_folder'])

      if (predictions_output):
        predicted_class = predictions_output[0]['predicted_class']
        DistractionService.save_distraction(data['driver_folder'], predictions_date, predicted_class)

      ret, buffer = cv2.imencode('.jpg', frame)
      if ret:
        frame = buffer.tobytes()
        socketio.emit('response video', {
          'frame': frame,
          'video_path': data['video_path'],
          'driver_folder': data['driver_folder'],
          'predictions': predictions_output,
          'predictions_date': predictions_date
        })
    except Exception as e:
      print('Exeption while responsing video: ', e)
      traceback.print_exc()
      pass

@socketio.on('stop video')
def handle_stoping_video(data):
  print('handle_stoping_video()')

  video_key = data['video_path']
  video_states[video_key] = False
