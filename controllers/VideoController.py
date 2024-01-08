import datetime
from service.DriverService import DriverService

class DriverVideoInfo:
  def __init__(self, video_name):
    self.start_time = datetime.datetime.now()
    self.videos = [video_name]

  def add_video(self, video_name):
    self.videos.append(video_name)

  def remove_video(self, video_name):
    self.videos.remove(video_name)

  def get_duration(self):
    duration = datetime.datetime.now() - self.start_time
    return duration.total_seconds()

  def get_video_amount(self):
    return len(self.videos)
  
  def is_video(self, video_name):
    return video_name in self.videos


class VideoController:
  def __init__(self):
    self.video_states = {}

  def init(self):
    self.video_states = {}

  def is_streaming(self, driver_folder, video_name):
    driver_info = self.video_states.get(driver_folder)
    if (driver_info):
      return driver_info.is_video(video_name)
    return False

  def start_video(self, driver_folder, video_path):
    driver_video = self.video_states.get(driver_folder)
    if (driver_video is None):
      self.video_states[driver_folder] = DriverVideoInfo(video_path)
    else:
      self.video_states[driver_folder].add_video(video_path)
    print('After start video: ', self.video_states)
  
  def stop_video(self, driver_folder, video_path):
    driver_videos = self.video_states.get(driver_folder)
    if (driver_videos):
      self.video_states[driver_folder].remove_video(video_path)
      if (driver_videos.get_video_amount() < 1):
        duration = driver_videos.get_duration()
        print ('Stop timer. Duration', duration)
        self.__delete_driver_info(driver_folder)
        self.__save_time_record(driver_folder, duration)


    print('Stop video: ', self.video_states)
    print(f'parameters: {driver_folder}, {video_path}')
  
  def __save_time_record(self, driver_folder, duration):
    DriverService.increase_driving_time_by_folder(driver_folder, duration)
    print('save')

  def __delete_driver_info(self, driver_folder):
    del self.video_states[driver_folder]
    print('deleted')