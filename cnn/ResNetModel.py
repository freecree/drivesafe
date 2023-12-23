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

transform = transforms.Compose([transforms.Resize((400, 400)),
                           transforms.RandomRotation(10),
                           transforms.ToTensor(),
                           transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
                          ])

class ResNetModel:
  def __init__(self):
    self.model = self.get_model()


  def get_model(self):
    model = models.resnet50()
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 7)
    model.load_state_dict(torch.load("weights/model-driver_7cat_final", map_location=torch.device('cpu')))
    model.eval()
    model.to('cpu')
    return model
  
  def predict_by_frame(self, frame):
    pixels = np.asarray(frame)
    im = Image.fromarray(pixels)
    # roi = cv2.resize(fr, (400, 400))
    im = transform(im)
    im = im.unsqueeze(0)
    output = self.model(im.to('cpu'))
    proba = nn.Softmax(dim=1)(output)
    proba = [round(float(elem),4) for elem in proba[0]]
    return proba

# model_resnet = get_model()

