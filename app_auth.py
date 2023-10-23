from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import base64
import json
import time
import datetime

import cv2
from tqdm import tqdm
import random
from ultralytics import YOLO

import numpy as np
from PIL import Image

import torch
import torch.nn as nn
import torchvision
from torchvision import models,transforms,datasets

from googleapiclient.discovery import build
from google.oauth2 import service_account
from flask_socketio import SocketIO


# Set your credentials JSON file path
CREDENTIALS_JSON_FILE = 'distracted_creds.json'
FOLDER_ID = '1fMCWStl4xy12clcR9pNfXEKP-y9yPgFX'

creds = service_account.Credentials.from_service_account_file(CREDENTIALS_JSON_FILE, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds)

font = cv2.FONT_HERSHEY_SIMPLEX

class_dict = {0 : "safe driving",
              1 : "texting - right",
              2 : "talking on the phone - right",
              3 : "texting - left",
              4 : "talking on the phone - left",
              5 : "operating the radio",
              6 : "drinking",
              7 : "reaching behind"}

class_dict_new = {0 : "safe driving",
              1 : "using cellphone",
              2 : "using cellphone",
              3 : "using cellphone",
              4 : "using cellphone",
              5 : "operating the radio",
              6 : "drinking",
              7 : "reaching behind"}

class_dict_ukr = {0 : "нормальне водіння",
              1 : "користування телефоном",
              2 : "користування телефоном",
              3 : "користування телефоном",
              4 : "користування телефоном",
              5 : "користування радіо",
              6 : "випивання",
              7 : "обертання назад" }

transform = transforms.Compose([transforms.Resize((400, 400)),
                           transforms.RandomRotation(10),
                           transforms.ToTensor(),
                           transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
                          ])

def get_model():
    model = models.resnet50()
    num_ftrs = model.fc.in_features
    model.fc = nn.Linear(num_ftrs, 7)
    model.load_state_dict(torch.load("weights/model-driver_7cat_final", map_location=torch.device('cpu')))
    model.eval()
    model.to('cpu')
    return model

model_resnet = get_model()

app = Flask(__name__)
socketio = SocketIO(app)

app.secret_key = 'your_secret_key'  # Change this to a strong secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    folder_id = db.Column(db.String(80), unique=True, nullable=False)
    # distraction = db.Column(db.String(80),nullable=True)

class Distraction(db.Model):
    __tablename__ = 'distractions'
    id = db.Column(db.Integer, primary_key=True)
    driver_folder = db.Column(db.Integer, db.ForeignKey('drivers.folder_id'), nullable=False)
    date = db.Column(db.String(80), nullable=False)
    distracted_class = db.Column(db.String(80), nullable=False)

# distractions = db.relationship('Distraction', backref='driver', lazy=True)
# driver = db.relationship('Driver', back_populates='distractions')



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

video_folder = "static"

# def list_google_folder():


# List folders within the specified folder
def list_folders(folder_id=FOLDER_ID):
    results = service.files().list(
        q=f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        fields="files(id, name)"
    ).execute()

    folders = results.get('files', [])
    folders_data = []
    if folders:
        for folder in folders:
            folder_name = folder['name']
            folders_data.append({"folder_id": folder['id'], "folder_name": folder_name})
    else:
        print("No folders found in the specified folder.")
    return folders_data


def list_videos(folder_id):
    # List videos in the specified Google Drive folder
    results = service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name)").execute()
    files = results.get('files', [])
    list_files = []
    for file in files:
        file_info = service.files().get(fileId=file['id'], fields='thumbnailLink').execute()
        if (file_info):
            thumbnail_link = file_info['thumbnailLink']
            list_files.append({"video_path": file['name'], "preview_image": thumbnail_link})
        else:
            print('file_info is not loaded')

    return list_files

def generate_video_previews():
    video_previews = []
    for filename in os.listdir(video_folder):
        if filename.endswith(".mp4"):
            video_path = os.path.join(video_folder, filename)
            cap = cv2.VideoCapture(video_path)
            success, frame = cap.read()
            if success:
                # Generate a preview image (you can customize this part)
                frame = cv2.resize(frame, (320, 240))
                _, buffer = cv2.imencode(".jpg", frame)
                preview_image = buffer.tobytes()
                preview_image = base64.b64encode(preview_image).decode() 
                video_previews.append({"video_path": filename, "preview_image": preview_image})
            else:
                print('Can not load the preview')
    return video_previews

def get_drivers(): 
    time.sleep(0.5)
    folders = list_folders(FOLDER_ID)
    drivers = []
    for folder in folders:
        folder_id = folder['folder_id']
        driver_videos = list_videos(folder_id)
        drivers.append({'name': folder['folder_name'], 'folder_id': folder_id, 'videos': driver_videos})
    # print('videos[0]: ', drivers[0]['videos'][0])
    return drivers

def load_video(video_path):
    # Render the video page template with the video path
    return render_template('video_page.html', video_path=video_path)

def add_drivers_if_not_exist(drivers_to_add):
    existing_driver_folders = [driver.folder_id for driver in Driver.query.all()]
    for driver in drivers_to_add:
        if (driver['folder_id'] not in existing_driver_folders):
            new_driver = Driver(folder_id=driver['folder_id'], name=driver['name'])
            db.session.add(new_driver)
    db.session.commit()

NORMAL_DRIVING_CLASS = 0

