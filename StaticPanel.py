# -*- coding: utf-8 -*-
"""
Created on Wed Apr 17 00:41:59 2024

@author: L340
"""

import pvlib
import pandas as pd
import matplotlib.pyplot as plt

latitude = 43.6109
longitude = 3.8772
altitude = 27
timezone = 'Etc/GMT+2'

# Retrieve module and inverter specifications
sandia_modules = pvlib.pvsystem.retrieve_sam('SandiaMod')
sapm_inverters = pvlib.pvsystem.retrieve_sam('cecinverter')


module = sandia_modules['Canadian_Solar_CS5P_220M___2009_']

# Get weather data for Montpellier for a specific day
weather_tuple = pvlib.iotools.get_pvgis_hourly(latitude, longitude)
weather = weather_tuple[0]  # Extract the DataFrame from the tuple

# Extract required weather components
dni = weather['poa_sky_diffuse'] - weather['poa_direct']  # Calculate DNI from GHI and DHI
temp_air = weather['temp_air']

# Calculate solar position
solpos = pvlib.solarposition.get_solarposition(
    time=weather.index,
    latitude=latitude,
    longitude=longitude,
    altitude=altitude,
    temperature=temp_air,
)

# Calculate total irradiance on the panel
total_irradiance = pvlib.irradiance.get_total_irradiance(
    surface_tilt=latitude,  # Panel tilt angle = Latitude (perpendicular to sun)
    surface_azimuth=180,    # Panel azimuth (south-facing)
    solar_zenith=solpos['apparent_zenith'],
    solar_azimuth=solpos['azimuth'],
    dni=dni,
    ghi=weather['poa_sky_diffuse'],
    dhi=weather['poa_direct'],
    dni_extra=pvlib.irradiance.get_extra_radiation(weather.index),
    model='haydavies',
)

# Calculate cell temperature
cell_temperature = pvlib.temperature.sapm_cell(
    total_irradiance['poa_global'],
    temp_air,
    weather["wind_speed"],
    **pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_glass'],
)

# Use the correct key for 'Paco' to access the maximum AC power rating of the inverter
paco = sapm_inverters['iPower__SHO_5_2__240V_']

# Calculate DC power output
dc = pvlib.pvsystem.sapm(
    effective_irradiance=total_irradiance['poa_global'],
    temp_cell=cell_temperature,
    module=module,
)


# Calculate AC power output using pvlib.inverter.sandia()
ac = pvlib.inverter.sandia(
    v_dc=dc['v_mp'],    # Use 'v_mp' as the DC voltage
    p_dc=dc['p_mp'],    # Use 'p_mp' as the DC power output
    inverter=paco,         # Maximum AC power rating of the inverter
)

# Plot daily power generation
ac.plot()
plt.ylabel('Power (W)')
plt.show()
