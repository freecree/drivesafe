from extensions import db
from models.driver import Driver
from models.distraction import Distraction
from collections import defaultdict

NORMAL_DRIVING_CLASS = 0
class_dict_ukr = {0 : "нормальне водіння",
              1 : "користування телефоном",
              2 : "користування телефоном",
              3 : "користування телефоном",
              4 : "користування телефоном",
              5 : "користування радіо",
              6 : "споживання напоїв",
              7 : "відволікання на речі позаду" }

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
  
  def group_distractions(distractions):
    grouped_distractions_dict = defaultdict(list)
    for distraction in distractions:
      distracted_class = distraction['distracted_class']
      grouped_distractions_dict[distracted_class].append(distraction)

    grouped_distractions = [
      {
        'distracted_class': distracted_class,
        'count': len(distractions),
        'description': class_dict_ukr[int(distracted_class)],
      }
      for distracted_class, distractions in grouped_distractions_dict.items()
    ]
    return grouped_distractions

