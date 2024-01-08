from extensions import db
from models.driver import Driver
from models.distraction import Distraction

NORMAL_DRIVING_CLASS = 0
class_dict_ukr = {0 : "нормальне водіння",
              1 : "користування телефоном",
              2 : "користування радіо",
              3 : "споживання напоїв",
              4 : "відволікання на речі позаду" }

class DriverService:

  def add_drivers_if_not_exist(drivers_to_add):
    existing_driver_folders = [driver.folder_id for driver in Driver.query.all()]
    for driver in drivers_to_add:
      if (driver['folder_id'] not in existing_driver_folders):
        new_driver = Driver(folder_id=driver['folder_id'], name=driver['name'])
        db.session.add(new_driver)
    db.session.commit()

  def get_driver_by_folder(driver_folder):
    return db.session.execute(db.select(Driver).where(Driver.folder_id == driver_folder)).scalar_one()

  def get_distractions_by_id(id):
    return db.session.execute(db.select(Distraction)
      .join(Driver)
      .filter(Driver.id == id)
      .filter(Distraction.distracted_class != NORMAL_DRIVING_CLASS)
    ).scalars().all()
  
  def increase_driving_time_by_folder(driver_folder, time_duration):
    driver = DriverService.get_driver_by_folder(driver_folder)

    driver.driving_time += time_duration
    db.session.commit()

    print('dr time increment')