@app.route('/report/<driver_folder>', methods=['GET',' POST'])
def report(driver_folder):
    driver = db.session.query(Driver).filter(Driver.folder_id == driver_folder).first()

    driver_distractions = db.session.query(Distraction) \
        .filter(Driver.folder_id == driver_folder) \
        .filter(Distraction.distracted_class != NORMAL_DRIVING_CLASS) \
        .all()
    driver_distractions_list = []
    for distraction in driver_distractions:
        driver_distractions_list.append({
            'distracted_class': distraction.distracted_class,
            'date': distraction.date,
            'description': class_dict_ukr[int(distraction.distracted_class)],
        })
    
    grouped_distractions = db.session.query(
        Distraction.distracted_class,
        func.count(Distraction.distracted_class)) \
            .filter(Driver.folder_id == driver_folder) \
            .filter(Distraction.distracted_class != NORMAL_DRIVING_CLASS) \
            .group_by(Distraction.distracted_class).all()

    grouped_distractions_list = []
    for distracted_class, count in grouped_distractions: 
        grouped_distractions_list.append({'distracted_class': distracted_class,
                       'count': count,
                       'description': class_dict_ukr[int(distracted_class)]})

    return render_template('report.html',
                        all_distractions=driver_distractions_list,
                        grouped_distractions=grouped_distractions_list,
                        driver_name=driver.name)


@app.route('/video')
def video():
    drivers = get_drivers()
    add_drivers_if_not_exist(drivers)

    print('driver1 added to db')
    return render_template("index.html", drivers=drivers)


@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            login_user(user)
            return redirect(url_for('video'))
        else:
            flash('Login failed. Please check your username and password.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

video_states = {}

PREDICTIONS_TEMP_SIZE = 10
temp_predictions = {
    'last_all': [],
    'last_summarise': 0,
    'last_pred_time': datetime.datetime.now()
}

def form_clever_predicts(driver_id, probabilities):
    if (temp_predictions['last_all'] >= PREDICTIONS_TEMP_SIZE):
        result_predicts = form_summarise_predicts(probabilities)
        clean_temp_predicts()
    set_last_predictions(driver_id, probabilities)

def form_summarise_predicts():
    sorted_predicts = temp_predictions
    return [{'predict_class': 1, 'predict_probability': 1}]
    
def clean_temp_predicts(): 
    temp_predictions['last_all'] = []

def set_last_predictions(driver_id, probabilities, general_prediction):
    pred_prob = max(probabilities)
    pred_class = probabilities.index(pred_prob)
    temp_predictions[driver_id].temp.append({
        'prediction_probability': pred_prob,
        'prediction_class': pred_class,
    })
    if (general_prediction):
        temp_predictions[driver_id].last_general = general_prediction
    # driver_last_predictions[driver_id].

#def get_result_predictions:


def get_predictions_output(probabilities):
    sorted_probabilities = sorted(probabilities, reverse=True)
    predictions = []

    first_max = sorted_probabilities[0]
    second_max = sorted_probabilities[1]

    predictions.append({ 'distracted_class': probabilities.index(first_max), 'probability': first_max })
    if (first_max - second_max < 0.35):
        predictions.append({'distracted_class': probabilities.index(second_max), 'probability': second_max })
    return predictions

def form_predict_per_time(proba):
    comp1 = temp_predictions['last_summarise'] == 0
    comp2 = proba.index(max(proba)) == 0
    if (comp2 and comp1):
        return 0
    current_datetime = datetime.datetime.now()
    time_threshold = datetime.timedelta(seconds=2)
    if (current_datetime - temp_predictions['last_pred_time'] >= time_threshold):
        print('predict per time')
        temp_predictions['last_pred_time'] = current_datetime
        temp_predictions['last_summarise'] = proba.index(max(proba))
        return get_predictions_output(proba)
    return 0

DISTRACTED_PHONE_CLASS = 1
DISTRACTED_PHONE_GROUPED_CLASSES = [1, 2, 3, 4]

@socketio.on('ask video')
def handle_asking_video(data):
    video_path = f"static/{data['video_path']}"
    cap = cv2.VideoCapture(video_path)

    video_states[video_path] = True
    while video_states[video_path]:
        ret, frame = cap.read()
        # time.sleep(3)
        if not ret:
            print('Can not read the video')
            break

        try:
            clean_frame = frame

            pixels = np.asarray(clean_frame)
            im = Image.fromarray(pixels)
            # roi = cv2.resize(fr, (400, 400))
            im = transform(im)
            im = im.unsqueeze(0)
            output = model_resnet(im.to('cpu'))
            proba = nn.Softmax(dim=1)(output)
            proba = [round(float(elem),4) for elem in proba[0]]

            predictions_output = form_predict_per_time(proba)

            current_datetime = datetime.datetime.now()
            predictions_date = current_datetime.strftime("[%y.%m.%d: %H:%M:%S]")

            distracted_class = proba.index(max(proba))
            if distracted_class in DISTRACTED_PHONE_GROUPED_CLASSES:
                distracted_class = DISTRACTED_PHONE_CLASS

            distraction_record = Distraction(
                driver_folder=data['driver_folder'],
                date=predictions_date,
                distracted_class=distracted_class
            )
            db.session.add(distraction_record)
            db.session.commit()

            # cv2.putText(frame, pred, (50, 50), font, 1, (0 ,0, 255), 1)
            # cv2.putText(frame, str(max(proba)), (50, 100), font, 1, (0 ,0, 255), 1)

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

# admin_user = User(username='admin', password='111110')
# db.session.add(admin_user)
# db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True)
