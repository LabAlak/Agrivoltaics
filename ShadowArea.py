# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 00:36:10 2024

@author: L340
"""

import numpy as np
import pandas as pd
import pvlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Location coordinates for Montpellier
latitude = 43.6109  # degrees
longitude = 3.8772  # degrees

# Date for computation
date = pd.Timestamp('2019-06-21', tz='Europe/Paris')
times = pd.date_range(start=date, end=date + pd.Timedelta(days=1), freq='H', tz='Europe/Paris')

# Solar position calculation
solar_position = pvlib.solarposition.get_solarposition(times, latitude, longitude)

# Define tilt angles in degrees
tilt_angles = [0, 30, 45, 60, 90]

# Panel dimensions
panel_height = 1  # in meters
panel_width = 1  # in meters
panel_elevation = 1  # panel height above the ground in meters

# Function to calculate shadow area
def compute_shadow_area(panel_height, panel_width, panel_elevation, tilt_angle, solar_position):
    shadow_areas = []
    for i in range(len(solar_position.index)):
        solar_altitude = solar_position['apparent_elevation'].iloc[i]
        
        if solar_altitude > 0:
            if tilt_angle == 0:
                # Panel is horizontal
                shadow_length = panel_elevation / np.tan(np.radians(solar_altitude))
                shadow_area = panel_width * shadow_length
            elif tilt_angle == 90:
                # Panel is vertical
                shadow_length = (panel_height + panel_elevation) / np.tan(np.radians(solar_altitude))
                shadow_area = shadow_length * panel_width
            else:
                # Panel is tilted
                effective_height = panel_elevation + (panel_height * np.sin(np.radians(tilt_angle)))
                shadow_length = effective_height / np.tan(np.radians(solar_altitude))
                shadow_area = shadow_length * panel_width
            shadow_areas.append(shadow_area)
        else:
            shadow_areas.append(0)
    return shadow_areas

# Calculate shadow areas and plot them
plt.figure(figsize=(14, 8))
average_shadow_areas = {}

for angle in tilt_angles:
    shadow_areas = compute_shadow_area(panel_height, panel_width, panel_elevation, angle, solar_position)
    average_shadow_areas[angle] = np.mean(shadow_areas)
    plt.plot(times, shadow_areas, label=f'Tilt angle: {angle}°')

# Formatting the x-axis
#plt.gca().xaxis.set_major_locator(mdates.HourLocator(interval=3))
#plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%I %p'))

plt.xlabel('Time')
plt.ylabel('Shadow Area (square meters)')
plt.title('Shadow Area under PV Panel')
plt.legend()
plt.grid(True)
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# Print average shadow areas
for angle in tilt_angles:
    print(f"Average shadow area for tilt angle {angle}°: {average_shadow_areas[angle]:.2f} square meters")

