# -*- coding: utf-8 -*-
"""
Created on Fri Jun 14 11:27:42 2024

@author: L340
"""

import pandas as pd
import numpy as np
from pvlib import location
from pvlib import tracking
from pvlib.bifacial.pvfactors import pvfactors_timeseries
from pvlib import temperature
from pvlib import pvsystem
import matplotlib.pyplot as plt
import warnings

# supressing shapely warnings that occur on import of pvfactors
warnings.filterwarnings(action='ignore', module='pvfactors')

# using Greensboro, NC for this example
lat, lon = 43.6119, 3.8772
tz = 'Etc/GMT-2'
times = pd.date_range('2023-06-21', '2023-06-22', freq='1min', tz=tz) #Summer solstice
#times = pd.date_range('2023-12-21', '2023-12-22', freq='1min', tz=tz) #Winter solstice

# create location object and get clearsky data
site_location = location.Location(lat, lon, tz=tz, name='Montpelier, FR')
cs = site_location.get_clearsky(times)

# get solar position data
solar_position = site_location.get_solarposition(times)

# set ground coverage ratio and max_angle to
# pull orientation data for a single-axis tracker
gcr = 0.35
max_phi = 60
orientation = tracking.singleaxis(solar_position['apparent_zenith'],
                                  solar_position['azimuth'],
                                  max_angle=max_phi,
                                  backtrack=True,
                                  gcr=gcr
                                  )

# set axis_azimuth, albedo, pvrow width and height, and use
# the pvfactors engine for both front and rear-side absorbed irradiance
axis_azimuth = 180
pvrow_height = 3
pvrow_width = 4
albedo = 0.2

########### FIXED TILT################

irrad = pvfactors_timeseries(
    solar_azimuth=solar_position['azimuth'],
    solar_zenith=solar_position['apparent_zenith'],
    surface_azimuth=180,  # south-facing array
    surface_tilt=20,
    axis_azimuth=90,  # 90 degrees off from surface_azimuth.  270 is ok too
    timestamps=times,
    dni=cs['dni'],
    dhi=cs['dhi'],
    gcr=gcr,
    pvrow_height=pvrow_height,
    pvrow_width=pvrow_width,
    albedo=albedo,
    n_pvrows=3,
    index_observed_pvrow=1
)

# turn into pandas DataFrame
irrad = pd.concat(irrad, axis=1)

effective_irrad_mono = irrad['total_abs_front']

# get cell temperature using the Faiman model
temp_cell = temperature.faiman(effective_irrad_mono, temp_air=25,
                               wind_speed=1)

# using the pvwatts_dc model and parameters detailed above,
# set pdc0 and return DC power for both bifacial and monofacial
pdc0 = 1
gamma_pdc = -0.0043
pdc_mono = pvsystem.pvwatts_dc(effective_irrad_mono,
                               temp_cell,
                               pdc0,
                               gamma_pdc=gamma_pdc
                               ).fillna(0)

###############SINGLE AXIS ###################

# explicitly simulate on pvarray with 3 rows, with sensor placed in middle row
# users may select different values depending on needs
irrad1 = pvfactors_timeseries(solar_position['azimuth'],
                             solar_position['apparent_zenith'],
                             orientation['surface_azimuth'],
                             orientation['surface_tilt'],
                             axis_azimuth,
                             cs.index,
                             cs['dni'],
                             cs['dhi'],
                             gcr,
                             pvrow_height,
                             pvrow_width,
                             albedo,
                             n_pvrows=3,
                             index_observed_pvrow=1
                             )

# turn into pandas DataFrame
irrad1 = pd.concat(irrad1, axis=1)

effective_irrad_mono1 = irrad1['total_abs_front']

# get cell temperature using the Faiman model
temp_cell1 = temperature.faiman(effective_irrad_mono1, temp_air=25,
                               wind_speed=1)

# using the pvwatts_dc model and parameters detailed above,
# set pdc0 and return DC power for both bifacial and monofacial
pdc0 = 1
gamma_pdc = -0.0043

pdc_mono1 = pvsystem.pvwatts_dc(effective_irrad_mono1,
                               temp_cell1,
                               pdc0,
                               gamma_pdc=gamma_pdc
                               ).fillna(0)

# Plotting the results
plt.figure(figsize=(14, 7))
plt.plot(pdc_mono, label='Fixed Tilt', color='blue')
plt.plot(pdc_mono1, label='Single Axis Tracker', color='red')
plt.xlabel('Time')
plt.ylabel('Power Output (kW)')
plt.title('Power Output Comparison: Fixed Tilt vs Single Axis Tracker')
plt.legend()
plt.grid(True)
plt.show()

# Calculate total power output over the day
total_power_fixed_tilt = pdc_mono.sum() / 60  # Convert from W-min to kWh
total_power_single_axis = pdc_mono1.sum() / 60  # Convert from W-min to kWh

print(f"Total power output over the day (Fixed Tilt): {total_power_fixed_tilt:.2f} kWh")
print(f"Total power output over the day (Single Axis Tracker): {total_power_single_axis:.2f} kWh")
