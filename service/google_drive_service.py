import time
from googleapiclient.discovery import build
from google.oauth2 import service_account

CREDENTIALS_JSON_FILE = 'distracted_creds.json'
FOLDER_ID = '1fMCWStl4xy12clcR9pNfXEKP-y9yPgFX'

creds = service_account.Credentials.from_service_account_file(CREDENTIALS_JSON_FILE, scopes=['https://www.googleapis.com/auth/drive'])
service = build('drive', 'v3', credentials=creds)

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


def get_drivers(): 
  # time.sleep(0.5)
  folders = list_folders(FOLDER_ID)
  drivers = []
  for folder in folders:
    folder_id = folder['folder_id']
    driver_videos = list_videos(folder_id)
    drivers.append({'name': folder['folder_name'], 'folder_id': folder_id, 'videos': driver_videos})
  # print('videos[0]: ', drivers[0]['videos'][0])
  return drivers