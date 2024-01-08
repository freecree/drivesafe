
class TimerService:
  def __init__(self):
    self.timers = {}
    print('In TimerService __init__()')
  
  def init_timer(self, driver_id):
    driver_timer = self.timers.get(driver_id)
    if (not driver_timer):
      self.timers[driver_id] = {'cams_count': 1}
    else:
      self.timers[driver_id]['cams_count'] += 1
    print('timers: ', self.timers)
  
  def stop_timer(self, driver_id):
    self.timers[driver_id]['cams_count'] -= 1
    print('STOP timers: ', self.timers)
    print('STOP timers driver_id: ', driver_id)
