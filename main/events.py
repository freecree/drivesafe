from app import socketio
import cv2
import datetime
import numpy as np
from PIL import Image
from torchvision import models,transforms,datasets
import torch
import torch.nn as nn
from models.distraction import Distraction
from extensions import db
from service.DistractionDetectionService import DistractionDetectionService

video_states = {}
distraction_detection_service = DistractionDetectionService()

@socketio.on('ask video')
def handle_asking_video(data):
  video_path = f"static/{data['video_path']}"
  cap = cv2.VideoCapture(video_path)

  video_states[video_path] = True

  while video_states[video_path]:
    ret, frame = cap.read()
    if not ret:
      print('Can not read the video')
      break
    try:
      print('data: ', data)
      predictions_output, predictions_date = \
        distraction_detection_service.make_prediction(frame, data['driver_folder'])
      ret, buffer = cv2.imencode('.jpg', frame)
      if ret:
        frame = buffer.tobytes()
        socketio.emit('response video', {
          'frame': frame,
          'video_path': data['video_path'],
          'predictions': predictions_output,
          'predictions_date': predictions_date
        })
    except Exception as e:
      print('Exeption while responsing video: ', e)
      pass

@socketio.on('stop video')
def handle_stoping_video(data):
    print('handle_stoping_video()')

    video_path = f"static/{data['video_path']}"
    video_states[video_path] = False
