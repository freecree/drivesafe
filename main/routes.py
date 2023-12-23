from main import bp
from flask import request, flash, render_template, redirect, url_for
from flask_login import login_required

from service.google_drive_service import get_drivers
from service.DriverService import DriverService, class_dict_ukr


@bp.route('/video', methods=['GET', 'POST'])
@login_required
def main():
  drivers = get_drivers()
  DriverService.add_drivers_if_not_exist(drivers)
  return render_template('index.html', drivers=drivers)


@bp.route('/report/<driver_folder>', methods=['GET',' POST'])
def report(driver_folder):
  driver = DriverService.get_driver_by_folder(driver_folder)
  driver_distractions = DriverService.get_distractions_by_id(driver.id)

  driver_distractions_list = [
    {
      'distracted_class': distraction.distracted_class,
      'date': distraction.date,
      'description': class_dict_ukr[int(distraction.distracted_class)],
    }
    for distraction in driver_distractions
  ]
  grouped_distractions = DriverService.group_distractions(driver_distractions_list)

  return render_template('report.html',
                      all_distractions=driver_distractions_list,
                      grouped_distractions=grouped_distractions,
                      driver_name=driver.name)