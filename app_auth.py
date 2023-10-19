from flask import Flask, render_template, redirect, url_for, request, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os
import base64

import cv2
import os
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


# Set your credentials JSON file path
CREDENTIALS_JSON_FILE = 'distracted_creds.json'
FOLDER_ID = '11qHfwdlJBcRgeFS09qkNP36iO5-YN1V6'

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


video_folder = "static"

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
        thumbnail_link = file_info['thumbnailLink']

        list_files.append({"video_path": file['name'], "preview_image": thumbnail_link})

    return list_files

def get_all_vid_from_folders():
    folders = list_folders(FOLDER_ID)
    names_videos_dict = {}
    all_ids = []

    for folder in folders:
        folder_id = folder['folder_id']
        vids = list_videos(folder_id)
        all_ids.append({'name': folder['folder_name'], "driver_vids": vids})
    return all_ids

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
    return video_previews


def load_video(video_path):
    # Render the video page template with the video path
    return render_template('video_page.html', video_path=video_path)


def process_video(video_path):
    # Initialize the video capture from a webcam or video file
    cap = cv2.VideoCapture(video_path)  # You can change this to a video file path

    while True:
        ret, frame = cap.read()
        if not ret:
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

            pred = class_dict_new[proba.index(max(proba))]

            cv2.putText(frame, pred, (50, 50), font, 1, (0 ,0, 255), 1)
            cv2.putText(frame, str(max(proba)), (50, 100), font, 1, (0 ,0, 255), 1)

            # Process the frame here or do any other task
            # For this example, we'll convert the frame to JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                frame = buffer.tobytes()
                yield (b'--frame\r\n' 
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
                       b'Content-Type: text/plain\r\n\r\n' + pred.encode() + b'\r\n'
                       )
        except:
            pass

# Route for streaming video to the web browser
@app.route('/video_feed/<video_path>', methods=['GET',' POST'])
def video_feed(video_path):
    # video_path = request.form.get("name")
    video_name = f'videos/{video_path}'
    return render_template('video_page.html', video_name=video_path)

@app.route('/video_ml/<video_name>')
def video_ml(video_name):
    full_video_path = f'static/{video_name}'
    return Response(process_video(full_video_path),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/video')
def video():
    all_vid = get_all_vid_from_folders()
    folders = list_folders()
    # print(names_videos_dict)
    # drivers = list(set(list(names_videos_dict.values())))
    return render_template("index.html", folders=folders, driver_name='', all_vid=all_vid, videos=[])



@app.route('/video_driver/<id>')
def video_driver(id):
    # videos_with_previews = generate_video_previews()
    videos_with_previews = list_videos(id)
    folders = list_folders()
    
    for folder in folders:
        if folder['folder_id'] == id:
            name = folder['folder_name']
    return render_template("index.html",folders=folders, all_vid=[], driver_name=name, videos=videos_with_previews)




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

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    # Create and start a thread for capturing video
    # capture_thread = threading.Thread(target=capture_video)
    # capture_thread.start()
    app.run(debug=True)
